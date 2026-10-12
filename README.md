# Репозиторий АСУ ТГ сервер

http://gitlabmskskb/department-2/sector-22/development/asu-tg/asutg_server

## Технологии и библиотеки:
- 	Язык программирования – Python3.12
-	Основной фреймворк – Flask
-	ОС – Alt Linux 11 (Основная система будет на WindowsServer)
-	База данных – Postgresql
-	Объектно-реляционное отображение (ORM) - sqlalchemy
-	Управление изменениями структуры БД (миграциями) – Flask-Migrate
-	Библиотека создания документов Word - docxtpl

## Установка зависимостей
Для запуска серверной части необходимо установить Python 3.12 и зависимости.

Python wheels находится в репозитори asutg_dev ([тык](http://gitlabmskskb/department-2/sector-22/development/asu-tg/asutg_dev/))

Установка зависимостей в изолированное виртуальное окружение (.venv):

```bash
# Linux
bash ./install_venv_alt.sh
```
```cmd
:: Windows
..\..\asutg_dev\install\install_python.bat
```
Инструкция в [README репозитория asutg_dev](http://gitlabmskskb/department-2/sector-22/development/asu-tg/asutg_dev/-/blob/master/README.md)

## Обновление БД после подтягивания изменений

Из папки asutg_server выполнить
```bash
./deploy_bd.sh all
```
## Сохранение изменений в структуре БД 

Из папки проекта asutg_server выполнить скрипт
```bash
.venv/bin/python3 -m flask db migrate -m "<Комментарий>" 
```
## Запуск сервера

### В PyCharm открыть проект
Открыть настройки (settings) -> Python -> Interpreter ->
Add interpreter -> add local interpreter -> select existing -> Убедиться что путь к интерпритатору ведёт в вашу рабочую папку и .venv
открыть проект и выполнить app.py

### В консоли 
Перейти в папку src. Выполнить:
```bash
./run-server.sh
```
## Запуск тестов

Из папки asutg_server выполнить
```bash
./run_pytest.sh
```

