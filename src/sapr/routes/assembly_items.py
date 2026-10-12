from flask import request, jsonify
from . import sapr_bp
from src.sapr.services.assembly_service import assembly_service
from src.sapr.dto import (
    AssemblyItemCreateRequestDTO,
    AssemblyItemUpdateRequestDTO,
    AssemblyItemResponseDTO,
    AssemblyItemLinkRequestDTO,
    AssemblyItemLinkResponseDTO,
    ItemResponseDTO,
    AssemblyTreeItemDTO
)
from src.orm.orm_sapr import Project
from src.sapr.exceptions import ProjectNotFoundError


@sapr_bp.route('/projects/<int:project_id>/assembly-items', methods=['POST'])
def create_assembly_item(project_id: int):
    data = request.get_json(silent=True) or {}
    data['project_id'] = project_id
    schema = AssemblyItemCreateRequestDTO()
    dto = schema.load(data)

    item = assembly_service.create_item(
        project_id=dto['project_id'],
        name=dto['name'],
        model_id=dto.get('model_id'),
        part_id=dto.get('part_id'),
        parent_id=dto.get('parent_id'),
        order=dto.get('order', 0),
    )
    return jsonify(AssemblyItemResponseDTO().dump(item)), 201


@sapr_bp.route('/projects/<int:project_id>/assembly', methods=['GET'])
def get_project_assembly(project_id: int):
    items = assembly_service.get_project_assembly(project_id)
    
    schema = AssemblyItemResponseDTO(many=True)
    
    return jsonify(schema.dump(items)), 200


@sapr_bp.route('/assembly-items/<int:item_id>', methods=['PUT'])
def update_assembly_item(item_id: int):
    data = request.get_json(silent=True) or {}
    schema = AssemblyItemUpdateRequestDTO()
    dto = schema.load(data)

    item = assembly_service.update_item(
        item_id=item_id,
        name=dto.get('name'),
        model_id=dto.get('model_id'),
        part_id=dto.get('part_id'),
        parent_id=dto.get('parent_id'),
        order=dto.get('order')
    )
    return jsonify(AssemblyItemResponseDTO().dump(item)), 200


@sapr_bp.route('/assembly-items/<int:item_id>', methods=['DELETE'])
def delete_assembly_item(item_id: int):
    assembly_service.delete_item(item_id)
    return jsonify({'message': 'Элемент сборки удалён'}), 200

@sapr_bp.route('/assembly/import-part', methods=['POST'])
def import_part_to_assembly():
    # Импортировать деталь в сборку
    data = request.get_json(silent=True) or {}
    
    assembly_item, link = assembly_service.import_part_to_assembly(
        project_id=data['project_id'],
        part_id=data['part_id'],
        parent_id=data.get('parent_id'),
        quantity=data.get('quantity', 1),
        position=data.get('position', {'x': 0, 'y': 0, 'z': 0}),
        rotation=data.get('rotation', {'x': 0, 'y': 0, 'z': 0}),
    )
    
    return jsonify({
        'success': True,
        'assembly_item': {
            'id': assembly_item.id,
            'project_id': assembly_item.project_id,
            'name': assembly_item.name,
            'model_id': assembly_item.model_id,
            'part_id': assembly_item.part_id,
            'parent_id': assembly_item.parent_id,
            'order': assembly_item.order,
        },
        'link': {
            'id': link.id,
            'assembly_item_id': link.assembly_item_id,
            'part_id': link.part_id,
            'quantity': link.quantity,
            'position': link.position,
            'rotation': link.rotation,
            'created_at': link.created_at.isoformat() if link.created_at else None,
        }
    }), 201

@sapr_bp.route('/assembly-items/<int:assembly_item_id>/link-item', methods=['POST'])
def link_item_to_assembly(assembly_item_id: int):
    data = request.get_json()
    if not data: 
        return jsonify({'error': 'Тело запроса обязательно'}), 400

    schema = AssemblyItemLinkRequestDTO()
    dto = schema.load(data)

    assembly_item = assembly_service.link_item_to_assembly(
        assembly_item_id=assembly_item_id,
        item_id=dto['item_id']
    )

    response_data = {
            'id': assembly_item.id,
            'name': assembly_item.name,
            'item_id': assembly_item.item_id,
            'item': ItemResponseDTO().dump(assembly_item.item) if assembly_item.item else None


        }
        
    return jsonify(AssemblyItemLinkResponseDTO().dump(response_data)), 200
        
@sapr_bp.route('/assembly-items/<int:assembly_item_id>/link-item', methods=['DELETE'])
def unlink_item_from_assembly(assembly_item_id: int):
    assembly_item = assembly_service.unlink_item_from_assembly(assembly_item_id)
    
    response_data = {
        'id': assembly_item.id,
        'name': assembly_item.name,
        'item_id': None,
        'item': None
    }
    
    return jsonify(AssemblyItemLinkResponseDTO().dump(response_data)), 200

@sapr_bp.route('/assembly-items/<int:assembly_item_id>/item', methods=['GET'])
def get_linked_item(assembly_item_id: int):
    item = assembly_service.get_linked_item_for_assembly(assembly_item_id)

    if item:
        return jsonify(ItemResponseDTO().dump(item)), 200 
    
    else:
        return jsonify(None), 200

@sapr_bp.route('/projects/<int:project_id>/assembly-tree', methods=['GET'])
def get_project_assembly_item_tree(project_id: int):
    project = Project.query.get(project_id)
    if not project:
        raise ProjectNotFoundError()

    tree = assembly_service.get_assembly_tree(project_id)

    return jsonify(AssemblyTreeItemDTO(many=True).dump(tree)), 200

@sapr_bp.route('/assembly-items/search', methods=['GET'])
def search_assembly_items():
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

    result = assembly_service.search_assembly_items(project_id, query, page, per_page)
    
    return jsonify(result), 200

