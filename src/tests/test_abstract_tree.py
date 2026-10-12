#!/usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
import pytest
from src import abstract_tree
from src.orm import orm_cls
from src.db import db

from src.tests.util_test import UtilTest, app_context

utilTest = UtilTest(write_data_file=False)

abstract_tree.subclass_abstract_tree_orm_list = [
    orm_cls.ClassifiersList
]

abstract_tree.factory_function_tree_url_rules(utilTest.app, utilTest.spec)

@pytest.mark.usefixtures("app_context")
class TestAbstractTable(unittest.TestCase):
    global utilTest
    def setUp(self):
        self.tearDown()
        db.session.execute(db.text("""
        INSERT INTO cls.classifiers_list (id, name_ru, class_path, table_name, "schema", parent_link) VALUES
        (0, 'Список классификаторов', 'src.orm.orm_cls.ClassifiersList', 'classifiers_list', 'cls', null),
        (4,'Категории технического состояния', 'src.orm.orm_cls.CategoriesTechnicalCondition', 'categories_technical_condition', 'cls', 0),
        (5,'Папка 1', 'src.orm.orm_cls.CategoriesTechnicalCondition', 'categories_technical_condition', 'cls', 0),
        (6,'Тест 1', 'src.orm.orm_cls.CategoriesTechnicalCondition', 'categories_technical_condition', 'cls', 5),
        (7,'Тест 2', 'src.orm.orm_cls.CategoriesTechnicalCondition', 'categories_technical_condition', 'cls', 5);"""))
        db.session.execute(db.text("""select setval(pg_get_serial_sequence('task.task','id'), 6);"""))

    def tearDown(self):
        db.session.execute(db.text("delete from cls.classifiers_list;"))

    def testGetClassifiersListShort(self):
        db.session.execute(db.text("delete from cls.classifiers_list where id > 4;"))
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/classifiers_list_tree/"))

    def testGetClassifiersList(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/classifiers_list_tree/"))

    def testGetClassifiersListEmpty(self):
        db.session.execute(db.text("delete from cls.classifiers_list;"))
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.
            get("/classifiers_list_tree/"))

if __name__ == '__main__':
    unittest.main()
