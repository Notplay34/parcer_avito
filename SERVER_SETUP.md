# Настройка сервера (Debian / RUVDS)

Если при копировании проекта с Windows скрипты падают с ошибками вроде `\r` или `invalid option`, или пакет `docker-compose-plugin` не найден — сделайте по шагам ниже.

---

## 1. Исправить переводы строк в скриптах (CRLF → LF)

На сервере в папке проекта выполните **один раз**:

```bash
cd ~/avito-monitor
sed -i 's/\r$//' scripts/*.sh
```

После этого `bash scripts/deploy.sh` не должен ругаться на `\r`.

---

## 2. Установить Docker на Debian (Bullseye и др.)

Пакет `docker-compose-plugin` в стандартных репозиториях Debian может отсутствовать. Ставим **docker.io** и отдельно **docker-compose**:

```bash
apt update
apt install -y docker.io
systemctl enable docker --now
```

Проверка: `docker run hello-world` (должен вывести приветствие и выйти).

Установка **docker-compose** (standalone):

```bash
apt install -y curl
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

Либо из пакетов (если есть в репозитории):

```bash
apt install -y docker-compose
```

Если установился — проверьте: `docker-compose --version`.

---

## 3. Запуск деплоя

```bash
cd ~/avito-monitor
sed -i 's/\r$//' scripts/*.sh
chmod +x scripts/*.sh
bash scripts/deploy.sh
```

Скрипт сам выберет `docker compose` или `docker-compose`, в зависимости от того, что установлено.
