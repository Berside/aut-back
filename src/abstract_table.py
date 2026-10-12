#!/usr/bin/python3
# -*- coding: utf-8 -*-
##Модуль абстрактной таблицы
from flask.views import MethodView
from flask import jsonify, request
from src.db import db
from src.orm import orm_cls, orm_sys
import json, logging, traceback
from sqlalchemy import cast, inspect, or_, String, and_
from sqlalchemy.orm import RelationshipProperty
#todo переделать. Вынести импорты и subclass_abstract_table_orm_list в отдельные файлы
from src.orm import orm_task, orm_file, orm_doc, orm_res, orm_sys
from src.orm import orm_list

from flask_jwt_extended import jwt_required, get_jwt
from src.auth.permissions_cache import get_permissions, PermissionsUnavailableError
from src.auth.decorators import ADMIN_GROUP

log = logging.getLogger(__name__)


#swagger
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import Schema, fields
from sqlalchemy import Integer, String, Float, Boolean
from marshmallow import fields

from src.configuration import configuration

from src.orm.orm_auth import PermissionMatrix

from src.config.swagger_const import SWAGGER_JSON, SWAGGER_EXAMPLE_FLAG_MAKER, SWAGGER_JSON_WAY
from src.admin.json_maker import extend_json, write_json_to_file

from src.configuration import swagger_data

from src.auth.decorators import jwt_required_mock


## Список ORM классов, из которых создаются класс потомки абстрактного класса таблица
subclass_abstract_table_orm_list = [
    orm_cls.DictKindRepair,
    orm_cls.DictTypeDocument,
    orm_cls.DictTypeTask,
    orm_cls.DictStatusTask,
    orm_cls.DictJobTitle,
    orm_cls.DictResource,
    orm_cls.DictLocationType,
    orm_cls.DictMilitaryRank,
    orm_cls.DictArticleStructure,
    orm_cls.DictAbsenceCause,
    orm_cls.DictOkei,
    orm_cls.DictResourceType,
    orm_cls.DictResourceCategory,

    orm_list.ListResourceLocation,
    orm_list.ListDepartment,
    orm_list.ListEmployee,
    orm_list.ListMilitaryUnit,
    orm_list.ListArticle,
    orm_list.ListSpecificationsArticle,
    orm_list.ListRepairDocumentation,

    orm_task.TaskArticleWork,
    orm_task.TemplateTaskArticleWork,

    orm_sys.Notification,
    orm_sys.FileType,

    orm_file.RepairDocumentation,
    orm_file.TaskFile,

    orm_res.DeliveryNoteResources,
    orm_res.DeliveryNote,

    orm_file.TechDocumentation
]


## Функция динамического создания подклассов абстрактного класса
def create_abstract_table_subclass(abstract_class, orm_table):
    class DynamicTableClass(abstract_class):
        cls = orm_table
        column_list_get = [column.name for column in cls.__table__.columns]
        column_list_post = column_list_get

    return DynamicTableClass


## Создает Marshmallow-схему фильтрации на основе SQLAlchemy-модели.
def create_filter_schema(model):


    attrs = {}

    for column in model.__table__.columns:
        column_type = column.type

        if isinstance(column_type, Integer):
            field = fields.Int(required=False)
        elif isinstance(column_type, Float):
            field = fields.Float(required=False)
        elif isinstance(column_type, Boolean):
            field = fields.Bool(required=False)
        else:
            field = fields.Str(required=False)

        attrs[column.name] = field

    return type(
        f"{model.__name__}FilterSchema",
        (Schema,),
        attrs
    )

## Автоматически регистрирует все ORM-модели в APISpec.
def register_models(spec):
    for model in subclass_abstract_table_orm_list:

        schema = create_schema(model)


        filter_schema = create_filter_schema(model)
        spec.components.schema(schema.__name__, schema=schema)
        spec.components.schema(filter_schema.__name__, schema=filter_schema)


## Создает Marshmallow-схему для одной SQLAlchemy-модели.
def create_schema(model):
    Meta = type(
        "Meta",
        (),
        {
            "model": model,
            "load_instance": True,
        },
    )

    schema = type(
        f"{model.__name__}Schema",
        (SQLAlchemyAutoSchema,),
        {
            "Meta": Meta,
        },
    )

    return schema

