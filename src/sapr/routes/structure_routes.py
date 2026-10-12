from flask import request, jsonify
from . import sapr_bp
from src.sapr.services.structure_service import structure_service
from src.sapr.dto import (
    ModelStructureNodeCreateRequestDTO,
    ModelStructureNodeUpdateRequestDTO,
    ModelStructureNodeResponseDTO,
    ModelStructureNodeTreeDTO
)


@sapr_bp.route('/model-structure/tree/<int:model_id>', methods=['GET'])
def get_structure_tree(model_id: int):
    tree = structure_service.get_tree(model_id)
    schema = ModelStructureNodeTreeDTO(many=True)
    return jsonify(schema.dump(tree)), 200


@sapr_bp.route('/model-structure/<string:node_id>', methods=['GET'])  
def get_structure_node(node_id: str):
    node = structure_service.get_node(node_id)
    return jsonify(ModelStructureNodeResponseDTO().dump(node)), 200


@sapr_bp.route('/model-structure', methods=['POST'])
def create_structure_node():
    data = request.get_json()
    schema = ModelStructureNodeCreateRequestDTO()
    dto = schema.load(data)

    node = structure_service.create_node(
        name=dto['name'],
        code=dto['code'],
        parent_id=dto.get('parent_id'),
        description=dto.get('description'),
        model_id=dto.get('model_id'),
        part_id=dto.get('part_id'),
        position=dto.get('position', 0)
    )

    return jsonify(ModelStructureNodeResponseDTO().dump(node)), 201


@sapr_bp.route('/model-structure/<string:node_id>', methods=['PUT'])  
def update_structure_node(node_id: str):
    data = request.get_json()
    schema = ModelStructureNodeUpdateRequestDTO()
    dto = schema.load(data)

    node = structure_service.update_node(
        node_id=node_id,
        name=dto.get('name'),
        code=dto.get('code'),
        description=dto.get('description'),
        parent_id=dto.get('parent_id'),
        model_id=dto.get('model_id'),
        part_id=dto.get('part_id'),
        position=dto.get('position')
    )

    return jsonify(ModelStructureNodeResponseDTO().dump(node)), 200


@sapr_bp.route('/model-structure/<string:node_id>', methods=['DELETE'])  
def delete_structure_node(node_id: str):
    cascade = request.args.get('cascade', 'false').lower() == 'true'
    structure_service.delete_node(node_id, cascade=cascade)
    return jsonify({'message': 'Узел структуры удален'}), 200