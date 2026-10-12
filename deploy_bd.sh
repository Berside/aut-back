#!/bin/bash
set -e
export PYTHONDONTWRITEBYTECODE=1
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
BIN_DIR="$SCRIPT_DIR/.venv/bin"
CONFIG_FILE="$SCRIPT_DIR/src//config/config.json"
DB_NAME="asutg"
DB_TEST_NAME="asutg_test"

# ---------------------------------------------------------------------------
# Автоподстановка пароля для psql
#
# Приоритет:
#   1) Если уже настроен ~/.pgpass — ничего не делаем, psql возьмёт пароль
#      оттуда сам.
#   2) Иначе, если задана переменная окружения DB_PASSWORD — используем её
#      через PGPASSWORD.
#   3) Иначе — предупреждаем, что psql может запросить пароль вручную.
#
# Пример настройки ~/.pgpass:
#   echo "localhost:5432:*:postgres:postgres" >> ~/.pgpass
#   chmod 600 ~/.pgpass
#
# Либо запуск с переменной окружения:
#   DB_PASSWORD=postgres ./deploy_bd.sh migrate
# ---------------------------------------------------------------------------
if [ -f "$HOME/.pgpass" ]; then
  : # пароль уже будет подхвачен из ~/.pgpass
elif [ -n "$DB_PASSWORD" ]; then
  export PGPASSWORD="$DB_PASSWORD"
else
  echo "Предупреждение: пароль для psql не найден (~/.pgpass отсутствует, DB_PASSWORD не задан)." >&2
  echo "psql может запросить пароль вручную при каждом обращении к БД." >&2
fi

usage() {
  cat <<'EOF'
Использование: ./deploy_bd.sh [опции]

Скрипт управления базами данных asutg / asutg_test: обрыв соединений,
пересоздание БД, применение миграций, наполнение данными и документами.

Опции (можно комбинировать, кроме "all", который включает всё сразу):
  all       Выполнить force + drop + data + doc
  force     Оборвать все текущие соединения с базами asutg и asutg_test
  drop      Пересоздать базы asutg и asutg_test (удалить и создать заново)
  migrate   Очистить старые файлы миграций и сгенерировать новую миграцию,
            затем применить миграции к основной и тестовой БД
  data      Запустить скрипт наполнения данными (script/data_system_control.py)
  docs       Запустить скрипт наполнения документами (../asutg_docs/deploy_documentation.sh)
  -h, --help   Показать эту справку и выйти

Примеры:
  ./deploy_bd.sh all              # полный сброс и пересоздание всего окружения
  ./deploy_bd.sh migrate          # только сгенерировать и применить миграции
  ./deploy_bd.sh drop force       # оборвать соединения и пересоздать базы
  ./deploy_bd.sh data             # только наполнить данными

Пароль для psql (при pam-аутентификации):
  Скрипт не запрашивает пароль сам — он либо берёт его из ~/.pgpass,
  либо из переменной окружения DB_PASSWORD (см. пример ниже).
    echo "localhost:5432:*:postgres:postgres" >> ~/.pgpass && chmod 600 ~/.pgpass
    # или
    DB_PASSWORD=postgres ./deploy_bd.sh all
EOF
}

case "$*" in
  *-h*|*--help*)
    usage
    exit 0
    ;;
esac

if [ -f "$CONFIG_FILE" ]; then
    URI=$(jq -r '.SQLALCHEMY_DATABASE_URI' "$CONFIG_FILE")
    URI_TEST=$(jq -r '.SQLALCHEMY_DATABASE_URI_TEST' "$CONFIG_FILE")
    if [ "$URI" != "null" ] && [ -n "$URI" ]; then
        DB_NAME="${URI##*/}"
    fi
    if [ "$URI_TEST" != "null" ] && [ -n "$URI_TEST" ]; then
        DB_TEST_NAME="${URI_TEST##*/}"
    fi
    echo -e "\nБазы данных из CONFIG"
    echo "Основная БД: $DB_NAME"
    echo "Тестовая БД: $DB_TEST_NAME"
else
    echo "Файл $CONFIG_FILE не найден. Используем стандартные имена."
fi

