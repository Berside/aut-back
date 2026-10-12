#!/usr/bin/python3
# -*- coding: utf-8 -*-
from functools import wraps

from flask import jsonify, current_app, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity, verify_jwt_in_request
from src.auth.service import auth_service, AuthError

from src.admin.message_sender import send_log


# засунуть в конфиг
ADMIN_GROUP = "ASUTG_Admins"


def group_required(*required_groups):
    """Требует валидный access-токен с хотя бы одной из указанных AD-групп.
    
    Если пользователь состоит в ADMIN_GROUP, проверка остальных групп 
    пропускается (полный доступ).
    """

    def decorator(view_func):
        @wraps(view_func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_groups = set(claims.get("ad_groups", []))

            if ADMIN_GROUP in user_groups:
                return view_func(*args, **kwargs)

            if not required_groups:
                return view_func(*args, **kwargs)

            if not user_groups.intersection(set(required_groups)):
                return jsonify({
                    "error": "forbidden",
                    "message": "Недостаточно прав для выполнения операции",
                    "required_groups": list(required_groups),
                }), 403

            return view_func(*args, **kwargs)

        return wrapper

    return decorator




'''def jwt_required_mock(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if current_app.config["AUTH_DEBUG_MODE"]:

            user, ad_groups = auth_service.authenticate("", "")
            tokens = auth_service.issue_token_pair(user, ad_groups)

            debug_token = tokens['access_token']

            original_authorization = request.environ.get(
                "HTTP_AUTHORIZATION"
            )

            request.environ["HTTP_AUTHORIZATION"] = (
                f"Bearer {debug_token}"
            )

            try:
                verify_jwt_in_request()

                return f(*args, **kwargs)

            finally:
                if original_authorization is None:
                    request.environ.pop(
                        "HTTP_AUTHORIZATION",
                        None,
                    )
                else:
                    request.environ["HTTP_AUTHORIZATION"] = (
                        original_authorization
                    )

        return jwt_required()(f)(*args, **kwargs)

    return decorated_function'''


def jwt_required_mock(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if current_app.config.get("AUTH_DEBUG_MODE"):
            user, ad_groups = auth_service.authenticate("", "")
            tokens = auth_service.issue_token_pair(user, ad_groups)

            debug_token = tokens["access_token"]

            original_authorization = request.environ.get(
                "HTTP_AUTHORIZATION"
            )

            request.environ["HTTP_AUTHORIZATION"] = (
                f"Bearer {debug_token}"
            )

            try:
                verify_jwt_in_request()

                claims = get_jwt()
                username = claims.get("username")
                endpoint = request.endpoint
                path = request.path

                print("USERNAME:", username)
                print("ENDPOINT:", endpoint)
                print("PATH:", path)

                send_log(
                    f"ENDPOINT: {endpoint}, PATH: {path}",
                    f'USERNAME:{username}'
                )

                return f(*args, **kwargs)

            finally:
                if original_authorization is None:
                    request.environ.pop(
                        "HTTP_AUTHORIZATION",
                        None,
                    )
                else:
                    request.environ["HTTP_AUTHORIZATION"] = (
                        original_authorization
                    )
        verify_jwt_in_request()

        claims = get_jwt()
        username = claims.get("username")
        endpoint = request.endpoint
        path = request.path

        send_log(
            f"ENDPOINT: {endpoint}, PATH: {path}",
            f'USERNAME:{username}'
        )
        return jwt_required()(f)(*args, **kwargs)

    return decorated_function