## Формирует стандартные ответы ошибок OpenAPI.
def error_responses():

    return {
        400: {
            "description": "Ошибка запроса",
            "schema": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "example": "Некорректные параметры запроса"
                    }
                }
            }
        },
        404: {
            "description": "Данные не найдены",
            "schema": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "example": "Данные не найдены"
                    }
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "schema": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "example": "Внутренняя ошибка сервера"
                    }
                }
            }
        }
    }


## Формирует описание метода GET для OpenAPI.
def get_operation(base_name, schema, filter_schema, example):

    responses = {
        200: {
            "description": "Успешный ответ",
            "schema": {
                "type": "array",
                "items": {
                    "$ref": f"#/definitions/{schema.__name__}"
                }
            },
            "examples": {
                "application/json": {
                    "data": [example],
                    "total": 1
                }
            }
        }
    }

    responses.update(error_responses())

    return {
        "tags": [base_name],
        "summary": f"Получить список {base_name}",
        "parameters": [
            {
                "name": "startRow",
                "in": "query",
                "required": False,
                "type": "integer",
                "description": "Смещение относительно первой записи"
            },
            {
                "name": "pageSize",
                "in": "query",
                "required": False,
                "type": "integer",
                "description": "Размер страницы (количество записей на странице)"
            },
            {
                "name": "filterStr",
                "in": "query",
                "required": False,
                "type": "string",
                "description": "Фильтр по строке"
            },
            {
                "name": "id",
                "in": "query",
                "required": False,
                "type": "integer",
                "description": 'Поиск по id'
            },
            {
                "name": "filterModel",
                "in": "query",
                "required": False,
                "type": "string",
                "description": 'JSON фильтра, например: {"id":{"type":"notEqual","filter":3}}'
            },
            {
                "name": "sortBy",
                "in": "query",
                "required": False,
                "type": "string",
                "description": "Имя поля для сортировки"
            },
            {
                "name": "descending",
                "in": "query",
                "required": False,
                "type": "boolean",
                "description": "Сортировка по убыванию"
            }
        ],
        "responses": responses
    }

## Формирует описание метода POST для OpenAPI.
def post_operation(base_name, schema,example):

    responses = {
        201: {
            "description": "Создано",
            "schema": {
                "$ref": f"#/definitions/{schema.__name__}"
            },
            "examples": {
                "application/json": [example]
            }
        }
    }

    responses.update(error_responses())

    return {
        "tags": [base_name],
        "summary": f"Создать {base_name}",
        "parameters": [

            {
            "name": "body",
            "in": "body",
            "required": False,
            "schema": {
                "$ref": f"#/definitions/{schema.__name__}"
            }
            }

        ],
        "responses": responses
    }

## Формирует описание метода DELETE для OpenAPI.
def delete_operation(base_name,schema,example):

    responses = {
        200: {
            "description": "Удалено"
        },
        "examples": {
                "application/json": [example]
            }
    }

    responses.update(error_responses())

    return {
        "tags": [base_name],
        "summary": f"Удалить {base_name}",
        "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": False,
            "schema": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "example": 1
                    }
                },
                "required": ["id"]
            }
        }
        ],
        "responses": responses
    }


## Объединяет описания методов GET, POST и DELETE в единый словарь операций OpenAPI для маршрута.
def create_operations(base_name, schema,filter_schema, example):
    return {
        "get": get_operation(base_name, schema, filter_schema, example),
        "post": post_operation(base_name, schema, example),
        "delete": delete_operation(base_name,schema, example)
    }

def get_example(model, schema_cls):
    try:
        obj = db.session.query(model).first()
    except Exception as e:
        print(f"Ошибка получения примера для {model.__name__}: {e}")
        return None

    if obj is None:
        #print('obj is none')
        return None

    return schema_cls().dump(obj)


def combobox_operation(base_name, model):
    example = model()
    return {
        "get": {
            "tags": [base_name],
            "summary": f"Получить combobox для {base_name}",
            "responses": {
                200: {
                    "description": "Данные из combobox",
                    "examples": {
                        "application/json": example.column_list_get
                    }
                }
            }
        }
    }

