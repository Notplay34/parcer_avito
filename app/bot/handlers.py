"""Telegram bot command handlers."""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from app.services import ensure_user, add_search, list_user_searches, delete_search

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if not message.from_user:
        return
    ensure_user(message.from_user.id)
    await message.answer(
        "Привет! Я бот мониторинга объявлений Avito.\n\n"
        "Добавить поиск: /add_search\n"
        "Мои поиски: /my_searches\n"
        "Удалить поиск: /delete_search <номер>\n\n"
        "Скопируйте ссылку с Avito: откройте Avito в браузере (телефон или компьютер), "
        "настройте фильтры и скопируйте ссылку из адресной строки.\n\n"
        "‼️ Обязательно укажите максимальную цену в фильтрах Avito. "
        "Если макс. цена не важна — укажите любую большую сумму, например 100000000. "
        "Без этого ссылка не будет принята."
    )


@router.message(Command("add_search"))
async def cmd_add_search(message: Message) -> None:
    if not message.from_user:
        return
    # /add_search <url> or /add_search <url> <name>
    text = (message.text or "").strip()
    parts = text.split(maxsplit=2)  # /add_search url [name]
    if len(parts) >= 2 and parts[1].startswith("http"):
        url = parts[1].strip()
        name = (parts[2].strip()[:200]) if len(parts) > 2 else "Поиск"
        success, msg, _ = add_search(message.from_user.id, url, name)
        await message.answer(msg)
        return
    await message.answer(
        "Скопируйте ссылку с вашим поиском Avito.\n\n"
        "Откройте Avito в браузере (телефон или компьютер), настройте нужные фильтры "
        "и скопируйте ссылку из адресной строки. Отправьте её сюда.\n\n"
        "‼️ Обязательно укажите максимальную цену в фильтрах Avito. "
        "Если максимальная цена не важна — укажите любую большую сумму, например 100000000. "
        "Без этого ссылка не будет принята."
    )


@router.message(Command("my_searches"))
async def cmd_my_searches(message: Message) -> None:
    if not message.from_user:
        return
    searches = list_user_searches(message.from_user.id)
    if not searches:
        await message.answer("У вас пока нет сохранённых поисков. Добавьте: /add_search")
        return
    lines = []
    for i, s in enumerate(searches, 1):
        lines.append(f"{i}. {s['name']}\n   {s['url']}")
    await message.answer(
        "Ваши поиски:\n\n" + "\n\n".join(lines) + "\n\n"
        "Удалить: /delete_search <номер> (например /delete_search 1)"
    )


@router.message(Command("delete_search"))
async def cmd_delete_search(message: Message) -> None:
    if not message.from_user:
        return
    text = (message.text or "").strip().split(maxsplit=1)
    if len(text) < 2:
        await message.answer(
            "Укажите номер поиска для удаления.\n"
            "Список поисков: /my_searches\n"
            "Пример: /delete_search 1"
        )
        return
    try:
        num = int(text[1].strip())
    except ValueError:
        await message.answer("Укажите номер цифрой, например: /delete_search 1")
        return
    searches = list_user_searches(message.from_user.id)
    if num < 1 or num > len(searches):
        await message.answer(f"Нет поиска с номером {num}. Ваши номера: 1–{len(searches)}. Список: /my_searches")
        return
    search_id = searches[num - 1]["id"]
    ok, msg = delete_search(message.from_user.id, search_id)
    await message.answer(msg)


@router.message(F.text, F.text.startswith("http"))
async def handle_search_link(message: Message) -> None:
    if not message.from_user:
        return
    url = (message.text or "").strip()
    if not url:
        return
    name = "Поиск"
    if "\n" in url:
        parts = url.split("\n", 1)
        url = parts[0].strip()
        if parts[1].strip():
            name = parts[1].strip()[:200]
    success, msg, _ = add_search(message.from_user.id, url, name)
    await message.answer(msg)
