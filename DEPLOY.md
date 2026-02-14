# Развёртывание на сервере для теста

## Сервер

- **Домен:** avitoparc.duckdns.org  
- **IP:** 194.87.103.157  

Подключение по SSH: `ssh user@avitoparc.duckdns.org` (или `ssh user@194.87.103.157`).  
Если откроете порт 8000 для API — проверка: `http://avitoparc.duckdns.org:8000/health`

---

## Очистка сервера и деплой с нуля (по шагам)

Если на сервере уже что-то крутится и нужно всё убрать и развернуть заново:

### Шаг 1. Подключиться к серверу

```bash
ssh user@avitoparc.duckdns.org
```

### Шаг 2. Остановить и удалить старое (если было развёрнуто через Docker)

Если проект уже лежит в папке (например `~/avito-monitor`):

```bash
cd ~/avito-monitor
bash scripts/clean_server.sh
```

Либо вручную:

```bash
cd ~/avito-monitor   # или где лежит проект
docker compose down -v --remove-orphans
docker compose down --rmi local
```

Удалить саму папку с кодом (чтобы положить свежую):

```bash
cd ~
rm -rf avito-monitor
```

### Шаг 3. Убедиться, что Docker установлен

```bash
docker --version
docker compose version
```

Если нет — установить (см. «Вариант 1» ниже).

### Шаг 4. Скопировать проект с ПК на сервер

**На своём ПК** (PowerShell или WSL, подставьте свой user и путь):

```bash
scp -r c:\dev\parcer_avito user@avitoparc.duckdns.org:~/avito-monitor
```

### Шаг 5. На сервере: создать .env

```bash
ssh user@avitoparc.duckdns.org
cd ~/avito-monitor
nano .env
```

Вставить (подставить свой BOT_TOKEN):

```env
BOT_TOKEN=ваш_токен_от_BotFather
DATABASE_URL=postgresql://avito:avito@db:5432/avito_monitor
CHECK_INTERVAL=60
MAX_SEARCHES=20
BLOCK_DURATION_SECONDS=600
```

Сохранить: Ctrl+O, Enter, Ctrl+X.

### Шаг 6. Запустить деплой

```bash
cd ~/avito-monitor
chmod +x scripts/*.sh
bash scripts/deploy.sh
```

Скрипт соберёт образы, поднимет контейнеры и покажет логи. Выйти из логов: Ctrl+C (контейнеры продолжат работать).

### Шаг 7. Проверить в Telegram

Найти бота, отправить `/start`, затем `/add_search` и ссылку на поиск Avito с параметром `maxPrice`.

---

## Что нужно на сервере

- **Docker** и **Docker Compose** (проще всего — всё в контейнерах)  
  **или**
- **Python 3.11**, **PostgreSQL** и **git**

Ниже два варианта: через Docker (рекомендуется) и без Docker.

---

## Вариант 1: Развёртывание через Docker (рекомендуется)

### 1. Установить Docker и Docker Compose на сервер

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable docker --now
sudo usermod -aG docker $USER
# выйти и зайти по SSH заново, чтобы группа docker применилась
```

### 2. Скопировать проект на сервер

На **своём компьютере** (из папки проекта):

```bash
# если есть git на сервере — так:
scp -r c:\dev\parcer_avito user@IP_СЕРВЕРА:/home/user/avito-monitor

# или архивом:
# tar -czvf avito-monitor.tar.gz parcer_avito/
# scp avito-monitor.tar.gz user@IP_СЕРВЕРА:/home/user/
```

На **сервере** (если копировали архив):

```bash
cd /home/user
tar -xzvf avito-monitor.tar.gz
cd parcer_avito   # или как у вас называется папка
```

### 3. Создать .env на сервере

На сервере в папке проекта:

```bash
nano .env
```

Вставить (подставьте свой BOT_TOKEN и при необходимости свой пароль БД):

```env
BOT_TOKEN=ваш_токен_от_BotFather
DATABASE_URL=postgresql://avito:avito@db:5432/avito_monitor
CHECK_INTERVAL=60
MAX_SEARCHES=20
BLOCK_DURATION_SECONDS=600
```

Сохранить (Ctrl+O, Enter, Ctrl+X в nano).

Важно: при запуске через `docker-compose` хост БД — это имя сервиса `db`, поэтому в DATABASE_URL указано `@db:5432`.

### 4. Запустить

```bash
cd /home/user/avito-monitor   # или ваш путь к parcer_avito
docker compose up -d
```

Проверить, что контейнеры работают:

```bash
docker compose ps
docker compose logs -f app
```

Бот должен писать логи; в Telegram можно отправить `/start`.

### 5. Остановить / перезапустить

```bash
docker compose down
docker compose up -d
```

---

## Вариант 2: Без Docker (Python + PostgreSQL на сервере)

### 1. Установить на сервер

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-client
```

### 2. Создать базу и пользователя PostgreSQL

```bash
sudo -u postgres psql -c "CREATE USER avito WITH PASSWORD 'avito';"
sudo -u postgres psql -c "CREATE DATABASE avito_monitor OWNER avito;"
```

### 3. Скопировать проект на сервер

(Как в варианте 1 — через scp или git.)

### 4. Создать .env

В папке проекта на сервере:

```env
BOT_TOKEN=ваш_токен_от_BotFather
DATABASE_URL=postgresql://avito:avito@localhost:5432/avito_monitor
CHECK_INTERVAL=60
MAX_SEARCHES=20
BLOCK_DURATION_SECONDS=600
```

### 5. Запустить приложение

```bash
cd /путь/к/parcer_avito
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

Чтобы бот работал после закрытия SSH, запускайте в **screen** или **tmux**:

```bash
screen -S avito
python -m app.main
# Отключиться: Ctrl+A, затем D
# Вернуться: screen -r avito
```

Или настроить systemd (см. ниже).

---

## Запуск как сервис (чтобы переживал перезагрузку)

Если развернули **без Docker** и хотите, чтобы бот стартовал после перезагрузки сервера:

### 1. Создать unit-файл

```bash
sudo nano /etc/systemd/system/avito-bot.service
```

Содержимое (подставьте свои пути и пользователя):

```ini
[Unit]
Description=Avito Monitor Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/avito-monitor
Environment="PATH=/home/ubuntu/avito-monitor/.venv/bin"
ExecStart=/home/ubuntu/avito-monitor/.venv/bin/python -m app.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Включить и запустить

```bash
sudo systemctl daemon-reload
sudo systemctl enable avito-bot
sudo systemctl start avito-bot
sudo systemctl status avito-bot
```

Логи: `journalctl -u avito-bot -f`

---

## Краткий чеклист для теста на сервере

| Шаг | Действие |
|-----|----------|
| 1 | Установить Docker (или Python 3.11 + PostgreSQL) |
| 2 | Скопировать проект на сервер |
| 3 | В папке проекта создать `.env` с BOT_TOKEN и DATABASE_URL |
| 4 | Запустить: `docker compose up -d` или `python -m app.main` |
| 5 | В Telegram написать боту `/start` и добавить поиск через `/add_search` + ссылку |

Если при развёртывании появится ошибка — пришлите вывод команды (например, `docker compose logs app` или текст из консоли при запуске `python -m app.main`).
