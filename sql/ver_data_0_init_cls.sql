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


INSERT INTO cls.dict_status_task (id, name_ru, name_en, note) VALUES
(1, 'Новая', 'New', 'Задача создана, но еще не назначена'),
(2, 'Назначена', 'Assigned', 'Задача назначена исполнителю'),
(3, 'Выполнена', 'Completed', 'Задача полностью завершена'),
(4, 'В работе', 'In Progress', 'Исполнитель приступил к выполнению задачи'),
(5, 'Частично выполнена', 'Partially Completed', 'Часть задачи выполнена, остается продолжить'),
(6, 'Отменена', 'Cancelled', 'Задача отменена по причине'),
(7, 'Приостановлена', 'Paused', 'Задача временно приостановлена'),
(8, 'Завершена', 'Finished', 'Задача завершена и закрыта'),
(9, 'На уточнении', 'Awaiting Clarification', 'Требуется уточнение информации по задаче'),
(10, 'На согласовании', 'Awaiting Approval', 'Задача ожидает согласования'),
(11, 'Отложена', 'Postponed', 'Задача отложена на более позднее время'),
(12, 'В ожидании', 'Pending', 'Задача ожидает необходимых ресурсов или условий'),
(13, 'Просрочена', 'Overdue', 'Задача не выполнена в установленный срок'),
(14, 'На проверке', 'Under Review', 'Задача находится на проверке качества'),
(15, 'На тестировании', 'Under Testing', 'Задача находится на этапе тестирования'),
(16, 'На модерации', 'Under Moderation', 'Задача ожидает модерации'),
(17, 'В архиве', 'Archived', 'Задача перемещена в архив'),
(18, 'Необходимо уточнить', 'Need Clarification', 'Требуется дополнительная информация'),
(19, 'Необходимо согласовать', 'Need Approval', 'Требуется согласование с руководством'),
(20, 'Завершена с замечаниями', 'Completed with Remarks', 'Задача завершена, но есть замечания');
SELECT setval(pg_get_serial_sequence('cls.dict_status_task','id'), 20);


INSERT INTO cls.dict_kind_repair (id, name_ru, note) VALUES
(1, 'Техническое обслуживание № 2 при хранении', null),
(2, 'Техническое обслуживание № 1', null),
(3, 'Сезонное техническое обслуживание', null),
(4, 'Техническое обслуживание № 1 при хранении', null),
(5, 'Регламентированное техническое обслуживание', null),
(6, 'Ежедневное техническое обслуживание', null),
(7, 'Единое техническое обслуживание', null),
(8, 'Средний ремонт', null),
(9, 'Текущий ремонт', null),
(10, 'Ремонт по техническому состоянию', null),
(11, 'Ремонт в стационарных условиях', null),
(12, 'Ремонт в полевых условиях', null),
(13, 'Капитальный ремонт', null),
(14, 'Капитальный ремонт с модернизацией и (или) заменой автомобильного базового шасси', null),
(15, 'Гарантийный ремонт', null),
(16, 'Регламентированный ремонт', null),
(17, 'Регламентированный ремонт с модернизацией и (или) заменой автомобильного базового шасси', null),
(18, 'Техническое обслуживание № 2', null),
(19, 'Техническое обслуживание № 2 при хранении с переконсервацией и контрольным пробегом', null);
SELECT setval(pg_get_serial_sequence('cls.dict_kind_repair','id'), 19);



