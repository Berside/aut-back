from flask import request, jsonify, send_file
from . import sapr_bp
from src.sapr.services.part_service import part_service
from src.sapr.dto import (
    PartCreateRequestDTO,
    PartUpdateRequestDTO,
    PartResponseDTO,
    ItemResponseDTO
)


@sapr_bp.route('/parts', methods=['GET'])
def get_parts():
    # Получить детали
    part_id = request.args.get('id', type=int)
    search_query = request.args.get('q', type=str)
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    category_id = request.args.get('category_id', type=int)
    type_id = request.args.get('type_id', type=int)
    is_standard = request.args.get('is_standard', type=lambda x: x.lower() == 'true')
    search_filter = request.args.get('search', type=str)
    project_id = request.args.get('project_id', type=int)
    
    # Получить одну деталь по ID
    if part_id:
        part = part_service.get_part(part_id, project_id)
        return jsonify({
            'data': part_service._serialize_part(part, full=True),
            'total': 1
        }), 200
    
    # Список с фильтрацией
    parts, total = part_service.get_parts_list(
        page=page,
        limit=limit,
        category_id=category_id,
        type_id=type_id,
        is_standard=is_standard,
        search=search_filter,
        project_id=project_id
    )
    
    return jsonify({
        'data': [part_service._serialize_part(p, full=True) for p in parts],
        'total': total,
        'page': page,
        'limit': limit
    }), 200

@sapr_bp.route('/parts/search', methods=['GET'])
def search_parts():
    query = request.args.get('q', '', type=str).strip()
    category_id = request.args.get('category_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    if not query:
        return jsonify({'error': 'Параметр поиска q обязателен'}), 400

    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 50

    result = part_service.search_parts(query, category_id, page, per_page)

    return jsonify(result), 200
    

@sapr_bp.route('/parts/<int:part_id>/item', methods=['GET'])
def get_part_item(part_id: int):
    item = part_service.get_part_item(part_id)
    return jsonify(ItemResponseDTO().dump(item)), 200


@sapr_bp.route('/parts', methods=['POST'])
def create_part():
    # Создать деталь
    data = request.get_json(silent=True) or {}
    schema = PartCreateRequestDTO()
    dto = schema.load(data)
    
    part = part_service.create_part(
        name=dto['name'],
        project_id=dto.get('project_id'),
        part_number=dto.get('part_number'),
        description=dto.get('description'),
        category_id=dto.get('category_id'),
        type_id=dto.get('type_id'),
        parameters=dto.get('parameters', {}),
        model_id=dto.get('model_id'),
        technical_name=dto.get('technical_name'),
        preview_image=dto.get('preview_image'),
        unit=dto.get('unit', 'шт'),
        is_standard=dto.get('is_standard', True),
        is_active=dto.get('is_active', True),
        created_by=dto.get('created_by'),
        quantity=dto.get('quantity', 1),
        custom_parameters=dto.get('custom_parameters', {}),
    )
    
    return jsonify({'message': 'Деталь создана', 'id': part.id}), 201


@sapr_bp.route('/parts/<int:part_id>', methods=['PUT'])
def update_part(part_id: int):
    # Обновить деталь
    data = request.get_json(silent=True) or {}
    schema = PartUpdateRequestDTO()
    dto = schema.load(data)
    
    part = part_service.update_part(
        part_id=part_id,
        name=dto.get('name'),
        part_number=dto.get('part_number'),
        description=dto.get('description'),
        category_id=dto.get('category_id'),
        type_id=dto.get('type_id'),
        parameters=dto.get('parameters'),
        model_id=dto.get('model_id'),
        technical_name=dto.get('technical_name'),
        preview_image=dto.get('preview_image'),
        unit=dto.get('unit'),
        is_standard=dto.get('is_standard'),
        is_active=dto.get('is_active')
    )
    return jsonify({'message': 'Деталь обновлена', 'id': part.id}), 200


@sapr_bp.route('/parts/<int:part_id>', methods=['DELETE'])
def delete_part(part_id: int):
    # Удалить деталь
    part_service.delete_part(part_id)
    return jsonify({'message': 'Деталь удалена'}), 200


@sapr_bp.route('/parts/<int:part_id>/download', methods=['GET'])
def download_part_file(part_id: int):
    # Скачать файл детали
    filepath, mimetype = part_service.download_file(part_id)
    return send_file(filepath, as_attachment=False, mimetype=mimetype)


@sapr_bp.route('/parts/batch', methods=['POST'])
def create_parts_batch():
    # Массовое создание деталей
    data = request.get_json(silent=True) or {}
    
    if not data or 'parts' not in data or not isinstance(data['parts'], list):
        return jsonify({'error': 'Поле parts должно быть массивом'}), 400
    
    created_parts, errors = part_service.batch_create(data['parts'])
    
    return jsonify({
        'created': [{
            'id': p.id,
            'name': p.name,
            'part_number': p.part_number,
        } for p in created_parts],
        'errors': errors,
        'total_created': len(created_parts),
        'total_errors': len(errors)
    }), 201 if created_parts else 400


@sapr_bp.route('/parts/batch', methods=['DELETE'])
def delete_parts_batch():
    # Массовое удаление деталей
    data = request.get_json(silent=True) or {}
    
    if not data or 'ids' not in data or not isinstance(data['ids'], list):
        return jsonify({'error': 'Поле ids должно быть массивом'}), 400
    
    deleted_count, errors = part_service.batch_delete(data['ids'])
    
    return jsonify({
        'deleted_count': deleted_count,
        'errors': errors
    }), 200