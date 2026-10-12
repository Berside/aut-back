#!/usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
import pytest
import json
from src.orm import orm_task, orm_file
from src import abstract_table
from src.tests import orm_test
from flask.views import MethodView
from src.db import db

from src.tests.util_test import UtilTest, app_context

utilTest = UtilTest(write_data_file=False)

abstract_table.subclass_abstract_table_orm_list = [
    orm_test.ClassifierTest,
    orm_test.ClassFieldsTest
]
abstract_table.factory_function_tables_url_rules(utilTest.app, utilTest.spec)

class TestFactoryFunction(unittest.TestCase):
    def test_create_abstract_table_subclass(self):
        result = abstract_table.create_abstract_table_subclass(abstract_table.AbstractTable, orm_test.ClassifierTest)
        self.assertTrue(issubclass(result, abstract_table.AbstractTable))
        self.assertTrue(issubclass(result, MethodView))
        self.assertEqual(result.cls, orm_test.ClassifierTest)

    def test_factory_function_tables_url_rules(self):
        found = 0
        for rule in utilTest.app.url_map.iter_rules():
            if rule.endpoint == "classifier_test":
                self.assertEqual(rule.methods, {'GET', 'DELETE', 'POST', 'HEAD', 'OPTIONS'})
                self.assertEqual(rule.rule, "/classifier_test/")
                found += 1
            if rule.endpoint == "classifier_test_columns":
                self.assertEqual(rule.methods, {'GET', 'HEAD', 'OPTIONS'})
                self.assertEqual(rule.rule, "/classifier_test_columns/")
                found += 1
            if rule.endpoint == "class_fields_test":
                self.assertEqual(rule.methods, {'GET', 'DELETE', 'POST', 'HEAD', 'OPTIONS'})
                self.assertEqual(rule.rule, "/class_fields_test/")
                found += 1
            if rule.endpoint == "class_fields_test_columns":
                self.assertEqual(rule.methods, {'GET', 'HEAD', 'OPTIONS'})
                self.assertEqual(rule.rule, "/class_fields_test_columns/")
                found += 1
        self.assertEqual(found, 4)


##Тест абстрактной таблицы с заданными результатами
##Строка до слова class позволяет тесту работать с БД
@pytest.mark.usefixtures("app_context")
class TestAbstractTableFixed(unittest.TestCase):
    def setUp(self):
        orm_test.populate_test_tables()

    def testGet(self):
        result = utilTest.client.get("/classifier_test/")
        self.assertEqual(result.status_code, 200)
        expected_data = {'data':
            [
                {"id" : 1, "name_ru" : "спам", "name_en" : "spam"},
                {"id" : 2, "name_ru" : "тест", "name_en" : "test"},
                {"id" : 3, "name_ru" : "Спам", "name_en" : "Spam"},
                {"id" : 4, "name_ru" : "ТЕСТ4", "name_en" : "TEST4"}
            ],
            "total" : 4
        }

        self.assertEqual(json.loads(result.data), expected_data)

    def testGetColumns(self):
        result = utilTest.client.get("/classifier_test_columns/")
        self.assertEqual(result.status_code, 200)
        expected_data = [
            {'column_type': 'number', 'field': 'id', 'label': 'Идентификатор', 'name': 'id', 'sortable': True, 'disable': True, "align" : "left"},
            {'column_type': 'text', 'field': 'name_ru', 'label': 'Наименование', 'name': 'name_ru', 'sortable': True, "align" : "left"},
            {'column_type': 'text', 'field': 'name_en', 'label': 'Наименование английское', 'name': 'name_en', 'sortable': True, "align" : "left"}
        ]
        self.assertEqual(json.loads(result.data), expected_data)

    def testPost(self):
        result = utilTest.client.post("/classifier_test/", headers={"Content-Type": "application/json"},
                                             data=json.dumps({"name_ru": "СПАМ", "name_en" : "SPAM"}))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.data), {"message": "Record added", "id": 5})

    def testUpdate(self):
        result = utilTest.client.post("/classifier_test/", headers={"Content-Type": "application/json"},
                                             data=json.dumps({"id": 1, "name_ru": "СПАМ"}))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.data), {"message": "Record edited", "id": 1})

    def testDelete(self):
        result = utilTest.client.delete("/classifier_test/", headers={"Content-Type": "application/json"},
                                               data=json.dumps({"id": 3}))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.data), {"message": "Record deleted"})

    def testDeleteWrong(self):
        result = utilTest.client.delete("/classifier_test/", headers={"Content-Type": "application/json"},
                                               data=json.dumps({"id": 5}))
        self.assertEqual(result.status_code, 404)
        self.assertEqual(json.loads(result.data), {"error": "Запись не найдена"})

        result = utilTest.client.delete("/classifier_test/", headers={"Content-Type": "application/json"},
                                               data=json.dumps({"name": 5}))
        self.assertEqual(result.status_code, 400)
        self.assertEqual(json.loads(result.data), {"error": "Не задан параметр json: id"})


