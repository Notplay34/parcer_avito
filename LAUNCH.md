# Запуск по шагам

## Шаг 1. Файл .env

Файл `.env` уже создан в корне проекта с вашим BOT_TOKEN.  
Осталось настроить **DATABASE_URL** (шаг 2).

---

## Шаг 2. Откуда взять DATABASE_URL

**DATABASE_URL** — строка подключения к PostgreSQL. Варианты:

### Вариант A. PostgreSQL через Docker (проще всего)

Поднять только базу одной командой:

```powershell
docker run -d --name avito-pg -p 5432:5432 -e POSTGRES_USER=avito -e POSTGRES_PASSWORD=avito -e POSTGRES_DB=avito_monitor postgres:16-alpine
```

Тогда в `.env` уже указано верно:

```
DATABASE_URL=postgresql://avito:avito@localhost:5432/avito_monitor
```

Менять ничего не нужно.

### Вариант B. Уже установленный PostgreSQL на компьютере

Если PostgreSQL уже стоит и запущен:

1. Создайте базу и пользователя (в psql или pgAdmin):
   - база: `avito_monitor`
   - пользователь: `avito`
   - пароль: `avito` (или свой)

2. В `.env` укажите (подставьте свой пароль и хост при необходимости):

```
DATABASE_URL=postgresql://avito:ваш_пароль@localhost:5432/avito_monitor
```

Формат: `postgresql://USER:PASSWORD@HOST:PORT/DATABASE`

### Вариант C. Всё через docker-compose

Тогда базу поднимает compose, и приложение само подставит URL к контейнеру `db`. Запуск — см. шаг 4 (Docker).

---

## Шаг 3. Запуск локально (без Docker для приложения)

1. Установить зависимости (один раз):

```powershell
cd c:\dev\parcer_avito
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Убедиться, что PostgreSQL запущен (вариант A или B выше) и в `.env` правильный **DATABASE_URL**.

3. Запустить бота и планировщик:

```powershell
python -m app.main
```

В консоли должно появиться что-то вроде:  
`Scheduler: check every 60 s` и старт поллинга бота.

4. Найти бота в Telegram и нажать **Start** (`/start`), затем добавить поиск через `/add_search` и ссылку.

---

## Шаг 4. Запуск через Docker (бот + API + БД)

Если хотите поднять всё одной командой (включая БД):

```powershell
cd c:\dev\parcer_avito
docker-compose up -d
```

- Бот и проверки объявлений — сервис **app**
- Health API — **http://localhost:8000/health**
- БД — сервис **db** (DATABASE_URL для app и api уже прописан в compose)

---

## Кратко: откуда DATABASE_URL

| Как поднимаете БД | DATABASE_URL |
|-------------------|--------------|
| Docker: `docker run ... postgres:16-alpine` (команда из варианта A) | `postgresql://avito:avito@localhost:5432/avito_monitor` (уже в .env) |
| Свой PostgreSQL на машине | `postgresql://USER:PASSWORD@localhost:5432/avito_monitor` |
| Только `docker-compose up` | Прописан в docker-compose, в .env для локального запуска можно оставить тот же с localhost |

Если что-то пойдёт не так — пришлите текст ошибки из консоли.
