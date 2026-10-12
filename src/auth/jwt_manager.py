"""Регистрация flask-jwt-extended и обработчиков отзыва/ошибок токена."""
import logging

from flask import jsonify
from flask_jwt_extended import JWTManager

from src.db import db
from src.orm.orm_auth import UserSession, utcnow

log = logging.getLogger(__name__)

jwt = JWTManager()


def init_jwt(app):
    jwt.init_app(app)


    @jwt.token_in_blocklist_loader
    def is_token_revoked(jwt_header, jwt_payload):
        sid = jwt_payload.get("sid")

        if not sid:
            log.info("Отклонён токен без sid (jti=%s)", jwt_payload.get("jti"))
            return True

        row = db.session.query(
            UserSession.revoked_at, UserSession.expires_at
        ).filter_by(sid=sid).first()

        if row is None:
            log.info("Отклонён токен с неизвестной сессией sid=%s", sid)
            return True

        revoked_at, expires_at = row
        return revoked_at is not None or expires_at <= utcnow()

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "token_expired", "message": "Токен истёк"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return jsonify({"error": "invalid_token", "message": reason}), 422

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        return jsonify({"error": "authorization_required", "message": reason}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "token_revoked", "message": "Токен отозван"}), 401

    return jwt
