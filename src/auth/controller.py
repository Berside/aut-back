from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity, verify_jwt_in_request
from marshmallow import ValidationError

from src.auth.dto import (
    LoginRequestDTO,
    TokenPairResponseDTO,
    AccessTokenResponseDTO,
    UserResponseDTO,
    SessionResponseDTO,
)
from src.auth.service import auth_service, AuthError

auth_sso_bp = Blueprint("auth_sso", __name__, url_prefix="/api/auth")


def get_identity():
    if current_app.config["AUTH_DEBUG_MODE"]:
        return "1"

    return get_jwt_identity()

from flask import g
from functools import wraps
import flask_jwt_extended

from functools import wraps

from flask import current_app, g
from flask_jwt_extended import jwt_required
from src.auth.decorators import jwt_required_mock

@auth_sso_bp.errorhandler(AuthError)
def handle_auth_error(error):
    return jsonify({"error": error.__class__.__name__, "message": error.message}), error.http_status


@auth_sso_bp.errorhandler(ValidationError)
def handle_validation_error(error):
    return jsonify({
        "error": "ValidationError",
        "message": "Некорректные данные запроса",
        "details": error.messages,
    }), 400


@auth_sso_bp.post("/login")
def login():
    if current_app.config["AUTH_DEBUG_MODE"]:
        user, ad_groups = auth_service.authenticate("", "")
    else:
        payload = LoginRequestDTO().load(request.get_json(silent=True) or {})

        user, ad_groups = auth_service.authenticate(payload["username"], payload["password"])
    tokens = auth_service.issue_token_pair(user, ad_groups)
    return jsonify(TokenPairResponseDTO().dump(tokens)), 200


@auth_sso_bp.post("/refresh")
#@jwt_required(refresh=True)
@jwt_required_mock
def refresh():
    if current_app.config["AUTH_DEBUG_MODE"]:
        return login()
    tokens = auth_service.refresh_access_token()
    return jsonify(AccessTokenResponseDTO().dump(tokens)), 200


@auth_sso_bp.post("/logout")
#@jwt_required(verify_type=False)
@jwt_required_mock
def logout():
    auth_service.revoke_current_session()
    return jsonify({"message": "Выход выполнен, сессия завершена"}), 200


@auth_sso_bp.post("/logout-all")
#@jwt_required(verify_type=False)
@jwt_required_mock
def logout_all():
    user_id = int(get_identity())
    count = auth_service.revoke_user_sessions(user_id)

    return jsonify({
        "message": "Все сессии завершены",
        "revoked": count,
    }), 200


from src.auth.permissions_cache import get_permissions, PermissionsUnavailableError


@auth_sso_bp.get("/sessions")
@jwt_required_mock
def sessions():
    user_id = int(get_identity())
    print(get_jwt())
    print(get_permissions())
    current_sid = get_jwt().get("sid")

    payload = [
        SessionResponseDTO().dump({
            "sid": s.sid,
            "issued_at": s.issued_at,
            "last_used_at": s.last_used_at,
            "expires_at": s.expires_at,
            "ip": s.ip,
            "user_agent": s.user_agent,
            "current": s.sid == current_sid,
        })
        for s in auth_service.list_user_sessions(user_id)
    ]

    return jsonify(payload), 200


@auth_sso_bp.get("/me")
@jwt_required()
def me():
    user = auth_service.get_current_user()
    claims = get_jwt()

    return jsonify(UserResponseDTO().dump({
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "active": user.active,
        "ad_groups": claims.get("ad_groups", []),
    })), 200