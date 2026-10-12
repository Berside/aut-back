#!/usr/bin/python3
# -*- coding: utf-8 -*-
##Модуль абстрактного дерева

from flask.views import MethodView
from flask import jsonify, request

from src.db import db
from src.orm import orm_cls, orm_list, orm_file, orm_doc, orm_res
from src.orm.orm_folder import DocumentFolder

#swagger
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import Schema, fields
from sqlalchemy import Integer, String, Float, Boolean
from marshmallow import fields

from src.abstract_table import SecuredMethodView

from src.config.swagger_const import SWAGGER_JSON, SWAGGER_EXAMPLE_FLAG_MAKER, SWAGGER_JSON_WAY
from src.admin.json_maker import extend_json, write_json_to_file

from src.orm.orm_auth import PermissionMatrix

from src.configuration import swagger_data


## Список ORM классов, из которых создаются класс потомки абстрактного класса дерева
subclass_abstract_tree_orm_list = [
    orm_cls.ClassifiersList,
    DocumentFolder,
]




## Преобразует поля Marshmallow-схемы в список query-параметров OpenAPI.
def fields2parameters(schema_cls):
    schema = schema_cls()


    params = []

    for name, field in schema.fields.items():
        if isinstance(field, fields.Int):
            typ = "integer"
        elif isinstance(field, fields.Float):
            typ = "number"
        elif isinstance(field, fields.Bool):
            typ = "boolean"
        else:
            typ = "string"

        params.append({
            "name": name,
            "in": "query",
            "required": False,
            "type": typ,
        })

    return params


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
def get_operation(base_name, schema, example):

    responses = {
        200: {
            "description": "Успешный ответ",
            "schema": {
                "type": "array",
                "items": {
                    "$ref": f"#/definitions/{schema.__name__}"
                }
            }
        }
    }

    responses.update(error_responses())

    return {
        "tags": [base_name],
        "summary": f"Получить список {base_name}",
        "parameters": [
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
        ], "responses": responses
    }

## Формирует описание метода PUT для OpenAPI.
def put_operation(base_name, schema, example):

    responses = {
        200: {
            "description": "Изменено",
            "schema": {
                "$ref": f"#/definitions/{schema.__name__}"
            },
            "examples": {
                "application/json": example
            }
        }
    }

    responses.update(error_responses())

    return {
        "tags": [base_name],
        "summary": f"Изменить {base_name}",
        "parameters": [
            {
                "name": "body",
                "in": "body",
                "required": True,
                "schema": {
                    "$ref": f"#/definitions/{schema.__name__}"
                }
            }
        ],
        "responses": responses
    }

## Объединяет описания методов PUT, POST и DELETE в единый словарь операций OpenAPI для маршрута.
def create_operations(base_name, schema, example, with_item_id=False):

    operations = {}

    if with_item_id:
        operations["put"] = put_operation(base_name, schema, example)
        operations["delete"] = delete_operation(base_name, schema, example)
        return operations

    operations = {
        "post": post_operation(base_name, schema, example),
        "get": get_operation(base_name, schema, example)

    }

    return operations

def get_example(model, schema_cls):
    try:
        obj = db.session.query(model).first()
    except Exception as e:
        print(f"Ошибка получения примера для {model.__name__}: {e}")
        return None

    if obj is None:
        return None

    return schema_cls().dump(obj)


## Функция динамического создания подклассов абстрактного класса
def create_abstract_tree_subclass(abstract_class, orm_tree):
    class DynamicTreeClass(abstract_class):
        cls = orm_tree
    return DynamicTreeClass

def factory_function_tree_url_rules(app, spec):
    records = []
    for subclass in subclass_abstract_tree_orm_list:

        cls_table = create_abstract_tree_subclass(AbstractTree, subclass)
        base_function_name = cls_table.cls.__tablename__.lower()

        app.add_url_rule('/%s_tree/' % base_function_name,
                         view_func=cls_table.as_view(base_function_name), methods=['GET'])
#todo проверить, вероятно, удалить

        app.add_url_rule('/%s_tree/' % base_function_name,
                         view_func=cls_table.as_view(base_function_name + '_create'),
                         methods=['POST'])
        
        app.add_url_rule('/%s_tree/<int:item_id>',
                         view_func=cls_table.as_view(base_function_name + '_update'),
                         methods=['PUT', 'DELETE'])
        schema = create_schema(subclass)

        spec.components.schema(
            schema.__name__,
            schema=schema
        )

        spec.path(
            path=f"/{base_function_name}_tree/",
            operations=create_operations(
                base_function_name,
                schema,
                swagger_data[f"/{base_function_name}_tree/"]
            )
        )

        spec.path(
            path=f"/{base_function_name}_tree/{{item_id}}",
            operations=create_operations(
                base_function_name,
                schema,
                swagger_data[f"/{base_function_name}_tree/{{item_id}}"],
                with_item_id=True
            )
        )



