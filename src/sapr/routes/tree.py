from flask import request, jsonify
from src.sapr.routes import sapr_bp
from src.sapr.services.tree_service import tree_service

from src.sapr.dto import (
    SaprTreeCreateRequestDTO,
    SaprTreeUpdateRequestDTO,
    SaprTreeNodeDTO
)


@sapr_bp.route('/projects/<int:project_id>/tree', methods=['GET'])
def get_tree(project_id: int):
    tree = tree_service.get_tree(project_id)
    schema = SaprTreeNodeDTO(many=True)
    return jsonify(schema.dump(tree)), 200


@sapr_bp.route('/tree', methods=['POST'])  
def create_tree_item():
    data = request.get_json()
    schema = SaprTreeCreateRequestDTO()
    dto = schema.load(data)

    item = tree_service.create_item(
        name=dto['name'],
        item_type=dto['item_type'],
        project_id=dto['project_id'],
        parent_link=dto.get('parent_link'),
        instruction_id=dto.get('instruction_id'),
        model_id=dto.get('model_id'),
        position=dto.get('position')
    )

    return jsonify({'id': item.id, 'message': 'Элемент создан'}), 201


@sapr_bp.route('/tree/<int:item_id>', methods=['PUT'])
def update_tree_item(item_id: int):
    data = request.get_json()
    schema = SaprTreeUpdateRequestDTO()
    dto = schema.load(data)

    item = tree_service.update_item(
        item_id=item_id,
        name=dto.get('name'),
        position=dto.get('position')
    )

    return jsonify({'id': item.id, 'message': 'Элемент обновлен'}), 200


@sapr_bp.route('/tree/<int:item_id>', methods=['DELETE'])
def delete_tree_item(item_id: int):
    cascade = request.args.get('cascade', 'false').lower() == 'true'
    tree_service.delete_item(item_id, cascade=cascade)
    return jsonify({'message': 'Элемент удален'}), 200


@sapr_bp.route('/tree/<int:item_id>/move', methods=['POST'])
def move_tree_item(item_id: int):
    data = request.get_json()
    new_parent_link = data.get('new_parent_link')
    new_position = data.get('new_position')

    item = tree_service.move_item(item_id, new_parent_link, new_position)
    return jsonify({'id': item.id, 'message': 'Элемент перемещен'}), 200