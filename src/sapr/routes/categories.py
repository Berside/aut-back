from flask import request, jsonify
from . import sapr_bp
from src.sapr.services.category_service import category_service
from src.sapr.dto import (
    CategoryCreateRequestDTO,
    CategoryUpdateRequestDTO,
)


@sapr_bp.route('/parts/categories', methods=['GET'])
def get_categories_tree():
    # Получить дерево категорий
    parent_id = request.args.get('parent_id', type=int)
    tree = category_service.get_tree(parent_id)
    return jsonify({'categories': tree}), 200


@sapr_bp.route('/parts/categories', methods=['POST'])
def create_category():
    # Создать категорию
    data = request.get_json(silent=True) or {}
    schema = CategoryCreateRequestDTO()
    dto = schema.load(data)
    
    category = category_service.create_category(
        name=dto['name'],
        parent_id=dto.get('parent_id'),
        sort_order=dto.get('sort_order', 0)
    )
    return jsonify({'message': 'Категория создана', 'id': category.id}), 201


@sapr_bp.route('/parts/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id: int):
    # Обновить категорию
    data = request.get_json(silent=True) or {}
    schema = CategoryUpdateRequestDTO()
    dto = schema.load(data)
    
    category = category_service.update_category(
        category_id=category_id,
        name=dto.get('name'),
        parent_id=dto.get('parent_id'),
        sort_order=dto.get('sort_order')
    )
    return jsonify({'message': 'Категория обновлена', 'id': category.id}), 200


@sapr_bp.route('/parts/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id: int):
    # Удалить категорию
    category_service.delete_category(category_id)
    return jsonify({'message': 'Категория удалена'}), 200