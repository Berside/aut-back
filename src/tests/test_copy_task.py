#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
import unittest
import pytest
import json
from src.db import db
from src.orm import orm_task
from src.tests.util_test import UtilTest, app_context
from src.tests.test_task import setup_classifiers_planning, teardown_db

utilTest = UtilTest(write_data_file=False)

@pytest.mark.usefixtures("app_context")
class TestCopyTask(unittest.TestCase):
    global utilTest

    def setUp(self):
        self.tearDown()
        setup_classifiers_planning()

    def tearDown(self):
        teardown_db()

    def test_copy_task_from_template(self):
        task_old_id = db.session.query(orm_task.Task).order_by(db.desc(orm_task.Task.id)).first().id
        task_zip_old_id = db.session.query(orm_task.TaskZip).order_by(db.desc(orm_task.TaskZip.id)).first().id
        task_tool_old_id = db.session.query(orm_task.TaskTool).order_by(db.desc(orm_task.TaskTool.id)).first().id
        task_prev_next_old_id = db.session.query(orm_task.TaskPreviousNext).order_by(db.desc(orm_task.TaskPreviousNext.id)).first().id
        db.session.flush()
        new_task = db.session.merge(orm_task.Task(name = "Test Task", type_link = 2))
        db.session.commit()
        utilTest.simple_test_api(self, utilTest.get_called_function_name(),
                                utilTest.client.post("/copy_task_from_template/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id_to" : new_task.id, "id_from" : 1})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_Task", db.session.query(orm_task.Task).
                                  filter(orm_task.Task.id > task_old_id).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TaskZip", db.session.query(orm_task.TaskZip).
                                  filter(orm_task.TaskZip.id > task_zip_old_id).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TaskTool", db.session.query(orm_task.TaskTool).
                                  filter(orm_task.TaskTool.id > task_tool_old_id).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TaskPreviousNext",
                                  db.session.query(orm_task.TaskPreviousNext).filter(orm_task.TaskPreviousNext.id > task_prev_next_old_id).count())


    def test_copy_template_from_task(self):
        task_old_id = db.session.query(orm_task.TemplateTask).order_by(db.desc(orm_task.TemplateTask.id)).first().id
        task_zip_old_id = db.session.query(orm_task.TemplateTaskZip).order_by(db.desc(orm_task.TemplateTaskZip.id)).first().id
        task_tool_old_id = db.session.query(orm_task.TemplateTaskTool).order_by(db.desc(orm_task.TemplateTaskTool.id)).first().id
        task_prev_next_old_id = db.session.query(orm_task.TemplateTaskPreviousNext).order_by(db.desc(orm_task.TemplateTaskPreviousNext.id)).first().id
        new_task = db.session.merge(orm_task.TemplateTask(name = "Test Task", type_link = 2))
        db.session.commit()
        utilTest.simple_test_api(self, utilTest.get_called_function_name(),
                                utilTest.client.post("/copy_template_from_task/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id_to" : new_task.id, "id_from" : 1})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTask", db.session.query(orm_task.TemplateTask).
                                  filter(orm_task.TemplateTask.id > task_old_id).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskZip", db.session.query(orm_task.TemplateTaskZip).
                                  filter(orm_task.TemplateTaskZip.id > task_zip_old_id).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskTool", db.session.query(orm_task.TemplateTaskTool).
                                  filter(orm_task.TemplateTaskTool.id > task_tool_old_id).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskPreviousNext",
                                  db.session.query(orm_task.TemplateTaskPreviousNext).filter(orm_task.TemplateTaskPreviousNext.id > task_prev_next_old_id).count())


    def test_copy_task_from_task(self):
        task_old_id = db.session.query(orm_task.Task).order_by(db.desc(orm_task.Task.id)).first().id
        task_zip_old_id = db.session.query(orm_task.TaskZip).order_by(db.desc(orm_task.TaskZip.id)).first().id
        task_tool_old_id = db.session.query(orm_task.TaskTool).order_by(db.desc(orm_task.TaskTool.id)).first().id
        task_prev_next_old_id = db.session.query(orm_task.TaskPreviousNext).order_by(db.desc(orm_task.TaskPreviousNext.id)).first().id
        new_task = db.session.merge(orm_task.Task(name = "Test Task", type_link = 2))
        db.session.commit()
        utilTest.simple_test_api(self, utilTest.get_called_function_name(),
                                utilTest.client.post("/copy_task_from_task/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id_to" : new_task.id, "id_from" : 1})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "row_Task",
                                  db.session.query(orm_task.Task).filter(orm_task.Task.id > task_old_id).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TaskZip", db.session.query(orm_task.TaskZip).
                                  filter(orm_task.TaskZip.id > task_zip_old_id).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TaskTool", db.session.query(orm_task.TaskTool).
                                  filter(orm_task.TaskTool.id > task_tool_old_id).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TaskPreviousNext",
                                  db.session.query(orm_task.TaskPreviousNext).filter(orm_task.TaskPreviousNext.id > task_prev_next_old_id).count())


    def test_copy_template_from_template(self):
        task_old_id = db.session.query(orm_task.TemplateTask).order_by(db.desc(orm_task.TemplateTask.id)).first().id
        task_zip_old_id = db.session.query(orm_task.TemplateTaskZip).order_by(db.desc(orm_task.TemplateTaskZip.id)).first().id
        task_tool_old_id = db.session.query(orm_task.TemplateTaskTool).order_by(db.desc(orm_task.TemplateTaskTool.id)).first().id
        task_prev_next_old_id = db.session.query(orm_task.TemplateTaskPreviousNext).order_by(db.desc(orm_task.TemplateTaskPreviousNext.id)).first().id
        new_task = db.session.merge(orm_task.TemplateTask(name = "Test Task", type_link = 2))
        db.session.commit()
        utilTest.simple_test_api(self, utilTest.get_called_function_name(),
                                utilTest.client.post("/copy_template_from_template/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id_to" : new_task.id, "id_from" : 1})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "row_TemplateTask",
                                  db.session.query(orm_task.TemplateTask).filter(orm_task.TemplateTask.id > task_old_id).all())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTask", db.session.query(orm_task.TemplateTask).
                                  filter(orm_task.TemplateTask.id > task_old_id).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskZip", db.session.query(orm_task.TemplateTaskZip).
                                  filter(orm_task.TemplateTaskZip.id > task_zip_old_id).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskTool", db.session.query(orm_task.TemplateTaskTool).
                                  filter(orm_task.TemplateTaskTool.id > task_tool_old_id).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskPreviousNext",
                                  db.session.query(orm_task.TemplateTaskPreviousNext).filter(orm_task.TemplateTaskPreviousNext.id > task_prev_next_old_id).count())

    def test_copy_template_from_template_post_template(self):
        task_old_id = db.session.query(orm_task.TemplateTask).order_by(db.desc(orm_task.TemplateTask.id)).first().id
        task_zip_old_id = db.session.query(orm_task.TemplateTaskZip).order_by(db.desc(orm_task.TemplateTaskZip.id)).first().id
        task_tool_old_id = db.session.query(orm_task.TemplateTaskTool).order_by(db.desc(orm_task.TemplateTaskTool.id)).first().id
        task_prev_next_old_id = db.session.query(orm_task.TemplateTaskPreviousNext).order_by(db.desc(orm_task.TemplateTaskPreviousNext.id)).first().id
        result_post = utilTest.client.post("/template_task/",
                             headers={"Content-Type": "application/json"}, data=json.dumps({"name": "Тест",
                                                                                            "assignee_link": 2, "type_link" :1}))
        result_post = json.loads(result_post.data)
        utilTest.simple_test_api(self, utilTest.get_called_function_name(),
                                utilTest.client.post("/copy_template_from_template/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id_to" : result_post.get("id"), "id_from" : 1})))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTask", db.session.query(orm_task.TemplateTask).
                                  filter(orm_task.TemplateTask.id > task_old_id).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskZip", db.session.query(orm_task.TemplateTaskZip).
                                  filter(orm_task.TemplateTaskZip.id > task_zip_old_id).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskTool", db.session.query(orm_task.TemplateTaskTool).
                                  filter(orm_task.TemplateTaskTool.id > task_tool_old_id).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskPreviousNext",
                                  db.session.query(orm_task.TemplateTaskPreviousNext).filter(orm_task.TemplateTaskPreviousNext.id > task_prev_next_old_id).count())


    def test_copy_template_from_template_10_times(self):
        task_old_id = db.session.query(orm_task.TemplateTask).order_by(db.desc(orm_task.TemplateTask.id)).first().id
        task_zip_old_id = db.session.query(orm_task.TemplateTaskZip).order_by(db.desc(orm_task.TemplateTaskZip.id)).first().id
        task_tool_old_id = db.session.query(orm_task.TemplateTaskTool).order_by(db.desc(orm_task.TemplateTaskTool.id)).first().id
        task_prev_next_old_id = db.session.query(orm_task.TemplateTaskPreviousNext).order_by(db.desc(orm_task.TemplateTaskPreviousNext.id)).first().id
        result_post_list = []
        for i in range(10):
            result_post = utilTest.client.post("/template_task/",
                                 headers={"Content-Type": "application/json"}, data=json.dumps({"name": "Тест",
                                                                                                "assignee_link": 2, "type_link" :1}))
            result_post = json.loads(result_post.data)
            result_post_list.append(result_post.get("id"))
        for i in result_post_list:
            utilTest.client.post("/copy_template_from_template/",
                headers={"Content-Type": "application/json"}, data=json.dumps({"id_to" : i, "id_from" : 1}))
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTask", db.session.query(orm_task.TemplateTask).
                                  filter(orm_task.TemplateTask.id > task_old_id).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskZip", db.session.query(orm_task.TemplateTaskZip).
                                  filter(orm_task.TemplateTaskZip.id > task_zip_old_id).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskTool", db.session.query(orm_task.TemplateTaskTool).
                                  filter(orm_task.TemplateTaskTool.id > task_tool_old_id).count())
        utilTest.simple_test_data(self, utilTest.get_called_function_name(), "count_TemplateTaskPreviousNext",
                                  db.session.query(orm_task.TemplateTaskPreviousNext).filter(orm_task.TemplateTaskPreviousNext.id > task_prev_next_old_id).count())



    def test_copy_task_from_template_id_from_empty_wrong(self):
        new_task = db.session.merge(orm_task.Task(name = "Test Task", type_link = 2))
        db.session.flush()
        utilTest.simple_test_api(self, utilTest.get_called_function_name(),
                                utilTest.client.post("/copy_task_from_template/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id_to" : new_task.id})))

    def test_copy_task_from_template_id_to_empty_wrong(self):
        new_task = db.session.merge(orm_task.Task(name = "Test Task", type_link = 2))
        db.session.flush()
        utilTest.simple_test_api(self, utilTest.get_called_function_name(),
                                utilTest.client.post("/copy_task_from_template/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id_from" : 1})))

    def test_copy_task_from_template_id_to_wrong(self):
        new_task = db.session.merge(orm_task.Task(name = "Test Task", type_link = 2))
        db.session.flush()
        utilTest.simple_test_api(self, utilTest.get_called_function_name(),
                                utilTest.client.post("/copy_task_from_template/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id_to" : 111111, "id_from" : 1})))

    def test_copy_task_from_template_id_from_wrong(self):
        new_task = db.session.merge(orm_task.Task(name = "Test Task", type_link = 2))
        db.session.flush()
        utilTest.simple_test_api(self, utilTest.get_called_function_name(),
                                utilTest.client.post("/copy_task_from_template/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id_to" : new_task.id, "id_from" : 1111111})))

    def test_copy_task_from_template_no_task_wrong(self):
        new_task = db.session.merge(orm_task.Task(name = "Test Task", type_link = 2))
        db.session.flush()
        utilTest.simple_test_api(self, utilTest.get_called_function_name(),
                                utilTest.client.post("/copy_task_from_template/",
            headers={"Content-Type": "application/json"}, data=json.dumps({"id_to" : new_task.id, "id_from" : 2})))

