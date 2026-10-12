#!/usr/bin/python3
# -*- coding: utf-8 -*-
from marshmallow import Schema, fields, validate


class LoginRequestDTO(Schema):
    username = fields.String(required=True, validate=validate.Length(min=1),
                             error_messages={"required": "Не задан логин"})
    password = fields.String(required=True, validate=validate.Length(min=1), load_only=True,
                             error_messages={"required": "Не задан пароль"})


class TokenPairResponseDTO(Schema):
    access_token = fields.String()
    refresh_token = fields.String()
    token_type = fields.String(dump_default="bearer")
    expires_in = fields.Integer()


class AccessTokenResponseDTO(Schema):
    access_token = fields.String()
    refresh_token = fields.String()
    token_type = fields.String(dump_default="bearer")
    expires_in = fields.Integer()


class SessionResponseDTO(Schema):
    sid = fields.String()
    issued_at = fields.DateTime()
    last_used_at = fields.DateTime()
    expires_at = fields.DateTime()
    ip = fields.String()
    user_agent = fields.String()
    current = fields.Boolean(metadata={"description": "Сессия текущего запроса"})


class UserResponseDTO(Schema):
    id = fields.Integer()
    username = fields.String()
    display_name = fields.String()
    active = fields.Boolean()
    ad_groups = fields.List(fields.String(), metadata={"description": "Группы AD из токена"})


class ErrorResponseDTO(Schema):
    error = fields.String()
    message = fields.String()