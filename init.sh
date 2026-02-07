#!/bin/bash

echo "Инициализация проекта Image Commander..."

# Создание необходимых директорий
mkdir -p \
    images \
    backups \
    logs/app \
    logs/nginx \
    logs/postgresql \
    logs/backup

# Создание .env файла если его нет
if [ ! -f .env ]; then
    cat > .env << EOF
# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=image_commander
POSTGRES_USER=username
POSTGRES_PASSWORD=$(openssl rand -base64 32)

EOF
    echo ".env файл создан с случайным паролем"
fi

# Установка прав
chmod 755 images backups logs
chmod 600 .env

# Создание файлов для бэкапов если их нет
if [ ! -f backup/backup.sh ]; then
    mkdir -p backup
    # Сюда нужно скопировать файлы из шагов выше
    echo "Скопируйте файлы бэкапа в папку backup/"
fi

echo "Инициализация завершена!"
echo "Запустите: docker-compose up --build"