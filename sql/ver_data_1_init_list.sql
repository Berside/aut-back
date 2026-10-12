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


INSERT INTO list.list_article
(id, name_ru, production_index, production_designation, serial_number, production_year) VALUES
(1, 'Модуль ФД12-3Е', 'Изделие 9А317Э', 'СТС 9С625М1', '12345', '2021'),
(2, 'Ячейка', 'ФА110А-01', 'ЫКЗ.051.316', '12345', '2021'),
(3, 'Средство подвижности', 'КамАЗ-6350', null, '12345', '2021'),
(4, 'Ячейка', '125Н623', 'СМАУ.256.154', 'Ф25145', '2024'),
(5, 'Ячейка', '25Д458', 'БИ.012.023', 'БТ12445', '2024'),
(6, 'Блок', 'ГН58', 'ТИ.145.256', '124897', '2023'),
(7, 'Подблок', '483КП02', 'МВИА.124502.025', '15Д2384', '2022'),
(8, 'Блок питания', 'БП6,3-12', 'ШИБФ.124578', '12Б56', '2018'),
(9, 'Блок питания', 'ФД10-71', null, '12245', '2020'),
(10, 'Подблок', '04.11.00.11', 'ИФШС.436624.001', '12356', '2021'),
(11, 'Силовой модуль', 'МПН2-10', 'ГС3.233.087-10', '13345', '2019'),
(12, 'Силовой модуль', 'НМП4-7', 'ГС3.233.100-35', '12365', '2025'),
(13, 'Подблок', 'Ф8.11.00.01', 'ЕФ3.238.090', '22345', '2023'),
(14, 'Ячейка', '125Н623', 'СМАУ.256.154', 'Ф25167', '2023'),
(15, 'Ячейка', 'Б04', 'ЦА3.038.317', '18345', '2024'),
(16, 'Силовой модуль', 'МПН2-10', 'ГС3.233.087-10', '13345', '2019'),
(17, 'Объект VVT', '9И56', 'ГС3.233.087-20', '14532', '2021'),
(18, 'Объект VVT', '9И56-8', 'ГС3.233.087-20', '14532', '2021'),
(19, 'Объект VVT', '9И112М2', 'ГС3.233.087-30', '12211', '2018'),
(20, 'Объект VVT', '9И113М2', 'ГС3.233.087-40', '11987', '2023'),
(21, 'Объект VVT', '9И114М2', 'ГС3.233.087-50', '15432', '2017'),
(22, 'Объект VVT', 'ЗРС «Тор-М1»', 'ГС3.233.087-60', '16789', '2020'),
(23, 'Объект VVT', '9М334', 'ГС3.233.087-70', '17890', '2016'),
(24, 'Объект VVT', '9М82МДЭ', 'ГС3.233.087-80', '18901', '2022'),
(25, 'Объект VVT', '9М83МЭ', 'ГС3.233.087-90', '19012', '2024'),
(26, 'Объект VVT', '9М317', 'ГС3.233.087-90', '19012', '2024'),
(27, 'Объект VVT', '«Тор-М1»', 'ГС3.233.087-100', '20123', '2019'),
(28, 'Объект VVT', 'ЗСУ-23-4М4 «Шилка-М4»', 'ГС3.233.087-110', '21234', '2020'),
(29, 'Объект VVT', 'СОУ 9А317Э', '215ДА1273', '21234', '2020');
SELECT setval(pg_get_serial_sequence('list.list_article', 'id'), 29);

UPDATE list.list_article
SET passport_number = 'ГС1.641.007-01ФО',
    dict_okei_link = '796'
WHERE id = 29;


INSERT INTO list.list_specifications_article
(id, article_link, operation_date, operating_work, resource_work, resource_period, guarantee_resource_work,
guarantee_period, operation_period, different_resource_work, different_resource_period, different_guarantee_resource, different_guarantee_period)
VALUES(1, 29, '12.12.2021', 457, 20000, '10 year', 4000, '2 year', '4 year 6 months', -8543, '5 year 6 months', 3543, '2 year 6 months');


