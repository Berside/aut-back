import psycopg2
#from odf.opendocument import OpenDocumentText
from odf.table import Table, TableColumn, TableRow, TableCell
from odf.text import P
from pathlib import Path
import csv, os


filter = ['alfakirill', 'bg_sost','dislokacia','dolg_brig', 'dolg_nach','edin_izm','izgot', 'spec','sroki',
          'struct_object_vvt', 'tip_blok','tip_elem','tip_izdelie', 'tip_kip','tip_remont','tip_sdz', 'tip_sostav_vvt','tip_svd',
          'tip_vch', 'tip_zip','tipy_doc','tochka_st', 'vid_pki','vid_rabot','vid_vs_rod']

filter1 = ['object_rso', 'object_vvt', 'pribor_vvt', 'cso', 'cso_pribor', 'cso_sist', 'podrazd', 'shtat_nach', 'rabotnik', 'baza', 'filial',
           'istoria_vvt', 'jurnal', 'kontrakt']

filter2 = ["akt_to","akt_vosst","protokol_predyav_kip","izvesh","tehn_akt_kip","uved_postavka","vybor_isp","table_all_doc_post","podtv_sch","table_all_doc","podtv_rab","tehn_akt","dok_rab_sch_obsh","remont_kip","uved_rabota_kip","izvesh_post","zakaz","aspvr_sch_obsh","rabotnik","uved_kontrakt","aspvr","kontrakt_kr","akt_sdacha","uved","uved_sch_vvt","akt_nerem_kip","avans_obsh_post","akt_sdacha_priem","izvesh_kip","akt_to_kip_obsh","podtv_soisp","uved_dogovor","uved_sch","akt_priem","rabotnik_uved","doc_obsh_post","shtat_nach","kontrakt_post","protok_sogl","podtv_soisp_kip","dogovor","svid_o_pov_kip","podtv_kr","protokol_priem_kip","remont","svid_o_pov_rem_kip","kontrakt","uved_kontrakt_post","sort_kip"]

filter_102M6_kls = ['dict_classifiers', 'location_classifiers', 'dict_categories_ret', 'dict_climatic_area', 'dict_degree_damage', 'dict_hran', 'dict_months', 'dict_storage_zip', 'dict_vid_ret', 'kls_okopf', 'okei', 'registr_company', 'registr_military_parts', 'type_complect_element', 'type_of_army', 'moni_object_species', 'view_classifiers', 'boudary_types', 'documents_statuses', 'spr_type_military_form', 'weapons_objects_content_types']
filter_102M6_obj = ['weapon_objects', 'staffin_structure', 'staffin_structure_zur', 'form_products', 'part487', 'directory_itemparts', 'form_zur', 'catalog_itemparts', 'components', 'spare_tools_and_accessories', 'normative_documents', 'doc_operation_and_repair']
filter_102M6_doc = ['contract', 'service_notify', 'service_request', 'work_request', 'service_fault', 'notify_numbers', 'fault_ext_data', 'defect_list', 'kts_limits', 'yeared_remont_plans', 'plan_so', 'proposal_in_schedule', 'remont_limits', 'remont_limits_approved_outlook','report_offers_service', 'mon_kts_limits', 'mon_perech_obr', 'mon_remont_limits', 'mon_remont_plans', 'mon_resource_consumption']
filter_102M6_zip = [ 'res_request', 'resource_consumption', 'resource_consumption_approved_outlook', 'storage', 'storage_zur', 'zip_norma' ]

filter_fucn = ['f_dgd_curr_rem','doklad_uved_filial_all','doklad_kip', 'zapoln_spravka_doklad_postavka', 'zapoln_spravka_doklad_sgk']
filter_tables = ['schema_gk_01', 'schema_gk', 'schema_gk_shablon']
db_params_kusto = {
            "dbname": "kusto",
            "user": "postgres",
            # "host": "192.168.1.88"
            "host": "localhost"
            }
db_params_asilp = {
            "dbname": "asilp",
            "user": "postgres",
            "host": "192.168.1.116"
            # "host": "localhost"
            }
db_params_CSU = {
            "dbname": "csu_old",
            "user": "postgres",
            # "host": "192.168.1.88"
            "host": "localhost"
            }
db_params_ASU = {
            "dbname": "asutg",
            "user": "postgres",
            # "host": "192.168.1.88"
            "host": "localhost"
            }
conn_asu = psycopg2.connect(**db_params_ASU)
cur_asu = conn_asu.cursor()

conn_kusto = psycopg2.connect(**db_params_kusto)
cur_kusto = conn_kusto.cursor()

# conn_asilp = psycopg2.connect(**db_params_asilp)
# cur_asilp = conn_asilp.cursor()

conn_csu = psycopg2.connect(**db_params_CSU)
cur_csu = conn_csu.cursor()

