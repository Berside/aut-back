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


INSERT INTO auth.PermissionMatrix (id, table_name, permissions, ad_groups) VALUES
(1,"/some_path_1/", 15, ARRAY['admin']),
(2,"/some_path_2/", 15, ARRAY['admin','user']),
(3,"/some_path_3/", 15, ARRAY[['admin','user'],['admin']]);