INSERT INTO list.list_department (id, name_ru, name_en, parent_link, date_deletion, note) VALUES
(1, 'Ремонтный завод', 'Repair Factory', null, null, ''),
    (2, 'Учетно-операционный отдел', 'Accounting and Operations Department', 1, null, ''),
    (3, 'Отдел хранения. Площадка временного хранения ВВТ', 'Storage Department. Temporary Storage Area for Aircraft', 1, null, ''),
    (4, 'Участок очистки и мойки', 'Cleaning and Washing Section', 1, null, ''),
    (5, 'Участок приёма изделий', 'Product Reception Section', 1, null, ''),
    (6, 'Участок разборки/сборки изделия', 'Disassembly/Assembly Section', 1, null, ''),
    (7, 'КРДО «РЕДИКОМ»', 'Maintenance Department "REDIKOM"', 1, null, ''),
        (8, 'АРМ СКДА-3', 'ARM SKDA-3', 7, null, ''),
        (9, 'ТРМ3-1', 'TRM3-1', 7, null, ''),
        (10, 'АРМ начальника КРДО', 'ARM Chief of Maintenance Department', 7, null, ''),
        (11, 'Склад ЗИП', 'SPARE PARTS Warehouse', 7, null, ''),
        (12, 'ТРМ-2', 'TRM-2', 7, null, ''),
        (13, 'ТРМ3-2', 'TRM3-2', 7, null, ''),
        (14, 'Контроль качества', 'Quality Control', 7, null, ''),
        (15, 'Участок комплектации изделия', 'Product Assembly Section', 7, null, ''),
    (16, 'Участок общей сборки изделия', 'Overall Product Assembly Section', 1, null, ''),
    (17, 'Испытательный полигон', 'Test Field', 1, null, ''),
    (18, 'Цех(участок) покраски', 'Painting Workshop', 1, null, ''),
    (19, 'Отдел хранения', 'Storage Department', 1, null, ''),
    (20, 'Служба качества', 'Quality Service', 1, null, ''),
    (21, 'Площадка временного хранения', 'Temporary Storage Area', 1, null, ''),
    (22, 'Участок (площадка) приёма изделий в ремонт', 'Reception Section for Products for Repair', 1, null, '');

select setval(pg_get_serial_sequence('list.list_department','id'), 22);

INSERT INTO list.list_resource_location (id, location, rack, shelf, place, placement, department_link, date_deletion, note) VALUES
(1, '1', 1, null, null, null, 1, null, null),
    (2, '2', 1, 1, null, null, 1, null, null),
        (3, '3', 1, 1, 1, null, 1, null, null),
        (4, '4', 1, 1, 1, 'A-1', 1, null, null),
        (5, '5', 1, 1, 1, 'A-2', 2, null, null),
        (6, '6', 1, 1, 1, 'B-1', 1, null, null),
    (7, '7', 1, 1, 2, null, 2, null, null),
(8, '8', 2, null, null, null, 2, null, null),
    (9, '9', 2, 1, null, null, 3, null, null),
    (10, '10', 2, 2, null, null, 2, null, null),
    (11, '11', 2, 3, null, null, 2, null, null),
        (12, '12', 2, 3, 1, null, 2, null, null),
        (13, 'A-1', 2, 3, 2, null, 2, null, null),
        (14, 'A-2', 2, 3, 3, null, 2, null, null),
    (15, '15', 2, 4, null, null, 2, null, null);
select setval(pg_get_serial_sequence('list.list_resource_location', 'id'), 15);


INSERT INTO list.list_military_unit
(id, name_ru, name_en, date_deletion, note) VALUES
(1, '1-я воинская часть', null, null, null),
(2, '2-я воинская часть', null, null, null);
select setval(pg_get_serial_sequence('list.list_military_unit', 'id'), 2);


INSERT INTO list.list_resources (id, date_created, dict_resource_link, resource_location_link, article, count_in_article, count_norm, current_stock, dict_okei_link, date_deletion) VALUES
(1, '2025-05-23 00:00:00', 1, 1, '9А331М2', 2, 5, 6, '796', null),
(2, '2025-10-09 00:00:00', 2, 2, 'BCH22OJ', 1, 10, 5, '796', null),
(3, '2025-09-27 00:00:00', 3, 3, 'VV2S4L', 1, 14, 18, '796', null),
(4, '2025-03-03 00:00:00', 4, 5, 'SDVG-538', 5, 20, 25, '796', null),
(5, '2025-11-23 00:00:00', 5, 13, 'BCS52KL', 2, 16, 16, '796', null);
select setval(pg_get_serial_sequence('list.list_resources','id'), 5);


