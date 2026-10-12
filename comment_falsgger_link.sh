#!/bin/bash

FILE="/usr/lib/python3/site-packages/flasgger/ui3/templates/flasgger/head.html"

TARGET='<link href="https://fonts.googleapis.com/css?family=Open+Sans:400,700|Source+Code+Pro:300,600|Titillium+Web:400,600,700" rel="stylesheet">'

if [ ! -f "$FILE" ]; then
    echo "[ERROR] Файл не найден: $FILE"
    exit 1
fi

if grep -Fq "<!-- $TARGET -->" "$FILE"; then
    echo "[INFO] Строка уже закомментирована."
    exit 0
fi

if ! grep -Fq "$TARGET" "$FILE"; then
    echo "[ERROR] Целевая строка не найдена."
    exit 1
fi

sed -i "s|$TARGET|<!-- $TARGET -->|" "$FILE"

echo "[OK] Строка успешно закомментирована."