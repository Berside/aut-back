#!/usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
import pytest
import json
from src.db import db
from src.task import factory_method_url_rules_task
from src.orm import orm_task, orm_sys
from src.tests.util_test import UtilTest, app_context

utilTest = UtilTest(write_data_file=False)

with utilTest.app.app_context():
    factory_method_url_rules_task(utilTest.app, utilTest.spec)


##Заполнение тестовых данных классификаторов
def setup_classifiers_planning():
    for sql_file_name in ["ver_data_0_init_cls.sql", "ver_data_0_init_okei.sql", "ver_data_1_init_list.sql", "ver_data_3_task.sql", "ver_data_5_template.sql"]:
        with open('sql/' + sql_file_name, 'r', encoding='utf-8') as sql_file:
            db.session.execute(db.text(sql_file.read()))
            db.session.commit()


def teardown_db():
    with open('sql/delete_bd.sql', 'r', encoding='utf-8') as sql_file:
        db.session.execute(db.text(sql_file.read()))
        db.session.commit()

@pytest.mark.usefixtures("app_context")
class TestPlanning(unittest.TestCase):
    global utilTest
    def setUp(self):
        self.tearDown()
        setup_classifiers_planning()

    def tearDown(self):
        teardown_db()

    def test_planning_columns_get(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.get("/planning_columns/"))

    def test_planning_properties_get(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.get("/planning_properties/"))

    def test_planning_get_repair_object_2(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.get("""/planning/?filterModel={"type_link":{"type":"equals","filter":2}}"""))

    def test_planning_get_children(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.get("""/planning/?filterModel={"parent_link":{"type":"equals","filter":1}}"""))

    def test_planning_get_part_9(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.get("""/planning/?filterModel={"type_link":{"type":"equals","filter":9}}"""))

    def test_planning_get_part_children(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.get("""/planning/?filterModel={"parent_link":{"type":"equals","filter":10}}"""))

    #todo не работает из-за отсутсвия правил удаления
    # def test_planning_delete(self):
    #     utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.delete("/planning/",
    #                                 headers={"Content-Type": "application/json"}, data=json.dumps({"id": 3})))
    #     utilTest.simple_test_data(self, utilTest.get_called_function_name(), "first", db.session.query(orm_task.Task).filter(orm_task.Task.id == 3).first())
    #     utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count", db.session.query(orm_task.Task).count())

    def test_planning_update(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning/",
                                    headers={"Content-Type": "application/json"}, data=json.dumps({"id": 1, "name" : "Тест"})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "name", db.session.query(orm_task.Task).filter(orm_task.Task.id == 1).first().name)
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count", db.session.query(orm_task.Task).count())

    def test_planning_update_wrong(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning/",
                                    headers={"Content-Type": "application/json"}, data=json.dumps({"id": 1, "name" : "Тест", "bad" : "bad"})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "name", db.session.query(orm_task.Task).filter(orm_task.Task.id == 1).first().name)
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count", db.session.query(orm_task.Task).count())

    def test_planning_post_zip(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"name" : "Тест",
            "assignee_link" : 1, "start_date" : "02-03-2026", "end_date" : "'03-03-2026'",
            "type_link" : 1,
            "TaskTool" : [{"tool_link": 1}, {"tool_link": 2}],
            "TaskZip" : [{"zip_link": 8, "kol_pln" : 5}, {"zip_link": 9, "kol_pln" : 3}]
        })))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "row_Task",
                                  db.session.query(orm_task.Task).order_by(db.desc(orm_task.Task.id)).first())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_Task", db.session.query(orm_task.Task).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TaskZip", db.session.query(orm_task.TaskZip).filter(orm_task.TaskZip.id > 2).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "rows_TaskZip",
                                  db.session.query(orm_task.TaskZip).filter(orm_task.TaskZip.id > 2).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TaskTool", db.session.query(orm_task.TaskTool).filter(orm_task.TaskTool.id > 6).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "rows_TaskTool",
                                  db.session.query(orm_task.TaskTool).filter(orm_task.TaskTool.id > 6).all())

    def test_planning_post_wrong(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"name" : "Тест",
            "assignee_link" : 1, "start_date" : "02-03-2026", "end_date" : "'03-03-2026'",
            "labor_costs" : 20, "type_link" : 1, "bad" : 534,
            "TaskTool" : [{"tool_link": 1}, {"tool_link": 2}],
            "TaskZip" : [{"zip_link": 8, "kol_pln" : 5}, {"zip_link": 9, "kol_pln" : 3}]
        })))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "row_Task",
                                  db.session.query(orm_task.Task).order_by(db.desc(orm_task.Task.id)).first())

    def test_planning_post_status_link_wrong(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"name" : "Тест",
            "assignee_link" : 1, "start_date" : "02-03-2026", "end_date" : "'03-03-2026'",
            "labor_costs" : 20, "type_link" : 1, "bad" : 534, "status_link" : 2,
            "TaskTool" : [{"tool_link": 1}, {"tool_link": 2}],
            "TaskZip" : [{"zip_link": 8, "kol_pln" : 5}, {"zip_link": 9, "kol_pln" : 3}]
        })))


    def test_planning_post_taskarticlework(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"name" : "Тест",
            "TaskArticleWork": {"object_link" : 1}})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TaskArticleWork", db.session.query(orm_task.TaskArticleWork).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "rows_TaskArticleWork",
                                  db.session.query(orm_task.TaskArticleWork).filter(orm_task.TaskArticleWork.id > 1).all())

    def test_planning_post_taskarticlework_wrong(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"name" : "Тест",
            "TaskArticleWork": {"bad_field" : 1}})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TaskArticleWork", db.session.query(orm_task.TaskArticleWork).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "rows_TaskArticleWork",
                                  db.session.query(orm_task.TaskArticleWork).filter(orm_task.TaskArticleWork.id > 1).all())

    def test_planning_post_previous_next(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"name" : "Тест",
            "assignee_link" : 2, "start_date" : "02-03-2026", "end_date" : "'03-03-2026'",
            "type_link" : 1, "parent_link" : 2,
            "NextTask" : 7
        })))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "row_Task",
                                  db.session.query(orm_task.Task).order_by(db.desc(orm_task.Task.id)).first())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_Task", db.session.query(orm_task.Task).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "rows_TaskPreviousNext",
                                  db.session.query(orm_task.TaskPreviousNext).order_by(db.desc(orm_task.TaskPreviousNext.id)).limit(1).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TaskPreviousNext", db.session.query(orm_task.TaskPreviousNext).count())

    def test_planning_post_previous_next_choice(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"name" : "Тест",
            "assignee_link" : 2, "start_date" : "02-03-2026", "end_date" : "'03-03-2026'",
            "type_link" : 1, "parent_link" : 2,
            "NextTask" : 7, "ChoiceNegTask" : 8
        })))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "row_Task",
                                  db.session.query(orm_task.Task).order_by(db.desc(orm_task.Task.id)).first())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_Task", db.session.query(orm_task.Task).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "rows_TaskPreviousNext",
                                  db.session.query(orm_task.TaskPreviousNext).order_by(db.desc(orm_task.TaskPreviousNext.id)).limit(1).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TaskPreviousNext", db.session.query(orm_task.TaskPreviousNext).count())

    def test_planning_form_get_1(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.get("/planning_form/?id=1"))

    def test_planning_form_get_3(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.get("/planning_form/?id=3"))

    def test_planning_form_get_19(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.get("/planning_form/?id=19"))

    def test_planning_form_get_22(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.get("/planning_form/?id=22"))

    def test_planning_form_get_recursive_children(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.get("/planning_form/?id=1&recursive_children=1"))

    def test_planning_form_post_start_1(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning_form/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id": 1, "status_link" : 2})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Task",
                                  db.session.query(orm_task.Task).filter(orm_task.Task.id.in_([1,2])).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Notification",
                                  db.session.query(orm_sys.Notification).all())


    def test_planning_form_post_start_3(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning_form/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id": 3, "status_link" : 2})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Task",
                                  db.session.query(orm_task.Task).filter(orm_task.Task.id.in_([3])).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Notification",
                                  db.session.query(orm_sys.Notification).all())

    def test_planning_form_post_start_10(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning_form/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id": 10, "status_link" : 2})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Task",
                                  db.session.query(orm_task.Task).filter(orm_task.Task.id.in_([10, 11])).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Notification",
                                  db.session.query(orm_sys.Notification).all())

    def test_planning_form_post_end_2(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning_form/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id": 2, "status_link" : 3})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Task",
                                  db.session.query(orm_task.Task).filter(orm_task.Task.id.in_([2,3])).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Notification",
                                  db.session.query(orm_sys.Notification).all())


    def test_planning_form_post_end_3(self):
        task = db.session.get(orm_task.Task, 3)
        task.start_date = '15-03-2026'
        db.session.flush()
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning_form/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id": 3, "status_link" : 3})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Task",
                                  db.session.query(orm_task.Task).filter(orm_task.Task.id.in_([3,4])).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Notification",
                                  db.session.query(orm_sys.Notification).all())

    def test_planning_form_post_end_9(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning_form/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id": 9, "status_link" : 3})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Task",
                                  db.session.query(orm_task.Task).filter(orm_task.Task.id.in_([9, 10, 11])).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Notification",
                                  db.session.query(orm_sys.Notification).all())

    def test_planning_form_post_end_41(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning_form/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id": 41, "status_link" : 3})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Task",
                                  db.session.query(orm_task.Task).filter(orm_task.Task.id.in_([10, 41, 42])).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Notification",
                                  db.session.query(orm_sys.Notification).all())

    def test_planning_form_post_end_55(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning_form/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id": 55, "status_link" : 3})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Task",
                                  db.session.query(orm_task.Task).filter(orm_task.Task.id.in_([1, 55])).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Notification",
                                  db.session.query(orm_sys.Notification).all())

    def test_planning_form_post_condition_wrong(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning_form/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id": 55, "status_link" : 3, "condition" : True})))

    def test_planning_form_post_condition_empty_wrong(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning_form/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id": 19, "status_link" : 3})))

    def test_planning_form_post_condition_true(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning_form/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id": 19, "status_link" : 3, "condition" : True})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Task",
                                  db.session.query(orm_task.Task).filter(orm_task.Task.id.in_([19, 20, 22])).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Notification",
                                  db.session.query(orm_sys.Notification).all())

    def test_planning_form_post_condition_false(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/planning_form/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id": 19, "status_link" : 3, "condition" : False})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Task",
                                  db.session.query(orm_task.Task).filter(orm_task.Task.id.in_([19, 20, 22])).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "Notification",
                                  db.session.query(orm_sys.Notification).all())

@pytest.mark.usefixtures("app_context")
class TestTemplateTask(unittest.TestCase):
    global utilTest
    def setUp(self):
        self.tearDown()
        setup_classifiers_planning()

    def tearDown(self):
        teardown_db()

    def test_template_task_get_2(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.get("""/template_task/?filterModel={"type_link":{"type":"equals","filter":2}}"""))

    def test_template_task_get_children(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.get("""/template_task/?filterModel={"parent_link":{"type":"equals","filter":1}}"""))

    def test_template_task_get_part_9(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.get("""/template_task/?filterModel={"type_link":{"type":"equals","filter":9}}"""))

    def test_template_task_get_part_children(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.get("""/template_task/?filterModel={"parent_link":{"type":"equals","filter":10}}"""))

    def test_template_task_get_filter(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(),
                                utilTest.client.get("""/template_task/?filterModel={"id": {"type": "notNone"}}"""))

    def test_template_task_post(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/template_task/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"name" : "Тест",
            "assignee_link" : 2,
        })))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "row_TemplateTaskArticleWork",
                                  db.session.query(orm_task.TemplateTaskArticleWork).order_by(db.desc(orm_task.TemplateTaskArticleWork.id)).first())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskArticleWork", db.session.query(orm_task.TemplateTaskArticleWork).count())

    def test_template_task_columns(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.get("/template_task_columns/"))

    def test_template_task_form(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.get("/template_task_form/?id=3"))

    # def test_template_task_delete(self):
    #     utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.delete("/template_task/",
    #                                 headers={"Content-Type": "application/json"}, data=json.dumps({"id": 3})))
    #     utilTest.simple_test_data(self, utilTest.get_called_function_name(), "first", db.session.query(orm_task.TemplateTask).filter(orm_task.TemplateTask.id == 3).first())
    #     utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count", db.session.query(orm_task.TemplateTask).count())

    def test_template_task_update(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/template_task/",
                                    headers={"Content-Type": "application/json"}, data=json.dumps({"id": 1, "name" : "Тест"})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "name", db.session.query(orm_task.TemplateTask).filter(orm_task.TemplateTask.id == 1).first().name)
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count", db.session.query(orm_task.TemplateTask).count())

    def test_template_task_update_wrong(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/template_task/",
                                    headers={"Content-Type": "application/json"}, data=json.dumps({"id": 1, "name" : "Тест", "bad" : "bad"})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "name", db.session.query(orm_task.TemplateTask).filter(orm_task.TemplateTask.id == 1).first().name)
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count", db.session.query(orm_task.TemplateTask).count())

    def test_template_task_post_zip(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/template_task/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"name" : "Тест",
            "assignee_link" : 1,
            "type_link" : 1,
            "TaskTool" : [{"tool_link": 1}, {"tool_link": 2}],
            "TaskZip" : [{"zip_link": 8, "kol_pln" : 5}, {"zip_link": 9, "kol_pln" : 3}]
        })))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "row_TemplateTask",
                                  db.session.query(orm_task.TemplateTask).order_by(db.desc(orm_task.TemplateTask.id)).first())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTask", db.session.query(orm_task.TemplateTask).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskZip", db.session.query(orm_task.TemplateTaskZip).filter(orm_task.TemplateTaskZip.id > 2).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "rows_TemplateTaskZip",
                                  db.session.query(orm_task.TemplateTaskZip).filter(orm_task.TemplateTaskZip.id > 2).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskTool", db.session.query(orm_task.TemplateTaskTool).filter(orm_task.TemplateTaskTool.id > 6).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "rows_TemplateTaskTool",
                                  db.session.query(orm_task.TemplateTaskTool).filter(orm_task.TemplateTaskTool.id > 6).all())

    def test_template_task_post_wrong(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/template_task/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"name" : "Тест",
            "assignee_link" : 1,
            "type_link" : 1, "bad" : 534,
            "TaskTool" : [{"tool_link": 1}, {"tool_link": 2}],
            "TaskZip" : [{"zip_link": 8, "kol_pln" : 5}, {"zip_link": 9, "kol_pln" : 3}]
        })))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "row_TemplateTask",
                                  db.session.query(orm_task.TemplateTask).order_by(db.desc(orm_task.TemplateTask.id)).first())

    def test_template_task_post_TemplateTaskArticleWork(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/template_task/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"name" : "Тест",
            "TemplateTaskArticleWork": {"object_link" : 4}})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskArticleWork", db.session.query(orm_task.TemplateTaskArticleWork).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "rows_TemplateTaskArticleWork",
                                  db.session.query(orm_task.TemplateTaskArticleWork).filter(orm_task.TemplateTaskArticleWork.id > 1).all())

    def test_template_task_post_TemplateTaskArticleWork_wrong(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/template_task/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"name" : "Тест",
            "TemplateTaskArticleWork": {"bad_field" : 1}})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskArticleWork", db.session.query(orm_task.TemplateTaskArticleWork).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "rows_TemplateTaskArticleWork",
                                  db.session.query(orm_task.TemplateTaskArticleWork).filter(orm_task.TemplateTaskArticleWork.id > 1).all())

    def test_template_task_post_previous_next(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/template_task/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"name" : "Тест",
            "assignee_link" : 2,
            "type_link" : 1, "parent_link" : 2,
            "NextTask" : 7
        })))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "row_TemplateTask",
                                  db.session.query(orm_task.TemplateTask).order_by(db.desc(orm_task.TemplateTask.id)).first())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTask", db.session.query(orm_task.TemplateTask).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "rows_TemplateTaskPreviousNext",
                                  db.session.query(orm_task.TemplateTaskPreviousNext).order_by(db.desc(orm_task.TemplateTaskPreviousNext.id)).limit(1).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskPreviousNext", db.session.query(orm_task.TemplateTaskPreviousNext).count())

    def test_template_task_post_previous_next_choice(self):
        utilTest.simple_test_api(self, utilTest.get_called_function_name(), utilTest.client.post("/template_task/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"name" : "Тест",
            "assignee_link" : 2,
            "type_link" : 1, "parent_link" : 2,
            "NextTask" : 7, "ChoiceNegTask" : 8
        })))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "row_TemplateTask",
                                  db.session.query(orm_task.TemplateTask).order_by(db.desc(orm_task.TemplateTask.id)).first())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTask", db.session.query(orm_task.TemplateTask).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "rows_TemplateTaskPreviousNext",
                                  db.session.query(orm_task.TemplateTaskPreviousNext).order_by(db.desc(orm_task.TemplateTaskPreviousNext.id)).limit(1).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskPreviousNext", db.session.query(orm_task.TemplateTaskPreviousNext).count())
