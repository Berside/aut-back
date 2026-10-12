#!/usr/bin/python3
# -*- coding: utf-8 -*-
#Основной модуль приложения
import os
from flask import Flask, jsonify, request
from flasgger import Swagger
from src.configuration import configuration
from src.db import db
from flask_cors import CORS
from flask_migrate import Migrate
import datetime
from src.routes.api import api
    # /home/user/src/asutg_server/src/app.py
from flask.json.provider import DefaultJSONProvider
# from abstract_import.routes.api import api


import src.orm.orm_task
import src.orm.orm_cls,  src.orm.orm_sys, src.orm.orm_file, src.orm.orm_doc
import src.orm.orm_folder, src.orm.orm_list, src.orm.orm_res, src.orm.orm_employee, src.orm.orm_rem_doc
import src.orm.orm_sapr
from src.document.document import upload_generate_document
from src.document.document import route_generate_document
from src.storage.file_manager import register_storage_routes
from src.auth.bootstrap import ensure_default_admin
from src.sapr.routes import sapr_bp

from src.auth.permissions_cache import load_permissions
from src.auth.service import get_ad_groups_from_server

from src.admin.matr_admin import matr_api

from src.config.swagger_const import SWAGGER_EXAMPLE_FLAG_MAKER
from src.config.PermissionMatrix_const import UPDATE_FLAG_MATR

from src.configuration import swagger_data

from src.admin.message_sender import send_log, send_Permission_rule, get_security_rules, get_ad_groups_from_server

app = Flask(__name__,
            static_folder='../static',
            template_folder='../templates')

#from src.admin.admin import init_admin
#admin = init_admin(app)

CORS(app)

if os.environ.get('USE_TEST_DB') is not None:
    app.config["SQLALCHEMY_DATABASE_URI"] = configuration["SQLALCHEMY_DATABASE_URI_TEST"]
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = configuration["SQLALCHEMY_DATABASE_URI"]

