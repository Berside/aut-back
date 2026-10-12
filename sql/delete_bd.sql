SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET escape_string_warning = off;
SET row_security = off;


-- ver_data_5_template.sql
DELETE FROM task.Template_Task_Article_Work;
DELETE FROM task.template_task_zip;
DELETE FROM task.template_task_tool;
DELETE FROM task.template_task_previous_next;
DELETE FROM task.template_task;


-- ver_data_4_doc.sql
DELETE FROM doc.order_content;
DELETE FROM doc.order;
DELETE FROM doc.repair_act;
DELETE FROM list.list_repair_documentation;
DELETE FROM doc.commission_initial_readings_report;
DELETE FROM doc.initial_readings_report;
DELETE FROM doc.Appendix_Receive_Transfer;
DELETE FROM doc.receive_transfer;


-- ver_data_3_task.sql
DELETE FROM task.Task_Article_Work;
DELETE FROM task.task_zip;
DELETE FROM task.task_tool;
DELETE FROM task.task_previous_next;
DELETE FROM task.task;


--ver_data_2_cls_list.sql
DELETE FROM cls.classifiers_list;


-- ver_data_1_init_list.sql
DELETE FROM list.list_technological_equipment;
DELETE FROM list.list_employee;
DELETE FROM list.list_resources;
DELETE FROM list.list_military_unit;
DELETE FROM list.list_resource_location;
DELETE FROM list.list_department;
DELETE FROM list.list_specifications_article;
DELETE FROM list.list_article;


-- ver_data_0_init_okei.sql
DELETE FROM cls.dict_okei;


-- ver_data_0_init_cls.sql
DELETE FROM cls.dict_type_document;
DELETE FROM cls.dict_type_task;
DELETE FROM cls.dict_absence_cause;
DELETE FROM cls.Dict_article_structure;
DELETE FROM cls.dict_resource;
DELETE FROM cls.dict_resource_type;
DELETE FROM cls.dict_resource_category;
DELETE FROM cls.dict_location_type;
DELETE FROM cls.dict_job_title;
DELETE FROM cls.dict_military_rank;
DELETE FROM cls.dict_kind_repair;
DELETE FROM cls.dict_status_task;










