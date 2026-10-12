import os
import uuid
import traceback

from flask import request, jsonify, current_app
from sqlalchemy import func, or_
from src.sapr.exceptions import ( 
    ProjectNotFoundError, FileSaveError, ProjectAlreadyExistsError)

from src.db import db
from src.orm.orm_sapr import (
    Project, Models
)

from src.orm.orm_file import TaskFile
from src.document.document import Document
from src.sapr.services.instruction_service import instruction_service


class ProjectService:
    def _save_file(self, file) -> str:
        extension = os.path.splitext(file.filename)[1]
        storage_name = f"{uuid.uuid4().hex}{extension}"
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], storage_name)
        try:
            file.save(save_path)
            return storage_name
        except Exception as e:
            raise FileSaveError(f'Не удалось сохранить файл: {str(e)}')

    def get_all_projects(self) -> list[Project]:
        return db.session.query(Project).all()

    def get_project(self, project_id: int) -> Project:
        project = Project.query.get(project_id)
        if not project:
            raise ProjectNotFoundError()
        return project

    @staticmethod 
    def get_project_instructions(project_id: int) -> list:
        # Получить список инструкций проекта
        project = Project.query.get(project_id)
        if not project:
            raise ProjectNotFoundError()

        return instruction_service.get_instructions_list(project_id=project_id)
    def create_project(self, name: str, description: str, primary_model_file=None) -> Project:
        existing = Project.query.filter_by(name=name).first()
        if existing:
            raise ProjectAlreadyExistsError(f'Проект {name} уже существует')

        model_storage_name = None
        model_original_name = None

        if primary_model_file:
            model_storage_name = self._save_file(primary_model_file)
            model_original_name = primary_model_file.filename

        project = Project(name=name, description=description)
        db.session.add(project)
        db.session.flush()

        if model_storage_name:
            model = Models(
                project_id=project.id,
                name=model_original_name,
                technical_name=model_storage_name,
                is_primary=True
            )
            db.session.add(model)

        db.session.commit()
        return project

    def update_project(self, project_id: int, name: str = None, description: str = None) -> Project:
        project = Project.query.get(project_id)
        if not project:
            raise ProjectNotFoundError()

        if name is not None and name != project.name:
            existing = Project.query.filter_by(name=name).first()
            if existing and existing.id != project_id:
                raise ProjectAlreadyExistsError(f'Проект "{name}" уже существует')
            project.name = name

        if description is not None:
            project.description = description

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise FileSaveError(f'Не удалось обновить проект: {str(e)}')

        return project

    def delete_project(self, project_id: int) -> bool:
        project = Project.query.get(project_id)
        if not project:
            raise ProjectNotFoundError()

        files_to_delete = [
            os.path.join(current_app.config['UPLOAD_FOLDER'], model.technical_name)
            for model in project.models if model.technical_name
        ]

        try:
            db.session.delete(project)
            db.session.commit()

            for filepath in files_to_delete:
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except OSError:
                        pass

            return True
            
        except Exception as e:
            db.session.rollback()
            raise FileSaveError(f"Ошибка при удалении: {str(e)}")

    @staticmethod
    def search_projects(query: str, page: int = 1, per_page: int = 50) -> dict:
        # Поиск проектов по названию и описанию
        if not query or len(query.strip()) < 2:
            return {'projects': [], 'total': 0, 'page': page, 'per_page': per_page}

        search_term = f'%{query.strip()}%'

        stmt = Project.query.filter(
            or_(
                Project.name.ilike(search_term),
                Project.description.ilike(search_term)
            )
        )

        total = stmt.count()

        projects = stmt.order_by(Project.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

        return {
            'projects': projects,
            'total': total,
            'page': page,
            'per_page': per_page
        }


project_service = ProjectService()