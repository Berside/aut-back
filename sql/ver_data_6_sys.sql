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

-- INSERT INTO sys.file_type(id, name,         note, config_path, parser_class, target_model) VALUES
-- (1, 'Склад', 'Загрузка', 'config_file_loader_1.json', 'XlsxParser', 'ListResources');
-- select setval(pg_get_serial_sequence('sys.file_type', 'id'), 1);


INSERT INTO sys.file_type(id, name, note, config_path, parser_class) VALUES
(1, 'Склад', 'Загрузка', 'config_file_loader_1.json', 'XlsxParser'),
(2, 'Склад_207', 'Загрузка_2', 'config_file_loader_2.json', 'XlsxParser');
select setval(pg_get_serial_sequence('sys.file_type', 'id'), 1);