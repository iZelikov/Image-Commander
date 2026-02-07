#!/bin/bash

set -e

source .env

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backups/${POSTGRES_DB}_backup_${TIMESTAMP}.sql.gz"

echo "Создание бэкапа базы данных ${POSTGRES_DB}..."

docker-compose exec -T postgres \
  pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | \
  gzip > "${BACKUP_FILE}"

echo "Бэкап создан: ${BACKUP_FILE}"

# Очистка старых бэкапов (храним 7 дней)
find backups -name "*.sql.gz" -mtime +7 -delete

echo "Очистка старых бэкапов завершена"