if [[ "$*" == *drop* || "$*" == *all* || "$*" == *damp* || "$*" == *migrate* ]]; then
    BACKUP_DIR="/home/user/db_backups"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)

    echo -e "\nСоздание резервных копий баз данных в $BACKUP_DIR..."
    mkdir -p "$BACKUP_DIR"
    if psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1; then
        pg_dump -U postgres -F c -b -f "$BACKUP_DIR/${DB_NAME}_$TIMESTAMP.dump" $DB_NAME
        pg_dump -U postgres -b -f "$BACKUP_DIR/${DB_NAME}_$TIMESTAMP.sql" $DB_NAME
    fi
fi

if [[ "$*" == *force* || "$*" == *all* ]]; then
  echo -e "\nОбрываем текущие соединения с бд"
  psql -U postgres -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '$DB_NAME'
    AND pid <> pg_backend_pid();
    "
  psql -U postgres -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '$DB_TEST_NAME'
    AND pid <> pg_backend_pid();
    "
fi

if [[ "$*" == *drop* || "$*" == *all* || "$*" == *migrate*  ]]; then
    echo -e "\nРоняем базы данных $DB_NAME и $DB_TEST_NAME"

    psql -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
    psql -U postgres -c "DROP DATABASE IF EXISTS $DB_TEST_NAME;"
    psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || psql -U postgres -c "CREATE DATABASE $DB_NAME;"
    psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_TEST_NAME'" | grep -q 1 || psql -U postgres -c "CREATE DATABASE $DB_TEST_NAME;"
fi

if  [[ "$*" == *migrate* ]]; then
  echo -e "\nОбновляем versions-миграции по текущему коду"
  echo "Очистка старых миграций..."
  MIGRATIONS_DIR="$SCRIPT_DIR/src/migrations/versions"
  if [ -d "$MIGRATIONS_DIR" ]; then
    rm -rf "$MIGRATIONS_DIR/__pycache__"
    find "$MIGRATIONS_DIR" -maxdepth 1 -type f -name "*.py" ! -name "*инициация*" -exec rm -v {} +
  else
    echo "Предупреждение: Папка $MIGRATIONS_DIR не найдена."
  fi
  cd  "$SCRIPT_DIR/src" || { echo "Папка src не найдена!"; exit 1; }
  export FLASK_APP=app.py
  export PYTHONPATH=.
  echo "Генерация новой миграции..."
  cd  "$SCRIPT_DIR/src" || { echo "Папка src не найдена!"; exit 1; }
  "$BIN_DIR/flask" db stamp head 2>/dev/null || true
  "$BIN_DIR/flask" db migrate -m "Таблицы актуальные на $(date '+%d.%m.%y')" || {
    echo "Ошибка: flask db migrate завершился с ошибкой! Прерываем выполнение." >&2
    exit 1
  }
fi

if  [[ "$*" == *drop* || "$*" == *all* ]]; then
  cd  "$SCRIPT_DIR/src" || { echo "Папка src не найдена!"; exit 1; }
  echo -e "\nПрименение миграций к основной БД..."
  "$BIN_DIR/flask" db upgrade || { echo "Ошибка миграции основной БД!"; exit 1; }
  echo "Применение миграций к тестовой БД..."
  USE_TEST_DB=true "$BIN_DIR/flask" db upgrade || { echo "Ошибка миграции тестовой БД!"; exit 1; }
fi

if  [[ "$*" == *data* || "$*" == *all* ]]; then
  echo -e "\nЗапуск скрипта наполнения данных..."
  "$BIN_DIR/python3" "$SCRIPT_DIR/script/data_system_control.py"
  if [ $? -ne 0 ]; then
    echo "Ошибка: Скрипт data_system_control.py завершился с ошибкой! Остановка." >&2
    exit 1
  fi
fi

if  [[ "$*" == *docs* || "$*" == *all* ]]; then
  if [ -d "$SCRIPT_DIR/../asutg_repair_documentation" ]; then
    echo -e "\nЗапуск скрипта наполнения документов..."
    cd "$SCRIPT_DIR/../asutg_repair_documentation/"
    ./deploy_documentation.sh
  else  cat <<- EOF

=== Отсутствуют файлы наполнения документов ===
Чтобы заполнить данные по ремонтной документации скачайте asutg_repair_documentation
И поместите в рабочую папку рядом с asutg_server

EOF
  fi
fi
echo -e "\nГотово!"