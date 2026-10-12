
"""Бутстрап учётной записи администратора при старте приложения.

Если в системе нет ни одного пользователя с permission_level >=
PERMISSION_LEVEL_ADMIN, создаёт его. Логин/пароль берутся из конфигурации
(DEFAULT_ADMIN_USERNAME / DEFAULT_ADMIN_PASSWORD)

Вызывается один раз при старте приложения, внутри app context (см.
src/app.py).
"""
from flask import current_app
from sqlalchemy.exc import IntegrityError

from src.db import db
from src.orm.orm_auth import Users, TokenBlocklist, PERMISSION_LEVEL_ADMIN


def ensure_default_admin():
    db.create_all()

    admin_exists = db.session.query(Users.id).filter(
        Users.permission_level >= PERMISSION_LEVEL_ADMIN
    ).first()
    if admin_exists:
        return

    username = current_app.config["DEFAULT_ADMIN_USERNAME"]
    password = current_app.config["DEFAULT_ADMIN_PASSWORD"]

    user = Users.query.filter_by(username=username).first()

    if user is None:
        user = Users(username=username, active=True, permission_level=PERMISSION_LEVEL_ADMIN)
        user.set_password(password)
        db.session.add(user)
        log_message = "Создан пользователь-администратор по умолчанию: %s" % username
    else:
        # Пользователь с таким логином уже существует, но не админ - повышаем его
        user.permission_level = PERMISSION_LEVEL_ADMIN
        user.active = True
        log_message = "Пользователь '%s' повышен до администратора по умолчанию" % username

    try:
        db.session.commit()
        print(log_message)
    except IntegrityError:
        db.session.rollback()