def get_example_for_columns(columns):
    example = {}
    for i in columns.column_list_get:
        example[i] = columns.column_info(i)
    return example

def columns_operation(base_name, model):
    example = model()
    return {
        "get": {
            "tags": [base_name],
            "summary": f"Получить columns для {base_name}",
            "responses": {
                200: {
                    "description": "Данные из combobox",
                    "examples": {
                        "application/json": get_example_for_columns(example)#example.get().get_json()
                    }
                }
            }
        }
    }


def get_example_for_properties(columns):
    properties = {"columns" : [], "formColumns" : [], "defaultVisibleColumns" : []}
    for i in columns.column_list_get:
        columns.column_info(i, properties)
    return properties


def properties_operation(base_name, model):
    example = model()
    return {
        "get": {
            "tags": [base_name],
            "summary": f"Получить columns для {base_name}",
            "responses": {
                "200": {
                    "description": "Данные из combobox",
                    "examples": {
                        "application/json": get_example_for_properties(example)#example.get().get_json()
                    }
                }
            }
        }
    }
## Фабричная функция создания подклассов абстрактной таблицы и url для них
def factory_function_tables_url_rules(app,spec):
    records = []
    for subclass in subclass_abstract_table_orm_list:
        schema = create_schema(subclass)
        filter_schema = create_filter_schema(subclass)

        cls_table = create_abstract_table_subclass(AbstractTable, subclass)
        base_function_name = cls_table.cls.__tablename__.lower()

        app.add_url_rule('/%s/' % base_function_name,
                        view_func=cls_table.as_view(base_function_name), methods=['GET', 'POST', 'DELETE'])


        #todo Удалить после перехода на properties
        cls_table_columns = create_abstract_table_subclass(AbstractTableColumns, subclass)
        app.add_url_rule('/%s_columns/' % base_function_name,
                         view_func=cls_table_columns.as_view('%s_columns' % base_function_name), methods=['GET'])

        spec.path(
                path=f"/{base_function_name}_columns/",
                operations=columns_operation(
                    base_function_name,
                    cls_table_columns
                    )
            )



        cls_table_properties = create_abstract_table_subclass(AbstractTableProperties, subclass)
        app.add_url_rule('/%s_properties/' % base_function_name,
                         view_func=cls_table_properties.as_view('%s_properties' % base_function_name), methods=['GET'])

        spec.path(
                path=f"/{base_function_name}_properties/",
                operations=properties_operation(
                    base_function_name,
                    cls_table_properties
                    )
            )

        if getattr(subclass, "__description_ru__", None) and getattr(subclass, "__description_en__", None):
            cls_table_columns = create_abstract_table_subclass(AbstractTableComboBox, subclass)
            app.add_url_rule('/%s_combobox/' % base_function_name,
                             view_func=cls_table_columns.as_view('%s_combobox' % base_function_name), methods=['GET'])

            spec.path(
                    path=f"/{base_function_name}_combobox/",
                    operations=combobox_operation(
                        base_function_name,
                        cls_table_columns
                        )
                )


            cls_table_combobox = create_abstract_table_subclass(
                AbstractTableComboBox,
                subclass
            )

            # todo доделать, не работает, если путь в swagger_data отсутствует!
            # spec.path(
            #     path=f"/{base_function_name}/",
            #     operations=create_operations(
            #         base_function_name,
            #         schema,
            #         filter_schema,
            #         swagger_data[base_function_name]
            #     )
            # )

def add_data_to_swagger():
    for subclass in subclass_abstract_table_orm_list:
        cls_table = create_abstract_table_subclass(AbstractTable, subclass)
        base_function_name = cls_table.cls.__tablename__.lower()
        if SWAGGER_EXAMPLE_FLAG_MAKER:
            abstract_table_data = {}
            schema = create_schema(subclass)
            abstract_table_data[base_function_name] = get_example(subclass,schema)
            extend_json(SWAGGER_JSON, abstract_table_data)
    if SWAGGER_EXAMPLE_FLAG_MAKER:
        write_json_to_file(SWAGGER_JSON, SWAGGER_JSON_WAY)


