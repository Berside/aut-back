from flask import Blueprint, request, jsonify, session
from src.file_parser.file_loader import FileLoader
from src.orm.orm_sys import FileType
import os
from flask import current_app
from src.db import db
import traceback

import Levenshtein
from Levenshtein import distance, ratio, jaro, seqratio, editops, opcodes, apply_edit, matching_blocks
api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/file-types', methods=['GET'])
def get_file_types():
    try:
        types = db.session.query(FileType).all()
        return jsonify([{'id': t.id, 'name': t.name, 'note': t.note, 'config_path': t.config_path,
            'parser_class': t.parser_class} for t in types])
    
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

    

@api.route('/upload/confirm', methods=['POST'])
def upload_confirm():
    data = request.json
    decisions = data.get('decisions')
    new_counts = data.get('newCounts')
    upload_data = session.get('upload_data')
    no_insert_models = upload_data.get('no_insert_models', [])
    unique_parts_by_model = upload_data.get('unique_parts_by_model', {})
    nullable_fields_by_model = upload_data.get('nullable_fields_by_model', {})
    groups = session.get('groups')
    if not upload_data:
        return jsonify({'error':'Нет данных для подтверждения'}), 400

    parsed_data = upload_data['parsed_data']
    file_type_id = upload_data['file_type_id']
    target_model = upload_data['config']['file_rules']['target_model'] 

    column_mapping = upload_data['config'].get('column_mapping', [])
    static_fields = upload_data.get('static_fields', [])

    to_remove = set()

    if decisions:
        for i, group in enumerate(groups):
            selected_local_indices = decisions[i] if i < len(decisions) else []
            if not selected_local_indices:
                for idx in group:
                    to_remove.add(idx) 
                continue
            selected_global = {group[idx] for idx in selected_local_indices}
            for idx in group:
                if idx not in selected_global:
                    to_remove.add(idx)

    if new_counts:
        for item in new_counts:
            group_idx = item['groupIndex']
            target_local_idx = item['targetLocalIndex']
            new_count = item['newCount']
            if group_idx < len(groups):
                global_idx = groups[group_idx][target_local_idx]
                parsed_data[global_idx]['current_stock'] = new_count

    final_data = [row for i, row in enumerate(parsed_data) if i not in to_remove ] #????????

    loader = FileLoader(db.session)
    count = loader.save_parsed_data(final_data, file_type_id, target_model, no_insert_models=no_insert_models, unique_parts_by_model=unique_parts_by_model, nullable_fields_by_model=nullable_fields_by_model, static_fields=static_fields)

    # session.pop('upload_data', None) - оставляем в сессии уже загруженные данные для повторного использования
    session.pop('groups', None)

    if not groups:
        return jsonify({'message': f'Дубликаты не найдены. Успешно загружено {count} записей'})

    return jsonify({'message': f'Успешно загружено {count} записей'})