#todo проверить, зачем это?
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "connect_args": {
        "options": "-c search_path=sapr,document,public"
    }
}
app.config['SRC_PATH'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.config['UPLOAD_FOLDER'] = os.path.join(app.config['SRC_PATH'], 'file_storage')
app.config['TEMPLATE_PATH'] = os.path.join(app.config['SRC_PATH'], 'src/document/template')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  #100MB

app.config["SECRET_KEY"] = configuration["SECRET_KEY"]
app.config["JWT_ACCESS_TOKEN_EXPIRES_MIN"] = configuration["JWT_ACCESS_TOKEN_EXPIRES_MIN"]
app.config["JWT_REFRESH_TOKEN_EXPIRES_MIN"] = configuration["JWT_REFRESH_TOKEN_EXPIRES_MIN"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(
    minutes=configuration["JWT_ACCESS_TOKEN_EXPIRES_MIN"])
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = datetime.timedelta(
    minutes=configuration["JWT_REFRESH_TOKEN_EXPIRES_MIN"])
app.config["DEFAULT_ADMIN_USERNAME"] = configuration["DEFAULT_ADMIN_USERNAME"]
app.config["DEFAULT_ADMIN_PASSWORD"] = configuration["DEFAULT_ADMIN_PASSWORD"]

app.config["LDAP_HOST"] = configuration["LDAP_HOST"]
app.config["LDAP_DOMAIN"] = configuration["LDAP_DOMAIN"]
app.config["LDAP_SEARCH_BASE"] = configuration["LDAP_SEARCH_BASE"]
app.config["LDAP_GROUP_PREFIX"] = configuration["LDAP_GROUP_PREFIX"]
app.config["AUTH_DEBUG_MODE"] = configuration["AUTH_DEBUG_MODE"]

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

app.config['SWAGGER'] = {
        'title': 'API Documentation',
        'version': '1.0',
        'description': 'Документация API Аналитики ЦСУ',
        'uiversion': 3,
        'tags': []
}


db.init_app(app)
migrate = Migrate(app, db)

#swagger = Swagger(app)

##Замена стандартного декодера JSON для изменения формата дата и даты/времени
class CustomJSONEncoder(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.__format__('%Y-%m-%d %H:%M')
        if isinstance(obj, datetime.date):
            return obj.__format__('%Y-%m-%d')
        if isinstance(obj, datetime.timedelta):
            return str(obj)
        return super().default(self, obj)
app.json = CustomJSONEncoder(app)

app.register_blueprint(api)

schemas = [
    'task', 'cls', 'org', 'doc', 'employee', 'document',
    'storage', 'sapr', 'list', 'res', 'sys', 'rem_doc', 'auth']
# TODO убрать, когда подключим migrate/liquibase
with app.app_context():
    for schema in schemas:
        db.session.execute(db.text(f'CREATE SCHEMA IF NOT EXISTS {schema}'))
    db.session.commit()
    #ensure_default_admin()

    # Первичная загрузка матрицы прав в память
    #load_permissions()

from apispec import APISpec

from apispec.ext.marshmallow import MarshmallowPlugin
    
from src import abstract_table
from src import abstract_tree
from src import task
from src import abstract_join_table

from apispec import APISpec

from apispec.ext.marshmallow import MarshmallowPlugin

spec = APISpec(
    title="API Documentation",
    version="1.0",
    openapi_version="2.0",
    info={
        "description": "Документация API Аналитики ЦСУ"
    },
    plugins=[
        MarshmallowPlugin()
    ]
)




# with app.app_context():
    #todo Доделать, не работает при запуске с пустой БД
    # if SWAGGER_EXAMPLE_FLAG_MAKER:
    #     abstract_table.add_data_to_swagger()
    #     abstract_tree.add_data_to_swagger()
    #     task.add_data_to_swagger()
    # if UPDATE_FLAG_MATR:
    #     abstract_table.add_data_to_PermissionMatrix()
    #     abstract_tree.add_data_to_PermissionMatrix()
    #     task.add_data_to_PermissionMatrix()
abstract_table.register_models(spec)
abstract_table.factory_function_tables_url_rules(app,spec)
abstract_tree.factory_function_tree_url_rules(app,spec)
abstract_join_table.factory_function_join_tables_url_rules(app)
task.factory_method_url_rules_task(app,spec)


app.config["SWAGGER"] = {
    "filter": True,
    "uiversion": 3,
    "operationsSorter": "alpha",
}


swagger = Swagger(
    app,
    template=spec.to_dict(),
    config={
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/swagger/",
    },
)

register_storage_routes(app)
upload_generate_document(app)
#
# TODO переделать Заглушка для авторизации пользователей
import secrets
import time

users = {
    "admin": {"password": "admin", "role": "admin"},
    "user": {"password": "user", "role": "user"}
}

tokens = {}


# Маршрут для логина
@app.route('/login/', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('email')
    password = data.get('password')
    # Проверка пользователя
    if username in users and users[username]['password'] == password:
        # Генерация токенов
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)

        # Сохраняем токены
        tokens[access_token] = {
            'username': username,
            'role': users[username]['role'],
            'expires': time.time() + 3600  # 1 час
        }

        tokens[refresh_token] = {
            'username': username,
            'role': users[username]['role'],
            'expires': time.time() + 86400  # 24 часа
        }

        return jsonify({
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token
        })

    return jsonify({
        'success': False,
        'message': 'Неверные учетные данные'
    }), 401

@app.route('/logout/', methods=['POST'])
def logout():
    return jsonify({
        'success': True,
        'message': ' Successfully logged out '
    }), 200

# Маршрут для обновления токена
@app.route('/refresh/', methods=['POST'])
def refresh():
    data = request.get_json()
    refresh_token = data.get('refresh_token')

    # Проверка наличия рефреш токена
    if not refresh_token:
        return jsonify({
            'success': False,
            'message': 'Токен обновления не предоставлен'
        }), 401

    # Проверка валидности рефреш токена
    if refresh_token not in tokens:
        return jsonify({
            'success': False,
            'message': 'Неверный или истекший токен обновления'
        }), 401

    # Проверка срока действия токена
    token_data = tokens[refresh_token]
    if time.time() > token_data['expires']:
        # Удаляем истекший токен
        del tokens[refresh_token]
        return jsonify({
            'success': False,
            'message': 'Токен обновления истек'
        }), 401

    # Генерация нового access токена
    new_access_token = secrets.token_urlsafe(32)

    # Сохраняем новый access токен
    tokens[new_access_token] = {
        'username': token_data['username'],
        'role': token_data['role'],
        'expires': time.time() + 3600  # 1 час
    }

    # Удаляем старый рефреш токен (опционально)
    # del tokens[refresh_token]

    return jsonify({
        'success': True,
        'access_token': new_access_token
    })


# Защищенный маршрут (для демонстрации)
@app.route('/profile', methods=['GET'])
def profile():
    # Проверка наличия токена в заголовке
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Доступ запрещен'}), 401

    token = auth_header.split(' ')[1]  # Получаем токен из "Bearer <token>"

    # Проверка валидности токена
    if token not in tokens:
        return jsonify({'message': 'Неверный или истекший токен'}), 401

    # Проверка срока действия токена
    token_data = tokens[token]
    if time.time() > token_data['expires']:
        del tokens[token]  # Удаляем истекший токен
        return jsonify({'message': 'Токен истек'}), 401

    return jsonify({
        'message': 'Доступ к профилю разрешен',
        'username': token_data['username'],
        'role': token_data['role']
    })


from src.auth.jwt_manager import init_jwt
init_jwt(app)

from src.auth.controller import auth_sso_bp
app.register_blueprint(auth_sso_bp)

app.register_blueprint(sapr_bp)

app.register_blueprint(matr_api)

# S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3
from src.s3.s3_client import S3Config, S3Client
from src.s3.s3_routes import S3Blueprint
s3_config = S3Config(
    endpoint=os.environ.get("MINIO_ENDPOINT", "192.168.1.135:9000"),
    access_key=os.environ.get("MINIO_ACCESS_KEY", "grnts3admin"),
    secret_key=os.environ.get("MINIO_SECRET_KEY", "qwertyui!@12345678"),
    bucket=os.environ.get("MINIO_BUCKET", "asutgbucket"),
    secure=False  # Используйте True, если MinIO доступен через HTTPS
)
s3_client = S3Client(s3_config)
if s3_client.ensure_bucket():
    s3_api = S3Blueprint(s3_client, url_prefix="/api/s3")
    app.register_blueprint(s3_api.blueprint)
else:
    print("Не удалось подключиться к MinIO и проверить существование бакета. Работаем без s3.")
# S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3 S3

send_log(
                    'start',
                    'ASUTG'
                )
#send_Permission_rule()
get_security_rules()
get_ad_groups_from_server()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)