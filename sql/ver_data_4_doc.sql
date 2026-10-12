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


INSERT INTO doc.receive_transfer
(id, department_link, approved_employee_link, act_number, task_link, date_of_act,
storage_representative_employee_link, sender_unit, sender, annex) VALUES
(1, 3, 16, '101-2026/12', 82, '20.04.26', 17, '16123', 'капитан С.С. Соколов', 'Акт технического состояния');
select setval(pg_get_serial_sequence('doc.receive_transfer', 'id'), 1);


INSERT INTO doc.Appendix_Receive_Transfer
(receive_transfer_link, id_document, class_document) VALUES
(1, 1, 'InitialReadingsReport'),
(1, 1, 'RepairAct');
select setval(pg_get_serial_sequence('doc.Appendix_Receive_Transfer', 'id'), 2);


INSERT INTO doc.initial_readings_report
(id, act_number, date_of_act, department_link, approved_employee_link, completeness,
technical_condition, reasons_for_early_wear, conclusion, senior_officer_conclusion)VALUES
(1, '101-2026/12', '20.04.2026', 5, 16, 'комплектность изделия согласно ведомости дефектации от «20» 04 2026 г.  № 124/56 (или карточки не комплектности от «20» 04 2026 г.  № 124/56',
 'требует ремонта, неисправность ЦВС', 'требуют выяснения', 'провести диагностику и ремонт СОУ 9А317Э', Null);
select setval(pg_get_serial_sequence('doc.initial_readings_report', 'id'), 1);


INSERT INTO doc.commission_initial_readings_report
(act_link, employee_link)VALUES
(1, 16), (1, 15), (1, 14);


INSERT INTO list.list_repair_documentation
(id, name_ru, name_en, resource_link)
VALUES(1, '123', '234', 1);


INSERT INTO doc.repair_act
(id, department_link, approved_employee_link, act_number, date_of_act, storage_representative_employee_link,
repair_representative_employee_link, task_link, ntd_document, conclusion, date_repair, rejection_reason)VALUES
(1, 7, 16, '111-2026/12', '20.08.2026', 15, 14, 82, 1, 'Ячейка Б04 ЦА3.038.317 зав. № 12345, 2021 года выпуска из состава 9С753, СОУ 9А317Э зав. № 215ДА1273 комплектность изделия согласно ведомости дефектации от «20» 04 2026 г.  № 126/12/6 ',
 '20.08.2026', 'комплектность изделия СОУ 9А317Э, зав. № 215ДА1273, 2021 года выпуска не соответствует ведомости комплектации ГС1.641.007-01ВЭ');
select setval(pg_get_serial_sequence('doc.repair_act', 'id'), 1);


INSERT INTO doc.order
(id, order_number, date_order, task_link, issuing_authority, valid_until_date,
operation_purpose, operation_basis, shipper_name, consignee_name, transport, transport_document_name,
 total, shipment_order)
VALUES(1, '56-2026', '12.03.2026', 82, 'Министерство обороны АРЕ', '31.12.2026',
'Ремонт', 'Указание МО АРЕ', 'Войсковая часть 16123', 'СРЦ', 'автомобильный транспорт', 'Товарно-транспортная накладная от 20.03.2026 № 25',
'1', 'средствами грузоотправителя ');
select setval(pg_get_serial_sequence('doc.order', 'id'), 1);


INSERT INTO doc.order_content
(id, sequence_number, material_link,order_link, increase, decrease, repair_type_link, execution_period, work_completion_note)
VALUES(1, 1, 29, 1, 1, 0, 1, '12.07.2026', Null);