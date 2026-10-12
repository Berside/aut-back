#!/usr/bin/python3
# -*- coding: utf-8 -*-
##Модуль задач

from flask import jsonify, request
from flask.views import MethodView
import traceback
from src.db import db
import datetime
from sqlalchemy import or_
from src import abstract_table
from src.orm.orm_list import ListArticle
from src.orm.orm_sys import Notification
from src.orm.orm_task import (Task, TaskZip, TaskTool, TaskPreviousNext, TaskArticleWork, TemplateTask, TemplateTaskPreviousNext, TemplateTaskZip,
                              TemplateTaskTool, TemplateTaskArticleWork)
from src.orm.orm_cls import DictStatusTask, DictResource
from src.orm import orm_file

#swagger
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import Schema, fields
from sqlalchemy import Integer, String, Float, Boolean
from marshmallow import fields
import json

from src.orm.orm_auth import PermissionMatrix

from src.config.swagger_const import SWAGGER_JSON, SWAGGER_EXAMPLE_FLAG_MAKER, SWAGGER_JSON_WAY
from src.admin.json_maker import extend_json, write_json_to_file
from src.configuration import swagger_data

def create_abstract_task_subclass(abstract_class, cls_, cls_zip_, cls_tool_, cls_previous_next_,
                                  cls_upper_, cls_upper_object_, task_column_list_):
    class DynamicTaskClass(abstract_class):
        cls = cls_
        cls_zip = cls_zip_
        cls_tool = cls_tool_
        cls_previous_next = cls_previous_next_
        cls_upper = cls_upper_
        cls_upper_object = cls_upper_object_
        task_column_list = task_column_list_
        column_list_get = task_column_list
    return DynamicTaskClass


def create_abstract_task_properties_subclass(abstract_class, cls_, cls_zip_, cls_tool_, cls_previous_next_,
                                  cls_upper_, cls_upper_object_, task_column_list_, additional_):
    class DynamicTaskClass(abstract_class):
        cls = cls_
        cls_zip = cls_zip_
        cls_tool = cls_tool_
        cls_previous_next = cls_previous_next_
        cls_upper = cls_upper_
        cls_upper_object = cls_upper_object_
        task_column_list = task_column_list_
        column_list_get = task_column_list
        additional = additional_
    return DynamicTaskClass


def create_abstract_copy_task_subclass(abstract_class, class_from_, class_to_, class_previous_from_,
                                       class_previous_to_, subclass_from_list_, subclass_to_list_, copied_column_names_):
    class DynamicCopyTaskClass(abstract_class):
        class_from = class_from_
        class_to = class_to_
        class_previous_from = class_previous_from_
        class_previous_to = class_previous_to_
        subclass_from_list = subclass_from_list_
        subclass_to_list = subclass_to_list_
        copied_column_names = copied_column_names_

    return DynamicCopyTaskClass


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
def get_operation(base_name, schema, filter_schema, example, get_param_code):

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
                "application/json":  example
            }
        }
    }


    parameters = [
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

    ]



    responses.update(error_responses())

    return {
        "tags": [base_name],
        "summary": f"Получить список {base_name}",
        "parameters": parameters,
        "responses": responses
    }

