#!/bin/bash
# Скрипт для добавления timestamp к статическим файлам
# Запускается из корня проекта

echo "Updating static file versions..."

# Генерируем timestamp
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# Копируем исходный файл
cp front/index.html front/index.html.bak

# Используем sed для обновления ссылок
# Убираем предыдущие версионные параметры и добавляем новый
sed -i.bak -E "s/(href=\"[^\"]*\.css)(\?v=[^\"]*)?(\")/\1?v=$TIMESTAMP\3/g; s/(src=\"[^\"]*\.js)(\?v=[^\"]*)?(\")/\1?v=$TIMESTAMP\3/g" front/index.html

# Удаляем временный файл
rm -f front/index.html.bak

echo "Version updated to: $TIMESTAMP"