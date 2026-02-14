#!/bin/bash
# НА СЕРВЕРЕ: из корня проекта — bash scripts/clean_server.sh
# Останавливает контейнеры и volumes этого проекта. Другие проекты не трогает.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if command -v docker-compose >/dev/null 2>&1; then
  DCO="docker-compose"
elif [ -x /usr/local/bin/docker-compose ]; then
  DCO="/usr/local/bin/docker-compose"
else
  DCO="docker compose"
fi
echo "=== Остановка контейнеров avito-monitor ==="
$DCO down -v --remove-orphans 2>/dev/null || true
echo "=== Удаление образов проекта ==="
$DCO down --rmi local 2>/dev/null || true
echo "Готово. Папку с кодом можно удалить вручную: rm -rf /path/to/avito-monitor"
