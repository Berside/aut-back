#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import threading
import time

from src.db import db
from src.orm.orm_auth import PermissionMatrix

log = logging.getLogger(__name__)

# В КОНФИГ
CACHE_TTL = 60

_lock = threading.RLock()

_permissions_cache = {
    "data": None,
    "last_updated": 0.0,
    "healthy": False,
}


class PermissionsUnavailableError(Exception):
    pass


def load_permissions():
    try:
        rows = db.session.query(PermissionMatrix).all()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            log.exception("Не удалось откатить сессию после сбоя чтения матрицы прав")

        with _lock:
            _permissions_cache["healthy"] = False
            has_stale = _permissions_cache["data"] is not None

        if has_stale:
            log.warning(
                "Не удалось обновить матрицу прав, работаем на устаревшей копии "
                "(загружена %.0f с назад)",
                time.time() - _permissions_cache["last_updated"],
                exc_info=True,
            )
        else:
            log.error(
                "Не удалось загрузить матрицу прав, валидной копии нет. "
                "Доступ будет закрыт до успешной загрузки.",
                exc_info=True,
            )
        return False

    cache_data = {}
    for row in rows:
        cache_data.setdefault((row.table_name, row.permissions), set()).update(row.get_tuple_ad_groups())

    with _lock:
        _permissions_cache["data"] = cache_data
        _permissions_cache["last_updated"] = time.time()
        _permissions_cache["healthy"] = True

    log.info("Матрица прав загружена. Записей: %d, ключей: %d", len(rows), len(cache_data))
    return True


def get_permissions():
    with _lock:
        data = _permissions_cache["data"]
        last_updated = _permissions_cache["last_updated"]

    if data is None or (time.time() - last_updated) > CACHE_TTL:
        load_permissions()
        with _lock:
            data = _permissions_cache["data"]

    if data is None:
        raise PermissionsUnavailableError("Матрица прав доступа недоступна")

    return data


def invalidate_permissions():
    with _lock:
        _permissions_cache["last_updated"] = 0.0


def permissions_healthy():
    with _lock:
        return _permissions_cache["healthy"]