INSERT INTO list.list_employee (id, first_name, middle_name, last_name, fio,job_title_link, rank_link, parent_link, department_link, date_employment, date_brith, note) VALUES
(1, 'Иван', 'Петрович', 'Иванов', 'Иванов И.П.', 1, 1, NULL, 1, '2020-01-15', '1985-03-20', 'Руководитель отдела'),
(2, 'Петр', 'Сергеевич', 'Петров', 'Петров П.С.', 2, 2, 1, 2, '2020-02-20', '1988-07-15', 'Заместитель руководителя'),
(3, 'Сергей', 'Викторович', 'Сидоров', 'Сидоров С.В.', 3, 3, 1, 3, '2020-03-10', '1990-11-08', 'Главный инженер'),
(4, 'Алексей', 'Михайлович', 'Козлов', 'Козлов А.М.', 4, 4, 3, 4, '2020-04-05', '1987-09-12', 'Инженер-электроник'),
(5, 'Михаил', 'Александрович', 'Морозов', 'Морозов М.А.', 5, 5, 3, 5, '2020-05-12', '1989-01-25', 'Инженер-радиотехник'),
(6, 'Дмитрий', 'Владимирович', 'Волков', 'Волков Д.В.', 6, 6, 3, 6, '2020-06-18', '1992-05-30', 'Инженер-программист'),
(7, 'Андрей', 'Семенович', 'Николаев', 'Николаев А.С.', 7, 7, 4, 7, '2020-07-22', '1986-08-14', 'Техник'),
(8, 'Владимир', 'Игоревич', 'Макаров', 'Макаров В.И.', 8, 8, 4, 8, '2020-08-30', '1984-12-03', 'Механик'),
(9, 'Олег', 'Андреевич', 'Захаров', 'Захаров О.А.', 9, 9, 4, 9, '2020-09-15', '1991-04-18', 'Слесарь'),
(10, 'Николай', 'Викторович', 'Белов', 'Белов Н.В.', 10, 10, 4, 10, '2020-10-25', '1988-06-22', 'Оператор'),
(11, 'Виктор', 'Петрович', 'Соколов', 'Соколов В.П.', 11, 11, 4, 11, '2020-11-10', '1990-02-14', 'Ремонтник'),
(12, 'Роман', 'Михайлович', 'Кузнецов', 'Кузнецов Р.М.', 12, 12, 3, 12, '2020-12-05', '1987-10-30', 'Инженер-конструктор'),
(13, 'Александр', 'Владимирович', 'Попов', 'Попов А.В.', 13, 13, 3, 13, '2021-01-12', '1989-08-17', 'Инженер-испытатель'),
(14, 'Максим', 'Сергеевич', 'Лебедев', 'Лебедев М.С.', 14, 14, 3, 14, '2021-02-20', '1991-12-08', 'Инженер-проектировщик'),
(15, 'Евгений', 'Александрович', 'Ковалев', 'Ковалев Е.А.', 15, 15, 3, 15, '2021-03-25', '1986-04-28', 'Инженер-технолог'),
(16, 'Орлов', 'Владимир', 'Сергеевич', 'Сергеевич О.В.',  3, 3, 1, 3, '2018-03-25', '1980-04-28', 'Главный инженер'),
(17, 'Петров', 'Александр', 'Антонович', 'Антонович П.А.',  1, 1, NULL, 3, '2019-03-25', '1982-04-28', 'Руководитель отдела');
select setval(pg_get_serial_sequence('list.list_employee', 'id'), 17);


INSERT INTO list.list_technological_equipment
(id, name_ru, name_en, serial_number, production_year, total_operating, component, res_location_link, employee_link, dict_okei_link, date_deletion, note) VALUES
(1, 'Фрезерный станок', 'Milling Machine', '012MH-3', 2024, 120, 'Блок управления', 5, 1, 796, null, 'Оборудование для обработки металла'),
(2, 'Токарный станок', 'Lathe Machine', '016TK-11', 2022, 235, 'Станина', 6, 1, 796, null, 'Оборудование для обработки заготовок');
select setval(pg_get_serial_sequence('list.list_technological_equipment', 'id'), 2);