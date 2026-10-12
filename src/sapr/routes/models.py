from flask import request, jsonify, current_app, send_file
from . import sapr_bp
from src.sapr.decorators import log_action
from src.sapr.services.model_service import model_service
from src.sapr.dto import ModelCreateRequestDTO, ModelResponseDTO, ItemResponseDTO
import os


@sapr_bp.route('/models/<int:model_id>', methods=['GET'])
@log_action(user_id=1)  
def get_model(model_id: int):
    model = model_service.get_model(model_id)
    return jsonify(ModelResponseDTO().dump(model)), 200

@sapr_bp.route('/projects/<int:project_id>/models', methods=['GET'])
def get_models_by_project(project_id: int):
    models = model_service.get_models_by_project(project_id)
    return jsonify(ModelResponseDTO(many=True).dump(models)), 200
    

@sapr_bp.route('/projects/<int:project_id>/models', methods=['POST'])
def add_model_to_project(project_id: int):
    if 'file' in request.files:
        file = request.files['file']
        name = request.form.get('name', file.filename)
        is_primary = request.form.get('is_primary', 'false').lower() == 'true'
        technical_name = request.form.get('technical_name')
    else:
        data = request.get_json(silent=True) or {}
        schema = ModelCreateRequestDTO()
        dto = schema.load(data)
        file = None
        name = dto['name']
        is_primary = dto.get('is_primary', False)
        technical_name = dto.get('technical_name')

    model = model_service.add_model_to_project(
        project_id=project_id,
        name=name,
        file=file,
        is_primary=is_primary,
        technical_name=technical_name
    )
    return jsonify(ModelResponseDTO().dump(model)), 201

@sapr_bp.route('/models/<int:model_id>', methods=['PUT'])
def update_model(model_id: int):
    if 'file' in request.files:
        file = request.files['file']
        name = request.form.get('name')
        is_primary_str = request.form.get('is_primary')
        is_primary = is_primary_str.lower() == 'true' if is_primary_str else None
    else:
        data = request.get_json(silent=True) or {}
        schema = ModelCreateRequestDTO()
        dto = schema.load(data)
        file = None
        name = dto['name']
        is_primary = dto.get('is_primary', False)

    model = model_service.update_model(
        model_id=model_id,
        name=name,
        file=file,
        is_primary=is_primary,
    )
    return jsonify(ModelResponseDTO().dump(model)), 200


@sapr_bp.route('/models/<int:model_id>', methods=['DELETE'])
def delete_model(model_id: int):
    result = model_service.delete_model(model_id)
    return jsonify(result), 200

@sapr_bp.route('/models/<int:model_id>/download', methods=['GET'])
def download_model(model_id: int):
    file_path, filename = model_service.download_model(model_id)
    return send_file(file_path, as_attachment=True, download_name=filename)

@sapr_bp.route('/models/<int:model_id>/items', methods=['GET'])
def get_model_items(model_id: int):
    items = model_service.get_items_by_model_id(model_id)
    return jsonify(ItemResponseDTO(many=True).dump(items)), 200

@sapr_bp.route('/models/search', methods=['GET'])
def search_models():
    query = request.args.get('q', '', type=str).strip()
    project_id = request.args.get('project_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    if not query:
        return jsonify({'error': 'Параметр поиска "q" обязателен'}), 400

    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 50

    result = model_service.search_models(query, project_id, page, per_page)

    schema = ModelResponseDTO(many=True)
    
    return jsonify({
        'models': schema.dump(result['models']),
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page']
    }), 200

