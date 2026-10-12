from flask import request, jsonify
from . import sapr_bp
from src.sapr.services.animation_step_service import animation_step_service
from src.sapr.dto import (
    AnimationStepCreateRequestDTO,
    AnimationStepUpdateRequestDTO,
    AnimationStepResponseDTO,
)


@sapr_bp.route('/projects/<int:project_id>/animation-steps', methods=['GET'])
def get_animation_steps_by_project(project_id):
    steps = animation_step_service.get_by_project_id(project_id)

    schema = AnimationStepResponseDTO(many=True)
    return jsonify(schema.dump(steps)), 200

@sapr_bp.route('/projects/<int:project_id>/animation-steps', methods=['POST'])
def create_animation_step(project_id: int):
    data = request.get_json(silent=True) or {}
    data['project_id'] = project_id
    schema = AnimationStepCreateRequestDTO()
    dto = schema.load(data)

    step = animation_step_service.create_step(
        project_id=dto['project_id'],
        name=dto['name'],
        model_id=dto.get('model_id'),
        duration=dto.get('duration', 1.0),
        order=dto.get('order', 0),
        is_active=dto.get('is_active', True),
        camera_position=dto.get('camera_position', {"x": 0.0, "y": 0.0, "z": 0.0}),
        camera_target=dto.get('camera_target', {"x": 0.0, "y": 0.0, "z": 0.0}),
        animation_ids=dto.get('animation_ids', [])
    )
    return jsonify(AnimationStepResponseDTO().dump(step)), 201

@sapr_bp.route('/animation-steps/<int:step_id>', methods=['PUT'])
def update_animation_step(step_id: int):
    data = request.get_json(silent=True) or {}
    schema = AnimationStepUpdateRequestDTO()
    dto = schema.load(data)

    step = animation_step_service.update_step(
        step_id=step_id,
        name=dto.get('name'),
        model_id=dto.get('model_id'),
        duration=dto.get('duration'),
        order=dto.get('order'),
        is_active=dto.get('is_active'),
        camera_position=dto.get('camera_position'),
        camera_target=dto.get('camera_target'),
        animation_ids=dto.get('animation_ids')
    )
    return jsonify(AnimationStepResponseDTO().dump(step)), 200

@sapr_bp.route('/animation-steps/<int:step_id>', methods=['DELETE'])
def delete_animation_step(step_id: int):
    animation_step_service.delete_step(step_id)
    return jsonify({'message': 'Шаг анимации удален'}), 200

@sapr_bp.route('/projects/<int:project_id>/animation-steps', methods=['DELETE'])
def delete_all_animation_steps(project_id: int):
    # Удалить все шаги анимации проекта
    animation_step_service.delete_all_by_project_id(project_id)
    return jsonify({'message': 'Все шаги анимации проекта удалены'}), 200

@sapr_bp.route('/projects/<int:project_id>/animation-steps/bulk', methods=['POST'])
def create_animation_steps_bulk(project_id: int):
    # Массовое создание шагов анимации
    data = request.get_json(silent=True) or {}
    
    steps_data = data if isinstance(data, list) else data.get('steps', [])
    
    if not steps_data:
        return jsonify({'message': 'Список шагов пуст', 'data': []}), 200

    steps = animation_step_service.create_steps_bulk(project_id, steps_data)
    
    schema = AnimationStepResponseDTO(many=True)
    return jsonify(schema.dump(steps)), 201

@sapr_bp.route('/animation-steps/search', methods=['GET'])
def search_animation_steps():
    project_id = request.args.get('project_id', type=int)
    query = request.args.get('q', '', type=str).strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    if not project_id:
        return jsonify({'error': 'Параметр project_id обязателен'}), 400

    if not query:
        return jsonify({'error': 'Параметр поиска "q" обязателен'}), 400

    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 50

    result = animation_step_service.search_animation_steps(project_id, query, page, per_page)

    return jsonify(result), 200