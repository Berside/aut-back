from flask import request, jsonify
from . import sapr_bp
from src.sapr.services.item_service import item_service
from src.sapr.dto import(
    ItemCreateRequestDTO, 
    ItemResponseDTO, 
    ItemUpdateRequestDTO,
    BomTreeItemDTO,
    RepairToolItemDTO,
    ItemSearchResponseDTO)


@sapr_bp.route('/items', methods=['GET'])
def get_items():
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=20, type=int)

    result = item_service.get_all_items(page=page, per_page=per_page)
    schema = ItemResponseDTO(many=True)

    return jsonify({
        'items': schema.dump(result['items']),
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages']
    }), 200


@sapr_bp.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id: int):
    item = item_service.get_item(item_id)
    return jsonify(ItemResponseDTO().dump(item)), 200


@sapr_bp.route('/items', methods=['POST'])
def create_item():
    data = request.get_json()
    schema = ItemCreateRequestDTO()
    dto = schema.load(data)

    item = item_service.create_item(
        article=dto['article'],
        name=dto['name'],
        standard=dto.get('standard'),
        unit=dto.get('unit', 'шт'),
        description=dto.get('description'),
        note=dto.get('note'),
        photo_path=dto.get('photo_path'),
        stock_quantity=dto.get('stock_quantity', 0)
    )

    return jsonify(ItemResponseDTO().dump(item)), 201


@sapr_bp.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id: int):
    data = request.get_json()
    schema = ItemUpdateRequestDTO()
    dto = schema.load(data)

    item = item_service.update_item(
        item_id=item_id,
        article=dto.get('article'),
        name=dto.get('name'),
        standard=dto.get('standard'),
        unit=dto.get('unit'),
        description=dto.get('description'),
        note=dto.get('note'),
        photo_path=dto.get('photo_path'),
        stock_quantity=dto.get('stock_quantity')
    )

    return jsonify(ItemResponseDTO().dump(item)), 200


@sapr_bp.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id: int):
    item_service.delete_item(item_id)
    return jsonify({'message': 'Изделие удалено'}), 200

@sapr_bp.route('/items/<int:item_id>/bom-tree', methods=['GET'])
def get_item_bom_tree(item_id: int):
    tree_data = item_service.get_bom_tree(item_id)

    return jsonify(BomTreeItemDTO().dump(tree_data)), 200

@sapr_bp.route('/items/<int:item_id>/repair-tools', methods=['GET'])
def get_item_repair_tools(item_id: int):
    return jsonify(RepairToolItemDTO(many=True).dump(item_service.get_repair_tools_for_item(item_id))), 200

@sapr_bp.route('/items/search', methods=['GET'])
def search_items():
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

    result = item_service.search_items(query, project_id, page, per_page)

    return jsonify({
        'items': ItemSearchResponseDTO(many=True).dump(result['items']),
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page']
    }), 200