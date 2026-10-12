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

INSERT INTO cls.classifiers_list
(id, name_ru, name_en, class_path, table_name, schema) VALUES
--(0, 'Список классификаторов', 'Classifiers list', 'src.orm.orm_cls.ClassifiersList', 'classifiers_list', 'cls'),
(DEFAULT,'Справочник типов задач', 'Dict Type Task', 'src.orm.orm_cls.DictTypeTask', 'dict_type_task', 'cls'),
(DEFAULT,'Справочник статусов задач', 'Dict status task', 'src.orm.orm_cls.DictStatusTask', 'dict_status_task', 'cls'),
(DEFAULT,'Справочник видов ремонтных работ', 'Dict kind repair', 'src.orm.orm_cls.DictKindRepair', 'dict_kind_repair', 'cls'),
(DEFAULT,'Справочник воинских званий', 'Dict Military Rank', 'src.orm.orm_cls.DictMilitaryRank', 'dict_military_rank', 'cls'),
(DEFAULT,'Справочник типов документов', 'Dict type document', 'src.orm.orm_cls.DictTypeDocument', 'dict_type_document', 'cls'),
(DEFAULT,'Справочник должностей', 'Dict Job Title', 'src.orm.orm_cls.DictJobTitle', 'dict_job_title', 'cls'),
(DEFAULT,'Справочник типов местоположений', 'Dict Location Type', 'src.orm.orm_cls.DictLocationType', 'dict_location_type', 'cls'),
(DEFAULT,'Общероссийский классификатор единиц измерения (ОКЕИ)', 'OKEI', 'src.orm.orm_cls.DictOkei', 'dict_okei', 'cls'),
(DEFAULT,'Справочник типов материальных ценностей', 'Dict Resource Type', 'src.orm.orm_cls.DictResourceType', 'dict_resource_type', 'cls'),
(DEFAULT,'Справочник категорий материальных ценностей', 'Dict Resource Category', 'src.orm.orm_cls.DictResourceCategory', 'dict_resource_category', 'cls'),
(DEFAULT,'Справочник материальных ценностей', 'Dict Resource', 'src.orm.orm_cls.DictResource', 'dict_resource', 'cls'),
(DEFAULT,'Справочник состава изделий', 'Dict Article Structure', 'src.orm.orm_cls.DictArticleStructure', 'dict_article_structure', 'cls'),
(DEFAULT,'Справочник основания отсутствия', 'Dict absence Cause', 'src.orm.orm_cls.DictAbsenceCause', 'dict_absence_cause', 'cls'),
(DEFAULT,'Реестр сотрудников', 'List Employee', 'src.orm.orm_list.ListEmployee', 'list_employee', 'list'),
(DEFAULT,'Реестр местоположений материальных ценностей', 'Resource Location', 'src.orm.orm_list.ListResourceLocation', 'list_resource_location', 'list'),
(DEFAULT,'Реестр ВФ', 'Military Unit', 'src.orm.orm_list.ListMilitaryUnit', 'list_military_unit', 'list'),
(DEFAULT,'Реестр технологического оборудования', 'Technological Equipment', 'src.orm.orm_list.ListTechnologicalEquipment', 'list_technological_equipment', 'list'),
(DEFAULT,'Подразделения', 'ListDepartment', 'src.orm.orm_list.ListDepartment', 'list_department', 'list'),
(DEFAULT,'Реестр изделий', 'ListArticle', 'src.orm.orm_list.ListArticle', 'list_article', 'list'),
(DEFAULT,'Технико-эксплуатационные показатели изделия', 'ListSpecificationsArticle', 'src.orm.orm_list.ListSpecificationsArticle', 'list_specifications_article', 'list'),
(DEFAULT,'Реестр ремонтной документации', 'ListRepairDocumentation', 'src.orm.orm_list.ListRepairDocumentation', 'list_repair_documentation', 'list'),
(DEFAULT,'Реестр ЗИП', 'ListResources', 'src.orm.orm_list.ListResources', 'list_resources', 'list');
