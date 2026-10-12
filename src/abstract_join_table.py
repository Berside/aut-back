#!/usr/bin/python3
# -*- coding: utf-8 -*-
##Модуль задач

from flask import jsonify, request
from flask.views import MethodView
import traceback

from sqlalchemy.exc import NoInspectionAvailable

from src.db import db
import datetime
from sqlalchemy import or_
from src import abstract_table
from sqlalchemy.inspection import inspect

from src.orm.orm_list import ListResources, ListResourceLocation, ListDepartment, ListEmployee, ListMilitaryUnit, ListTechnologicalEquipment
from src.orm.orm_cls import DictResource, DictResourceType, DictResourceCategory, DictOkei
from src.orm.orm_res import ResourcesMovement, DeliveryNoteResources, DeliveryNote, Request, RequestResources

## Список
subclass_abstract_join_table_list = [
    {
        "url" : "list_resources",
        "cls" : ListResources,
        "join_tables" : [ListResourceLocation, DictResource, DictResourceType],
        "column_list_get" : ["id", "DictResource.name_ru" , "DictResource.DictResourceType.name_ru",
            "DictResource.designation_ru", "DictResource.DictResourceCategory.name_ru",
            "article", "count_in_article", "count_norm", "current_stock",
            "DictOkei.name", "ListResourceLocation.rack", "ListResourceLocation.shelf",
            "ListResourceLocation.place", "ListResourceLocation.placement", "date_created"],
    },
    {
        "url" : "resources_movement",
        "cls" : ResourcesMovement,
        "join_tables" : [DeliveryNoteResources, ListResources],
        "column_list_get" : ["date_record", "DeliveryNoteResources.DictResource.DictResourceType.name_ru",
            "DeliveryNoteResources.DictResource.name_ru", "DeliveryNoteResources.DictResource.designation_ru",
            "DeliveryNoteResources.DictResource.DictResourceCategory.name_ru", "ListResources.article",
            "DeliveryNoteResources.quantity", "DeliveryNoteResources.ListResourceLocation.rack",
            "DeliveryNoteResources.ListResourceLocation.shelf", "DeliveryNoteResources.ListResourceLocation.place",
            "DeliveryNoteResources.ListResourceLocation.placement", "ListResources.count_norm", "ListResources.current_stock",
            "decrease", "increase", "DeliveryNoteResources.DeliveryNote.date_delivery_note", "DeliveryNoteResources.DeliveryNote.power_attorney",
            "DeliveryNoteResources.DeliveryNote.number_delivery_note", "DeliveryNoteResources.DeliveryNote.InputEmployee.last_name",
            "DeliveryNoteResources.DeliveryNote.InputEmployee.first_name", "DeliveryNoteResources.DeliveryNote.InputEmployee.middle_name",
            "DeliveryNoteResources.DeliveryNote.OutputListDepartment.name_ru",],
            "combine_fields":[ # работает скрытие столбцов source и их объединение в столбец из label
            {
                "output": "InputEmployee",
                "source": [
                    "DeliveryNoteResources.DeliveryNote.InputEmployee.last_name", "DeliveryNoteResources.DeliveryNote.InputEmployee.first_name",
                    "DeliveryNoteResources.DeliveryNote.InputEmployee.middle_name",
                ],
                "delimiter": " ",
                "label": "ФИО",
            },
            ]
    },
    {
        "url" : "request",
        "cls" : Request,
        "join_tables" : [RequestResources],
        "expand_entity": "RequestResources", # для множественных строк в one-to-many
        "column_list_get" : ["name", "Task.name", "RequestResources.DictResource.name_ru", "RequestResources.quantity",
            "RequestResources.ListResourceLocation.rack", "RequestResources.ListResourceLocation.shelf",
            "RequestResources.ListResourceLocation.place", "RequestResources.ListResourceLocation.placement",
            "RequestResources.DictResource.name_ru", "RequestResources.DictOkei.name", "ListDepartment.name_ru",
            "InputEmployee.last_name", "InputEmployee.first_name", "InputEmployee.middle_name", "OutputEmployee.last_name",
            "OutputEmployee.first_name", "OutputEmployee.middle_name", "ListMilitaryUnit.name_ru"],

        "combine_fields":[ # работает скрытие столбцов source и их объединение в столбец из label
            {
                "output": "location",
                "source": [
                    "RequestResources.ListResourceLocation.rack", "RequestResources.ListResourceLocation.shelf",
                    "RequestResources.ListResourceLocation.place", "RequestResources.ListResourceLocation.placement",
                ],
                "delimiter": "-",
                "label": "Местоположение",
            },
            {
                "output": "InputEmployee",
                "source": [
                    "InputEmployee.last_name", "InputEmployee.first_name",
                    "InputEmployee.middle_name",
                ],
                "delimiter": " ",
                "label": "ФИО",

            },
            {
                "output": "OutputEmployee",
                "source": [
                    "OutputEmployee.last_name", "OutputEmployee.first_name",
                    "OutputEmployee.middle_name",
                ],
                "delimiter": " ",
                "label": "ФИО",

            },
        ]
    },
    {
        "url" : "list_technological_equipment",
        "cls" : ListTechnologicalEquipment,
        "join_tables" : [ListResourceLocation],
        "column_list_get" : ["name_ru", "serial_number", "ListResourceLocation.rack", "ListResourceLocation.shelf",
            "ListResourceLocation.place", "ListResourceLocation.placement", "total_operating", "production_year", "component",
            "ListEmployee.last_name", "ListEmployee.first_name", "ListEmployee.middle_name", "DictOkei.name"],

        "combine_fields":[ # работает скрытие столбцов source и их объединение в столбец из label
            {
                "output": "employee",
                "source": [
                    "ListEmployee.last_name", "ListEmployee.first_name",
                    "ListEmployee.middle_name",
                ],
                "delimiter": " ",
                "label": "ФИО",
            }
        ]

    },
]