INSERT INTO cls.dict_military_rank (id, name_ru, name_en, note) VALUES
(1, 'Майор', 'Major', 'Командный ранг'),
(2, 'Подполковник', 'Lieutenant Colonel', 'Командный ранг'),
(3, 'Полковник', 'Colonel', 'Командный ранг'),
(4, 'Капитан', 'Captain', 'Командный ранг'),
(5, 'Старший лейтенант', 'Senior Lieutenant', 'Командный ранг'),
(6, 'Лейтенант', 'Lieutenant', 'Командный ранг'),
(7, 'Сержант', 'Sergeant', 'Комендантский ранг'),
(8, 'Старший сержант', 'Senior Sergeant', 'Комендантский ранг'),
(9, 'Прапорщик', 'Warrant Officer', 'Комендантский ранг'),
(10, 'Рядовой', 'Private', 'Комендантский ранг'),
(11, 'Ефрейтор', 'Corporal', 'Комендантский ранг'),
(12, 'Младший сержант', 'Junior Sergeant', 'Комендантский ранг'),
(13, 'Мастер-сержант', 'Master Sergeant', 'Комендантский ранг'),
(14, 'Старший мастер-сержант', 'Senior Master Sergeant', 'Комендантский ранг'),
(15, 'Главный мастер-сержант', 'Chief Master Sergeant', 'Комендантский ранг'),
(16, 'Младший лейтенант', 'Junior Lieutenant', 'Командный ранг'),
(17, 'Капитан', 'Captain', 'Командный ранг'),
(18, 'Подполковник', 'Lieutenant Colonel', 'Командный ранг'),
(19, 'Полковник', 'Colonel', 'Командный ранг');
SELECT setval(pg_get_serial_sequence('cls.dict_military_rank','id'), 19);


INSERT INTO cls.dict_job_title (id, name_ru, name_en, parent_link, note) VALUES
(1, 'Начальник отдела', 'Department Head', null, 'Руководитель отдела'),
(2, 'Заместитель начальника отдела', 'Deputy Department Head', 1, 'Заместитель начальника отдела'),
(3, 'Главный инженер', 'Chief Engineer', 1, 'Главный инженер отдела'),
(4, 'Инженер-электроник', 'Electronics Engineer', 3, 'Инженер по электронике'),
(5, 'Инженер-радиотехник', 'Radio Engineer', 3, 'Инженер по радиотехнике'),
(6, 'Инженер-программист', 'Software Engineer', 3, 'Программист'),
(7, 'Техник', 'Technician', 4, 'Техник по ремонту'),
(8, 'Механик', 'Mechanic', 4, 'Механик по ремонту'),
(9, 'Слесарь', 'Fitter', 4, 'Слесарь'),
(10, 'Оператор', 'Operator', 4, 'Оператор оборудования'),
(11, 'Ремонтник', 'Repairman', 4, 'Ремонтник'),
(12, 'Инженер-конструктор', 'Design Engineer', 3, 'Конструктор'),
(13, 'Инженер-испытатель', 'Test Engineer', 3, 'Инженер по испытаниям'),
(14, 'Инженер-проектировщик', 'Design Engineer', 3, 'Проектировщик'),
(15, 'Инженер-технолог', 'Process Engineer', 3, 'Технолог');
SELECT setval(pg_get_serial_sequence('cls.dict_job_title','id'), 15);


INSERT INTO cls.dict_location_type (id, name_ru, name_en, date_deletion, note) VALUES
(1, 'Стеллаж', 'Rack', null, ''),
(2, 'Полка', 'Shelf', null, ''),
(3, 'Место', 'Place', null, ''),
(4, 'Укладка', 'Placement', null, '');
select setval(pg_get_serial_sequence('cls.dict_location_type','id'), 4);


INSERT INTO cls.dict_resource_category (id, name_ru, name_en, date_deletion, note) VALUES
(1, 'ЗИП', 'ZIP', null, '');
select setval(pg_get_serial_sequence('cls.dict_resource_category','id'), 1);


INSERT INTO cls.dict_resource_type (id, name_ru, name_en, date_deletion, note) VALUES
(1, 'Конденсатор', 'Capacitor', null, ''),
(2, 'Транзистор ', 'Transistor', null, ''),
(3, 'Микросхема', 'Microcircuit', null, ''),
(4, 'Блок', 'Block', null, ''),
(5, 'Дроссель', 'Сhoke', null, ''),
(6, 'Катушка', 'Coil', null, ''),
(7, 'Стабилитрон', 'Stabilitron', null, ''),
(8, 'Резистор', 'Resistor', null, ''),
(9, 'Терморезистор', 'Termoresistor', null, ''),
(10, 'Матрица', 'Matrix', null, '');

select setval(pg_get_serial_sequence('cls.dict_resource_type','id'), 10);