# Выдает название таблиц,комментарии к ней, количество строк, количество пустых стобцов. Принимает необязательно в себя название схемы (schema = '') и массив с именами кокретными таблицами
def Analysis_Tables(filter = None, output_filename = "/home/user/Desktop/Analysis_Tables.odt", schema = 'granit'):
    # try:
    data_all_tables = []
    first_schema = schema
    first_filter = filter
    if type(first_schema) != list:
        schema = [first_schema]
    for schema in schema:
        if first_filter == None:
            filter = []
            cur_kusto.execute(f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = '{schema}'
                and table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            for  _ in range(cur_kusto.rowcount):
                filter.append(*cur_kusto.fetchone())
        filter.sort()

        cur_kusto.execute(f"""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = '{schema}'
            ORDER BY table_name;
            """)
        columns_all_schema = cur_kusto.fetchall()
        count_empty_columns = {}
        for table, column in columns_all_schema:
            if table in filter:
                if table not in count_empty_columns:
                    count_empty_columns[table] = 0
                cur_kusto.execute(f'SELECT EXISTS (SELECT 1 FROM "{schema}"."{table}" WHERE "{column}" IS NOT NULL LIMIT 1);')
                if not cur_kusto.fetchone()[0]:
                    count_empty_columns[table] += 1


        for item in filter:
            cur_kusto.execute(f"""
                SELECT 
                    table_name as "Название таблицы",
                    obj_description((table_schema || '.' || table_name)::regclass) AS Комментарии,
                    (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from %I.%I', table_schema, table_name), false, true, '')))[1]::text::bigint AS "Количество заполненных строк"
                FROM information_schema.tables
                WHERE table_schema = '{schema}' and table_name = '{item}'
                    AND table_type = 'BASE TABLE';
                """)
            if type(first_schema) == list:
                data_all_tables.append([schema, *cur_kusto.fetchall()[0], count_empty_columns.get(item, 'Не найдено')])
            else:
                data_all_tables.append([*cur_kusto.fetchall()[0], count_empty_columns.get(item, 'Не найдено')])


    table = Table(name="MyDataTable")
    if type(first_schema) == list:
        colnames = ['Название схемы', *[item[0] for item in cur_kusto.description], 'Полностью пустые столбцы']
    else:
        colnames = [*[item[0] for item in cur_kusto.description], 'Полностью пустые столбцы']
    for _ in range(len(colnames)):
        table.addElement(TableColumn())
    header_row = TableRow()

    for col in colnames:
        cell = TableCell()
        cell.addElement(P(text=str(col)))
        header_row.addElement(cell)

    table.addElement(header_row)
    for row_data in data_all_tables:
        tr = TableRow()
        for item in row_data:
            tc = TableCell()
            tc.addElement(P(text=str(item)))
            tr.addElement(tc)
        table.addElement(tr)



    # except Exception as e:
    #     print(f"Ошибка: {e}")
    #     return

    textdoc = OpenDocumentText()
    textdoc.text.addElement(table)
    textdoc.save(output_filename)
    print(f"Файл {output_filename} успешно сохранен.")

# Выводит название схемы, название функции и комментарии к фукнции по всей переданной схеме
def function_analysis(output_filename = "/home/user/Desktop/Analysis_Function.odt", schema = 'granit'):
    try:
        data_all_tables = []
        # for item in filter:
        cur_kusto.execute(f"""
        SELECT
            n.nspname as schema_name,
            p.proname as function_name,
            d.description as comment
        FROM pg_proc p
        LEFT JOIN pg_namespace n ON n.oid = p.pronamespace
        LEFT JOIN pg_description d ON d.objoid = p.oid
        WHERE n.nspname = '{schema}' 
        ORDER BY function_name; 
            """)
        data_all_tables.append([*cur_kusto.fetchall()])
        for item in data_all_tables[0]:
            print(item)
        return data_all_tables


    except Exception as e:
        print(f"Ошибка, Ахтунг!: {e}")
        return

# Для Кусто kls выдаёт Наименование классификатора", "ID", "Количество классов"
def kusto_kls(output_filename = "/home/user/Desktop/kusto_kls.odt"):
    data_all = []
    cur_kusto.execute(f"""
                SELECT name_full, id
                FROM kls.tqual
                ORDER BY id;
            """)
    for _ in range(cur_kusto.rowcount):
        data_all.append([*cur_kusto.fetchone()])

    for id, item in enumerate(data_all):
        cur_kusto.execute(f"""
                    SELECT count(*)
                    FROM kls.tkls
                    where link ={item[1]};
                """)
        data_all[id] = [data_all[id][0], data_all[id][1], *cur_kusto.fetchone()]

    table = Table(name="MyDataTable")
    colnames = ["Название классификатора", "ID", "Количество записей"]
    for _ in range(len(colnames)):
        table.addElement(TableColumn())
    header_row = TableRow()

    for col in colnames:
        cell = TableCell()
        cell.addElement(P(text=str(col)))
        header_row.addElement(cell)

    table.addElement(header_row)
    for row_data in data_all:
        tr = TableRow()
        for item in row_data:
            tc = TableCell()
            tc.addElement(P(text=str(item)))
            tr.addElement(tc)
        table.addElement(tr)

    textdoc = OpenDocumentText()
    textdoc.text.addElement(table)
    textdoc.save(output_filename)
    print(f"Файл {output_filename} успешно сохранен.")

    # print(data_all)

# Для Кусто psn выдаёт Наименование классификатора", "ID", "Количество классов"
def kusto_psn(output_filename = "/home/user/Desktop/kusto_psn_kls.odt"):
    data_all = []
    cur_kusto.execute(f"""
                SELECT distinct id_kls_vvt
                FROM psn.tpsn
                ORDER BY psn.tpsn.id_kls_vvt;
            """)
    for _ in range(cur_kusto.rowcount):
        data_all.append([*cur_kusto.fetchone()])

    for id, item in enumerate(data_all):
        if item[0] != None:
            cur_kusto.execute(f"""
                        SELECT name_kls
                        FROM kls.tkls
                        where id = {item[0]};
                    """)
            data_all[id].insert(0, *cur_kusto.fetchone())
            cur_kusto.execute(f"""
                                SELECT count(id_kls_vvt)
                                FROM psn.tpsn
                                where id_kls_vvt = {item[1]};
                            """)
            data_all[id].insert(2, *cur_kusto.fetchone())
        else:
            data_all[id].insert(0, "Классификатор не имеет название (Null)")
            cur_kusto.execute(f"""
                        SELECT count(*)
                        FROM psn.tpsn
                        where id_kls_vvt is NULL;
                    """)
            data_all[id].insert(2, *cur_kusto.fetchone())

    table = Table(name="MyDataTable")
    colnames = ["Название классификатора", "ID", "Количество записей"]
    for _ in range(len(colnames)):
        table.addElement(TableColumn())
    header_row = TableRow()

    for col in colnames:
        cell = TableCell()
        cell.addElement(P(text=str(col)))
        header_row.addElement(cell)

    table.addElement(header_row)
    for row_data in data_all:
        tr = TableRow()
        for item in row_data:
            tc = TableCell()
            tc.addElement(P(text=str(item)))
            tr.addElement(tc)
        table.addElement(tr)

    textdoc = OpenDocumentText()
    textdoc.text.addElement(table)
    textdoc.save(output_filename)
    print(f"Файл {output_filename} успешно сохранен.")

# Для Кусто выдаёт наименование, ID и количество классификаторов, что используются в psn
def kusto_count_kls_psn(output_filename = "/home/user/Desktop/kusto_count_kls.odt"):
    data_all = []
    cur_kusto.execute(f"""
                SELECT distinct id_kls_tip_psn
                FROM psn.tpsn
                ORDER BY id_kls_tip_psn
            """)
    id_psn_list = cur_kusto.fetchall()
    dict_link = set()
    # dict_link.remove(None)
    for item in id_psn_list:
        if str(*item) != 'None':
            cur_kusto.execute(f"""
                        SELECT distinct link
                        FROM kls.tkls
                        where id = {str(*item)}
                        ORDER BY link
                    """)
            dict_link.add(*cur_kusto.fetchone())

    for item in dict_link:
        cur_kusto.execute(f"""
                    SELECT name_full, id
                    FROM kls.tqual
                    where id = {item}
                    ORDER BY id
                """)
        data_all.append([*cur_kusto.fetchone()])

    for id, item in enumerate(data_all):
        cur_kusto.execute(f"""
                    SELECT count(*)
                    FROM kls.tkls
                    where link = {item[1]}
                """)
        data_all[id].append(*cur_kusto.fetchone())

    table = Table(name="MyDataTable")
    colnames = ["Наименование классификатора", "ID", "Количество классов"]
    for _ in range(len(colnames)):
        table.addElement(TableColumn())
    header_row = TableRow()

    for col in colnames:
        cell = TableCell()
        cell.addElement(P(text=str(col)))
        header_row.addElement(cell)

    table.addElement(header_row)
    for row_data in data_all:
        tr = TableRow()
        for item in row_data:
            tc = TableCell()
            tc.addElement(P(text=str(item)))
            tr.addElement(tc)
        table.addElement(tr)

    textdoc = OpenDocumentText()
    textdoc.text.addElement(table)
    textdoc.save(output_filename)
    print(f"Файл {output_filename} успешно сохранен.")

# Для Кусто и 102М6. Сравнивает класификаторы по Uuid и название и выводит все сопоставления
def uuid_like_kusto_102M6(output_filename = "/home/user/Desktop/kls_like_102M6.odt"):
    data_kusto = []
    result = []
    uuid_list = []
    name_list = []
    cur_kusto.execute(f"""
                SELECT b.name_full, a.name_kls, a.s , a.uuid,
                FROM kls.tkls as a
                right join kls.tqual as b
                on a.link = b.id;
            """)
    for _ in range(cur_kusto.rowcount):
        buf = [*cur_kusto.fetchone()]
        data_kusto.append(buf)
        uuid_list.append(buf[1])
        name_list.append(buf[0])

    list_dict = ['location_classifiers', "dict_categories_ret", "dict_climatic_area", "dict_degree_damage", "dict_hran", "dict_hurt", "dict_months", "dict_vid_ret", "kls_okopf","okei", "registr_company","registr_military_parts", "type_complect_element", "type_of_army", "moni_object_species", "view_classifiers", "boudary_types", "directory_itempart_location", "documents_statuses", "spr_type_military_form", "weapons_objects_content_types" ]

    for item in list_dict:
        cur_asilp.execute(f"""
                    SELECT A.id, A.name_full, C.name_classifier
                    FROM data.{item} as A
                    left join refs.location_classifiers as B on A.id = B.id
                    left join data.dict_classifiers as C on C.id = B.id_classifier
                    ORDER BY id;
                """)
        for id in range(cur_asilp.rowcount):
            buf = list(cur_asilp.fetchone())
            if buf[0] in uuid_list:
                result.append([*data_kusto[uuid_list.index(buf[0])],*buf])
            elif buf[1] in name_list:
                result.append([*data_kusto[name_list.index(buf[1])],*buf])

    result.sort(key = lambda x: x[2])
    table = Table(name="MyDataTable")
    colnames = ["Название класса Кусто", "UUID кусто", "Название классификатора","uuid 102 м6", "название из 102 м6", "Название классификатора из ASILP"]
    for _ in range(len(colnames)):
        table.addElement(TableColumn())
    header_row = TableRow()

    for col in colnames:
        cell = TableCell()
        cell.addElement(P(text=str(col)))
        header_row.addElement(cell)

    table.addElement(header_row)
    for row_data in result:
        tr = TableRow()
        for item in row_data:
            tc = TableCell()
            tc.addElement(P(text=str(item)))
            tr.addElement(tc)
        table.addElement(tr)

    textdoc = OpenDocumentText()
    textdoc.text.addElement(table)
    textdoc.save(output_filename)
    print(f"Файл {output_filename} успешно сохранен.")


    print(result)
    print(len(result))

# Для Кусто и 102М6. Сравнивает класификаторы и выводит общее количество совпадений
def diff_kls_kusto_102M6 (output_filename = "/home/user/Desktop/diff_kls_kusto_102M6.odt"):
    list_dict = ["dict_categories_ret", "dict_climatic_area", "dict_degree_damage", "dict_hran", "dict_hurt", "dict_months", "dict_vid_ret", "kls_okopf","okei", "registr_company","registr_military_parts", "type_complect_element", "type_of_army", "moni_object_species", "view_classifiers", "boudary_types", "directory_itempart_location", "documents_statuses", "spr_type_military_form", "weapons_objects_content_types" ]
    result = []
    data_kusto = []
    kusto_uuid_list = []
    kusto_name_list = []
    kusto_kls = []
    kusto_kls_count = []
    dict_diff = dict()
    asip_ksl = []
    asip_kls_count = {}

    # Собираем данные по кусто: лист уидов, названий, и полный список
    cur_kusto.execute(f"""
                SELECT b.name_full, a.name_kls , a.uuid
                FROM kls.tkls as a
                right join kls.tqual as b
                on a.link = b.id;
            """)
    for _ in range(cur_kusto.rowcount):
        buf = [*cur_kusto.fetchone()]
        data_kusto.append(buf)
        kusto_uuid_list.append(buf[2])
        kusto_name_list.append(buf[1])

    # Отдельно создаём список c количеством записей в классификаторе
    cur_kusto.execute(f"""
                SELECT b.name_full, count(a.name_kls)
                FROM kls.tkls as a
                join kls.tqual as b
                on a.link = b.id
                group by b.name_full;
                
            """)
    for _ in range(cur_kusto.rowcount):
        buf = [*cur_kusto.fetchone()]
        kusto_kls.append(buf[0])
        kusto_kls_count.append(buf)

    # Данные по классификаторами Asip из таблицы location_classifiers
    cur_asilp.execute(f"""
                 SELECT A.name_full, A.id, C.name_classifier
                 FROM data.location_classifiers as A
                 left join refs.location_classifiers as B on A.id = B.id
                 left join data.dict_classifiers as C on C.id = B.id_classifier
                 ORDER BY id;
             """)
    for _ in range(cur_asilp.rowcount):
        buf = [*cur_asilp.fetchone()]
        asip_ksl.append(buf)
    # Данные по классификаторами Asip из массива таблиц list_dict
    for item in list_dict:
        cur_asilp.execute(f"""
                     SELECT A.name_full, A.id,
                     obj_description('data.{item}'::regclass, 'pg_class') as table
                     FROM data.{item} as A
                     
                     ORDER BY id;
                 """)
        for _ in range(cur_asilp.rowcount):
            buf = [*cur_asilp.fetchone()]
            asip_ksl.append(buf)

    # Посчитаем количество записей для словаря классификаторов (классификатор классификаторов)
    for item in asip_ksl:
        if item[2] not in asip_kls_count:
            asip_kls_count[item[2]] = 0
        asip_kls_count[item[2]] += 1




    # Создаём словарь и заполняем его сравнением классификаторов Asip и Kusto
    for buf in asip_ksl:
        if buf[1] in kusto_uuid_list:
            # result.append([*data_kusto[kusto_uuid_list.index(buf[1])],*buf])
            if buf[2] not in dict_diff:
                dict_diff[buf[2]] = {}
                dict_diff[buf[2]]['Совпадений по Uuid'] = 0
                dict_diff[buf[2]]['Совпадений по названию'] = 0
            dict_diff[buf[2]]['Совпадений по Uuid'] += 1

            buf2 = kusto_uuid_list.index(buf[1])
            if data_kusto[buf2][0] not in dict_diff[buf[2]]:
                dict_diff[buf[2]][f'{data_kusto[buf2][0]}'] = 0
            dict_diff[buf[2]][f'{data_kusto[buf2][0]}'] += 1

        elif buf[0] in kusto_name_list:
            if buf[2] not in dict_diff:
                dict_diff[buf[2]] = {}
                dict_diff[buf[2]]['Совпадений по Uuid'] = 0
                dict_diff[buf[2]]['Совпадений по названию'] = 0
            dict_diff[buf[2]]['Совпадений по названию'] += 1


            buf2 = kusto_name_list.index(buf[0])
            if data_kusto[buf2][0] not in dict_diff[buf[2]]:
                dict_diff[buf[2]][f'{data_kusto[buf2][0]}'] = 0
            dict_diff[buf[2]][f'{data_kusto[buf2][0]}'] += 1
            # result.append([*data_kusto[kusto_name_list.index(buf[0])],*buf])

    for item in dict_diff:
        for meti in dict_diff[item]:
            try:
                asd = kusto_kls.index(meti)
                dict_diff[item][meti] = {'Совпадений с 102М6': dict_diff[item][meti]}, {'Всего классификаторов': kusto_kls_count[asd][1]}
            except: continue
        dict_diff[item]['Всего записей в 102М6'] = asip_kls_count.get(item)

    dict_diff = dict(sorted(dict_diff.items(),
                                   key=lambda item: (item[1]['Совпадений по Uuid'] + item[1]['Совпадений по названию']), reverse=True))

    # Записываем данные в файл
    table = Table(name="MyDataTable")
    table.addElement(TableColumn(numbercolumnsrepeated=3))
    for key, item in dict_diff.items():
        row_header = TableRow()
        cell_header = TableCell(numbercolumnsspanned=3)
        cell_header.addElement(P(text='Название классификатора из 102М6: "' + key + '"'))
        row_header.addElement(cell_header)
        row_header.addElement(TableCell())
        row_header.addElement(TableCell())
        table.addElement(row_header)

        row_data = TableRow()
        cell = TableCell()
        cell.addElement(P(text=('Совпадений по Uuid: ' + f"{dict_diff[key]['Совпадений по Uuid']}")))
        row_data.addElement(cell)

        cell = TableCell()
        cell.addElement(P(text=('Совпадений по названию: ' + f"{dict_diff[key]['Совпадений по названию']}")))
        row_data.addElement(cell)

        cell = TableCell()
        cell.addElement(P(text=('Всего записей в 102М6: ' + f"{dict_diff[key]['Всего записей в 102М6']}")))
        row_data.addElement(cell)
        table.addElement(row_data)

        for key_sub, item_sub in item.items():
            if key_sub in ['Совпадений по названию', 'Совпадений по Uuid', 'Всего записей в 102М6']:
                continue
            row_data = TableRow()
            cell = TableCell()
            cell.addElement(P(text=('Название классификатора из 50Ш6: "' + key_sub + '"')))
            row_data.addElement(cell)

            cell = TableCell()
            cell.addElement(P(text=('Совпадений с 102М6: ' + f"{item_sub[0]['Совпадений с 102М6']}")))
            row_data.addElement(cell)

            cell = TableCell()
            cell.addElement(P(text=('Всего записей в 50Ш6: ' + f"{item_sub[1]['Всего классификаторов']}")))
            row_data.addElement(cell)

            table.addElement(row_data)


    textdoc = OpenDocumentText()
    textdoc.text.addElement(table)
    textdoc.save(output_filename)
    print(f"Файл {output_filename} успешно сохранен.")

    print(dict_diff)

    print(result)
    print(len(result))


# Вывести все классификаторы 102М6 и кусто
def Kls_kusto_and_102M6(output_filename1="/home/user/Desktop/Kusto_cls_all.odt", output_filename2="/home/user/Desktop/102M6_cls_all.odt", output_filename3 ="/home/user/Desktop/csu_cls_all.odt"):
    list_dict = ["dict_categories_ret", "dict_climatic_area", "dict_degree_damage", "dict_hran", "dict_hurt",
                 "dict_months", "dict_vid_ret", "kls_okopf", "okei", "registr_company", "registr_military_parts",
                 "type_complect_element", "type_of_army", "moni_object_species", "view_classifiers", "boudary_types",
                 "directory_itempart_location", "documents_statuses", "spr_type_military_form",
                 "weapons_objects_content_types"]
    csu_table = ['dolg_brig', 'dolg_nach', 'edin_izm', 'izgot', 'spec', 'sroki', 'tip_blok', 'tip_elem',
                 'tip_izdelie',  'tip_sdz', 'tip_sostav_vvt', 'tip_svd', 'tip_vch', 'tip_zip', 'tipy_doc', 'vid_pki', 'vid_rabot', 'vid_vs_rod' ]
    # 'tip_kip', 'tip_remont',

    kusto_list = []
    csu_list = []
    asip_ksl = []

    # Собираем данные по кусто: лист уидов, названий, и полный список
    cur_kusto.execute(f"""
                SELECT b.name_full, a.name_kls
                FROM kls.tkls as a
                right join kls.tqual as b
                on a.link = b.id;
            """)
    for _ in range(cur_kusto.rowcount):
        buf = [*cur_kusto.fetchone()]
        kusto_list.append([buf[0],buf[1]])

    cur_kusto.execute(f"""
                SELECT name_psn
                FROM psn.tpsn;
            """)
    for _ in range(cur_kusto.rowcount):
        buf = [*cur_kusto.fetchone()]
        kusto_list.append(['Словарь ПСН',buf[0]])

    # Данные по классификаторами Asip из таблицы location_classifiers
    cur_asilp.execute(f"""
                 SELECT 
                 C.name_classifier,
                 A.name_full
                 FROM data.location_classifiers as A
                 left join refs.location_classifiers as B on A.id = B.id
                 left join data.dict_classifiers as C on C.id = B.id_classifier
                 ORDER BY C.name_classifier;
             """)
    for _ in range(cur_asilp.rowcount):
        buf = [*cur_asilp.fetchone()]
        asip_ksl.append(buf)
    # Данные по классификаторами Asip из массива таблиц list_dict
    for item in list_dict:
        cur_asilp.execute(f"""
                     SELECT 
                     obj_description('data.{item}'::regclass, 'pg_class') as table, 
                     A.name_full                     
                     FROM data.{item} as A
                     ORDER BY obj_description('data.{item}'::regclass, 'pg_class');
                 """)
        for _ in range(cur_asilp.rowcount):
            buf = [*cur_asilp.fetchone()]
            asip_ksl.append(buf)

    # Заполненеие таблицы с классификаторами ЦСУ
    for item in csu_table:
        cur_csu.execute(f"""
                     SELECT 
                     obj_description('granit.{item}'::regclass, 'pg_class') as table, 
                     name                 
                     FROM granit.{item} as A
                     ORDER BY obj_description('granit.{item}'::regclass, 'pg_class');
                 """)
        for _ in range(cur_csu.rowcount):
            buf = [*cur_csu.fetchone()]
            csu_list.append(buf)

    # Записываем данные в файл
    TableKusto = Table(name="MyDataTable")
    TableKusto.addElement(TableColumn(numbercolumnsrepeated=2))
    for item in kusto_list:
        row_data = TableRow()
        cell = TableCell()
        cell.addElement(P(text=(item[0])))
        row_data.addElement(cell)

        cell = TableCell()
        cell.addElement(P(text=(item[1])))
        row_data.addElement(cell)
        TableKusto.addElement(row_data)

    textdoc = OpenDocumentText()
    textdoc.text.addElement(TableKusto)
    textdoc.save(output_filename1)


    Table102M6= Table(name="MyDataTable2")
    Table102M6.addElement(TableColumn(numbercolumnsrepeated=2))
    for item in asip_ksl:
        row_data = TableRow()
        cell = TableCell()
        cell.addElement(P(text=(item[0])))
        row_data.addElement(cell)

        cell = TableCell()
        cell.addElement(P(text=(item[1])))
        row_data.addElement(cell)
        Table102M6.addElement(row_data)

    textdoc = OpenDocumentText()
    textdoc.text.addElement(Table102M6)
    textdoc.save(output_filename2)


    TableCsu= Table(name="MyDataTable3")
    TableCsu.addElement(TableColumn(numbercolumnsrepeated=2))
    for item in csu_list:
        row_data = TableRow()
        cell = TableCell()
        cell.addElement(P(text=(item[0])))
        row_data.addElement(cell)

        cell = TableCell()
        cell.addElement(P(text=(item[1])))
        row_data.addElement(cell)
        TableCsu.addElement(row_data)

    textdoc = OpenDocumentText()
    textdoc.text.addElement(TableCsu)
    textdoc.save(output_filename3)

    print(f"Файл {output_filename1} успешно сохранен.")
    print(f"Файл {output_filename2} успешно сохранен.")
    print(f"Файл {output_filename3} успешно сохранен.")



def found_word():
    word_found = 'ООО'
    cur_f = cur_asilp
    data_all = []
    with open ('./bufer.txt', 'w', encoding='utf-8') as f:
        cur_f.execute( f""" 
                DO $$
                DECLARE
                    r RECORD;
                    search_term TEXT := '{word_found}';
                BEGIN
                    FOR r IN
                        SELECT table_schema, table_name, column_name
                        FROM information_schema.columns
                        WHERE data_type IN ('character varying', 'text', 'character')
                          AND table_schema NOT IN ('pg_catalog', 'information_schema')
                    LOOP
                        EXECUTE format('SELECT 1 FROM %I.%I WHERE %I::text ILIKE %L LIMIT 1',
                            r.table_schema, r.table_name, r.column_name, '%' || search_term || '%')
                        INTO r.table_name; 
                
                        IF FOUND THEN
                            RAISE NOTICE 'Найдено в таблице: %.%, колонка: %', r.table_schema, r.table_name, r.column_name;
                        END IF;
                    END LOOP;
                END $$;
                """)
        for _ in range(cur_f.rowcount):
            buf = [*cur_f.fetchone()]
            f.write(str(*buf) + '\n')


    with open('./bufer.txt', 'r', encoding='utf-8') as f, \
            open('./output.txt', 'w', encoding='utf-8') as output:
                for line in f:
                    cur_f.execute(line)
                    for _ in range(cur_f.rowcount):
                        buf = [*cur_f.fetchone()]
                        if buf != []:
                           output.write(str(buf) + '\n')

    print("Хотово, смотри output.txt")




def kusto_separation(list_kls = []):
    cwd = str(Path(__file__).resolve().parent)

    with open (cwd + '/data/cls.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            list_kls.append(row)

    cur_kusto.execute(f"""
    drop schema if exists test cascade;
    create schema if not exists test;
    comment on schema test is 'Не трогать! Производятся ремонтные работы'; 
    """)

    for item in list_kls:
        cur_kusto.execute(f"""
                    create table if not exists test.{(item[0])} (
                    id serial4 primary key NOT NULL,
                    idv int4 DEFAULT 0 NOT NULL,
                    name_kls text NOT NULL,
                    shifr_kls text NULL,
                    note text NULL,
                    date_del timestamp NULL,
                    image text NULL,
                    id_kls_v int4 NULL,
                    code text NULL,
                    used bool NULL
                    );
                    comment on table test.{(item[0])} is '{item[1]}';
                    COMMENT ON COLUMN test.{(item[0])}.id IS 'Ключ';
                    COMMENT ON COLUMN test.{(item[0])}.idv IS 'Код родителя';
                    COMMENT ON COLUMN test.{(item[0])}.name_kls IS 'Наименование класса ';
                    COMMENT ON COLUMN test.{(item[0])}.shifr_kls IS 'Шифр класса';
                    COMMENT ON COLUMN test.{(item[0])}.note IS 'Примечание';
                    COMMENT ON COLUMN test.{(item[0])}.date_del IS 'Дата удаления';
                    COMMENT ON COLUMN test.{(item[0])}.image IS 'Картинка';
                    COMMENT ON COLUMN test.{(item[0])}.id_kls_v IS 'Позиция связанного классификатора';
                    COMMENT ON COLUMN test.{(item[0])}.code IS 'Код';
                    COMMENT ON COLUMN test.{(item[0])}.used IS 'Используется при загрузке классификаторов из ИЛО';
                 """)
        cur_kusto.execute(f"""
                INSERT INTO test.{(item[0])}
                select id, idv, name_kls, shifr_kls, note, date_del, image, id_kls_v, code, used 
                from kls.tkls 
                where link = '{item[2]}';
                """)

    conn_kusto.commit()

#Сохраняем данные из бд Kusto в SQL файл
def copy_data_kls_kusto_asu():
    import re
    schema = 'cls'
    cwd = str(Path(__file__).resolve().parent)
    list_kls = []

    with open((cwd + f'/data/{schema}.csv'), mode='r') as csv_file:
        reader = csv.reader(csv_file, delimiter= ';')
        for line in reader:
            list_kls.append(line[0])

    with open( f'./../sql/ver_data_init.sql', mode='w') as f:
        f.write("""SET statement_timeout = 0;
                    SET lock_timeout = 0;
                    SET idle_in_transaction_session_timeout = 0;
                    SET client_encoding = 'UTF8';
                    SET standard_conforming_strings = off;
                    SELECT pg_catalog.set_config('search_path', '', false);
                    SET check_function_bodies = false;
                    SET xmloption = content;
                    SET client_min_messages = warning;
                    SET escape_string_warning = off;
                    SET row_security = off; \n\n\n""")

        for item in list_kls:
            f.write(f"INSERT INTO cls.{item} (id, idv, name_kls, shifr_kls, note, date_del, image, id_kls_v, code, used) VALUES \n")
            cur_kusto.execute( f"""
                                SELECT id, idv, name_kls, shifr_kls, note, date_del, image, id_kls_v, code, used from test.{item};
                                """)
            data = cur_kusto.fetchall()
            count = 0
            for line in data:
                count += 1
                f.write(str(line))
                if count != len(data):
                    f.write(',\n')
                else:
                    f.write('; \n \n \n')

        # ЭТО ТАБЛИЦА ORG
        f.write(f"""INSERT INTO org.organization (id, idv, inn, kpp, ogrn, okpo, name_s, name_f, num, is_vf, prim, contact, addres, disl, date_del, b, l, ip_adres, port_value, okato, okopf, is_rem, b1, l1) VALUES \n""")
        cur_kusto.execute(f"""SELECT id, idv, inn, kpp, ogrn, okpo, name_s, name_f, num, is_vf, prim, contact, addres, disl, date_del, b, l, ip_adres, port_value, okato, okopf, is_rem, b1, l1 from org.organization order by idv, id;""")
        data = cur_kusto.fetchall()
        count = 0
        for line in data:
            count += 1
            f.write(str(line))
            if count != len(data):
                f.write(',\n')
            else:
                f.write('; \n \n \n')

        # ЭТО ТАБЛИЦА PSN
        f.write(f"""INSERT INTO psn.tpsn (id, name_psn, obozn_psn, deznum_psn, org_dev_link, org_manuf_link, is_zip, note, shifr_psn, date_del, fnn, pr_sovr, shifr, is_in_control_primer, from_podderzhka) VALUES""")
        cur_kusto.execute(f"""SELECT id, name_psn, obozn_psn, deznum_psn, id_org_dev, id_org_manuf, is_zip, note, shifr_psn, date_del, fnn, pr_sovr, shifr, is_in_control_primer, from_podderzhka from psn.tpsn;""")
        data = cur_kusto.fetchall()
        count = 0
        for line in data:
            count += 1
            f.write(str(line))
            if count != len(data):
                f.write(',\n')
            else:
                f.write(';')

    with open(f'./../sql/ver_data_init.sql', 'r', encoding='utf-8', errors = 'strict') as f:
        content = f.read()
        content = re.sub(r'\bNone\b', 'NULL', content)
        content = re.sub(r'\\xa0', ' ', content)

        def fix_any_datetime(match):
            # Извлекаем все числа из скобок (разбиваем по запятой и чистим пробелы)
            nums = [n.strip() for n in match.group(1).split(',')]

            # Минимум нам нужны год, месяц, день, час, минута
            y, m, d, h, mi = nums[:5]
            # Секунды берем, если они есть, иначе "00"
            s = nums[5] if len(nums) > 5 else "0"

            # Собираем стандарт 'YYYY-MM-DD HH:MM:SS' (микросекунды обычно в SQL не критичны)
            return f"'{y}-{m.zfill(2)}-{d.zfill(2)} {h.zfill(2)}:{mi.zfill(2)}:{s.zfill(2)}'"
        # Регулярка: 5 обязательных групп чисел и 1 необязательная (шестая)
        pattern = r'datetime\.datetime\((.*?)\)'

        # Применяем замену
        content = re.sub(pattern, fix_any_datetime, content)

        # 3. Сохраняем результат content = content.replace('\xa0', ' ')
    with open(f'./../sql/ver_data_init.sql', 'w', encoding='utf-8', errors = 'replace') as f:
        f.write(content)



def imput_data_cls_kusto():

    cwd = str(Path(__file__).resolve().parent)
    if len(os.listdir(cwd + '/data')) <1:
        print('Не найдены файлы, копирование осталновлено')
        return
    schema = 'cls'
    list_kls = []

    with open((cwd + f'/data/{schema}.csv'), mode='r') as csv_file:
        reader = csv.reader(csv_file, delimiter= ';')
        for line in reader:
            list_kls.append(line[0])
    for item in list_kls:
        with open((cwd + f'/data/{item}.csv'), mode='r') as csv_file:
            sql =   f""" COPY {schema}.{item} FROM STDIN WITH (FORMAT CSV, HEADER) """
            cur_asu.copy_expert(sql, csv_file)

    with open((cwd + f'/data/torg.csv'), mode='r') as csv_file:
        sql = f""" COPY org.torg FROM STDIN WITH (FORMAT CSV, HEADER) """
        cur_asu.copy_expert(sql, csv_file)
    with open((cwd + f'/data/tpsn.csv'), mode='r') as csv_file:
        sql = f""" COPY psn.tpsn FROM STDIN WITH (FORMAT CSV, HEADER) """
        cur_asu.copy_expert(sql, csv_file)
    print('Данные классификаторов, ПСН и Орг заполенны')

    conn_asu.commit()
    cur_asu.close()
    conn_asu.close()


if __name__ == "__main__":
    # kusto_count_kls_psn()
    # kusto_kls()
    # kusto_psn()
    # Analysis_Tables(filter = filter_102M6_doc, output_filename = "/home/user/Desktop/doc_data_102M6.odt", schema = 'data' )
    # # print (table_names_schema(filter_tables))
    # diff_kls_kusto_102M6()
    # Kls_kusto_and_102M6()
    # found_word()
    # kusto_separation()
    copy_data_kls_kusto_asu()
    # imput_data_cls_kusto()
    # function_analysis(1)

    cur_kusto.close()
    conn_kusto.close()