## Формирует описание метода POST для OpenAPI.
def post_operation(base_name, schema,example, copy_flag):

    if not copy_flag:

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
    else:
        responses = {}

    responses.update(error_responses())

    if not copy_flag:
        parameters = [

            {
                "name": "body",
                "in": "body",
                "required": False,
                "schema": {
                    "$ref": f"#/definitions/{schema.__name__}"
                    }
            }
        ]
    else:
        parameters = [


                {
            "name": "body",
            "in": "body",
            "required": False,
            "schema": {
                "type": "object",
                "properties": {
                    "id_from": {
                        "type": "integer",
                        "example": 1
                    },
                    "id_to": {
                        "type": "integer",
                        "example": 2
                    }
                }

            }
        }
            ]

    return {
        "tags": [base_name],
        "summary": f"Создать {base_name}",
        "parameters": parameters,
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
def create_operations(base_name, schema,filter_schema, example, ops_code, get_param_code = None, copy_flag = False):
    ops = {}
    if ops_code['get']:
        ops['get'] = get_operation(base_name, schema, filter_schema, example, get_param_code)

    if ops_code['post']:
        ops['post'] = post_operation(base_name, schema, example, copy_flag)

    if ops_code['delete']:
        ops['delete'] = delete_operation(base_name,schema, example)


    return ops


def get_example(model, schema_cls):
    try:
        obj = db.session.query(model).all()
    except Exception as e:
        print(f"Ошибка получения примера для {model.__name__}: {e}")
        return {}

    if obj is None:
        return {}

    return schema_cls().dump(obj[-1])


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

## Автоматически регистрирует все ORM-модели в APISpec.
def register_models(spec):
    #task_column_list_ = ["id", "name", "description", "start_date", "end_date",
    #                     "labor_costs", "type_link", "status_link", "parent_link", "unit_link", "assignee_link",
    #                     "condition", "created_at"]
    planning_params = (Task, TaskZip,
                            TaskTool, TaskPreviousNext)

    for model in planning_params:

        schema = create_schema(model)


        filter_schema = create_filter_schema(model)
        spec.components.schema(schema.__name__, schema=schema)
        spec.components.schema(filter_schema.__name__, schema=filter_schema)



def factory_method_url_rules_task(app,spec):
    task_column_list_ = Task.__table__.columns.keys()
    planning_params = (Task, TaskZip,
                            TaskTool, TaskPreviousNext, TaskArticleWork, ListArticle, task_column_list_)
    cls_task = create_abstract_task_subclass(AbstractTask, *planning_params)
    cls_task_form = create_abstract_task_subclass(AbstractTaskForm, *planning_params)
    cls_task_columns = create_abstract_task_subclass(AbstractTaskColumns, *planning_params)
    planning_list_params = (*planning_params, {"defaultVisibleColumns": ["id",
                              "name", "status_link", "start_date", "end_date"]})

    cls_task_properties = create_abstract_task_properties_subclass(AbstractTaskProperties, *planning_list_params)


    ops_code = {
        'get' : True,
        'post' : True,
        'delete' : True
    }

    app.add_url_rule('/planning/',
                        view_func=cls_task.as_view('planning'), methods=['GET', 'POST', 'DELETE'])

    schema = create_schema(Task)
    filter_schema = create_filter_schema(Task)
    #example = json.dumps(cls_task().get_example())
    example = None


    #todo доделать, не работает, если путь в swagger_data отсутствует!
    # spec.path(
    #     path="/planning/",
    #     operations=create_operations(
    #         "planning",
    #         schema,
    #         filter_schema,
    #         swagger_data['/planning/'],
    #         ops_code,
    #     )
    # )


    app.add_url_rule('/planning_form/',
                        view_func=cls_task_form.as_view('planning_form'), methods=['GET', 'POST'])

    ops_code = {
        'get' : True,
        'post' : True,
        'delete' : False
    }

    # todo доделать, не работает, если путь в swagger_data отсутствует!
    #example = cls_task_form().get_form_example()
    # spec.path(
    #     path="/planning_form/",
    #     operations=create_operations(
    #         "planning_form",
    #         schema,
    #         filter_schema,
    #         swagger_data['/planning_form/'],
    #         ops_code,
    #         "form"
    #     )
    # )


    app.add_url_rule('/planning_columns/',
                        view_func=cls_task_columns.as_view('planning_columns'), methods=['GET'])
    app.add_url_rule('/planning_properties/',
                        view_func=cls_task_properties.as_view('planning_properties'), methods=['GET'])

    ops_code = {
        'get' : True,
        'post' : False,
        'delete' : False
    }



    #example = cls_task_columns().get().get_json()
    # todo доделать, не работает, если путь в swagger_data отсутствует!
    # spec.path(
    #     path="/planning_columns/",
    #     operations=create_operations(
    #         "planning_columns",
    #         schema,
    #         filter_schema,
    #         swagger_data['/planning_columns/'],
    #         ops_code,
    #     )
    # )



    task_template_column_list = TemplateTask.__table__.columns.keys()

    template_params = (TemplateTask, TemplateTaskZip,
    TemplateTaskTool, TemplateTaskPreviousNext, TemplateTaskArticleWork,
    DictResource, task_template_column_list)
    cls_template_task = create_abstract_task_subclass(AbstractTask, *template_params)
    cls_template_task_form = create_abstract_task_subclass(AbstractTaskForm, *template_params)
    cls_template_task_columns = create_abstract_task_subclass(AbstractTaskColumns, *template_params)

    schema = create_schema(TemplateTask)
    filter_schema = create_filter_schema(TemplateTask)
    #example = cls_template_task().get_example().get_json()


    app.add_url_rule('/template_task/',
                        view_func=cls_template_task.as_view('template_task'), methods=['GET', 'POST', 'DELETE'])

    ops_code = {
        'get' : True,
        'post' : True,
        'delete' : True
    }

    # todo доделать, не работает, если путь в swagger_data отсутствует!
    # spec.path(
    #     path="/template_task/",
    #     operations=create_operations(
    #         "template_task",
    #         schema,
    #         filter_schema,
    #         swagger_data['/template_task/'],
    #         ops_code,
    #     )
    # )


    app.add_url_rule('/template_task_form/',
                        view_func=cls_template_task_form.as_view('template_task_form'), methods=['GET'])

    ops_code = {
        'get' : True,
        'post' : False,
        'delete' : False
    }

    # todo доделать, не работает, если путь в swagger_data отсутствует!
    # spec.path(
    #     path="/template_task_form/",
    #     operations=create_operations(
    #         "template_task_form",
    #         schema,
    #         filter_schema,
    #         swagger_data['/template_task_form/'],
    #         ops_code,
    #     )
    # )


    app.add_url_rule('/template_task_columns/',
                        view_func=cls_template_task_columns.as_view('template_task_columns'), methods=['GET'])

    # todo доделать, не работает, если путь в swagger_data отсутствует!
    # spec.path(
    #     path="/template_task_columns/",
    #     operations=create_operations(
    #         "template_task_columns",
    #         schema,
    #         filter_schema,
    #         swagger_data['/template_task_columns/'],
    #         ops_code,
    #     )
    # )


    copied_column_names = ["name", "note", "type_link", "department_link", "production_task", "labor_costs", "job_title_signed_link",
                           "job_title_assignee_link"]

    ops_code = {
        'get': False,
        'post': True,
        'delete': False
    }

    cls_copy_task_from_template = create_abstract_copy_task_subclass(AbstractCopyTask,
                                                                         TemplateTask, Task, TemplateTaskPreviousNext, TaskPreviousNext,
                                                      [TemplateTaskZip, TemplateTaskTool],[TaskZip, TaskTool], copied_column_names)
    app.add_url_rule('/copy_task_from_template/', view_func=cls_copy_task_from_template.as_view('copy_task_from_template'), methods=['POST'])

    example = None
    # todo доделать, не работает, если путь в swagger_data отсутствует!
    # spec.path(
    #     path="/copy_task_from_template/",
    #     operations=create_operations(
    #         "copy_task_from_template",
    #         schema,
    #         filter_schema,
    #         None,
    #         ops_code,
    #         copy_flag=True
    #     )
    # )

    cls_copy_template_from_task = create_abstract_copy_task_subclass(AbstractCopyTask,
                                                                         Task, TemplateTask, TaskPreviousNext, TemplateTaskPreviousNext,
                                                      [TaskZip, TaskTool], [TemplateTaskZip, TemplateTaskTool], copied_column_names)
    app.add_url_rule('/copy_template_from_task/', view_func=cls_copy_template_from_task.as_view('copy_template_from_task'), methods=['POST'])

    # todo доделать, не работает, если путь в swagger_data отсутствует!
    # spec.path(
    #     path="/copy_template_from_task/",
    #     operations=create_operations(
    #         "copy_template_from_task",
    #         schema,
    #         filter_schema,
    #         None,
    #         ops_code,
    #         copy_flag=True
    #     )
    # )

    cls_copy_task_from_task = create_abstract_copy_task_subclass(AbstractCopyTask,
                                                                         Task, Task, TaskPreviousNext, TaskPreviousNext,
                                                      [TaskZip, TaskTool], [TaskZip, TaskTool], copied_column_names)
    app.add_url_rule('/copy_task_from_task/', view_func=cls_copy_task_from_task.as_view('copy_task_from_task'), methods=['POST'])

    # todo доделать, не работает, если путь в swagger_data отсутствует!
    # spec.path(
    #     path="/copy_task_from_task/",
    #     operations=create_operations(
    #         "copy_task_from_task",
    #         schema,
    #         filter_schema,
    #         None,
    #         ops_code,
    #         copy_flag=True
    #     )
    # )

    cls_copy_template_from_template = create_abstract_copy_task_subclass(AbstractCopyTask,
                                                                         TemplateTask, TemplateTask, TemplateTaskPreviousNext, TemplateTaskPreviousNext,
                                                      [TemplateTaskZip, TemplateTaskTool], [TemplateTaskZip, TemplateTaskTool], copied_column_names)
    app.add_url_rule('/copy_template_from_template/', view_func=cls_copy_template_from_template.as_view('copy_template_from_template'), methods=['POST'])

    # todo доделать, не работает, если путь в swagger_data отсутствует!
    # spec.path(
    #     path="/copy_template_from_template/",
    #     operations=create_operations(
    #         "copy_template_from_template",
    #         schema,
    #         filter_schema,
    #         None,
    #         ops_code,
    #         copy_flag=True
    #     )
    # )

    spec.components.schema(
        schema.__name__,
        schema=schema
    )



def add_data_to_swagger():
    if SWAGGER_EXAMPLE_FLAG_MAKER:
        task_data = {}
        task_column_list_ = ["id", "name", "description", "start_date", "end_date",
                         "labor_costs", "type_link", "status_link", "parent_link", "unit_link", "assignee_link",
                         "condition", "created_at"]
        planning_params = (Task, TaskZip,
                            TaskTool, TaskPreviousNext, WorkOnProduct, RepairObject, task_column_list_)
        cls_task = create_abstract_task_subclass(AbstractTask, *planning_params)
        cls_task_form = create_abstract_task_subclass(AbstractTaskForm, *planning_params)
        cls_task_columns = create_abstract_task_subclass(AbstractTaskColumns, *planning_params)
        task_template_column_list = ["id", "name", "description",
                            "type_link", "parent_link", "unit_link", "assignee_link", "created_at"]

        template_params = (TemplateTask, TemplateTaskZip,
        TemplateTaskTool, TemplateTaskPreviousNext, TemplateTable,
        Tpsn, task_template_column_list)
        cls_template_task = create_abstract_task_subclass(AbstractTask, *template_params)
        cls_template_task_form = create_abstract_task_subclass(AbstractTaskForm, *template_params)
        cls_template_task_columns = create_abstract_task_subclass(AbstractTaskColumns, *template_params)
        task_data['/planning/'] = cls_task().get_example().get_json()['data']
        task_data['/planning_form/'] = cls_task_form().get_form_example()
        task_data['/planning_form/']["Children"] = task_data['/planning_form/']["Children"][0]
        task_data['/planning_columns/'] = cls_task_columns().get().get_json()[0]
        task_data['/template_task/'] = cls_template_task().get_example().get_json()
        task_data['/template_task_form/'] = cls_template_task_form().get_form_example()
        task_data['/template_task_columns/'] = cls_template_task_columns().get().get_json()[0]
        extend_json(SWAGGER_JSON, task_data)
        write_json_to_file(SWAGGER_JSON, SWAGGER_JSON_WAY)

def add_data_to_PermissionMatrix():
    records = []
    records.append(PermissionMatrix().create_record(table_name = '/planning/', permissions = 14,
                        ad_groups = [["ASUTG_admin"]]))
    records.append(PermissionMatrix().create_record(table_name = '/copy_template_from_template/', permissions = 4,
                        ad_groups = [["ASUTG_admin"]]))
    records.append(PermissionMatrix().create_record(table_name = '/copy_task_from_task/', permissions = 4,
                        ad_groups = [["ASUTG_admin"]]))
    records.append(PermissionMatrix().create_record(table_name = '/copy_template_from_task/', permissions = 4,
                        ad_groups = [["ASUTG_admin"]]))
    records.append(PermissionMatrix().create_record(table_name = '/copy_task_from_template/', permissions = 8,
                        ad_groups = [["ASUTG_admin"]]))
    records.append(PermissionMatrix().create_record(table_name = '/template_task_columns/', permissions = 8,
                        ad_groups = [["ASUTG_admin"]]))
    records.append(PermissionMatrix().create_record(table_name = '/template_task_form/', permissions = 8,
                        ad_groups = [["ASUTG_admin"]]))
    records.append(PermissionMatrix().create_record(table_name = '/template_task/', permissions = 14,
                        ad_groups = [["ASUTG_admin"]]))
    records.append(PermissionMatrix().create_record(table_name = '/planning_columns/', permissions = 8,
                        ad_groups = [["ASUTG_admin"]]))
    records.append(PermissionMatrix().create_record(table_name = '/planning_form/', permissions = 12,
                        ad_groups = [["ASUTG_admin"]]))
    PermissionMatrix().add_records_list(records)


##Класс для планирования работ.
##В отличии от большинства остальных классов в нем в явном виде задаются relationship и поля
##Классы планирования делались под конкретный, а не общий случай
class AbstractTask(abstract_table.AbstractTable):
    cls = None
    cls_zip = None
    cls_tool = None
    task_column_list = None
    column_list_get = None
    cls_previous_next = None
    cls_upper = None
    cls_upper_object = None

    def format_task(self, row, row_data):
        if "parent_link" in row_data:
            row_data.pop("parent_link", None)
        if row.Parent:
            row_data["Parent"] = {"id": row.Parent.id, "value": row.Parent.name}
        if row.NextTask:
            row_data["NextTask"] = {"id": row.NextTask.id, "value": row.NextTask.name}
        if row.ChoiceNegTask:
            row_data["ChoiceNegTask"] = {"id": row.ChoiceNegTask.id, "value": row.ChoiceNegTask.name}
        if row.PreviousTask:
            previoustask_text_list = []
            for previous_row in row.PreviousTask:
                previoustask_text_list.append({"id": previous_row.id, "value": previous_row.name})
            row_data["PreviousTask"] = previoustask_text_list

    def format_get(self, rows, total_count, lang):
        data = []
        for row in rows:
            #todo Обсудить формат ссылок для перехода между задачами задач. Пока пишу просто id задачи
            row_data = self.format_get_data(self.cls, [row], self.task_column_list, lang)[0]
            self.format_task(row, row_data)
            row_upper_object = None
            if getattr(row, self.cls_upper.__name__) and getattr(getattr(row, self.cls_upper.__name__)[0], self.cls_upper_object.__name__):
                row_upper_object = getattr(getattr(row, self.cls_upper.__name__)[0], self.cls_upper_object.__name__)
            elif row.Parent and getattr(row.Parent , self.cls_upper.__name__) and\
                    getattr(getattr(row.Parent , self.cls_upper.__name__)[0], self.cls_upper_object.__name__):
                row_upper_object = getattr(getattr(row.Parent , self.cls_upper.__name__)[0], self.cls_upper_object.__name__)
            if row_upper_object:
                for column in self.cls_upper_object.__table__.columns:
                    if column.primary_key:
                        continue
                    row_data[self.cls_upper_object.__name__ + "." + column.name] = getattr(row_upper_object, column.name)
            data.append(row_data)
        return jsonify({
            'data': data,
            'totalCount': total_count
        })

    def post(self):
        data = request.get_json()
        try:
            if "status_link" in data:
                return jsonify({"error": "Неправильный ключ для записи: status_link"}), 400
            # db.session.begin()
            nexttask = data.pop("NextTask") if "NextTask" in data else None
            choicenegtask = data.pop("ChoiceNegTask") if "ChoiceNegTask" in data else None
            previoustask = data.pop("PreviousTask") if "PreviousTask" in data else None
            taskzip = data.pop("TaskZip") if "TaskZip" in data else []
            tasktool = data.pop("TaskTool") if "TaskTool" in data else []
            upper_object = data.pop(self.cls_upper.__name__) if self.cls_upper.__name__ in data else {}

            record = db.session.merge(self.cls(**data))
            db.session.flush()
            #todo здесь и далее переделать полное удаление на запрос + удаление лишних с проверкой существования записи
            db.session.query(self.cls_zip).filter(self.cls_zip.task_link == record.id).delete()
            for table_data in taskzip:
                table_data["task_link"] = record.id
                db.session.merge(self.cls_zip(**table_data))
            db.session.flush()
            db.session.query(self.cls_tool).filter(self.cls_tool.task_link == record.id).delete()
            for table_data in tasktool:
                table_data["task_link"] = record.id
                db.session.merge(self.cls_tool(**table_data))
            db.session.query(self.cls_previous_next).filter(self.cls_previous_next.previous_link == record.id).delete()
            if previoustask:
                db.session.merge(self.cls_previous_next(next_link=record.id, previous_link=previoustask))
            if nexttask or choicenegtask:
                previous_next_data = {"previous_link" : record.id}
                if nexttask:
                    previous_next_data["next_link"] = nexttask
                if choicenegtask:
                    previous_next_data["choice_neg_task_link"] = choicenegtask
                db.session.merge(self.cls_previous_next(**previous_next_data))
            if upper_object:
                db.session.query(self.cls_upper).filter(self.cls_upper.task_link == record.id).delete()
                upper_object["task_link"] = record.id
                db.session.merge(self.cls_upper(**upper_object))
            db.session.query(self.cls_tool).filter(self.cls_tool.task_link == record.id).delete()
            db.session.commit()
            return jsonify({"message": "Record added", "id" : record.id}), 200
        except AttributeError as e:
            # print (traceback.format_exc())
            # db.session.rollback()
            return jsonify({"error": str(e)}), 400
        except TypeError as e:
            # print (traceback.format_exc())
            # db.session.rollback()
            return jsonify({"error": str(e)}), 400
        except:
            print (traceback.format_exc())
            # db.session.rollback()
            return jsonify({"error": "Record not added"}), 400


##Получение данных в форме редактирование записи
class AbstractTaskForm(AbstractTask):
    cls = None
    cls_zip = None
    cls_tool = None
    task_column_list = None
    cls_upper = None
    cls_upper_object = None

    def recursiveGetChildren(self, row, row_data, recursive_children=False, lang = "ru"):
        if row.Children:
            children_list = self.format_get_data(self.cls, row.Children, self.task_column_list, lang)
            children_list_formatted = []
            for child, child_data in zip(row.Children, children_list):
                self.format_task(child, child_data)
                if recursive_children:
                    self.recursiveGetChildren(child, child_data, recursive_children=True, lang = lang)
                children_list_formatted.append(child_data)
            row_data["Children"] = children_list_formatted

    def get(self):
        form_id = int(request.args.get('id', 0))
        lang = request.args.get('lang', 'ru')
        recursive_children = request.args.get('recursive_children', None)
        if not form_id:
            return "Не задан параметр id", 400
        row = db.session.query(self.cls).filter(self.cls.id == form_id).first()
        row_data = self.format_get_data(self.cls, [row], self.task_column_list, lang)[0]
        self.format_task(row, row_data)
        self.recursiveGetChildren(row, row_data, recursive_children, lang)
        row_upper_object = None
        if getattr(row, self.cls_upper.__name__) and getattr(getattr(row, self.cls_upper.__name__)[0],
                                                             self.cls_upper_object.__name__):
            row_upper_object = getattr(getattr(row, self.cls_upper.__name__)[0], self.cls_upper_object.__name__)
        elif row.Parent and getattr(row.Parent, self.cls_upper.__name__) and \
                getattr(getattr(row.Parent, self.cls_upper.__name__)[0], self.cls_upper_object.__name__):
            row_upper_object = getattr(getattr(row.Parent, self.cls_upper.__name__)[0], self.cls_upper_object.__name__)
        if row_upper_object:
            upper_object_dict = {}
            for column in self.cls_upper_object.__table__.columns:
                upper_object_dict[column.name] = getattr(row_upper_object, column.name)
            self.format_get_classifier_data(self.cls_upper_object, row_upper_object, upper_object_dict, lang)
            row_data[self.cls_upper.__name__] = upper_object_dict
        return row_data, 200

    def post(self):
        data = request.get_json()
        try:
            record_id = data.get("id")
            if not data.keys() <= {"id", "status_link", "condition"}:
                return jsonify({"error": "Неправильный формат данных для записи"}), 400
            if not record_id:
                return jsonify({"error": "Отсутствует id записи"}), 400
            record = db.session.get(self.cls, record_id)
            if not record:
                return jsonify({"error": "Отсутствует запись с id: %s" % record_id}), 400
            status = db.session.get(DictStatusTask, data.get("status_link"))
            if not status:
                return jsonify({"error": "Неизвестный статус с id: %s" % data.get("status_link")}), 400
            now = datetime.datetime.now()
            if "condition"  in data and record.type_link != 3:
                return jsonify({"error": "Параметр condition можно задавать только для типа задачи условие"}), 400
            if record.type_link == 3 and "condition" not in data:
                return jsonify({"error": "Для типа задачи условие нужно задавать параметр condition"}), 400

            #todo Временная функция для оповещений. Переделать
            def write_notification(task_record, start_flag, now_):
                return
                start_text = "started" if start_flag else "completed"
                data_notification = {"title" : "Task %s" % start_text,
                        "text" : "Task #%s %s %s" % (task_record.id, task_record.name, start_text),
                        "datetime" : now_, "task_link" : task_record.id, "read" : False}
                #Кастыль для нескольких пользователей, пока переключил на одного
                # user_list = []
                # if task_record.assignee_link in [1,2]:
                #     user_list = [1, 2]
                # elif task_record.assignee_link == 3:
                #     user_list = [1, 2, 3]
                # elif task_record.assignee_link == 4:
                #     user_list = [1, 2, 3, 4]
                # elif task_record.assignee_link == 5:
                #     user_list = [1, 2, 5]
                # for user in user_list:
                #     data_user = data_notification.copy()
                #     data_user["user_link"] = user
                #     db.session.add(Notification(**data_user))
                data_notification["user_link"] = 1
                db.session.add(Notification(**data_notification))

                db.session.commit()

            # todo Переделать оповещения
            if data.get("status_link") == 2:
                record.start_date = now
                write_notification(record, True, now)
                for child in record.Children:
                    if not child.PreviousTask:
                        child.status_link = data.get("status_link")
                        child.start_date = now
                        write_notification(child, True, now)
            elif data.get("status_link") == 3 and "condition" in data:
                record.end_date = now
                write_notification(record, False, now)
                record.condition = data.get("condition")
                if data.get("condition"):
                    if record.NextTask:
                        record.NextTask.status_link = 2
                        record.NextTask.start_date = now
                        write_notification(record.NextTask, True, now)
                else:
                    if record.ChoiceNegTask:
                        record.ChoiceNegTask.status_link = 2
                        record.ChoiceNegTask.start_date = now
                        write_notification(record.ChoiceNegTask, True, now)
            elif data.get("status_link") == 3:
                record.end_date = now
                write_notification(record, False, now)
                if not record.start_date:
                    record.start_date = now
                if record.NextTask:
                    record.NextTask.status_link = 2
                    record.NextTask.start_date = now
                    write_notification(record.NextTask, True, now)
                elif record.Parent:
                    record.Parent.status_link = data.get("status_link")
                    record.Parent.end_date = now
                    write_notification(record.Parent, False, now)
                    if not record.Parent.start_date:
                        record.Parent.start_date = now
                    if record.Parent.NextTask:
                        record.Parent.NextTask.status_link = 2
                        record.Parent.NextTask.start_date = now
                        write_notification(record.Parent.NextTask, True, now)
            record.status_link = data.get("status_link")
            record = db.session.merge(record)
            db.session.commit()
            return jsonify({"message": "Record edited", "id" : record.id}) if record_id else jsonify({"message": "Record added", "id" : record.id}), 200
        except AttributeError as e:
            return jsonify({"error": str(e)}), 400
        except:
            print (traceback.format_exc())
            return jsonify({"error": "Record not changed"}), 400

    def get_form_example(self):
        row = db.session.query(self.cls).filter(self.cls.id == 1).first()
        row_data = self.format_get_data(self.cls, [row], self.task_column_list)[0]
        self.format_task(row, row_data)
        self.recursiveGetChildren(row, row_data,None)
        row_upper_object = None
        if getattr(row, self.cls_upper.__name__) and getattr(getattr(row, self.cls_upper.__name__)[0],
                                                             self.cls_upper_object.__name__):
            row_upper_object = getattr(getattr(row, self.cls_upper.__name__)[0], self.cls_upper_object.__name__)
        elif row.Parent and getattr(row.Parent, self.cls_upper.__name__) and \
                getattr(getattr(row.Parent, self.cls_upper.__name__)[0], self.cls_upper_object.__name__):
            row_upper_object = getattr(getattr(row.Parent, self.cls_upper.__name__)[0], self.cls_upper_object.__name__)
        if row_upper_object:
            upper_object_dict = {}
            for column in self.cls_upper_object.__table__.columns:
                upper_object_dict[column.name] = getattr(row_upper_object, column.name)
            row_data[self.cls_upper.__name__] = upper_object_dict
        return row_data





# todo удалить после перехода на properties
class AbstractTaskColumns(abstract_table.AbstractTableColumns):
    cls = None
    cls_zip = None
    cls_tool = None
    task_column_list = None
    cls_upper = None
    cls_upper_object = None

    def get(self):
        lang = request.args.get('lang', 'ru')
        column_list = []
        for column in self.task_column_list:
            column_list.append(self.column_info(column))
        for subtable in [{"prefix" : "NextTask", "label" : "Next task"},
                         {"prefix" : "ChoiceNegTask", "label": "Next task on NO condition"},
                         {"prefix" : "Parent", "label" : "Parent task"},]:
            column_list.append({
                "field": subtable["prefix"],
                "name": subtable["prefix"],
                "label": subtable["label"],
                "column_type": "classifier_options",
                "sortable": False,
                "align": "left"
            })
        column_list.append({
                "field": "PreviousTask",
                "name": "PreviousTask",
                "label": "Previous task",
                "column_type": "previous_task_options",
                "sortable": False,
                "align": "left"
            })
        for column in self.cls_upper_object.__table__.columns:
            if column.primary_key:
                continue
            column_list.append(self.column_info(column.name, prefix = self.cls_upper_object.__name__ + ".", cls = self.cls_upper_object))

        self.process_classified_fields(self.cls, column_list, lang)

        return jsonify(column_list)


class AbstractTaskProperties(abstract_table.AbstractTableProperties):
    cls = None
    cls_zip = None
    cls_tool = None
    task_column_list = None
    cls_upper = None
    cls_upper_object = None
    additional = None

    def get(self):
        lang = request.args.get('lang', 'ru')
        properties = {"columns" : [], "formColumns" : [], "defaultVisibleColumns" : []}
        for param in ["formColumns", "defaultVisibleColumns", "rowKey"]:
            if self.additional.get(param, None):
                properties[param] = self.additional.get(param)
        for column in self.task_column_list:
            self.column_info(column, properties)
        for subtable in [{"prefix" : "NextTask", "label" : "Next task"},
                         {"prefix" : "ChoiceNegTask", "label": "Next task on NO condition"},
                         {"prefix" : "Parent", "label" : "Parent task"}]:
            properties["columns"].append({
                "field": subtable["prefix"],
                "name": subtable["prefix"],
                "label": subtable["label"],
                "column_type": "classifier_options",
                "sortable": False,
                "align": "left"
            })
        properties["columns"].append({
                "field": "PreviousTask",
                "name": "PreviousTask",
                "label": "Previous task",
                "column_type": "previous_task_options",
                "sortable": False,
                "align": "left"
            })
        for column in self.cls_upper_object.__table__.columns:
            if column.primary_key:
                continue
            self.column_info(column.name, properties, prefix = self.cls_upper_object.__name__ + ".", lang = lang, cls = self.cls_upper_object)

        self.process_classified_fields(self.cls, properties, lang)
        bad_property_check = self.check_bad_properties(properties)
        if bad_property_check:
            return jsonify({"errors" : bad_property_check}), 400
        return jsonify(properties)

class AbstractCopyTask(abstract_table.SecuredMethodView):
    class_from = None
    class_to = None
    class_previous_from = None
    class_previous_to = None
    subclass_from_list = None
    subclass_to_list = None
    copied_column_names = None

    def post(self):
        data = request.get_json()
        id_from = data.get("id_from")
        id_to = data.get("id_to")
        if not id_from:
            return "Не задан параметр id_from", 400
        if not id_to:
            return "Не задан параметр id_to", 400
        to_task = db.session.get(self.class_to, id_to)
        if not to_task:
            return "Задача с id: %s не существует" % id_to, 400
        from_task = db.session.get(self.class_from, id_from)
        if not from_task:
            return "Копируемой задачи с id: %s не существует" % id_from, 400
        if not from_task.Children:
            return "У копируемой задачи с id: %s отсутсвуют подзадачи" % id_from, 400
        #todo удаление предыдущих задач перед записью, предупреждение
        task_prev_new_dict = {}
        for subtask in from_task.Children:
            task_data = {field: getattr(subtask, field) for field in self.copied_column_names}
            from_id = subtask.id
            task_data["parent_link"] = to_task.id
            task_new = self.class_to(**task_data)
            db.session.add(task_new)
            db.session.flush()
            task_prev_new_dict[from_id] = task_new.id
            for sub_table_from, sub_table_to in zip(self.subclass_from_list, self.subclass_to_list):
                for sub_row in getattr(subtask, sub_table_from.__name__.replace("Template", "")):
                    sub_data = {field.name: getattr(sub_row, field.name) for field in sub_table_from.__table__.columns}
                    sub_data.pop("id")
                    sub_data["task_link"] = task_new.id

                    ##Обработка работ по СЧ / шаблонов работ по СЧ
                    if self.class_to == Task and self.class_from == TemplateTask and sub_data.get("type_link") == 23:
                        sub_data["type_link"] = 9
                    elif self.class_to == TemplateTask and self.class_from == Task and sub_data.get("type_link") == 9:
                        sub_data["type_link"] = 23

                    db.session.add(sub_table_to(**sub_data))
        db.session.flush()
        previous_next_tasks = db.session.query(self.class_previous_from).filter(or_(
                                self.class_previous_from.previous_link.in_(task_prev_new_dict.keys()),
                                self.class_previous_from.next_link.in_(task_prev_new_dict.keys()),
                                self.class_previous_from.choice_neg_task_link.in_(task_prev_new_dict.keys()))).all()
        for prev_next_task in previous_next_tasks:
            sub_data = {field.name: getattr(prev_next_task, field.name) for field in self.class_previous_from.__table__.columns}
            sub_data.pop("id")
            for link_type in ["previous_link", "next_link", "choice_neg_task_link"]:
                if link_type in sub_data:
                    sub_data[link_type] = task_prev_new_dict.get(sub_data[link_type], None)
            db.session.add(self.class_previous_to(**sub_data))
        db.session.flush()
        db.session.commit()

        return jsonify({"message": "Tasks copied"}), 200
