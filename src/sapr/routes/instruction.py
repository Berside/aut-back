#!/usr/bin/python3
# -*- coding: utf-8 -*-
from flask import request, jsonify
from src.sapr.routes import sapr_bp
from src.sapr.services.model_service import model_service
from src.sapr.dto import (
    InstructionCreateRequestDTO, 
    InstructionResponseDTO, 
    ModelResponseDTO, 
    InstructionListItemDTO, 
    InstructionUpdateRequestDTO)
from src.sapr.services.instruction_service import instruction_service


@sapr_bp.route('/instructions', methods=['POST'])
def create_instruction():
    data = request.get_json(silent=True) or {}
    schema = InstructionCreateRequestDTO()
    dto = schema.load(data)

    instruction = instruction_service.create_instruction(
        dmc=dto['dmc'],
        project_id=dto['project_id'],
        title=dto['title'],
        content=dto.get('content'),
        part_id=dto.get('part_id'),
        animation_step_id=dto.get('animation_step_id'),
    )

    return jsonify(InstructionResponseDTO().dump(instruction)), 201

@sapr_bp.route('/instructions/<int:instruction_id>', methods=['PUT'])
def update_instruction(instruction_id: int):
    data = request.get_json(silent=True) or  {}

    schema = InstructionUpdateRequestDTO()
    dto = schema.load(data)

    instruction = instruction_service.update_instruction(
        instruction_id=instruction_id,
        dmc=dto['dmc'],
        project_id=dto['project_id'],
        title=dto['title'],
        content=dto.get('content'),
        part_id=dto.get('part_id'),
        animation_step_id=dto.get('animation_step_id'),
    )

    return jsonify(InstructionResponseDTO().dump(instruction)), 200


@sapr_bp.route('/instructions/<int:instruction_id>', methods=['GET'])
def get_instruction(instruction_id):
    instruction = instruction_service.get_by_id(instruction_id)
    return jsonify(InstructionResponseDTO().dump(instruction)), 200


@sapr_bp.route('/instructions/dmc/<string:dmc>', methods=['GET'])
def get_current_by_dmc(dmc):
    instruction = instruction_service.get_current_by_dmc(dmc)
    
    return jsonify(InstructionResponseDTO().dump(instruction)), 200


@sapr_bp.route('/instructions/<int:instruction_id>', methods=['DELETE'])
def delete_instruction(instruction_id):
    instruction_service.delete(instruction_id)
    return jsonify({'message': 'Инструкция удалена'}), 200


@sapr_bp.route('/instructions', methods=['GET'])
def get_instructions_list():
    project_id = request.args.get('project_id', type=int)
    part_id = request.args.get('part_id', type=int)

    instructions = instruction_service.get_instructions_list(project_id, part_id)

    schema = InstructionListItemDTO(many=True)
    return jsonify(schema.dump(instructions)), 200


@sapr_bp.route('/instructions/dmc/<string:dmc>/versions', methods=['GET'])
def get_instruction_versions(dmc):
    versions = instruction_service.get_all_versions_by_dmc(dmc)

    schema = InstructionResponseDTO(many=True)
    return jsonify(schema.dump(versions)), 200

@sapr_bp.route('/instructions/<int:instruction_id>/file', methods=['GET'])
def get_instruction_file(instruction_id: int):
    instruction_data = instruction_service.get_instruction_file(instruction_id)
    return jsonify(instruction_data), 200


@sapr_bp.route('/instructions/search', methods=['GET'])
def search_instructions():
    query = request.args.get('q', '', type=str).strip()
    project_id = request.args.get('project_id', type=int)

    if not query:
        return jsonify({'error': 'Параметр поиска "q" обязателен'}), 400

    instructions = instruction_service.search_instructions(query, project_id)

    schema = InstructionResponseDTO(many=True)
    return jsonify(schema.dump(instructions)), 200