def add_data_to_PermissionMatrix():
    records = []
    for subclass in subclass_abstract_table_orm_list:
        cls_table = create_abstract_table_subclass(AbstractTable, subclass)
        base_function_name = cls_table.cls.__tablename__.lower()
        records.append(PermissionMatrix().create_record(table_name = '/%s/' % base_function_name, permissions = 14,
                        ad_groups = [["ASUTG_admin"]]))
        records.append(PermissionMatrix().create_record(table_name = '/%s_columns/' % base_function_name, permissions = 8,
                        ad_groups = [["ASUTG_admin"]]))

        records.append(PermissionMatrix().create_record(table_name = '/%s_combobox/' % base_function_name, permissions = 8,
                        ad_groups = [["ASUTG_admin"]]))
    PermissionMatrix().add_records_list(records)

class SecuredMethodView(MethodView):
    """Расширяет MethodView проверкой матрицы прав перед выполнением действия."""

    decorators = [jwt_required_mock]

    permission_name = None

    def _permission_key(self):
        if self.permission_name:
            return self.permission_name

        orm_cls = getattr(self, "cls", None)
        tablename = getattr(orm_cls, "__tablename__", None)
        if tablename:
            return tablename

        return request.endpoint or self.__class__.__name__.lower()

    def dispatch_request(self, *args, **kwargs):
        if configuration["AUTH_DEBUG_MODE"]:
            claims = {'type': 'access', 'sub': '1',
                    'username': 'asutg_admin', 'ad_groups': ["ASUTG_Admins"]}

        else:
            claims = get_jwt()
        user_groups = set(claims.get("ad_groups", []))

        if ADMIN_GROUP in user_groups:
            return super().dispatch_request(*args, **kwargs)

        table_name = self._permission_key()
        action = request.method

        try:
            permissions = get_permissions()
        except PermissionsUnavailableError:
            log.error(
                "Матрица прав недоступна, запрос %s %s отклонён",
                action, table_name,
            )
            return jsonify({
                "error": "permissions_unavailable",
                "message": "Матрица прав доступа временно недоступна, "
                           "обратитесь к администратору",
            }), 503

        required_groups = permissions.get((table_name, action))

        if not required_groups or not user_groups.intersection(required_groups):
            return jsonify({
                "error": "forbidden",
                "message": f"Недостаточно прав для {action} в таблице {table_name}",
            }), 403

        return super().dispatch_request(*args, **kwargs)


