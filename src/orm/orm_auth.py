from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, func, UniqueConstraint, SmallInteger, CheckConstraint, ARRAY
)
from src.db import db

from src.admin.message_sender import send_Permission_rule

PERMISSION_LEVEL_ADMIN = 1

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Users(db.Model):
    __tablename__ = "users"
    __table_args__ = ({"schema": "auth"},)

    def __str__(self):
        return self.display_name or self.username

    id = Column(Integer, primary_key=True, autoincrement=True)
    ad_guid = Column(String(36), unique=True, index=True, nullable=False, comment="objectGUID")
    username = Column(String(80), unique=True, nullable=False, comment="sAMAccountName")
    display_name = Column(String(255), nullable=True, comment="ФИО из AD")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


class TokenBlocklist(db.Model):
    __tablename__ = "token_blocklist"
    __table_args__ = {"schema": "auth"}

    id = Column(Integer, primary_key=True)
    jti = Column(String(36), nullable=False, unique=True, index=True)
    token_type = Column(String(10), nullable=False)
    user_id = Column(Integer, ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False)
    revoked_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

class PermissionMatrix(db.Model):
    __tablename__ = "permission_matrix"
    __table_args__ = {"schema": "auth"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(80), unique = True, nullable=False, comment="Имя таблицы (из __tablename__)")
    permissions = Column(
      SmallInteger,
      CheckConstraint('permissions >= 0 AND permissions <= 15', name='check_num_4bit_unsigned'),
      nullable=False, comment="HTTP метод: GET (старший бит), POST (второй по старшинству бит), DELETE (третий по старшинству  бит), PUT (младший бит)"
    )
    ad_groups = Column(ARRAY(String(80), dimensions=2),nullable=False, comment="Название группы из AD")

    def create_record(self,table_name, permissions, ad_groups):
        rows = db.session.query(PermissionMatrix).filter(PermissionMatrix.table_name == table_name).first()
        if rows == None:
            send_Permission_rule(
                {
                    'name' : table_name,
                    'ad_groups' : self.code_ad_groups_for_LDAP(ad_groups),
                    'code' : permissions
                }
            )
            return PermissionMatrix(
                table_name = table_name,
                permissions = permissions,
                ad_groups = ad_groups
            )
        else:
            return None
    
    def code_ad_groups_for_LDAP(self,ad_groups):
        code_ad_groups = []
        for group in ad_groups:
            temp_string = ''
            if len(group) > 1:
                for i in group:
                    temp_string+=i+"-+-"
            else:
                temp_string = group[0]
            code_ad_groups.append(temp_string)
        return code_ad_groups

    def add_records_list(self, records):
        records = list(set(records))
        try:
            records.remove(None)
            db.session.add_all(records)
            db.session.commit()
        except:
            ...

    def clear_all(self,):
        for i in db.session.query(PermissionMatrix).all():
            db.session.delete(i)
        db.session.commit()


    def get_permissions(self):
        return self.permissions
    
    def set_permissions(self, code=-1):
        if code < 0:
            print(f"Передан некорректный код: {code}")
            return
        self.permissions = code
    
    #GET = 3
    #POST = 2
    #DELETE = 1
    #PUT = 0
    permissions_code = ['get','post','delete','put']

    def grant_permission(self, bit):
        mask = 1 << bit

        if self.permissions & mask:
            print(f"{permissions_code[bit]}: Это право уже выдано")

        self.permissions = self.permissions | mask, 0


    def revoke_permission(self, bit):
        mask = 1 << bit

        if not permissions & mask:
            print(f"{permissions_code[bit]}: Это право уже отозвано")

        self.permissions = self.permission & ~mask, 0

    def take_get_permissions(self,):
        return int(bin(self.permissions)[-4])
    
    def take_post_permissions(self,):
        return int(bin(self.permissions)[-3])

    def take_delete_permissions(self,):
        return int(bin(self.permissions)[-2])

    def take_put_permissions(self,):
        return int(bin(self.permissions)[-1])

    def get_ad_groups(self,):
        return self.ad_groups

    def get_tuple_ad_groups(self):
        result = []

        def flatten(value):
            if isinstance(value, (list, tuple)):
                for item in value:
                    flatten(item)
            else:
                result.append(value)

        flatten(self.ad_groups)

        return tuple(result)
    
    def set_ad_groups(self, groups):
        if groups in self.ad_groups:
            print(f"Передан некорректный код: {groups}")
            return
        self.ad_groups.append(groups)




class UserSession(db.Model):
    __tablename__ = "sessions"
    __table_args__ = {"schema": "auth"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    sid = Column(String(36), nullable=False, unique=True, index=True,
                 comment="Идентификатор сессии, claim sid в обоих токенах")
    user_id = Column(Integer, ForeignKey("auth.users.id", ondelete="CASCADE"),
                     nullable=False, index=True)

    refresh_jti = Column(String(36), nullable=False, index=True)
    prev_refresh_jti = Column(String(36), nullable=True)
    rotated_at = Column(DateTime, nullable=True)

    issued_at = Column(DateTime, nullable=False, default=utcnow)
    last_used_at = Column(DateTime, nullable=False, default=utcnow)
    expires_at = Column(DateTime, nullable=False,
                        comment="Момент истечения refresh-токена")

    revoked_at = Column(DateTime, nullable=True)
    revoke_reason = Column(String(40), nullable=True,
                           comment="logout | logout_all | inactive | reuse_detected | admin")

    ip = Column(String(45), nullable=True, comment="IPv4/IPv6 клиента")
    user_agent = Column(String(255), nullable=True)

    def is_valid(self, now=None):
        now = now or utcnow()
        return self.revoked_at is None and self.expires_at > now


class UserGroup(db.Model):
    __tablename__ = "user_groups"
    __table_args__ = (
        UniqueConstraint("user_id", "group_name", name="uq_user_groups_user_group"),
        {"schema": "auth"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("auth.users.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    group_name = Column(String(80), nullable=False, comment="CN группы из AD")
    synced_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)