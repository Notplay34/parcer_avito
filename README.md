# Avito Monitor MVP

Сервис мониторинга объявлений Avito с уведомлениями в Telegram.

## Возможности

- Telegram-бот: команды `/start`, `/add_search`
- Добавление поиска по ссылке Avito (обязателен параметр `maxPrice` в URL)
- Фоновая проверка каждые 60 секунд
- Уведомления о новых объявлениях (название, цена, ссылка)
- При 403/429 поиск временно отключается на 10 минут
- Лимит: не более 20 поисков на сервер

## Технологии

- Python 3.11
- FastAPI (health-check API)
- aiogram (Telegram bot)
- PostgreSQL + SQLAlchemy
- APScheduler
- requests + BeautifulSoup (парсинг HTML/JSON)

## Структура проекта

```
parcer_avito/
├── app/
│   ├── __init__.py
│   ├── api.py          # FastAPI, /health
│   ├── main.py         # Точка входа: бот + планировщик
│   ├── bot/
│   │   ├── handlers.py # /start, /add_search, приём ссылки
│   ├── database.py     # Сессия БД, init_db
│   ├── models.py       # User, Search, SeenAd
│   ├── monitor.py      # Фоновая проверка и уведомления
│   ├── parser/
│   │   └── avito.py    # HTTP + парсинг страницы поиска
│   └── services/
│       └── search.py   # CRUD поисков и пользователей
├── alembic/            # Миграции (опционально)
├── config.py           # Настройки из .env
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Запуск

### Локально

1. Создайте виртуальное окружение и установите зависимости:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

2. Создайте `.env` по примеру:

   ```env
   BOT_TOKEN=your_telegram_bot_token
   DATABASE_URL=postgresql://user:password@localhost:5432/avito_monitor
   CHECK_INTERVAL=60
   MAX_SEARCHES=20
   BLOCK_DURATION_SECONDS=600
   ```

3. Запустите PostgreSQL (или используйте `docker-compose up -d db`).

4. Запуск бота и планировщика:

   ```bash
   python -m app.main
   ```

5. (Опционально) Отдельно API для health-check:

   ```bash
   uvicorn app.api:app --reload --port 8000
   ```

### Docker

```bash
# Сборка и запуск всех сервисов
docker-compose up -d

# Бот + планировщик — сервис app
# API — сервис api (порт 8000)
# БД — сервис db
```

Переменные окружения задаются в `.env`; для БД в compose подставлен `DATABASE_URL=postgresql://avito:avito@db:5432/avito_monitor`.

## Использование бота

1. Найти бота в Telegram и нажать **Start** (`/start`).
2. Добавить поиск: `/add_search` и отправить ссылку на поиск Avito с `maxPrice`, например:
   `https://www.avito.ru/rossiya?q=iphone&maxPrice=50000`
3. Можно одной командой: `/add_search https://... Название поиска`.

Бот будет проверять результаты раз в `CHECK_INTERVAL` секунд и присылать новые объявления.

## Ограничения MVP

- Не более 1 запроса в 60 секунд на один поиск
- Не более 20 поисков на сервер (`MAX_SEARCHES`)
- При HTTP 403 или 429 поиск блокируется на 10 минут (`BLOCK_DURATION_SECONDS`)
- Логи: все ошибки и факты блокировок пишутся в stdout

## Ревью кода (архитектура и логика)

- **БД:** `get_active_searches` возвращает список и закрывает сессию до HTTP-запросов — сессия не висит открытой.
- **Бот:** во всех хендлерах проверяется `message.from_user` (защита при вызове не из лички).
- **Лимит:** сообщение о лимите использует `MAX_SEARCHES` из конфига.
- **Мониторинг:** при 403/429 поиск блокируется на 10 минут, в лог пишутся коды и счётчики блокировок.