## Абстрактный класс таблицы
class AbstractTable(SecuredMethodView):
    cls = None
    column_list_get = None
    combine_fields = []
    expand_entity = None

    #Вернуть переведенное значение из классификатора
    def get_relation_description_lang(self, row, default_value, cls, lang):
        value = None
        if lang == "en":
            value = getattr(row, getattr(cls, "__description_en__"))
            if not value:
                value = getattr(row, getattr(cls, "__description_ru__"))
        elif lang == "ru":
            value = getattr(row, getattr(cls, "__description_ru__"))
            if not value:
                value = getattr(row, getattr(cls, "__description_en__"))
        if not value:
            value = default_value
        return value

    ##Обработка классификационных значений для одной строки
    def format_get_classifier_data(self, cls, row, row_data, lang):
        for rel_name, rel_obj in inspect(cls).relationships.items():
            if not rel_obj.uselist and getattr(rel_obj.mapper.class_, "__description_ru__", None) and getattr(rel_obj.mapper.class_, "__description_en__", None) and \
                    len(rel_obj.local_columns) == 1 and next(iter(rel_obj.local_columns)).name in row_data and\
                    row_data[next(iter(rel_obj.local_columns)).name] is not None:
                value = self.get_relation_description_lang(getattr(row, rel_name), row_data[next(iter(rel_obj.local_columns)).name], rel_obj.mapper.class_, lang)
                row_data[next(iter(rel_obj.local_columns)).name] = {"id": row_data[next(iter(rel_obj.local_columns)).name], "value": value}

    #Получение колонки из класса или получение данных колонки из строки
    def get_entity_column(self, entity, column):
        try:
            return getattr(entity, column)
        except AttributeError:
            return None

    #Получение данных get запроса
    def format_get_data(self, cls, rows, columns, lang):
        data = []
        for row in rows:
            if self.expand_entity:
                parent, child = row[0], row[1]
            else:
                parent, child = row, None

            row_data = {}
            prefix = f"{self.expand_entity}." if self.expand_entity else None

            for column in columns:
                if child is not None and prefix and column.startswith(prefix):
                    sub_path = column[len(prefix):]
                    row_data[column] = self.get_entity_column(child, sub_path)
                else:
                    row_data[column] = self.get_entity_column(parent, column)

            self.format_get_classifier_data(cls, parent, row_data, lang)

            row_data = self.apply_combine_fields(row_data)
            data.append(row_data)
        return data

    # Форматирование полученных данных get-запроса
    def format_get(self, rows, total_count, lang):
        data = self.format_get_data(self.cls, rows, self.column_list_get, lang)
        return jsonify({
            'data': data,
            'total': total_count
        })

    def query_join(self, query):
        return query

    def get(self):
        startRow = request.args.get('startRow')
        if startRow:
            startRow = int(startRow)
        pageSize = request.args.get('pageSize')
        if pageSize:
            pageSize = int(pageSize)
        filterStr = request.args.get('filterStr')
        sortBy = request.args.get('sortBy')
        descending = request.args.get('descending') == 'true'
        filterModel = request.args.get('filterModel')
        if filterModel in ["{}", "[]", "null"]:
            filterModel = None
        if sortBy in ["{}", "[]", "null"]:
            sortBy = None
        lang = request.args.get('lang', 'ru')

        query = db.session.query(self.cls)

        # Автоматическая фильтрация по колонкам

        filter_schema = create_filter_schema(self.cls)
        schema = filter_schema()
        for name, field in schema.fields.items():

            value = request.args.get(name)

            if value is None:
                continue

            column = getattr(self.cls, name, None)

            if column is None:
                continue

            if isinstance(field, fields.Int):
                value = int(value)

            elif isinstance(field, fields.Float):
                value = float(value)

            elif isinstance(field, fields.Bool):
                value = value.lower() == "true"

            query = query.filter(column == value)

        query = self.query_join(query)

        if request.args.get('id'):
            query = db.session.get(self.cls, request.args.get('id'))
            if not query:
                return jsonify({"error": "Запись с id: %s отсутствует" % request.args.get('id')}), 400
            return self.format_get([query], 1, lang)


        ##Фильтрация по включению строки во всех колонках
        if filterStr:
            filter_list = []
            for column in self.column_list_get:
                prop = self.get_entity_column(self.cls, column)
                filter_list.append(cast(prop, String).icontains(filterStr))
            ##Фильтрация классификационных значений
            for rel_name, rel_obj in inspect(self.cls).relationships.items():
                if not rel_obj.uselist and getattr(rel_obj.mapper.class_, "__description_ru__", None) and\
                        getattr(rel_obj.mapper.class_, "__description_en__", None) and len(rel_obj.local_columns) == 1:
                    if lang == "ru":
                        filter_list.append(getattr(self.cls, rel_name).has(getattr(rel_obj.mapper.class_,
                            getattr(rel_obj.mapper.class_, "__description_ru__")).icontains(filterStr)))
                    elif lang == "en":
                        filter_list.append(getattr(self.cls, rel_name).has(getattr(rel_obj.mapper.class_,
                            getattr(rel_obj.mapper.class_, "__description_en__")).icontains(filterStr)))
            query = query.filter(or_(*filter_list))

        ##Фильтрация по стандартным фильтрам по колонкам
        if filterModel:
            try:
                filterModel = json.loads(filterModel)
                filter_conditions = []
                for field, condition in filterModel.items():
                    operator = condition.get('type')
                    filter_value = condition.get('filter')
                    if not field:
                        return jsonify({"error": "Пустое имя колонки в фильтрах"}), 400
                    column = self.get_entity_column(self.cls, field)
                    if not column:
                        return jsonify({"error": "Не найдена колонка в фильтрах: %s" % field}), 400
                    if not filter_value and operator not in ["none", "notNone"]:
                        return jsonify({"error": "Не задано значение колонки в фильтре: %s" % field}), 400
                    if operator == 'equals':
                        filter_conditions.append(column == filter_value)
                    elif operator == 'notEqual':
                        filter_conditions.append(column != filter_value)
                    elif operator == 'greaterThan':
                        filter_conditions.append(column > filter_value)
                    elif operator == 'greaterThanOrEqual':
                        filter_conditions.append(column >= filter_value)
                    elif operator == 'lessThan':
                        filter_conditions.append(column < filter_value)
                    elif operator == 'lessThanOrEqual':
                        filter_conditions.append(column <= filter_value)
                    elif operator == 'contains':
                        filter_conditions.append(column.contains(filter_value))
                    elif operator == 'notContains':
                        filter_conditions.append(~column.contains(filter_value))
                    elif operator == 'startsWith':
                        filter_conditions.append(column.startswith(filter_value))
                    elif operator == 'endsWith':
                        filter_conditions.append(column.endswith(filter_value))
                    elif operator == 'none':
                        filter_conditions.append(column == None)
                    elif operator == 'notNone':
                        filter_conditions.append(column != None)
                    else:
                        return jsonify({"error": "Неизвестный оператор сравнения в фильтрах: %s" % operator}), 400
                    #todo добавить остальные условия, обработку ошибок
                if filter_conditions:
                    query = query.filter(and_(*filter_conditions))
            except:
                print(traceback.format_exc())

        if sortBy:
            column = self.get_entity_column(self.cls, sortBy)
            if column is None:
                return jsonify({"error": "Неизвестная колонка в сортировке: %s" % sortBy}), 400
            if hasattr(column, "prop") and isinstance(column.prop, RelationshipProperty):
                if getattr(column.mapper.class_, "__description_ru__", None) and getattr(column.mapper.class_, "__description_en__", None):
                    classifier_column = None
                    if lang == "ru":
                        classifier_column = getattr(column.mapper.class_, getattr(column.mapper.class_, "__description_ru__", "name"))
                    if lang == "en":
                        classifier_column = getattr(column.mapper.class_, getattr(column.mapper.class_, "__description_en__", "name"))
                    query = query.join(column).order_by(classifier_column.desc() if descending else classifier_column.asc())
            else:
                query = query.order_by(column.desc() if descending else column.asc())
        elif getattr(self.cls, "id", None):
            query = query.order_by(self.cls.id.asc())

        total_count = query.count()
        if startRow:
            query = query.offset(startRow-1)
        if pageSize:
            query = query.limit(pageSize)
        rows = query.all()

        return self.format_get(rows, total_count, lang)

    # Функция добавления записей
    # Update также делается функцией post
    # Если не передать в json параметр id - добавится новая запись, если передать - обновится существующая
    # Если переден несуществующий id - будет ошибка
    def post(self):
        data = request.get_json()
        try:
            record_id = data.get("id")
            if record_id:
                record = db.session.query(self.cls).filter(self.cls.id == record_id).first()
                if not record:
                    return jsonify({"error": "Отсутствует запись с id: %s" % record_id}), 400
            record = self.cls(**data)
            record = db.session.merge(record)
            db.session.commit()
            return jsonify({"message": "Record edited", "id" : record.id}) if record_id else jsonify({"message": "Record added", "id" : record.id}), 200
        except AttributeError as e:
            return jsonify({"error": str(e)}), 400
        except:
            print (traceback.format_exc())
            if "id" in data:
                return jsonify({"error": "Record not edited"}), 400
            else:
                return jsonify({"error": "Record not added"}), 400

    # Функция удаления записей
    def delete(self):
        data = request.get_json()
        try:
            record_id = data.get("id")

            if not record_id:
                return jsonify({"error": "Не задан параметр json: id"}), 400
            record = db.session.query(self.cls).filter(self.cls.id == record_id).first()
            if not record:
                return jsonify({"error": "Запись не найдена"}), 404
            db.session.delete(record)
            db.session.commit()
            return jsonify({"message": "Record deleted"}), 200
        except:
            print (traceback.format_exc())
            return jsonify({"error": "Запись не удалена"}), 409


    def get_example(self):
        obj = db.session.query(self.cls).first()

        if obj is None:
            return {}

        return self.format_get([obj], 1, "ru")

    def apply_combine_fields(self, row_data):
        return row_data


