from functools import wraps
from flask import request
from src.db import db
from src.orm.orm_sapr import History
import logging

logger = logging.getLogger(__name__)


def log_action(user_id: int = 1):
    # Декоратор для логгирования действий пользователя
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)

            try:
                entry = History(
                    user_id=user_id,
                    endpoint=request.path,
                    method=request.method
                )
                db.session.add(entry)
                db.session.commit()

            except Exception as e:
                db.session.rollback()
                logger.warning(f'Не удалось записать в историю {e}')

            return response
        return wrapper
    return decorator

