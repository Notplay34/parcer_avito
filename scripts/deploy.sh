#!/bin/bash
# Запуск на сервере: из корня проекта выполнить bash scripts/deploy.sh
# Поддерживает и "docker compose" (плагин), и "docker-compose" (standalone)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# На сервере часто стоит только docker-compose (без плагина), путь может быть не в PATH
if command -v docker-compose >/dev/null 2>&1; then
  DCO="docker-compose"
elif [ -x /usr/local/bin/docker-compose ]; then
  DCO="/usr/local/bin/docker-compose"
else
  DCO="docker compose"
fi
echo "=== Avito Monitor: deploy ==="
$DCO down --remove-orphans 2>/dev/null || true
$DCO build
$DCO up -d
echo "=== Containers ==="
$DCO ps
echo "=== Logs (Ctrl+C to exit) ==="
$DCO logs -f app
