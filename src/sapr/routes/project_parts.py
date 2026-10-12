from flask import request, jsonify
from . import sapr_bp
from src.sapr.services.project_part_service import project_part_service
from src.sapr.dto import ProjectPartCreateRequestDTO, ProjectPartWithStockCheckResponseDTO

@sapr_bp.route('/projects/<int:project_id>/parts/batch', methods=['POST'])
def add_parts_to_project_batch(project_id: int):
    # Массовое добавление деталей в проект
    data = request.get_json(silent=True) or {}
    
    if not data or 'parts' not in data or not isinstance(data['parts'], list):
        return jsonify({'error': 'Поле parts должно быть массивом'}), 400
    
    added_parts, errors = project_part_service.add_to_project_batch(project_id, data['parts'])
    
    return jsonify({
        'added': [{
            'id': pp.id,
            'part_id': pp.part_id,
            'quantity': pp.quantity,
        } for pp in added_parts],
        'errors': errors,
        'total_added': len(added_parts),
        'total_errors': len(errors)
    }), 201 if added_parts else 400


@sapr_bp.route('/projects/<int:project_id>/parts/batch', methods=['DELETE'])
def remove_parts_from_project_batch(project_id: int):
    # Массовое удаление деталей из проекта
    data = request.get_json(silent=True) or {}
    
    if not data or 'part_ids' not in data or not isinstance(data['part_ids'], list):
        return jsonify({'error': 'Поле part_ids должно быть массивом'}), 400
    
    deleted_count, errors = project_part_service.remove_from_project_batch(project_id, data['part_ids'])
    
    return jsonify({
        'deleted_count': deleted_count,
        'errors': errors
    }), 200

@sapr_bp.route('/projects/<int:project_id>/parts', methods=['POST'])
def add_part_to_project(project_id: int):
    data = request.get_json(silent=True) or {}
    data['project_id'] = project_id

    schema = ProjectPartCreateRequestDTO()
    dto = schema.load(data)

    project_part, remaining_stock, warning = project_part_service.add_part_to_project_with_stock_check(
        project_id=dto['project_id'],
        part_id=dto['part_id'],
        quantity=dto.get('quantity', 1),
        custom_parameters=dto.get('custom_parameters'),
        added_by=dto.get('added_by')
    )

    response_data = {
        'success': True,
        'message': 'Деталь добавлена в проект',
        'project_part': project_part,
        'remaining_stock': remaining_stock,
        'warning': warning
    }

    return jsonify(ProjectPartWithStockCheckResponseDTO().dump(response_data)), 201