@api.route('upload/preview', methods=['POST'])
def upload_preview():
    if 'file' not in request.files:
        return jsonify({'error': 'Нет файла'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    file_type_id = request.form.get('file_type_id')
    if not file_type_id:
        return jsonify({'error': 'Нужен id файла'}), 400

    filename = file.filename
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    try:
        loader = FileLoader(db.session)
        parsed_data, config, headers, no_insert_models, unique_parts_by_model, nullable_fields_by_model, static_fields = loader.parse_file(file_type_id, file_path)
        
        column_mapping = config.get('column_mapping', {})
        target_model = config.get('file_rules', {}).get('target_model', '')
        ignore_columns = {item['column'] for item in column_mapping if item.get('type') == 'ignore'}


        preview_data = [row.copy() for row in parsed_data]
        for row in preview_data:
            for item in column_mapping:
                if item.get('type') == 'column_parsing' and item.get('to_parse'):
                    field = item.get('field')
                    to_parse = item.get('to_parse')
                    parts = []
                    for p in to_parse: 
                        key = f"{field}.{p}"
                        if key in row:
                            val = row.get(key)
                            if val is not None and str(val).strip():
                                parts.append(str(val).strip())
                            del row[key]
                    if parts:
                        row[field] = '-'.join(parts)
        
        columns_info = []
        
        for item in column_mapping:
            col_letter = item.get('column')
            field = item.get('field')
            if col_letter in ignore_columns:
                continue              

            label = headers.get(col_letter, field)

            columns_info.append({'key': field, 'label': label})

        session['upload_data'] = {
            'parsed_data': parsed_data,
            'preview_data': preview_data, # для отображения и поиска дублей
            'file_type_id': file_type_id,
            'target_model': target_model,
            'config': config,
            'columns_info': columns_info,
            'no_insert_models': no_insert_models, 
            'unique_parts_by_model': unique_parts_by_model,
            'nullable_fields_by_model': nullable_fields_by_model,
            'static_fields': static_fields
        }
        
        preview_rows = preview_data[:3]
        return jsonify({
            'columns': columns_info,
            'preview': preview_rows
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@api.route('upload/find-duplicates', methods=['POST'])
def find_duplicates():
    data = request.json
    selected_keys = data.get('columns', [])

    if not selected_keys:
        return jsonify({'error': 'Не выбрано ни одного столбца для сравнения'}), 400

    upload_data = session.get('upload_data')
    if not upload_data:
        return jsonify({'error': 'Нет данных. Загрузите файл'}), 400

    parsed_data = upload_data['preview_data'] or upload_data['parsed_data']
    columns_info = upload_data.get('columns_info', [])

    selected_columns_info = [col for col in columns_info if col['key'] in selected_keys]

    column_labels = {col['key']: col['label'] for col in columns_info if col['key'] in selected_keys}

    loader = FileLoader(db.session)
    group_data, groups = loader.find_duplicate_groups(parsed_data, selected_keys, column_labels)
    session['groups'] = groups

    return jsonify({'groups': group_data, 'has_duplicates': bool(group_data), 'selected_columns': selected_columns_info})






# ============================================================================================================================
# СТАРЫЕ АПИШКИ ДЛЯ СКЛАДА - (ТОВАРЫ, АЛЁРТЫ) - переделываются

# ========== INVENTORY ITEMS (УПРАВЛЕНИЕ ЗАПАСАМИ ЗИП) ==========

# def inventory_item_to_dict(item):
#     """Преобразовать InventoryItem в JSON с расчетом доступного количества"""
#     db = SessionLocal()
#     try:
#         # Рассчитываем доступное количество = текущее - сумма активных заявок
#         active_requests = db.query(models.InventoryRequest).filter(
#             models.InventoryRequest.inventory_item_id == item.id,
#             models.InventoryRequest.status.in_(["новая", "в_процессе"])
#         ).all()
        
#         requested_total = sum(req.requested_quantity for req in active_requests)
#         # available_count = item.current_count - item.reserved_count - requested_total
#         available_count = max(0, item.current_count - item.reserved_count - requested_total)

#         return {
#             "id": item.id,
#             "article": item.article,
#             "nameRus": item.name_rus,
#             "nameEng": item.name_eng,
#             "currentCount": item.current_count,
#             "minStock": item.min_stock,
#             "availableCount": available_count,  
#             "storageName": item.storage_name,
#             "reservedCount": item.reserved_count,
#             "comment": item.comment,
#             "pdfUrl": item.pdf_url,
#             "imgName": item.image_Name,
#             "unitMeasurement": getattr(item, 'unit_measurement', None) or "шт.",
#             "createdAt": item.created_at.isoformat() if item.created_at else None,
#             "updatedAt": item.updated_at.isoformat() if item.updated_at else None
#         }
#     finally:
#         db.close()


# @app.route("/api/inventory", methods=["GET"])
# def get_inventory_items():
#     """Получить все товары со склада ЗИП"""
#     db = SessionLocal()
#     try:
#         items = db.query(models.InventoryItem).order_by(models.InventoryItem.article).all()
#         return jsonify([inventory_item_to_dict(item) for item in items])
#     finally:
#         db.close()


# @app.route("/api/inventory/<int:item_id>", methods=["GET"])
# def get_inventory_item(item_id):
#     """Получить конкретный товар со склада"""
#     db = SessionLocal()
#     try:
#         item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
#         if not item:
#             return jsonify({"error": "Item not found"}), 404
#         return jsonify(inventory_item_to_dict(item))
#     finally:
#         db.close()


# @app.route("/api/inventory", methods=["POST"])
# def create_inventory_item():
#     """Создать новый товар на складе"""
#     db = SessionLocal()
#     try:
#         data = request.get_json()
        
#         # Проверяем уникальность артикула
#         existing = db.query(models.InventoryItem).filter(
#             models.InventoryItem.article == data.get("article")
#         ).first()
        
#         if existing:
#             return jsonify({"error": "Item with this article already exists"}), 400
        
#         item = models.InventoryItem(
#             article=data.get("article"),
#             name_rus=data.get("nameRus"),
#             name_eng=data.get("nameEng"),
#             current_count=data.get("currentCount", 0),
#             min_stock=data.get("minStock", 0),
#             storage_name=data.get("storageName"),
#             comment=data.get("comment"),
#             pdf_url=data.get("pdfUrl")
#         )
#         db.add(item)
#         db.commit()
#         db.refresh(item)
#         return jsonify(inventory_item_to_dict(item)), 201
#     finally:
#         db.close()


# @app.route("/api/inventory/<int:item_id>", methods=["PUT"])
# def update_inventory_item(item_id):
#     """Обновить товар на складе"""
#     db = SessionLocal()
#     try:
#         item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
#         if not item:
#             return jsonify({"error": "Item not found"}), 404
        
#         data = request.get_json()
        
#         if "article" in data and data["article"] != item.article:
#             # Проверяем уникальность нового артикула
#             existing = db.query(models.InventoryItem).filter(
#                 models.InventoryItem.article == data["article"]
#             ).first()
#             if existing:
#                 return jsonify({"error": "Item with this article already exists"}), 400
#             item.article = data["article"]
        
#         if "nameRus" in data:
#             item.name_rus = data["nameRus"]
#         if "nameEng" in data:
#             item.name_eng = data["nameEng"]
#         if "currentCount" in data:
#             item.current_count = data["currentCount"]
#         if "minStock" in data:
#             item.min_stock = data["minStock"]
#         if "storageName" in data:
#             item.storage_name = data["storageName"]
#         if "comment" in data:
#             item.comment = data["comment"]
#         if "pdfUrl" in data:
#             item.pdf_url = data["pdfUrl"]
        
#         item.updated_at = datetime.utcnow()
#         db.commit()
#         db.refresh(item)
#         return jsonify(inventory_item_to_dict(item))
#     finally:
#         db.close()


# @app.route("/api/inventory/<int:item_id>", methods=["DELETE"])
# def delete_inventory_item(item_id):
#     """Удалить товар со склада"""
#     db = SessionLocal()
#     try:
#         item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
#         if not item:
#             return jsonify({"error": "Item not found"}), 404
        
#         db.delete(item)
#         db.commit()
#         return jsonify({"message": "Item deleted successfully"})
#     finally:
#         db.close()


# @app.route("/api/inventory/check-low-stock", methods=["POST"]) 
# def check_low_stock():
#     """
#     Проверить товары с критически низким запасом
#     и автоматически создать заявки для пополнения
#     """
#     db = SessionLocal()
#     try:
#         items = db.query(models.InventoryItem).all()
#         low_stock_items = []
#         created_requests = []
        
#         for item in items:
#             # Рассчитываем доступное количество
#             active_requests = db.query(models.InventoryRequest).filter(
#                 models.InventoryRequest.inventory_item_id == item.id,
#                 models.InventoryRequest.status.in_(["новая", "в_процессе"])
#             ).all()
#             requested_total = sum(req.requested_quantity for req in active_requests)
#             available_count = item.current_count - requested_total
            
#             # Если доступное количество ниже минимума
#             if available_count < item.min_stock and item.current_count < item.min_stock:
#                 low_stock_items.append({
#                     "id": item.id,
#                     "article": item.article,
#                     "nameRus": item.name_rus,
#                     "currentCount": item.current_count,
#                     "minStock": item.min_stock,
#                     "availableCount": available_count
#                 })
                
#                 # Создаём автоматическую заявку если её ещё нет
#                 existing_auto_request = db.query(models.InventoryRequest).filter(
#                     models.InventoryRequest.inventory_item_id == item.id,
#                     models.InventoryRequest.reason == "auto",
#                     models.InventoryRequest.status.in_(["новая", "в_процессе"])
#                 ).first()
                
#                 if not existing_auto_request:
#                     # Вычисляем необходимое количество для пополнения
#                     quantity_to_order = item.min_stock - available_count
                    
#                     auto_request = models.InventoryRequest(
#                         inventory_item_id=item.id,
#                         requested_quantity=quantity_to_order,
#                         reason="auto",
#                         status="новая",
#                         created_by="system"
#                     )
#                     db.add(auto_request)
#                     db.flush()  # Получить ID заявки

#                     # Создаём оповещение
#                     alert = models.InventoryAlert(
#                         inventory_request_id=auto_request.id,
#                         alert_type="warning",
#                         event_type="auto_request_created",
#                         message=f"Автоматическая заявка на пополнение запаса: {item.name_rus} ({item.article}) - {quantity_to_order} шт."
#                     )
#                     db.add(alert)
                    
#                     created_requests.append({
#                         "requestId": auto_request.id,
#                         "itemId": item.id,
#                         "itemArticle": item.article,
#                         "quantity": quantity_to_order
#                     })
        
#         db.commit()
        
#         return jsonify({
#             "lowStockItems": low_stock_items,
#             "createdAutoRequests": created_requests,
#             "message": f"Found {len(low_stock_items)} items with low stock"
#         })
#     finally:
#         db.close()

# @app.route("/api/reports/check-zip/<int:report_id>", methods=["POST"])
# def check_zip_for_report(report_id):
#     """
#     Проверить ЗИП из used_zip отчета и создать автоматические заявки если недостаточно
#     """
#     db = SessionLocal()
#     try:
#         report = db.query(models.ReportRecord).filter(models.ReportRecord.id == report_id).first()
#         if not report:
#             return jsonify({"error": "Report not found"}), 404
        
#         if not report.used_zip or not report.used_zip.strip():
#             return jsonify({"message": "No ZIP specified"}), 200
        
#         # Парсим used_zip по разделителю ;
#         zip_items = [item.strip() for item in report.used_zip.split(';') if item.strip()]
#         created_requests = []
        
#         for zip_item in zip_items:
#             if ' (шт. - ' in zip_item and zip_item.endswith(')'):
#                 item_part = zip_item.rsplit(' (шт. - ', 1)[0]
#                 qty_part = zip_item.rsplit(' (шт. - ', 1)[1].rstrip(')')
#                 item_name = item_part.strip()
#                 quantity_to_order = int(qty_part.strip()) if qty_part.strip().isdigit() else 1
#             else:
#                 item_name = zip_item.strip()
#                 quantity_to_order = 1
            
#             item_name = item_name.strip()
            
#             # Ищем товар по артикулу или названию
#             item = db.query(models.InventoryItem).filter(
#                 (models.InventoryItem.article == item_name) | 
#                 (models.InventoryItem.name_rus == item_name) |
#                 (models.InventoryItem.name_eng == item_name)
#             ).first()
            
#             if not item:
#                 # Если товар не найден, пропускаем
#                 continue
            
#             # Рассчитываем доступное количество
#             active_requests = db.query(models.InventoryRequest).filter(
#                 models.InventoryRequest.inventory_item_id == item.id,
#                 models.InventoryRequest.status.in_(["новая", "в_процессе"])
#             ).all()
#             # Исключаем auto-заявки для этого отчета, чтобы не учитывать свои старые заявки дважды
#             requested_total = sum(req.requested_quantity for req in active_requests 
#                 if not (req.reason == "auto" and req.related_report_id == report_id))
#             available_count = item.current_count - item.reserved_count - requested_total

#             to_reserve = min(quantity_to_order, available_count)
#             item.reserved_count += to_reserve

#             # Если доступное недостаточно, создаём заявку на разницу
#             shortage = quantity_to_order - to_reserve

#             if shortage > 0:                
#                 auto_request = models.InventoryRequest(
#                     inventory_item_id=item.id,
#                     requested_quantity=shortage,
#                     reason="auto",
#                     status="новая",
#                     created_by="system",
#                     related_report_id=report_id
#                 )
#                 db.add(auto_request)
#                 db.flush()
                    
#                 # Создаём оповещение
#                 alert = models.InventoryAlert(
#                     inventory_request_id=auto_request.id,
#                     alert_type="warning",
#                     event_type="auto_request_created",
#                     message=f"Автоматическая заявка на ЗИП для ремонта: {item.name_rus} ({item.article}) - {shortage} шт. (Отчет #{report_id})"
#                 )
#                 db.add(alert)
                    
#                 created_requests.append({
#                     "requestId": auto_request.id,
#                     "itemId": item.id,
#                     "itemArticle": item.article,
#                     "quantity": shortage
#                 })
#         db.commit()
        
#         return jsonify({
#             "createdRequests": created_requests,
#             "message": f"Checked ZIP for report {report_id}"
#         })
#     finally:
#         db.close()


# @app.route("/api/reports/release-zip/<int:report_id>", methods=["POST"])
# def release_zip_for_report(report_id):
#     """
#     Снять резерв ЗИП для отчета при деактивации статуса
#     """
#     db = SessionLocal()
#     try:
#         report = db.query(models.ReportRecord).filter(models.ReportRecord.id == report_id).first()
#         if not report:
#             return jsonify({"error": "Report not found"}), 404
        
#         if not report.used_zip or not report.used_zip.strip():
#             return jsonify({"message": "No ZIP specified"}), 200
        
#         # Парсим used_zip
#         zip_items = [item.strip() for item in report.used_zip.split(';') if item.strip()]
        
#         for zip_item in zip_items:
#             if ' (шт. - ' in zip_item and zip_item.endswith(')'):
#                 item_part = zip_item.rsplit(' (шт. - ', 1)[0]
#                 qty_part = zip_item.rsplit(' (шт. - ', 1)[1].rstrip(')')
#                 item_name = item_part.strip()
#                 quantity_to_release = int(qty_part.strip()) if qty_part.strip().isdigit() else 1
#             else:
#                 item_name = zip_item.strip()
#                 quantity_to_release = 1
            
#             item_name = item_name.strip()
            
#             item = db.query(models.InventoryItem).filter(
#                 (models.InventoryItem.article == item_name) | 
#                 (models.InventoryItem.name_rus == item_name) |
#                 (models.InventoryItem.name_eng == item_name)
#             ).first()
            
#             if item and item.reserved_count >= quantity_to_release:
#                 item.reserved_count -= quantity_to_release
        
#         db.commit()
#         return jsonify({"message": f"Released ZIP for report {report_id}"})
#     finally:
#         db.close()

# ============================================================================================================================