##Тест абстрактной таблицы с записью в файл data_
##Два варианта тестов сделаны специально как пример для разных случаев.
@pytest.mark.usefixtures("app_context")
class TestAbstractTable(unittest.TestCase):
    def setUp(self):
        orm_test.populate_test_tables()

    def testGetPage1(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/class_fields_test/?startRow=1&pageSize=5"))

    def testGetPage2(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/class_fields_test/?startRow=2&pageSize=5"))

    def testGetSortBy(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/class_fields_test/?sortBy=id&descending=true&pageSize=5"))

    def testGetSortClassifierAsc(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/class_fields_test/?sortBy=ClassifierTest&descending=true&pageSize=6"))

    def testGetSortClassifierDesc(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/class_fields_test/?sortBy=ClassifierTest&descending=false&pageSize=6"))

    def testGetFilterStr3(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/class_fields_test/?filterStr=3"))

    def testGetFilterStrFloat(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/class_fields_test/?filterStr=1.2"))

    def testGetFilterStrTime(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/class_fields_test/?filterStr=07:00"))

    def testGetFilterStrDate(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/class_fields_test/?filterStr=02-23"))

    def testGetFilterStr(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/class_fields_test/?filterStr=ест1"))

    def testGetFilterStrCase(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/class_fields_test/?filterStr=еСТ2"))

    def testGetFilterClassifier(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/class_fields_test/?filterStr=спа"))

    def testGetFilterClassifierLang(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/class_fields_test/?filterStr=spa&lang=en"))

    def testGetColumns(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/class_fields_test_columns/"))

    def testGetProperties(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/class_fields_test_properties/"))

    def testGetPropertiesLangEn(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/class_fields_test_properties/?lang=en"))

    def testUpdateEmpty(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/class_fields_test/", headers={"Content-Type": "application/json"},
                                  data=json.dumps({"id": 1, "text": None, "classifier_link": None})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "title",
                                  db.session.query(orm_test.ClassFieldsTest).filter(orm_test.ClassFieldsTest.id == 1).first())
        

    def testGetFilterEquals(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?filterModel={"id":{"type":"equals","filter":3}}"""))

    def testGetFilterNotEquals(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?filterModel={"id":{"type":"notEqual","filter":3}}"""))

    def testGetFilterGreaterThan(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?filterModel={"id":{"type":"greaterThan","filter":3}}"""))

    def testGetFilterGreaterThanOrEqual(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?filterModel={"id":{"type":"greaterThanOrEqual","filter":3}}"""))

    def testGetFilterLessThan(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?filterModel={"id":{"type":"lessThan","filter":3}}"""))

    def testGetFilterLessThanOrEqual(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?filterModel={"id":{"type":"lessThanOrEqual","filter":3}}"""))

    def testGetFilterСontains(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?filterModel={"text":{"type":"contains","filter":"ест3"}}"""))

    def testGetFilterNotContains(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?filterModel={"text":{"type":"notContains","filter":"ест3"}}"""))

    def testGetFilterStartsWith(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?filterModel={"text":{"type":"startsWith","filter":"тест3"}}"""))

    def testGetFilterEndsWith(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?filterModel={"text":{"type":"endsWith","filter":"3"}}"""))

    def testGetFilterNone(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?filterModel={"text":{"type":"none"}}"""))

    def testGetFilterNotNone(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?filterModel={"text":{"type":"notNone"}}"""))

    def testGetId(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?id=3"""))

    def testGetLang(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?lang=en"""))

    def testGetComboBox(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/classifier_test_combobox/"""))

    def testGetComboBoxLang(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/classifier_test_combobox/?lang=en"""))

    def testGetIdWrong(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?id=12"""))

    def testGetFilterOperatorWrong(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?filterModel={"text":{"type":"bad"}}"""))

    def testGetFilterTypeWrong(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?filterModel={"bad":{"type":"notNone"}}"""))

    def testGetFilterValueWithWrong(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("""/class_fields_test/?filterModel={"text":{"type":"endsWith"}}"""))

    def testGetSortByWrong(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/class_fields_test/?sortBy=bad&descending=true&pageSize=5"))


if __name__ == '__main__':
    unittest.main()