def create_abstract_join_table_subclass(abstract_class, cls_, column_list_get_, join_tables_, combine_fields_, expand_entity_, additional_):
    class DynamicTaskClass(abstract_class):
        cls = cls_
        column_list_get = column_list_get_
        additional = additional_
        join_tables = join_tables_
        combine_fields = combine_fields_ or None
        expand_entity = expand_entity_
    return DynamicTaskClass


def factory_function_join_tables_url_rules(app):
    for subclass in subclass_abstract_join_table_list:
        for key in ['column_list_get', 'cls']:
            if not key in subclass:
                raise RuntimeError(f"Key {key} not in subclass of AbstractJoinTable")
        cls_table = create_abstract_join_table_subclass(AbstractJoinTable, subclass.get("cls"), subclass.get("column_list_get"), subclass.get("join_tables"), subclass.get("combine_fields", []), subclass.get("expand_entity", []), subclass)
        base_function_name = subclass.get("url") if "url" in subclass else cls_table.cls.__tablename__.lower()
        app.add_url_rule('/%s/' % base_function_name,
                        view_func=cls_table.as_view(base_function_name), methods=['GET', 'POST', 'DELETE'])

        cls_table_columns = create_abstract_join_table_subclass(AbstractJoinTableColumns, subclass.get("cls"), subclass.get("column_list_get"), subclass.get("join_tables"), subclass.get("combine_fields", []), subclass.get("expand_entity", []), subclass)
        app.add_url_rule('/%s_columns/' % base_function_name,
                        view_func=cls_table_columns.as_view('%s_columns' % base_function_name), methods=['GET'])

        cls_table_properties = create_abstract_join_table_subclass(AbstractJoinTableProperties, subclass.get("cls"), subclass.get("column_list_get"),
                                                                   subclass.get("join_tables"), subclass.get("combine_fields", []), subclass.get("expand_entity", []), subclass)
        app.add_url_rule('/%s_properties/' % base_function_name,
                        view_func=cls_table_properties.as_view('%s_properties' % base_function_name), methods=['GET'])