## Абстрактный класс, возвращающий колонки таблицы
#todo удалить после перехода на properties
class AbstractTableColumns(AbstractTable):
    cls = None
    column_list_get = None

    ##Вернуть тип колонки
    def get_column_type(self, column):
        if column is None or not hasattr(column, 'type'):
            return 'text'
        column_type = {
            'INTEGER': 'number',
            'TEXT': 'textarea',
            'VARCHAR': 'text',
            'DATETIME': 'datetime',
            'DATE': 'date',
            'BOOLEAN': 'boolean',
            'FLOAT': 'number',
        }
        if str(column.type).startswith('VARCHAR'):
            return 'text'
        return column_type.get(str(column.type))

    #todo перевод колонок. переделать
    def comment_traslation(self, column, prefix, lang):
        if column is None:
            return prefix
        label = column.name
        if lang == "ru":
            label = column.comment or column.info or prefix + column.name
        return label[0].upper() + label[1:].replace("_link", "").replace("_", " ")


    ##Форматирование данных колонки
    def column_info(self, column, lang = "ru", prefix = "", cls = None):
        propery = self.get_entity_column(cls or self.cls, column)
        result =  {
            "field": prefix + column,
            "name": prefix + column,
            "label": self.comment_traslation(propery, prefix, lang) if propery is not None else prefix + column,
            "sortable": True,
            "align": "left",
            "column_type" : self.get_column_type(propery)
        }
        if propery is not None and propery.primary_key:
            result["disable"] = True
        return result

    ##Обработка классификационных колонок
    ##Получает на вход и изменяет параметр список колонок column_list
    def process_classified_fields(self, cls, column_list, lang):
        for rel_name, rel_obj in inspect(cls).relationships.items():
            if not rel_obj.uselist and getattr(rel_obj.mapper.class_, "__description_ru__", None) and\
                    getattr(rel_obj.mapper.class_, "__description_en__", None) and len(rel_obj.local_columns) == 1:
                local_column = next(iter(rel_obj.local_columns))
                try:
                    ind = next(i for i, column in enumerate(column_list) if local_column.name == column.get("name", None))
                except StopIteration:
                    continue
                query = db.session.query(rel_obj.mapper.class_)
                classifier_option = query.count() <= 100
                if classifier_option:
                    query = query.all()
                    column_list[ind]["column_type"] = "classifier_options"
                    options_dict = []
                    for row in query:
                        options_dict.append({"id" : row.id, "name" :
                                    self.get_relation_description_lang(row, row.id, rel_obj.mapper.class_, lang)})
                    column_list[ind]["options_dict"] = options_dict
                else:
                    column_list[ind]["column_type"] = "classifier_select"
                    column_list[ind]["classifier_url"] = rel_obj.mapper.class_.__tablename__.lower()

    def get(self):
        lang = request.args.get('lang', 'ru')
        column_list = []
        for column in self.column_list_get:
            column_list.append(self.column_info(column, lang))
        self.process_classified_fields(self.cls, column_list, lang)
        return jsonify(column_list)

    def get_example(self):
        column_list = []
        for column in self.column_list_get:
            column_list.append(self.column_info(column, "ru"))
        return jsonify(column_list)



