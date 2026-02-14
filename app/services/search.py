"""Search and user DB operations."""
import base64
import json
import logging
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from sqlalchemy import func
from app.database import get_db
from app.models import User, Search, SeenAd

logger = logging.getLogger(__name__)

AVITO_DOMAINS = ("avito.ru", "www.avito.ru", "m.avito.ru")


def _extract_max_price_from_f_param(f_value: str) -> float | None:
    """Извлечь макс. цену из параметра f (Avito кодирует фильтры в base64). Пример: ...XeyJmcm9tIjowLCJ0byI6MTAwMDAwMH0 -> to=1000000."""
    if not f_value:
        return None
    # Ищем base64-подобную подстроку, начинающуюся с eyJ (base64 для "{")
    match = re.search(r"eyJ[A-Za-z0-9+/=_-]+", f_value.replace("~", ""))
    if not match:
        return None
    b64 = match.group(0)
    # Добить padding при необходимости
    pad = 4 - len(b64) % 4
    if pad != 4:
        b64 += "=" * pad
    try:
        data = json.loads(base64.b64decode(b64).decode("utf-8"))
        if isinstance(data, dict) and "to" in data:
            return float(data["to"])
    except (ValueError, TypeError, UnicodeDecodeError):
        pass
    return None


def _validate_avito_search_url(url: str) -> tuple[bool, str | None, float | None]:
    """Check URL is Avito search and extract maxPrice. Returns (ok, error_message, max_price)."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Некорректная ссылка.", None
    if parsed.scheme not in ("http", "https"):
        return False, "Ссылка должна начинаться с http или https.", None
    netloc = (parsed.netloc or "").lower().replace("www.", "")
    if not any(netloc == d or netloc.endswith("." + d) for d in AVITO_DOMAINS):
        return False, "Поддерживаются только ссылки на поиск Avito.", None
    qs = parse_qs(parsed.query)
    price_val = None
    # 1) Явный параметр maxPrice / max_price
    max_price = qs.get("maxPrice") or qs.get("max_price")
    if max_price and len(max_price) >= 1:
        try:
            price_val = float(max_price[0].replace(" ", "").replace(",", "."))
        except (ValueError, TypeError):
            pass
    # 2) Фильтр в параметре f (формат Avito с кодированными фильтрами)
    if price_val is None and "f" in qs and qs["f"]:
        price_val = _extract_max_price_from_f_param(qs["f"][0])
    if price_val is None:
        return False, "В ссылке нет максимальной цены. На Avito в фильтрах укажите макс. цену (если не важна — например 100000000), обновите страницу и скопируйте ссылку заново. Либо добавьте в конец ссылки: &maxPrice=100000000", None
    if price_val <= 0:
        return False, "Максимальная цена должна быть больше 0.", None
    return True, None, price_val


def ensure_user(telegram_id: int) -> User:
    """Get or create user by telegram_id."""
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id)
            db.add(user)
            db.flush()
        return user


def add_search(telegram_id: int, search_url: str, search_name: str) -> tuple[bool, str, int | None]:
    """
    Validate URL, check limits, add search. Returns (success, message, search_id or None).
    """
    ok, err, max_price = _validate_avito_search_url(search_url)
    if not ok:
        return False, err or "Ошибка валидации.", None

    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id)
            db.add(user)
            db.flush()
        from config import settings
        count = db.query(func.count(Search.id)).scalar()
        if count >= settings.max_searches:
            return False, f"Достигнут лимит поисков на сервере ({settings.max_searches}). Попробуйте позже.", None
        search = Search(
            user_id=user.id,
            search_url=search_url.strip(),
            max_price=max_price,
            name=search_name or "Поиск",
            is_active=True,
        )
        db.add(search)
        db.flush()
        search_id = search.id
    return True, f"Поиск «{search_name or 'Поиск'}» добавлен. Ожидайте уведомления о новых объявлениях.", search_id


def get_active_searches(limit: int = 20) -> list[dict]:
    """Return list of active, non-blocked searches. Closes DB session before returning."""
    from config import settings
    from datetime import datetime as dt
    now = dt.utcnow()
    with get_db() as db:
        rows = (
            db.query(Search.id, User.telegram_id, Search.search_url, Search.name, Search.last_check_at)
            .join(User, Search.user_id == User.id)
            .filter(Search.is_active == True)
            .filter((Search.blocked_until == None) | (Search.blocked_until <= now))
            .limit(limit)
            .all()
        )
        return [
            {
                "search_id": r.id,
                "telegram_id": r.telegram_id,
                "search_url": r.search_url,
                "search_name": r.name,
                "last_check_at": r.last_check_at,
            }
            for r in rows
        ]


def get_seen_ad_ids(search_id: int) -> set[str]:
    with get_db() as db:
        rows = db.query(SeenAd.avito_ad_id).filter(SeenAd.search_id == search_id).all()
        return {r[0] for r in rows}


def mark_ad_seen(search_id: int, avito_ad_id: str) -> None:
    with get_db() as db:
        existing = db.query(SeenAd).filter(
            SeenAd.search_id == search_id,
            SeenAd.avito_ad_id == avito_ad_id,
        ).first()
        if not existing:
            db.add(SeenAd(search_id=search_id, avito_ad_id=avito_ad_id))


def update_last_check(search_id: int) -> None:
    with get_db() as db:
        s = db.query(Search).filter(Search.id == search_id).first()
        if s:
            s.last_check_at = datetime.utcnow()


def set_search_blocked(search_id: int, blocked_until: datetime) -> None:
    with get_db() as db:
        s = db.query(Search).filter(Search.id == search_id).first()
        if s:
            s.blocked_until = blocked_until