##Абстрактный класс для показа данных из объединения нескольких таблиц
class AbstractJoinTable(abstract_table.AbstractTable):
    cls = None
    column_list_get = None
    join_tables = []
    combine_fields = []
    expand_entity = None # для таблиц one-to-many

    def query_join(self, query):
        for join_table in self.join_tables:
            query = query.join(join_table)


        if self.expand_entity: # для таблиц one-to-many
            rel = inspect(self.cls).relationships[self.expand_entity]
            child_cls = rel.mapper.class_
            query = query.add_columns(child_cls)


        return query


    def get_entity_column(self, entity, column):
        result = entity
        for attr in column.split("."):
            if result is None:
                return None

            if isinstance(result, list):
                if not result:
                    return None
                result = result[0]

            try:
                try:
                    result = inspect(result).relationships[attr].mapper.class_
                except:
                    result = getattr(result, attr)
            except AttributeError:
                result = None
        return result

    def apply_combine_fields(self, row_data):
        for rule in self.combine_fields or []:
            output = rule.get("output")
            sources = rule.get("source", [])
            delimiter = rule.get("delimiter")
            parts = []
            for src in sources:
                v = row_data.get(src)
                if v is not None and str(v).strip():
                    parts.append(str(v).strip())
            row_data[output] = delimiter.join(parts) if parts else None
        return row_data





#todo удалить после перехода на properties
class AbstractJoinTableColumns(abstract_table.AbstractTableColumns, AbstractJoinTable):
    cls = None
    column_list_get = None
    join_tables = []
    combine_fields = []

    def get(self):
        lang = request.args.get('lang', 'ru') # тут обрабатываем колонки, вместо которых которых показываются объединенные
        hidden = set()
        for rule in self.combine_fields or []:
            hidden.update(rule.get("source", []))

        column_list = []
        for column in self.column_list_get:
            if column in hidden:
                continue
            column_list.append(self.column_info(column))

        for rule in self.combine_fields or []:
            column_list.append({
                "field": rule.get("output"),
                "name": rule.get("output"),
                "label": rule.get("label") or rule.get("output"),
                "sortable": False, #??? надо ли тут
                "align": "left",
                "column_type": "text",
            })
        self.process_classified_fields(self.cls, column_list, lang)
        return jsonify(column_list)

class AbstractJoinTableProperties(abstract_table.AbstractTableProperties, AbstractJoinTable):
    cls = None
    column_list_get = None
    additional = None
    join_tables = []

# if __name__ == "__main__":
#     from src.configuration import configuration
#     from flask import Flask
#     from src.orm.orm_list import ListResources
#     app = Flask(__name__)
#     app.config["SQLALCHEMY_DATABASE_URI"] = configuration["SQLALCHEMY_DATABASE_URI"]
#     db.init_app(app)
#     with app.app_context():

#         dn =  db.session.query(DeliveryNote).first()
#         print("LLLL", dn.number_delivery_note)
#         print("NNNN", dn.DeliveryNoteResources) # список строк накладной

#         for dd in dn.DeliveryNoteResources:
#             print("AAA", dd.quantity, dd.ResourcesMovement.id)

        # mv = db.session.query(ResourcesMovement).first()

        # print(mv.id, mv.date_record)
        # print("ListResources:", mv.ListResources) # 1 к 1
        # print("DeliveryNoteResources:", mv.DeliveryNoteResources) # 1 ко многим

        # for dnr in mv.DeliveryNoteResources:
        #     print(" dnr id:", dnr.id, "qty:", dnr.quantity)
        #     print(" dnr.DeliveryNote:", dnr.DeliveryNote.number_delivery_note)
        #     print(" dnr.DictResource:", dnr.DictResource.name_ru)
        #     print(" dnr.ResourceMovement:", dnr.ResourcesMovement.id) # обратная ссылка (должна быть == id движения исходящего)