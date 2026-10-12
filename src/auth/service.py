#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import uuid

import ssl

from flask import current_app, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_jwt,
    get_jwt_identity,
)
from ldap3 import Server, Connection, ALL, SUBTREE, Tls
from ldap3.core.exceptions import (
    LDAPException,
    LDAPBindError,
    LDAPCommunicationError,
)

try:
    from ldap3.core.exceptions import LDAPInvalidCredentialsResult
except ImportError:
    LDAPInvalidCredentialsResult = LDAPBindError
from ldap3.utils.conv import escape_filter_chars
from ldap3.utils.dn import parse_dn
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.db import db
from src.orm.orm_auth import Users, UserSession, UserGroup, utcnow

log = logging.getLogger(__name__)

REFRESH_GRACE_SECONDS = 30

def get_identity():
    if current_app.config["AUTH_DEBUG_MODE"]:
        return "1"
    return get_jwt_identity()

def get_ad_groups_from_server():
    ldap_server = Server(current_app.config["LDAP_HOST"], get_info=ALL, use_ssl = True, tls=tls_config)
    conn = Connection(ldap_server, user='asutg_admin', password='3c3Kbs9XiTpd8avTWGxdmQVM3uFuBzuN', auto_bind=True)
    search_base = current_app.config["LDAP_SEARCH_BASE"]
    group_dn = "CN=ASUTG_,CN=Users,DC=server,DC=local"

    conn.search(
        search_base=search_base,
        search_filter=(
            "(&(objectCategory=person)"
            "(objectClass=user)"
            f"(memberOf={group_dn}))"
        ),
        attributes=[
            "sAMAccountName",
            "displayName"
        ]
    )

    for user in conn.entries:
        print(user.sAMAccountName, user.displayName)

class AuthError(Exception):
    http_status = 400
    default_message = "Ошибка авторизации"

    def __init__(self, message=None):
        self.message = message or self.default_message
        super().__init__(self.message)


class InvalidCredentialsError(AuthError):
    http_status = 401
    default_message = "Неверный логин или пароль"


class UserInactiveError(AuthError):
    http_status = 403
    default_message = "Учётная запись отключена"


class UserNotFoundError(AuthError):
    http_status = 404
    default_message = "Пользователь не найден"


class UserConflictError(AuthError):
    http_status = 409
    default_message = "Конфликт учётных данных пользователя"


class SessionRevokedError(AuthError):
    http_status = 401
    default_message = "Сессия завершена, требуется повторный вход"


class DirectoryUnavailableError(AuthError):
    http_status = 503
    default_message = ("Служба каталогов временно недоступна, "
                       "повторите попытку позже")


tls_config = Tls(
    validate=ssl.CERT_REQUIRED,
    ca_certs_file='/etc/pki/tls/certs/ca-bundle.crt',
    version=ssl.PROTOCOL_TLSv1_2
)

