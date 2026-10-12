from flask import request, jsonify
from . import sapr_bp

from src.sapr.services.project_service import project_service
from src.sapr.dto import (
    ProjectCreateRequestDTO, 
    ProjectResponseDTO,
    InstructionListItemDTO
)
from src.sapr.exceptions import ProjectAlreadyExistsError, ProjectNotFoundError
from src.sapr.services.project_service import project_service
from src.sapr.services.instruction_service import instruction_service

@sapr_bp.route('/projects/', methods=['GET'])
def get_projects_list():
    projects = project_service.get_all_projects()
    schema = ProjectResponseDTO(many=True)
    return jsonify(schema.dump(projects)), 200


@sapr_bp.route('/projects/<int:project_id>', methods=['GET'])
def get_project(project_id: int):
    project = project_service.get_project(project_id)
    return jsonify(ProjectResponseDTO().dump(project)), 200

@sapr_bp.route('/projects/<int:project_id>/instructions', methods=['GET'])
def get_project_instructions(project_id: int):
    instructions = project_service.get_project_instructions(project_id)

    return jsonify(InstructionListItemDTO(many=True).dump(instructions)), 200


@sapr_bp.route('/projects/', methods=['POST'])
def create_or_update_project():
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form.to_dict()
        file = request.files.get('primary_model')
    else:
        data = request.get_json(silent=True) or {}
        file = None

   
    project_id = data.get('id')
    
    if project_id:
        try:
            updated_project = project_service.update_project(
                project_id=int(project_id),
                name=data.get('name'),
                description=data.get('description')
            )
            return jsonify(ProjectResponseDTO().dump(updated_project)), 200
        except ProjectAlreadyExistsError as e:
            return jsonify({'error': str(e)}), 409
        except ProjectNotFoundError:
            return jsonify({'error': 'Проект не найден'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Иначе — создание нового проекта
    schema = ProjectCreateRequestDTO()
    dto = schema.load(data)

    new_project = project_service.create_project(
        name=dto['name'],
        description=dto.get('description', ''),
        primary_model_file=file
    )

    return jsonify(ProjectResponseDTO().dump(new_project)), 201


@sapr_bp.route('/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id: int):
    data = request.get_json(silent=True) or {}
    
    try:
        updated_project = project_service.update_project(
            project_id=project_id,
            name=data.get('name'),
            description=data.get('description')
        )
        return jsonify(ProjectResponseDTO().dump(updated_project)), 200
    except ProjectAlreadyExistsError as e:
        return jsonify({'error': str(e)}), 409
    except ProjectNotFoundError:
        return jsonify({'error': 'Проект не найден'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sapr_bp.route('/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id: int):
    project_service.delete_project(project_id)
    return jsonify({'message': 'Проект удален и все связанные данные'}), 200

@sapr_bp.route('/projects/search', methods=['GET'])
def search_projects():
    query = request.args.get('q', '', type=str).strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    if not query:
        return jsonify({'error': 'Параметр поиска q обязателен'}), 400

    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 50

    result = project_service.search_projects(query, page, per_page)
    schema = ProjectResponseDTO(many=True)

    return jsonify({
        'projects': schema.dump(result['projects']),
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page']
    }), 200
