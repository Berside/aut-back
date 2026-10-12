#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
import os

import flask
import pytest
import json
import importlib
import inspect
from src.db import db
from src.configuration import configuration
from sqlalchemy.schema import CreateSchema
import sqlalchemy

from apispec import APISpec

from apispec.ext.marshmallow import MarshmallowPlugin


app = flask.Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = configuration["SQLALCHEMY_DATABASE_URI_TEST"]
app.config['SRC_PATH'] = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(os.path.abspath(__file__)))))
app.config['UPLOAD_FOLDER'] = os.path.join(app.config['SRC_PATH'], 'file_storage')
app.config['TEMPLATE_PATH'] = os.path.join(app.config['SRC_PATH'], 'src/document/template')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
app.config["TESTING"] = True
app.config["DEBUG"] = True
db.init_app(app)
with app.app_context():
    if not "test" in sqlalchemy.inspect(db.session.get_bind()).get_schema_names():
        db.session.execute(CreateSchema("test"))
        db.session.commit()
    db.create_all()


##Специальная функцию для теста, прокидывающая контекст приложения
##Если у класса теста не будет использована - будет ошибка, если используется sqlalchemy
##Импортируйте во всех тестах, в классах тестов используйте декоратор:
## @pytest.mark.usefixtures("app_context")
@pytest.fixture(scope="class")
def app_context():
    with app.app_context():
        yield


##Класс с вспомогательными функциями для тестирования
##Импортируйте класс во всех тестах и создавайте экземпляр класса
class UtilTest:
    def __init__(self, write_data_file = False):
        global app
        self.app = app
        self.write_data_file = write_data_file
        self.json_data = {}
        self.client = self.app.test_client()
        self.data_file = None
        self.spec = APISpec(
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

    ##Получить имя функции и название файла, из которого вызвана данная функция
    def get_called_function_name(self):
        called_function = inspect.getouterframes(inspect.currentframe(), 2)
        return {"called_file_name" : called_function[1][1], "called_function_name" : called_function[1][3]}

    ##Вспомогательная функция для открытия файла data_ теста для записи эталонных результатов
    def write_file(self, called_function):
            self.data_file = open(called_function["called_file_name"].replace("test_", "data_").replace(".py", ".json"), "w")
            self.data_file.write(json.dumps(self.json_data, indent=4, ensure_ascii=False, default=str))

    ##Вспомогательная функция для открытия файла data_ теста для чтения эталана и сравнения с результатами
    def read_data_file(self, called_function):
        if not self.json_data:
            file = open(called_function["called_file_name"].replace("test_", "data_").replace(".py", ".json"), "r")
            self.json_data = json.load(file)

    ##Форматирование строки sqlalchemy в читаемый вид
    def format_row(self, row):
        result = {}
        for field in row.__table__.columns:
            if field.name in ["id", "created_at", "updated_at", "start_date", "end_date", "datetime", "created_at"]:
                continue
            elif (isinstance(getattr(row, field.name), datetime.datetime) or
                  isinstance(getattr(row, field.name), datetime.date) or
                  isinstance(getattr(row, field.name), datetime.time)):
                result[field.name] = str(getattr(row, field.name))
            else:
                result[field.name] = getattr(row, field.name)
        return result

    ##Форматирование результатов тестов в формат для записи в файл / чтения
    def format_result(self, func_result):
        if isinstance(func_result, db.Model):
            result = self.format_row(func_result)
        elif isinstance(func_result, list):
            result = []
            for row in func_result:
                if isinstance(row, db.Model):
                    result.append(self.format_row(row))
                else:
                    result.append(row)
        else:
            result = func_result
        try:
            json_data = json.loads(result)
            return json_data
        except:
            if isinstance(result, dict) or isinstance(result, list):
                return result
            elif isinstance(result, bytes):
                return result.decode("utf-8")
            else:
                return result

    ##Простой тест API. Сохраняет и считывает эталонный результат в файл data_<имя>
    def simple_test_api(self, tested_class, called_function, func_result):
        data = self.format_result(func_result.data)
        status = self.format_result(func_result.status)
        param_name_data = "%s_%s" % (called_function["called_function_name"], "data")
        param_name_status = "%s_%s" % (called_function["called_function_name"], "status")
        if self.write_data_file:
            self.json_data[param_name_data] = data
            self.json_data[param_name_status] = status
            self.write_file(called_function)
        else:
            self.read_data_file(called_function)
            if hasattr(data, "__iter__"):
                tested_class.assertCountEqual(self.json_data.get(param_name_data), data)
            else:
                tested_class.assertEqual(self.json_data.get(param_name_data), data)
            tested_class.assertEqual(self.json_data.get(param_name_status), status)

    ##Простой тест данных. Сохраняет и считывает эталонный результат в файл data_<имя>
    def simple_test_data(self, tested_class, called_function, suffix, func_result):
        result = self.format_result(func_result)
        param_name = "%s_%s" % (called_function["called_function_name"], suffix)
        if self.write_data_file:
            self.json_data[param_name] = result
            self.write_file(called_function)
        else:
            self.read_data_file(called_function)
            if hasattr(result, "__iter__"):
                tested_class.assertCountEqual(self.json_data.get(param_name), result)
            else:
                tested_class.assertEqual(self.json_data.get(param_name), result)