class AuthService:

    def authenticate(self, username, password):
        """Аутентификация через AD. Возвращает кортеж (user, ad_groups)."""
        if current_app.config["AUTH_DEBUG_MODE"]:
            username = "asutg_admin"
            ad_guid = "081b8ecc-230f-48ef-bc78-8111ab2b22c1"
            display_name = ["ASUTG_"]
            ad_groups = ["ASUTG_"]

        else:
            username = (username or "").strip()
            if not username or not password:
                raise InvalidCredentialsError()

            ad_guid, display_name, ad_groups = self._ldap_authenticate(username, password)

        user = self._sync_user(ad_guid, username, display_name)
        self.sync_user_groups(user, ad_groups)
        return user, ad_groups

    def _ldap_authenticate(self, username, password):
        ldap_server = Server(current_app.config["LDAP_HOST"], get_info=ALL, use_ssl = True, tls=tls_config)
        user_dn = f"{username}@{current_app.config['LDAP_DOMAIN']}"
        search_base = current_app.config["LDAP_SEARCH_BASE"]

        conn = None
        try:
            conn = Connection(ldap_server, user=user_dn, password=password, auto_bind=True)
            safe_username = escape_filter_chars(username)
            conn.search(
                search_base,
                f'(sAMAccountName={safe_username})',
                SUBTREE,
                attributes=['objectGUID', 'displayName', 'memberOf'],
            )

            if not conn.entries:
                log.warning(
                    "Пользователь %s успешно прошёл bind, но не найден в %s. "
                    "Проверьте LDAP_SEARCH_BASE.",
                    username, search_base,
                )
                raise InvalidCredentialsError()

            ad_user = conn.entries[0]
            ad_guid = str(ad_user.objectGUID.value).strip('{}')
            display_name = ad_user.displayName.value if 'displayName' in ad_user else username
            ad_groups = self._extract_groups(ad_user)

            log.info("Успешный вход в AD: %s (guid=%s, группы=%s)",
                     username, ad_guid, ad_groups)

            return ad_guid, display_name, ad_groups

        except (LDAPBindError, LDAPInvalidCredentialsResult) as e:
            log.info("Отказ AD в bind для %s: %s", username, e)
            raise InvalidCredentialsError()

        except LDAPCommunicationError as e:
            log.error("AD недоступен (%s) при входе %s: %s",
                      current_app.config["LDAP_HOST"], username, e)
            raise DirectoryUnavailableError()

        except LDAPException as e:
            log.exception("Ошибка LDAP при входе %s: %s", username, e)
            raise DirectoryUnavailableError()

        finally:
            if conn is not None:
                try:
                    conn.unbind()
                except LDAPException:
                    log.debug("Не удалось корректно закрыть LDAP-соединение",
                              exc_info=True)

    def _extract_groups(self, ad_user):
        group_prefix = current_app.config.get("LDAP_GROUP_PREFIX", "ASUTG_")
        ad_groups = []

        for dn in (ad_user.memberOf.values if 'memberOf' in ad_user else []):
            try:
                cn = parse_dn(dn)[0][1]
            except Exception:
                log.warning("Не удалось распарсить DN группы: %s", dn)
                continue

            if cn.startswith(group_prefix):
                ad_groups.append(cn)

        return ad_groups

    def _sync_user(self, ad_guid, username, display_name):
        try:
            user = Users.query.filter_by(ad_guid=ad_guid).first()
            
            if user is None:
                user = Users(ad_guid=ad_guid, username=username,
                             display_name=display_name, active=True)
                db.session.add(user)
                
            else:
                if not user.active:
                    db.session.rollback()
                    log.info("Попытка входа отключённой учётной записи: %s", username)
                    raise UserInactiveError()

                user.username = username
                user.display_name = display_name
            db.session.commit()
            
            return user

        except IntegrityError:
            db.session.rollback()
            log.exception("Конфликт уникальности при синхронизации %s (guid=%s)",
                          username, ad_guid)
            raise UserConflictError(
                f"Логин '{username}' уже закреплён за другой учётной записью"
            )

        except SQLAlchemyError:
            db.session.rollback()
            log.exception("Ошибка БД при синхронизации пользователя %s", username)
            raise DirectoryUnavailableError("Хранилище учётных записей недоступно")

    def _build_access_claims(self, user, ad_groups, sid):
        return {
            "username": user.username,
            "ad_groups": ad_groups,
            "sid": sid,
        }

    def _token_ttl_seconds(self, config_key):
        return int(current_app.config[config_key].total_seconds())

    def sync_user_groups(self, user, ad_groups):
        UserGroup.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        for name in set(ad_groups):
            db.session.add(UserGroup(user_id=user.id, group_name=name))
        db.session.commit()

    def get_user_groups(self, user_id):
        rows = db.session.query(UserGroup.group_name).filter_by(user_id=user_id).all()
        return sorted(name for (name,) in rows)

    def issue_token_pair(self, user, ad_groups):
        sid = str(uuid.uuid4())
        refresh_ttl = current_app.config["JWT_REFRESH_TOKEN_EXPIRES"]
        access_token, refresh_token, refresh_jti = self._mint_pair(user, ad_groups, sid)

        db.session.add(UserSession(
            sid=sid,
            user_id=user.id,
            refresh_jti=refresh_jti,
            expires_at=utcnow() + refresh_ttl,
            ip=self._client_ip(),
            user_agent=(request.user_agent.string or None)[:255] if request else None,
        ))
        db.session.commit()

        log.info("Открыта сессия %s для %s (ip=%s)", sid, user.username, self._client_ip())

        return self._token_response(access_token, refresh_token)

    def refresh_access_token(self):
        claims = get_jwt()
        sid = claims.get("sid")
        jti = claims.get("jti")

        if not sid:
            raise SessionRevokedError("Формат токена устарел, войдите заново")

        session = UserSession.query.filter_by(sid=sid).first()
        if session is None or not session.is_valid():
            raise SessionRevokedError()

        if jti != session.refresh_jti:
            if self._within_grace(session, jti):
                log.info("Повторный refresh в пределах грейс-окна, сессия %s", sid)
                user = db.session.get(Users, session.user_id)
                if user is None or not user.active:
                    self.revoke_session(session, "inactive")
                    raise UserInactiveError()
                ad_groups = self.get_user_groups(user.id)
                access_token = create_access_token(
                    identity=str(user.id),
                    additional_claims=self._build_access_claims(user, ad_groups, sid),
                )
                return self._token_response(access_token, None)

            log.warning(
                "Повторное использование refresh-токена, сессия %s гасится "
                "(предъявлен jti=%s, ожидался %s)", sid, jti, session.refresh_jti,
            )
            self.revoke_session(session, "reuse_detected")
            raise SessionRevokedError(
                "Обнаружено повторное использование токена, сессия завершена"
            )

        user = db.session.get(Users, session.user_id)
        if user is None:
            self.revoke_session(session, "admin")
            raise UserNotFoundError()
        if not user.active:
            self.revoke_session(session, "inactive")
            raise UserInactiveError()

        ad_groups = self.get_user_groups(user.id)

        access_token, refresh_token, new_jti = self._mint_pair(user, ad_groups, sid)

        session.prev_refresh_jti = session.refresh_jti
        session.refresh_jti = new_jti
        session.rotated_at = utcnow()
        session.last_used_at = utcnow()
        db.session.commit()

        return self._token_response(access_token, refresh_token)

    def _mint_pair(self, user, ad_groups, sid):
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=self._build_access_claims(user, ad_groups, sid),
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims={"sid": sid},
        )
        refresh_jti = decode_token(refresh_token)["jti"]
        return access_token, refresh_token, refresh_jti

    def _within_grace(self, session, jti):
        if session.prev_refresh_jti != jti or session.rotated_at is None:
            return False
        return (utcnow() - session.rotated_at).total_seconds() <= REFRESH_GRACE_SECONDS

    def _token_response(self, access_token, refresh_token):
        payload = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self._token_ttl_seconds("JWT_ACCESS_TOKEN_EXPIRES"),
        }
        if refresh_token is not None:
            payload["refresh_token"] = refresh_token
        return payload

    def _client_ip(self):
        if not request:
            return None
        forwarded = request.headers.get("X-Forwarded-For", "")
        return (forwarded.split(",")[0].strip() or request.remote_addr) if forwarded \
            else request.remote_addr

    def revoke_session(self, session, reason):
        if session.revoked_at is not None:
            return
        session.revoked_at = utcnow()
        session.revoke_reason = reason
        db.session.commit()
        log.info("Сессия %s отозвана (%s)", session.sid, reason)

    def revoke_current_session(self, reason="logout"):
        
        sid = get_jwt().get("sid")
        if not sid:
            return
        session = UserSession.query.filter_by(sid=sid).first()
        if session is not None:
            self.revoke_session(session, reason)

    def revoke_user_sessions(self, user_id, reason="logout_all", keep_sid=None):
        query = UserSession.query.filter(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
        )
        if keep_sid:
            query = query.filter(UserSession.sid != keep_sid)

        now = utcnow()
        count = 0
        for session in query.all():
            session.revoked_at = now
            session.revoke_reason = reason
            count += 1

        db.session.commit()
        log.info("Отозвано сессий пользователя %s: %d (%s)", user_id, count, reason)
        return count

    def list_user_sessions(self, user_id):
        now = utcnow()
        return UserSession.query.filter(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        ).order_by(UserSession.last_used_at.desc()).all()

    def purge_expired_sessions(self):
        deleted = UserSession.query.filter(
            UserSession.expires_at < utcnow()
        ).delete(synchronize_session=False)
        db.session.commit()
        if deleted:
            log.info("Удалено истёкших сессий: %d", deleted)
        return deleted

    def get_current_user(self):
        user = db.session.get(Users, int(get_identity()))
        if user is None:
            raise UserNotFoundError()
        return user

    


auth_service = AuthService()