def add_data_to_swagger():
    for subclass in subclass_abstract_tree_orm_list:
        cls_table = create_abstract_tree_subclass(AbstractTree, subclass)
        base_function_name = cls_table.cls.__tablename__.lower()
        if SWAGGER_EXAMPLE_FLAG_MAKER:
            abstract_table_data = {}
            schema = create_schema(subclass)
            abstract_table_data[f"/{base_function_name}_tree/"] = get_example(subclass,schema)
            abstract_table_data[f"/{base_function_name}_tree/{{item_id}}"] = get_example(subclass,schema)
            extend_json(SWAGGER_JSON, abstract_table_data)
    if SWAGGER_EXAMPLE_FLAG_MAKER:
        write_json_to_file(SWAGGER_JSON, SWAGGER_JSON_WAY)

def add_data_to_PermissionMatrix():
    records = []
    for subclass in subclass_abstract_tree_orm_list:
        cls_table = create_abstract_tree_subclass(AbstractTree, subclass)
        base_function_name = cls_table.cls.__tablename__.lower()
        records.append(PermissionMatrix().create_record(table_name = '/%s_tree/' % base_function_name,permissions = 12,
                        ad_groups = [["ASUTG_admin"]]))
        records.append(PermissionMatrix().create_record(table_name = '/%s_tree/' % base_function_name, permissions = 4,
                        ad_groups = [["ASUTG_admin"]]))
        records.append(PermissionMatrix().create_record(table_name = '/%s_tree/<int:item_id>'% base_function_name, permissions = 3,
                        ad_groups = [["ASUTG_admin"]]))
    PermissionMatrix().add_records_list(records)

def swagger_data_maker():
        records = []
        for subclass in subclass_abstract_tree_orm_list:

            cls_table = create_abstract_tree_subclass(AbstractTree, subclass)
            base_function_name = cls_table.cls.__tablename__.lower()

            schema = create_schema(subclass)

            example = get_example(subclass, schema)

            spec.path(
                path=f"/{base_function_name}_tree/",
                operations=create_operations(
                    base_function_name,
                    schema,
                    example
                )
            )

            spec.path(
                path=f"/{base_function_name}_tree/{{item_id}}",
                operations=create_operations(
                    base_function_name,
                    schema,
                    example,
                    with_item_id=True
                )
            )

            records.append(PermissionMatrix().create_record(table_name = '/%s_tree/' % base_function_name,permissions = 12,
                            ad_groups = [["ASUTG_admin"]]))

            records.append(PermissionMatrix().create_record(table_name = '/%s_tree/' % base_function_name, permissions = 4,
                            ad_groups = [["ASUTG_admin"]]))
            records.append(PermissionMatrix().create_record(table_name = '/%s_tree/<int:item_id>'% base_function_name, permissions = 3,
                            ad_groups = [["ASUTG_admin"]]))

            if SWAGGER_EXAMPLE_FLAG_MAKER:
                abstract_table_data = {}
                schema = create_schema(subclass)
                abstract_table_data[base_function_name] = get_example(subclass,schema)
                extend_json(SWAGGER_JSON, abstract_table_data)

        PermissionMatrix().add_records_list(records)
        if SWAGGER_EXAMPLE_FLAG_MAKER:

            write_json_to_file(SWAGGER_JSON, SWAGGER_JSON_WAY)

##Абстрактный класс для деревьев
class AbstractTree(SecuredMethodView):
    cls = None
    ##Рекурсивная функция наполнения дерева
    def recurse_fill_tree(self, id):
        q = db.session.query(self.cls).filter(self.cls.parent_link == id).all()
        result = []
        for row in q:
            row_data = {field.name: getattr(row, field.name) for field in row.__table__.columns}
            children = self.recurse_fill_tree(row.id)
            if children:
                row_data['children'] = children
                row_data["hasChildren"] = True
            else:
                row_data["hasChildren"] = False
            result.append(row_data)
        return result

    def get(self):
        data = self.recurse_fill_tree(None)
        return jsonify(data)
    
    def post(self):
        try: 
            data = request.get_json()
            if not data: 
                return jsonify({
                    'error': 'Не переданы данные'
                }), 400
            
            if 'name' not in data: 
                return jsonify({
                    'error': 'Поле name обязательно'
                }), 400
            
            new_item = self.cls(**data)
            db.session.add(new_item)
            db.session.commit()

            return jsonify({
                'id': new_item.id,
                'message': 'Элемент создан',
                'data': {field.name: getattr(new_item, field.name) for field in new_item.__table__.columns}
            }), 201
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
        
    
    def put(self, item_id):
        try:
            item = db.session.query(self.cls).get(item_id)

            if not item:
                return jsonify({'error': 'Элемент не найден'}), 404
            
            data = request.get_json()

            if not data:
                return jsonify({'error': 'Не переданы данные'}), 400
            
            for key, value in data.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            
            db.session.commit()

            return jsonify({
                'message': 'Элемент обновлен',
                'data': {field.name: getattr(item, field.name) for field in item.__table__.columns}
            })
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
        
    def delete(self, item_id):
        try:
            item = db.session.query(self.cls).get(item_id)

            if not item:
                return jsonify({'error': 'Элемент не найден'}), 404
            
            children = db.session.query(self.cls).filter(
                self.cls.parent_link == item_id
            ).all()

            if children:
                return jsonify({
                    'error': 'Нельзя удалить: есть дочерние элементы',
                    'children_count': len(children)
                }), 400
            
            db.session.delete(item)
            db.session.commit()

            return jsonify({'message': 'Элемент удален'})
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
