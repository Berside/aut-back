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

INSERT INTO res.resources_movement(id, date_record, resource_link, increase, decrease, date_deletion, note) VALUES
(1, '12.10.2025', 1, 10, 10, Null, Null),
(2, '02.04.2025', 2, 2, 1, Null, Null),
(3, '01.02.2025', 3, 10, 6, Null, Null),
(4, '09.09.2026', 4, 22, 20, Null, Null);
select setval(pg_get_serial_sequence('res.resources_movement', 'id'), 1);


INSERT INTO res.delivery_note(id, number_delivery_note, date_delivery_note, reason, power_attorney, total_issue, department_input_link, department_output_link, head_employee_link, input_employee_link, output_employee_link, task_link, military_unit_link, date_deletion, note) VALUES
(1, '123-321', '22.12.2025', 'Недостаток', 'Накладная', 12, 3, 4, 2, 3, 4, 55, 2, Null, Null),
(2, 'ABC-456', '09.04.2024', 'Запрос', 'Наряд', 10, 5, 6, 15, 14, 12, 4, 1, Null, Null),
(3, 'AA-55-BB', '14.10.2026', 'Запрос', 'Накладная', 13, 10, 13, 2, 4, 6, 44, 2, Null, Null);
select setval(pg_get_serial_sequence('res.delivery_note', 'id'), 1);


INSERT INTO res.delivery_note_resources(id, delivery_note, resources_movement_link, okei_link, location_link, resource_link, quantity, note, date_deletion) VALUES
(1, 1, 1, 796, 5, 1, 10, Null, Null),
(2, 1, 2, 796, 7, 2, 2, Null, Null),
(3, 2, 3, 796, 6, 3, 10, Null, Null),
(4, 3, 4, 796, 3, 4, 13, Null, Null);
select setval(pg_get_serial_sequence('res.delivery_note_resources', 'id'), 1);


INSERT INTO res.request(id, name, department_link, input_employee_link, output_employee_link, task_link, military_unit_link, date_deletion) VALUES
(1, 'Заявка-123', 10, 10, 3, 44, 2, Null),
(2, 'Заявка-ABC', 22, 11, 5, 32, 2, Null),
(3, 'Заявка-678', 4, 8, 6, 58, 1, Null);
select setval(pg_get_serial_sequence('res.request', 'id'), 1);


INSERT INTO res.request_resources(id, okei_link, quantity, request_link, department_link, location_link, resource_link, date_deletion, note) VALUES
(1, 796, 5, 1, 12, 9, 3, Null, Null),
(2, 796, 11, 2, 4, 4, 6, Null, Null),
(3, 796, 4, 3, 20, 8, 7, Null, Null),
(4, 796, 22, 3, 15, 6, 9, Null, Null),
(5, 796, 18, 2, 17, 14, 2, Null, Null);
select setval(pg_get_serial_sequence('res.request_resources', 'id'), 1);