INSERT INTO cls.dict_resource (id, name_ru, name_en, type_link, designation_ru, designation_en, category_link, date_deletion, note) VALUES
(1, 'К10-17а-М47-120 пФ±10%-В', 'K10-17a-M47-120 pF±10%-V', 2, 'Конденсатор ОЖ0.460.107ТУ', 'Capacitor ОЖ0.460.107ТУ', 1, null, ''),
(2, '2Т368А9/ПК', '2T368A9/PK', 3, 'Транзистор АУЯР.432140.380ТУ', 'Transistor АУЯР.432140.380ТУ', 1, null, ''),
(3, '1564ЛА2', '1564LA2', 4, 'Микросхема бК0.347.479-05ТУ', 'Microcircuit бК0.347.479-05ТУ', 1, null, ''),
(4, 'Б19К-1-1-200 кОм±5%', 'B1K-1-1-200 kOm±5%', 5, 'Блок ОЖ0.206.018ТУ', 'Block ОЖ0.206.018ТУ', 1, null, ''),
(5, 'ДМ-0,1-80±5%В', 'DM-0,1-80±5%V', 1, 'Дроссель высокочастотный ЦКСН.671342.001ТУ', 'High frequincy choke ЦКСН.671342.001ТУ', 1, null, ''),
(6, 'ЫК4.777.240-01', 'IK4.777.240-01', 1, 'Катушка индуктивности В 0,22 ЫК0.477.002ТУ', 'Inductance coil В 0,22 ЫК0.477.002ТУ', 1, null, ''),
(7, '2С530А1', '2C530A1', 7, 'Стабилитрон СМ3.362.823ТУ', 'Stabilitron СМ3.362.823ТУ', 1, null, ''),
(8, 'С2-33-0,125-360 Ом±5%-А-Д-В', 'C2-33-0,125-360 Om±5%-A-D-V', 8, 'Резистор ОЖ0.467.093ТУ', 'Resistor ОЖ0.467.093ТУ', 1, null, ''),
(9, 'СТ3-17В-330 Ом±10%', 'CT3-17V-330 Om±10%', 9, 'Терморезистор ОЖ0.468.096ТУ', 'Termoresistor ОЖ0.468.096ТУ', 1, null, ''),
(10, '1НТ251', '1NT251', 10, 'Матрица транзисторная И93.456.000ТУ', 'Matrix,transistor И93.456.000ТУ', 1, null, '');
select setval(pg_get_serial_sequence('cls.dict_resource','id'), 10);


INSERT INTO cls.Dict_article_structure (id, name_ru, name_en, part_link, article_link, note) VALUES
(1, 'Основная часть', 'Main Part', 1, 10, 'Основная часть изделия'),
(2, 'Электрическая схема', 'Electrical Schema', 2, 10, 'Электрическая схема'),
(3, 'Механическая конструкция', 'Mechanical Structure', 3, 10, 'Механическая конструкция'),
(4, 'Контрольный модуль', 'Control Module', 4, 10, 'Контрольный модуль'),
(5, 'Индикатор', 'Indicator', 5, 10, 'Индикатор состояния'),
(6, 'Датчик температуры', 'Temperature Sensor', 6, 10, 'Датчик температуры'),
(7, 'Источник питания', 'Power Source', 7, 10, 'Источник питания'),
(8, 'Контроллер', 'Controller', 8, 10, 'Управляющий контроллер'),
(9, 'Корпус', 'Housing', 9, 10, 'Корпус изделия'),
(10, 'Система охлаждения', 'Cooling System', 10, 10, 'Система охлаждения');
SELECT setval(pg_get_serial_sequence('cls.Dict_article_structure','id'), 10);


