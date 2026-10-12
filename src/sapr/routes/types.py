from flask import request, jsonify
from . import sapr_bp
from src.sapr.services.type_service import type_service
from src.sapr.dto import (
    TypeCreateRequestDTO,
    TypeUpdateRequestDTO,
    TypeResponseDTO,
)


@sapr_bp.route('/parts/types', methods=['GET'])
def get_types():
    # Получить список типов 
    category_id = request.args.get('category_id', type=int)
    types = type_service.get_types(category_id)
    
    schema = TypeResponseDTO(many=True)
    return jsonify({
        'types': schema.dump(types)
    }), 200


@sapr_bp.route('/parts/types', methods=['POST'])
def create_type():
    # Создать тип
    data = request.get_json(silent=True) or {}
    schema = TypeCreateRequestDTO()
    dto = schema.load(data)
    
    part_type = type_service.create_type(
        name=dto['name'],
        category_id=dto.get('category_id')
    )
    return jsonify({'message': 'Тип создан', 'id': part_type.id}), 201


@sapr_bp.route('/parts/types/<int:type_id>', methods=['PUT'])
def update_type(type_id: int):
    # Обновить тип
    data = request.get_json(silent=True) or {}
    schema = TypeUpdateRequestDTO()
    dto = schema.load(data)
    
    part_type = type_service.update_type(
        type_id=type_id,
        name=dto.get('name'),
        category_id=dto.get('category_id')
    )
    return jsonify({'message': 'Тип обновлен', 'id': part_type.id}), 200


@sapr_bp.route('/parts/types/<int:type_id>', methods=['DELETE'])
def delete_type(type_id: int):
    # Удалить тип
    type_service.delete_type(type_id)
    return jsonify({'message': 'Тип удален'}), 200