import json
import importlib
import Levenshtein 
from Levenshtein import editops
import rapidfuzz
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import inspect, event
from src.orm.orm_sys import FileType
from src.orm.orm_list import ListResources, ListResourceLocation
from src.orm.orm_cls import DictResource, DictResourceType, DictResourceCategory, DictOkei
from src.file_parser.xlsxparser import AbstractParser, XlsxParser
from pathlib import Path
from .similar import are_similar

class FileLoader:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.inserted_count = 0
        self.main_model_class = None
        event.listen(self.db, 'before_flush', self.before_flush)

    def before_flush(self, session, flush_context, instances):
        if self.main_model_class is None:
            return
        for obj in session.new:
            if isinstance(obj, self.main_model_class):
                self.inserted_count += 1

    def parse_file(self, file_type_id, file_path):
        """Только парсинг"""
        file_type = self.db.query(FileType).filter(FileType.id == file_type_id).first()
        if not file_type:
            raise ValueError(f"Файл с id {file_type_id} не найден")
        
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent
        config_file = f'{project_root}/config/{file_type.config_path}'
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

            column_mapping = config.get('column_mapping', [])
            static_fields = config.get('static_fields', [])

            target_model = config.get('file_rules', {}).get('target_model')
            unique_parts_by_model = {}
            nullable_fields_by_model = {}
            no_insert_models = []

            for item in column_mapping:
                field = item.get('field')
                if not field:
                    continue

                if item.get('type') == 'classifier_find' and '.' in field: # запрет на вставку
                    parts = field.split('.')
                    model_name = parts[-2]
                    if model_name not in no_insert_models:
                        no_insert_models.append(model_name)
                    unique_parts_by_model.setdefault(model_name, []).append([parts[-1]])
                    continue

                # обработка уникальности для полей с разбивкой (как локация)
                if item.get('type') == 'column_parsing':
                    child_model = field
                    to_parse = item.get('to_parse')
                    unique_fields = item.get('unique_fields', []) if item.get('unique_fields') is not None else item.get('to_parse', [])

                    # для дочерней модели
                    for f in unique_fields:
                        unique_parts_by_model.setdefault(child_model, []).append([f])
                    # для target_model - FK
                    if item.get('dictionary_property'):
                        unique_parts_by_model.setdefault(target_model, []).append([child_model])

                    nullable_fields_by_model[child_model] = list(to_parse)
                    continue

                if '.' in field:
                    parts = field.split('.')
                    attr = parts[-1]

                    # для последней модели добавляем атрибут
                    model_owner = parts[-2]
                    unique_parts_by_model.setdefault(model_owner, []).append([attr])

                    # для всех промежуточных моделей добавляем путь от след. части до конца
                    for i in range(len(parts) - 2):
                        model = parts[i]
                        path = parts[i+1:]

                        unique_parts_by_model.setdefault(model, []).append(path)

                    if item.get('dictionary_property'):
                        unique_parts_by_model.setdefault(target_model, []).append([parts[0]])

                # поле без точки - для целевой
                elif item.get('dictionary_property'):
                    unique_parts_by_model.setdefault(target_model, []).append([field])

            for sf in static_fields:
                if sf.get('dictionary_property'):
                    unique_parts_by_model.setdefault(target_model, []).append([sf['model']])

            parser_class_name = file_type.parser_class
            try:
                module = importlib.import_module(f"src.file_parser.{parser_class_name.lower()}")
                parser_cls = getattr(module, parser_class_name)
            except (ImportError, AttributeError) as e:
                raise ImportError(f"Парсер {parser_class_name} не найден")
                
            parser = AbstractParser = parser_cls()
            parsed_data = parser.parse(file_path, config)
            headers = getattr(parser, 'headers', {})

        return parsed_data, config, headers, no_insert_models, unique_parts_by_model, nullable_fields_by_model, static_fields

    def parse_nested_keys(self, flat_dict, target_model=None):
        """Преобразует словарь с ключами с точкой во вложенный словарь"""
        result = {}
        for key, value in flat_dict.items():
            if '.' in key:
                parts = key.split('.')
                if target_model and parts[0] == target_model:
                    parts = parts[1:]
                    if not parts:
                        continue
                current = result
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                result[key] = value
        return result

    def get_fk_column(self, model, related_model):
        """Возвращает имя столбца, явл. внешним ключом / или None, если нет"""
        for rel_obj in inspect(model).relationships:
            if not rel_obj.uselist and rel_obj.mapper.class_ is related_model:
                local_columns = list(rel_obj.local_columns)
                if len(local_columns) == 1:
                    return local_columns[0].name
        return None


    def create_or_update_model(self, model_name, model_class, model_mapping, data, session, no_insert_models=None, unique_parts_by_model=None, nullable_fields_by_model=None, static_fields=None):
        if no_insert_models is None:
            no_insert_models = []
        if unique_parts_by_model is None:
            unique_parts_by_model = {}
        if nullable_fields_by_model is None:
            nullable_fields_by_model = {}
        if static_fields is None:
            static_fields = []

        # рекурсия для поиска дочерних
        children = {}
        for child_name, child_class in model_mapping.items():
            if child_name in data and isinstance(data[child_name], dict):
                child_obj = self.create_or_update_model(child_name, child_class, model_mapping, data[child_name], session, no_insert_models, unique_parts_by_model, nullable_fields_by_model, static_fields)
                if child_obj is not None:
                    children[child_name] = child_obj


        for sf in static_fields:
            child_class = model_mapping.get(sf.get('model'))
            if not child_class:
                continue
            fk_field = self.get_fk_column(model_class, child_class)
            if not fk_field:
                continue

            identity_field = sf.get('identity', 'name_ru') # по умолчанию - name_ru

            field_values = {
                k: v for k, v in sf.items()
                if k not in ('model', 'id', 'dictionary_property', 'identity') # отсеивает служебные ключи, берет только те, что нужны для работы с базой
            }
            child_obj = self.get_or_create_static(
                session, child_class, field_values, identity_field=identity_field, obj_id=sf.get('id')
            )
            children[sf['model']] = child_obj

        has_data = any(key not in model_mapping and value is not None for key, value in data.items())

        if not has_data:
            return None

        # получить уникальные пути для текущей модели
        paths = unique_parts_by_model.get(model_name)
        nullable = nullable_fields_by_model.get(model_name, list())

        # построить фильтры для поиска записи
        filters = []

        if paths:
            for path in paths:
                key = path[0] if isinstance(path, list) else path
                if key in model_mapping: # FK на дочернюю модель
                    child_obj = children.get(key)
                    if child_obj is None:
                        continue
                    child_class = model_mapping[key]
                    fk_field = self.get_fk_column(model_class, child_class)
                    if not fk_field:
                        continue
                    filters.append(getattr(model_class, fk_field) == child_obj.id)
                else: # прямое поле
                    if key not in data:
                        continue
                    value = data.get(key)
                    if value is None:
                        if key in nullable:
                            continue
                        filters = None
                        break
                    filters.append(getattr(model_class, key) == value)

        # ПОИСК
        obj = None
        if filters:
            query = session.query(model_class)
            for fil in filters:
                query = query.filter(fil)
            obj = query.first()

        # если найден - обновить - кроме влож. моделей
        if obj is not None:
            for key, value in data.items():
                if key not in model_mapping and key != 'id':
                    setattr(obj, key, value)

            for child_name, child_obj in children.items():
                child_class = model_mapping.get(child_name)
                if child_class:
                    fk_field = self.get_fk_column(model_class, child_class)
                    if fk_field:
                        setattr(obj, fk_field, child_obj.id)

            return obj

        if model_name in no_insert_models:
            return None


        # СОЗДАНИЕ нового
        obj = model_class()
        obj.new_created = True
        for key, value in data.items():
            if key not in model_mapping and key != 'id':
                setattr(obj, key, value)

        for child_name, child_obj in children.items():
            child_class = model_mapping.get(child_name)
            if child_class:
                fk_field = self.get_fk_column(model_class, child_class)

                if fk_field:
                    setattr(obj, fk_field, child_obj.id)

        session.add(obj)
        session.flush()

        return obj


    def save_parsed_data(self, parsed_data, file_type_id, target_model_name, no_insert_models=None, unique_parts_by_model=None, nullable_fields_by_model=None, static_fields=None):
        """Только сохранение уже спаршеного"""
        model_mapping = {
            'ListResources': ListResources,
            'DictResource': DictResource,
            'DictResourceName': DictResourceName,
            'DictResourceCategory': DictResourceCategory,
            'DictOkei': DictOkei,
            'ListResourceLocation': ListResourceLocation,
            'ListDepartment': ListDepartment
            # Дальше другие модели
        }

        if no_insert_models is None:
            no_insert_models = []
        if nullable_fields_by_model is None:
            nullable_fields_by_model = {}
        if static_fields is None:
            static_fields = []

        MainModel = model_mapping.get(target_model_name)
        self.main_model_class = MainModel
        self.inserted_count = 0

        if not MainModel:
            raise ValueError(f"Основная модель {target_model_name} не найдена")

        for flat_row in parsed_data:
            nested_row = self.parse_nested_keys(flat_row, target_model_name)
            main_obj = self.create_or_update_model(target_model_name, MainModel, model_mapping, nested_row, self.db, no_insert_models, unique_parts_by_model, nullable_fields_by_model, static_fields)
            
        self.db.commit()
        self.main_model_class = None
        return self.inserted_count


    def find_duplicate_groups(self, parsed_data, selected_columns, column_labels):
        """Возвращает список групп дубликатов. Каждая группа – список индексов строк в parsed_data."""
        groups = []
        used = set()
        steps_cache = {}
        for i, row1 in enumerate(parsed_data):
            if i in used:
                continue

            if not any(row1.get(col) for col in selected_columns): # проускаем пустые элементы из выбранного столбца
                continue

            group = [i]
            for j, row2 in enumerate(parsed_data[i+1:], start=i+1):
                if j in used:
                    continue

                if not any(row2.get(col) for col in selected_columns): # проускаем пустые элементы из выбранного столбца
                    continue
            
                all_similar = True  

                for col in selected_columns:
                    val1 = row1.get(col)
                    val2 = row2.get(col)

                    if not val1 or not val2:                                  # в этом случае при выборе двух столбцов, 
                        all_similar = False                                   # если в одном пустые значения, дублями НЕ считаются
                        break
                    if not(are_similar(str(val1), str(val2))):
                        all_similar = False
                        break

                if all_similar:
                    group.append(j)
                    used.add(j)
                else: 
                    continue
            if len(group) > 1:
                groups.append(group)
                used.add(i)


        group_data = []
        for g in groups:
            first_idx = g[0]
            first_row = parsed_data[first_idx]
            col_diffs = {}
            rows_out = []

            for idx in g:
                row = parsed_data[idx]
                texts = {}
                row_diffs = {}

                for col_key in selected_columns:
                    col_label = column_labels.get(col_key, col_key)
                    cur_val = row.get(col_key)

                    first_val = first_row.get(col_key, '')

                    if cur_val is None:
                        display = ''
                    elif isinstance(cur_val, list):
                        display = ' '.join(str(v) for v in cur_val)
                    else:
                        display = str(cur_val)

                    texts[col_key] = display

                    if idx == first_idx:
                        row_diffs[col_key]=  []

                    else:
                        s1 = '' if first_val is None else str(first_val)
                        if s1 == display:
                            row_diffs[col_key] = []
                        else:
                            diffs, _, diff2 = self.analyze_diff(s1, display)
                            row_diffs[col_key] = diff2
                            if diffs:
                                col_diffs.setdefault(col_label, set()).update(diffs)

                rows_out.append({
                    'texts': texts,
                    'diffs': row_diffs,
                    'row_index': idx + 1,
                    'current_stock': row.get('current_stock', 0)
                    # 'current_count': row.get('current_count', row.get('current_stock', 0)) or 0 #! надо ли брать именно так
                })

            description_parts = []
            for col_label, diffs_set in col_diffs.items():
                if diffs_set:
                    description_parts.append(f"Столбец '{col_label}': {', '.join(sorted(diffs_set))}")

            if not description_parts:
                description_parts.append("Идентичны")

            group_data.append({
                'rows': rows_out,
                'description': ', '.join(description_parts) if description_parts else 'Нормализованы'
            })

        return group_data, groups


    def analyze_diff(self, s1, s2):
        """Возвращает признаки, по которым строки отличаются"""

        ed = editops(s1, s2)
        result = set()
        diff_indices = []
        min_len = min(len(s1), len(s2))
        diff1 = []
        diff2 = []

        upper_map = {
                'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M',
                'Н': 'H', 'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T',
                'Х': 'X', 
        }
        trans_upper = str.maketrans(upper_map)

        lower_map = {
                'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c',
                'у': 'y', 'х': 'x', 
        }
        trans_lower = str.maketrans(lower_map)

        for tag, i, j in ed:
            ch1 = s1[i:i+1] #Берем s1[i], но избегаем out of range
            ch2 = s2[j:j+1]
            if tag == 'replace':

                if ch1.lower() == ch2.lower():
                    result.add('Различается регистр')
                
                elif ch1 == ' ' or ch2 == ' ':
                    result.add("Лишний пробел")

                if (ch1 == ' ' and ch2 in ('-', '—')) and (s1[i+1:i+2] in ('-', '—') and s2[j+1:j+2] == ' '):
                    result.add('Различаются тире')

                elif ch1.translate(trans_upper) == ch2.translate(trans_upper):
                    result.add("Различается язык заглавных букв")    

                elif ch1.translate(trans_lower) == ch2.translate(trans_lower):
                    result.add("Различается язык строчных букв")    

                elif ((ch1 in ('з', 'З')) and ch2 == '3') or ((ch2 in ('з', 'З')) and ch1 == '3'):
                    result.add("Перепутаны 'три' и 'зэт'")

                elif ((ch1 in ('o', 'о')) and ch2 == '0') or ((ch2 in ('o', 'о')) and ch1 == '0'):
                    result.add("Перепутаны 'ноль' и 'о'")

                elif (ch1 == '.' and ch2 == ',') or (ch2 == '.' and ch1 == ','):
                    result.add('Различаются точка и запятая')

                elif (ch1 == '-' and ch2 == '—') or (ch2 == '-' and ch1 == '—'):
                    result.add('Различаются тире')

                elif (ch1 == '±' and ch2 == '+' and s2[j+1:j+2] in ('-', '')) or (ch2 == '±' and ch1 == '+' and s1[i+1:i+2] in ('-', '')):
                    result.add('Различаются "±" и "+-"')

                diff_indices.append(i)
                diff_indices.append(j)

            elif tag == 'insert':
                if (ch2.isspace() and not ch1.isspace() or ch1.isspace() and not ch2.isspace()):
                    result.add("Лишний пробел")
                
                elif (ch1 == '-' and ch2 == '—') or (ch2 == '-' and ch1 == '—'):
                    result.add('Различаются тире')

                elif (ch1 == '±' and ch2 == '+' and s2[j+1:j+2] in ('-', '')) or (ch2 == '±' and ch1 == '+' and s1[j+1:j+2] in ('-', '')):
                    result.add('Различаются "±" и "+-"')
                    
                elif are_similar(s1, s2):
                    result.add("Проблема с величинами")
                
                diff_indices.append(i)
                diff_indices.append(j)

            elif tag == 'delete':
                if (ch2.isspace() and not ch1.isspace() or ch1.isspace() and not ch2.isspace()):
                    result.add("Лишний пробел")
                    diff_indices.append(i)
                    diff_indices.append(j-1)

                elif (ch1 == '-' and ch2 == '—') or (ch2 == '-' and ch1 == '—'):
                    result.add('Различаются тире')
                    diff_indices.append(i)
                    diff_indices.append(j)

                elif (ch1 in ('-', '—') and ch2 not in ('-', '—')):
                    result.add('Различаются тире')

                elif are_similar(s1, s2):
                    result.add("Проблема с величинами")
                    diff_indices.append(i)
                    diff_indices.append(j)
                

            diff1 = diff_indices[0::2]
            diff2 = diff_indices[1::2]

        if ed and not result:
            result.add("Различаются по другим признакам")
        
        return result, diff1, diff2



    def get_or_create_static(self, session, model_class, field_values, identity_field='name_ru', obj_id=None):
        identity_value = field_values.get(identity_field)

        obj = session.query(model_class).filter(getattr(model_class, identity_field) == identity_value).first()
        if not obj:
            obj = model_class(**field_values)
            if obj_id is not None:
                obj.id = obj_id
            session.add(obj)
            session.flush()
            return obj

        # если запись найдена - обновляем
        for k, v in field_values.items():
            if k == identity_field:
                continue
            setattr(obj, k, v)
        session.flush()
        return obj