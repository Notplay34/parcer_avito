"""Background job: check Avito searches and send Telegram notifications."""
import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot
from config import settings
from app.parser.avito import fetch_search_page, parse_search_page
from app.services import (
    get_active_searches,
    get_seen_ad_ids,
    mark_ad_seen,
    update_last_check,
    set_search_blocked,
)

logger = logging.getLogger(__name__)

BLOCK_DURATION = timedelta(seconds=settings.block_duration_seconds)
block_count_403 = 0
block_count_429 = 0


async def _run_check_async(bot: Bot) -> None:
    """Async implementation of check loop."""
    global block_count_403, block_count_429
    for search in get_active_searches(limit=settings.max_searches):
        search_id = search["search_id"]
        telegram_id = search["telegram_id"]
        url = search["search_url"]
        name = search["search_name"]
        status, html, err = fetch_search_page(url)
        if err:
            logger.warning("Search %s fetch error: %s", search_id, err)
            continue
        if status == 403:
            block_count_403 += 1
            logger.warning(
                "HTTP 403 for search %s; blocking for %s s (total 403: %s)",
                search_id, settings.block_duration_seconds, block_count_403,
            )
            set_search_blocked(search_id, datetime.utcnow() + BLOCK_DURATION)
            continue
        if status == 429:
            block_count_429 += 1
            logger.warning(
                "HTTP 429 for search %s; blocking for %s s (total 429: %s)",
                search_id, settings.block_duration_seconds, block_count_429,
            )
            set_search_blocked(search_id, datetime.utcnow() + BLOCK_DURATION)
            continue
        logger.info("Search %s HTTP %s", search_id, status)
        if status != 200 or not html:
            continue
        try:
            ads = parse_search_page(html)
        except Exception as e:
            logger.exception("Parse error for search %s: %s", search_id, e)
            update_last_check(search_id)
            continue
        seen = get_seen_ad_ids(search_id)
        for ad in ads:
            if ad.id in seen:
                continue
            mark_ad_seen(search_id, ad.id)
            text = (
                f"🆕 Новое объявление ({name})\n\n"
                f"{ad.title}\n"
                f"Цена: {ad.price}\n"
                f"{ad.url}\n\n"
                f"Обнаружено: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"
            )
            try:
                await bot.send_message(telegram_id, text, disable_web_page_preview=True)
            except Exception as e:
                logger.exception("Send notification failed: %s", e)
        update_last_check(search_id)


def run_check(bot: Bot) -> None:
    """Fetch active searches, parse pages, notify. Called every CHECK_INTERVAL (sync for APScheduler)."""
    try:
        asyncio.run(_run_check_async(bot))
    except Exception as e:
        logger.exception("Monitor job failed: %s", e)