## Абстрактный класс, возвращающий настройки таблицы
class AbstractTableProperties(AbstractTable):
    cls = None
    column_list_get = None
    additional = {}
    column_list_ = None

    ##Вернуть тип колонки
    def get_column_type(self, column):
        column_type = {
            'INTEGER': 'number',
            'TEXT': 'textarea',
            'VARCHAR': 'text',
            'DATETIME': 'datetime',
            'DATE': 'date',
            'BOOLEAN': 'boolean',
            'FLOAT': 'number',
        }
        if str(column.type).startswith('VARCHAR'):
            return 'text'
        return column_type.get(str(column.type))

    #todo перевод колонок. переделать
    def comment_traslation(self, column, prefix, lang):
        if column is None:
            return prefix
        label = column.name
        if lang == "ru":
            label = column.comment or column.info or prefix + column.name
        return label[0].upper() + label[1:].replace("_link", "").replace("_", " ")

    ##Форматирование данных колонки
    def column_info(self, column, properties, lang = "ru", prefix = "", cls = None):
        prop = self.get_entity_column(cls or self.cls, column)
        if isinstance(prop.info, dict) and prop.info.get("hidden"):
            return
        result =  {
            "field": prefix + column,
            "name": prefix + column,
            "label": self.comment_traslation(prop, prefix, lang),
            "sortable": True,
            "align": "left",
            "column_type" : self.get_column_type(prop)
        }
        properties["columns"].append(result)
        if not self.additional.get("formColumns"):
            if not (isinstance(prop.info, dict) and prop.info.get("hidden")) and not prop.primary_key:
                properties["formColumns"].append(prefix + column)
        if not self.additional.get("defaultVisibleColumns"):
            if not (isinstance(prop.info, dict) and prop.info.get("hidden")) and not prop.primary_key:
                properties["defaultVisibleColumns"].append(prefix + column)
        if prop.primary_key and not properties.get("rowKey"):
            properties["rowKey"] = prefix + column

    ##Обработка классификационных колонок
    ##Получает на вход и изменяет параметр список колонок column_list
    def process_classified_fields(self, cls, properties, lang):
        for rel_name, rel_obj in inspect(cls).relationships.items():
            if not rel_obj.uselist and getattr(rel_obj.mapper.class_, "__description_ru__", None) and\
                    getattr(rel_obj.mapper.class_, "__description_en__", None) and len(rel_obj.local_columns) == 1:
                local_column = next(iter(rel_obj.local_columns))
                try:
                    ind = next(i for i, column in enumerate(properties["columns"]) if local_column.name == column.get("name", None))
                except StopIteration:
                    continue
                query = db.session.query(rel_obj.mapper.class_)
                classifier_option = query.count() <= 100
                if classifier_option:
                    query = query.all()
                    properties["columns"][ind]["column_type"] = "classifier_options"
                    options_dict = []
                    for row in query:
                        options_dict.append({"id" : row.id, "name" :
                                    self.get_relation_description_lang(row, row.id, rel_obj.mapper.class_, lang)})
                    properties["columns"][ind]["options_dict"] = options_dict
                    properties["columns"][ind]["classifier_url"] = rel_obj.mapper.class_.__tablename__.lower()
                else:
                    properties["columns"][ind]["column_type"] = "classifier_select"
                    properties["columns"][ind]["classifier_url"] = rel_obj.mapper.class_.__tablename__.lower()

    #Проверка плохих, неправильно заполненных параметров
    def check_bad_properties(self, properties):
        result = []
        for column_list_name in ["formColumns", "defaultVisibleColumns"]:
            for form_column in properties.get(column_list_name, []):
                if not any(column.get("field") == form_column for column in properties["columns"]):
                    result.append("Поле %s из параметра %s отсутствует в списке колонок" % (form_column, column_list_name))
        if not any(column.get("field") == properties["rowKey"] for column in properties["columns"]):
            result.append("Поле %s из параметра %s отсутствует в списке колонок" % (properties["rowKey"], "rowKey"))
        return result

    def get(self):
        lang = request.args.get('lang', 'ru')
        properties = {"columns" : [], "formColumns" : [], "defaultVisibleColumns" : []}
        for param in ["formColumns", "defaultVisibleColumns", "rowKey"]:
            if self.additional.get(param, None):
                properties[param] = self.additional.get(param)
        for column in self.column_list_get:
            self.column_info(column, properties, lang)
        self.process_classified_fields(self.cls, properties, lang)
        bad_property_check = self.check_bad_properties(properties)
        if bad_property_check:
            return jsonify({"errors" : bad_property_check}), 400
        return jsonify(properties)

    def get_example(self):
        return self.get()


## Абстрактный класс, возвращающий колонки таблицы
class AbstractTableComboBox(AbstractTable):
    cls = None
    column_list_get = None

    def get(self):
        lang = request.args.get('lang', 'ru')
        result = {}
        query = db.session.query(self.cls)
        classifier_option = query.count() <= 100
        if classifier_option:
            query = query.all()
            result["column_type"] = "classifier_options"
            options_dict = []
            for row in query:
                value = self.get_relation_description_lang(row, row.id, self.cls, lang)
                if value:
                    options_dict.append({"id": row.id, "name": value})
            result["options_dict"] = options_dict
        else:
            result["column_type"] = "classifier_select"
            result["classifier_url"] = self.cls.__tablename__.lower()
        return jsonify(result)
