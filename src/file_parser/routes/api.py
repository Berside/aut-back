# from flask import Blueprint, request, jsonify, session
# from src.file_parser.file_loader import FileLoader
# from src.orm.orm_sys import FileType
# import tempfile, os, shutil
# from flask import current_app
# from src.db import db
# from werkzeug.utils import secure_filename 
# import traceback

# import Levenshtein
# from Levenshtein import distance, ratio, jaro, seqratio, editops, opcodes, apply_edit, matching_blocks
# api = Blueprint('api', __name__, url_prefix='/api')

# # @api.route('/file-types', methods=['GET'])
# # def get_file_types():
# #     try:
# #         types = db.session.query(FileType).all()
# #         print("oooo")

# #         return jsonify([{'id': t.id, 'name': t.name, 'note': t.note, 'config_path': t.config_path,
# #             'parser_class': t.parser_class, 'target_model': t.target_model} for t in types])
    
# #     except Exception as e:
# #         print("[[[[[[]]]]]]")
# #         return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

#     #

# @api.route('/upload/confirm', methods=['POST'])
# def upload_confirm():
#     data = request.json
#     decisions = data.get('decisions')
#     new_counts = data.get('newCounts')
#     upload_data = session.get('upload_data')
#     groups = session.get('groups')
#     if not upload_data:
#         return jsonify({'error':'Нет данных для подтверждения'}), 400

#     parsed_data = upload_data['parsed_data']
#     file_type_id = upload_data['file_type_id']
#     target_model = upload_data['target_model']

#     to_remove = set()

#     if decisions:
#         for i, group in enumerate(groups):
#             selected_local_indices = decisions[i] if i < len(decisions) else []
#             if not selected_local_indices:
#                 for idx in group:
#                     to_remove.add(idx) 
#                 continue
#             selected_global = {group[idx] for idx in selected_local_indices}
#             for idx in group:
#                 if idx not in selected_global:
#                     to_remove.add(idx)

#     if new_counts:
#         for item in new_counts:
#             group_idx = item['groupIndex']
#             target_local_idx = item['targetLocalIndex']
#             new_count = item['newCount']
#             if group_idx < len(groups):
#                 global_idx = groups[group_idx][target_local_idx]
#                 parsed_data[global_idx]['current_count'] = new_count

#     final_data = [row for i, row in enumerate(parsed_data) if i not in to_remove ] #????????

#     loader = FileLoader(db.session)
#     count = loader.save_parsed_data(final_data, file_type_id, target_model)

#     # session.pop('upload_data', None) - оставляем в сессии уже загруженные данные для повторного использования
#     session.pop('groups', None)

#     if not groups:
#         return jsonify({'message': f'Дубликаты не найдены. Успешно загружено {count} записей'})

#     return jsonify({'message': f'Успешно загружено {count} записей'})

# @api.route('/upload/preview', methods=['POST'])
# def upload_preview():
#     if 'file' not in request.files:
#         return jsonify({'error': 'Нет файла'}), 400

#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({'error': 'Файл не выбран'}), 400
    
#     file_type_id = request.form.get('file_type_id')
#     if not file_type_id:
#         return jsonify({'error': 'Нужен id файла'}), 400

#     filename = secure_filename(file.filename)    
#     upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
#     os.makedirs(upload_folder, exist_ok=True)

#     file_path = os.path.join(upload_folder, filename)
#     file.save(file_path)

#     try:
#         loader = FileLoader(db.session)
#         parsed_data, target_model, config, headers = loader.parse_file(file_type_id, file_path)

#         column_mapping = config.get('row_rules', {}).get('column_mapping', {})
#         ignore_columns = config.get('row_rules', {}).get('ignore_columns', [])  #буквами по столбцам excel
        
#         columns_info = []

#         for col_letter, field in column_mapping.items():
#             if col_letter in ignore_columns:
#                 continue

#             label = headers.get(col_letter, field)

#             columns_info.append({'key': field, 'label': label})

#         session['upload_data'] = {
#             'parsed_data': parsed_data,
#             'file_type_id': file_type_id,
#             'target_model': target_model,
#             'config': config,
#             'columns_info': columns_info
#         }

#         preview_rows = parsed_data[:3]
#         return jsonify({
#             'columns': columns_info,
#             'preview': preview_rows
#         })

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
#     finally:
#         if os.path.exists(file_path):
#             os.remove(file_path)


# @api.route('upload/find-duplicates', methods=['POST'])
# def find_duplicates():
#     data = request.json
#     selected_keys = data.get('columns', [])

#     if not selected_keys:
#         return jsonify({'error': 'Не выбрано ни одного столбца для сравнения'}), 400

#     upload_data = session.get('upload_data')
#     if not upload_data:
#         return jsonify({'error': 'Нет данных. Загрузите файл'}), 400

#     parsed_data = upload_data['parsed_data']
#     columns_info = upload_data.get('columns_info', [])

#     selected_columns_info = [col for col in columns_info if col['key'] in selected_keys]

#     column_labels = {col['key']: col['label'] for col in columns_info if col['key'] in selected_keys}

#     loader = FileLoader(db.session)
#     group_data, groups = loader.find_duplicate_groups(parsed_data, selected_keys, column_labels)
#     session['groups'] = groups

#     return jsonify({'groups': group_data, 'has_duplicates': bool(group_data), 'selected_columns': selected_columns_info})


# @api.route('/warehouse_table', methods=['GET'])
# def get_file_types():
#     try:
#         types = db.session.query(FileType).all()  #todo вместо FileType название ОРМа Вани

#         return jsonify([{'id': t.id, 'name': t.name, 'note': t.note, 'config_path': t.config_path, #todo и поля
#             'parser_class': t.parser_class, 'target_model': t.target_model} for t in types])
    
#     except Exception as e:
#         return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500