import os
import json
import psycopg2
from pathlib import Path
# from src import app

with open('../src/config/config.json', 'r', encoding='utf-8') as json_file:
    config = json.load(json_file)

if 'USE_TEST_DB' in os.environ:
    db_params = config['SQLALCHEMY_DATABASE_URI_TEST']
else:
    db_params = config["SQLALCHEMY_DATABASE_URI"]
# print('Текущая база данных - ' + db_params)

con = psycopg2.connect(db_params)
cur = con.cursor()

name_version = set()
name_file = set()
cur.execute(f"""SELECT to_regclass ('data_version');""")
table = cur.fetchall()[0][0]
if table is None:
    cur.execute(f"""CREATE TABLE public.data_version (
                id serial NOT NULL,
                name_version varchar NOT NULL,
                data_upload date DEFAULT CURRENT_DATE NULL,
                CONSTRAINT id_data_version_pk PRIMARY KEY (id));
                COMMENT ON TABLE public.data_version IS 'Загруженные файлы данных';
                COMMENT ON COLUMN public.data_version.id IS 'Индификатор';
                COMMENT ON COLUMN public.data_version.name_version IS 'Название загруженных файлов';
                COMMENT ON COLUMN public.data_version.data_upload IS 'Время загрузки файла данных';
                """)
    con.commit()
    # print('Я сделял')

else:
    list_version = cur.execute(f"""SELECT * from public.data_version;""")
    list_version = [*cur.fetchall()]
    for row in list_version:
        name_version.add(row[1])
    # print(list_version)
    # print(name_version)

ver_list = list(Path('./../sql').glob('ver_data*.sql'))
for item in ver_list:
    name_file.add(item.name)

result_data = sorted(name_file - name_version)
if len(result_data) != 0:
    for item in result_data:
        with open('./../sql/' + item, 'r', encoding='utf-8') as cmd_sql:
            cmd_sql = cmd_sql.read()
            cur.execute(cmd_sql)
            cur.execute(f"""INSERT INTO sys.data_version
                            ( name_version, date_upload)
                            VALUES('{item}', CURRENT_DATE);""")
            con.commit()
            print(f'Загружен файл - {item}')
else:
    print('Данные актуальны')

cur.close()
con.close()


