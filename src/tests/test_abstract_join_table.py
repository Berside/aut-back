#!/usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
import pytest
import json
from src import abstract_join_table
from src.tests.orm_test import populate_join_test_tables, ClassJoinTest, ClassifierTestTwo, ClassifierTest
from src.orm import orm_task, orm_file
from src.db import db

from src.tests.util_test import UtilTest, app_context

utilTest = UtilTest(write_data_file=False)


abstract_join_table.subclass_abstract_join_table_list = [
    {
        "url" : "class_join_test",
        "cls" : ClassJoinTest,
        "join_tables" : [ClassifierTestTwo, ClassifierTest],
        "column_list_get" : ["id", "text", "classifier_two_link", "ClassifierTestTwo.name_two",
                            "ClassifierTestTwo.ClassifierTest.name"],
        "formColumns" : ["id", "text", "classifier_two_link"],
        "defaultVisibleColumns" : ["text", "ClassifierTestTwo.name_two",
                            "ClassifierTestTwo.ClassifierTest.name"],
        "rowKey" : "id"
    }
]
abstract_join_table.factory_function_join_tables_url_rules(utilTest.app)


@pytest.mark.usefixtures("app_context")
class TestAbstractJoinTable(unittest.TestCase):
    def setUp(self):
        populate_join_test_tables()

    def testGetPage1(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
                                get("/class_join_test/?startRow=1&pageSize=2"))

    def testGetSortBy(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
                                get("/class_join_test/?sortBy=id&descending=true&pageSize=5"))

    def testGetSortClassifierDesc(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
                                get("/class_join_test/?sortBy=ClassifierTestTwo.ClassifierTest.name&descending=false"))

    def testGetSortClassifierAsc(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
                                get("/class_join_test/?sortBy=ClassifierTestTwo.ClassifierTest.name&descending=true"))

    def testGetFilterStr3(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
                                get("/class_join_test/?filterStr=oo5"))

    def testGetFilterClassifier(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
                                get("/class_join_test/?filterStr=тест"))

    def testGetFilterClassifier2(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
                                get("/class_join_test/?filterStr=boo3"))

    def testGetFilterClassifier3(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
                                get("/class_join_test/?filterStr=проверка2"))

    def testGetColumns(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
                                get("/class_join_test_columns/"))

    def testGetProperties(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
                                get("/class_join_test_properties/"))

    def testGetFilterClassifierEmpty(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
                                get("/class_join_test/?filterStr=Спам3"))

    def testGetFilterEquals(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
                                get("""/class_join_test/?filterModel={"ClassifierTestTwo.ClassifierTest.name":{"type":"equals","filter":"Спам"}}"""))

    def testGetFilterСontains(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
                                get(
            """/class_join_test/?filterModel={"ClassifierTestTwo.name_two":{"type":"contains","filter":"верка2"}}"""))

    def testPost(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/class_join_test/", headers={"Content-Type": "application/json"},
                                data=json.dumps({"text": 'Тест', "classifier_two_link": 3})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count",
                                db.session.query(ClassJoinTest).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "title",
                                db.session.query(ClassJoinTest).order_by(db.desc(ClassJoinTest.id)).first())

    def testDelete(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.delete("/class_join_test/", headers={"Content-Type": "application/json"},
                                data=json.dumps({"id": 3})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count",
                                db.session.query(ClassJoinTest).count())

    def testGetFilterValueWithWrong(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
                                get("""/class_join_test/?filterModel={"ClassifierTestTwo.ClassifierTest.bad":{"type":"equals"}}"""))

    def testGetSortByWrong(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
                                get("/class_join_test/?sortBy=ClassifierTestTwo.ClassifierTest.bad&descending=true&pageSize=5"))


if __name__ == '__main__':
    unittest.main()