INSERT INTO cls.dict_absence_cause (id, name_ru, name_en, date_deletion, note) VALUES
(1, 'Больничный лист', 'Sick leave', null, 'Отпуск по болезни'),
(2, 'Отпуск без сохранения заработной платы', 'Unpaid leave', null, 'Отгул без оплаты'),
(3, 'Отпуск по уходу за ребенком', 'Parental leave', null, 'Отпуск по уходу за ребенком до 3 лет'),
(4, 'Отпуск по уходу за больным членом семьи', 'Leave for family member illness', null, 'Отпуск по уходу за больным родственником'),
(5, 'Отпуск по беременности и родам', 'Pregnancy and maternity leave', null, 'Отпуск по беременности и родам'),
(6, 'Дополнительный отпуск', 'Additional leave', null, 'Дополнительный отпуск по уходу за ребенком'),
(7, 'Отпуск по уходу за ребенком до 1.5 лет', 'Leave for child up to 1.5 years', null, 'Отпуск по уходу за ребенком до 1.5 лет'),
(8, 'Отпуск по уходу за ребенком до 3 лет', 'Leave for child up to 3 years', null, 'Отпуск по уходу за ребенком до 3 лет'),
(9, 'Отпуск по уходу за ребенком до 3 лет (вне графика)', 'Leave for child up to 3 years (outside schedule)', null, 'Отпуск по уходу за ребенком вне графика'),
(10, 'Отпуск по уходу за ребенком до 1.5 лет (вне графика)', 'Leave for child up to 1.5 years (outside schedule)', null, 'Отпуск по уходу за ребенком вне графика до 1.5 лет');
SELECT setval(pg_get_serial_sequence('cls.dict_absence_cause','id'), 10);


INSERT INTO cls.dict_type_task (id, name_ru, name_en) VALUES
(1, 'Шаблон (Работы по изделию)', 'Template (Work on Product)'),
(2, 'Работы по изделию', 'Work on Product'),
(3, 'Задача-условие', 'Condition Task'),
(4, 'Поступление изделия в ремонт', 'Product Receipt for Repair'),
(5, 'Приём изделия', 'Product Reception'),
(6, 'Мойка и очистка изделия', 'Cleaning and Washing of Product'),
(7, 'Дифектация изделия в собранном виде', 'Defecting of Product in Assembled State'),
(8, 'Демонтаж несправных составных частей', 'Disassembly of Faulty Components'),
(9, 'Работы по составной части', 'Work on Component'),
(10, 'Приём составной части', 'Component Reception'),
(11, 'Внешний осмотр составной части', 'External Inspection of Component'),
(12, 'Очистка составной части', 'Cleaning of Component'),
(13, 'Устранение механических повреждений составных частей', 'Elimination of Mechanical Damages of Components'),
(14, 'Диагностика составной части', 'Diagnosis of Component'),
(15, 'Устранение неисправности составной части', 'Elimination of Component Failure'),
(16, 'Замена неисправных неремонтопригодных составных частей', 'Replacement of Faulty Non-Repairable Components'),
(17, 'Контроль качества составной части', 'Quality Control of Component'),
(18, 'Общая сборка изделия', 'Overall Product Assembly'),
(19, 'Испытание изделия', 'Product Testing'),
(20, 'Внешний ремонт изделия', 'External Product Repair'),
(21, 'Контроль качества изделия', 'Product Quality Control'),
(22, 'Передача изделия заказчику', 'Product Transfer to Customer'),
(23, 'Шаблон (Работы по составной части)', 'Template (Work on Component)');
SELECT setval(pg_get_serial_sequence('cls.dict_type_task','id'), 23);


INSERT INTO cls.dict_type_document (id, name_ru) VALUES
(1, 'Наряд'),
(2, 'Акт приёма-передачи'),
(3, 'Акт на сдачу в ремонт'),
(4, 'Деф. ведомость (ведомость дефектов)'),
(5, 'Рекламационный акт'),
(6, 'Акт тех. состояния'),
(7, 'Производственное задание СКДА-1.-2,-3-4'),
(8, 'Ремонтный журнал'),
(9, 'Годовой План-график ремонта'),
(10, 'Месячный План-график ремонта'),
(11, 'Месячный отчет по ремонту'),
(12, 'Протокол ПСИ'),
(13, 'Протокол стац. испытаний'),
(14, 'Протокол пробег. испытаний'),
(15, 'Акт выдачи из ремонта'),
(16, 'Заявка на ЗИП материалы'),
(17, 'Ведомость (перечень) израсход. ЗИП и материалов'),
(18, 'Учет движения, содержания и хранения ЗИП и материалов'),
(19, 'Акт утилизации (ликвидации)'),
(20, 'Учет неисправного ВВТ'),
(21, 'Накладная');
SELECT setval(pg_get_serial_sequence('cls.dict_type_document','id'), 21);