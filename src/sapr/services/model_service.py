import os
import uuid
from flask import current_app
from src.db import db
from src.orm.orm_sapr import Models, Item, Project, ModelSpta
from src.sapr.exceptions import(
    ModelNotFoundError,
    ProjectNotFoundError,
    FileSaveError,
    ModelUploadError,
    PhysicalFileNotFoundError
)
from sqlalchemy import or_

class ModelService:
    def _save_file(self, file) -> str:
        # Сохраняет файл и возвращает новое имя
        if not file or file.filename == '':
            raise ModelUploadError("Файл не предоставлен или имеет пустое имя")
        
        extension = os.path.splitext(file.filename)[1]
        storage_name = f"{uuid.uuid4().hex}{extension}"
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], storage_name)
        
        try:
            file.save(save_path)
            return storage_name
        except Exception as e:
            raise FileSaveError(f"Не удалось сохранить файл модели: {str(e)}")

    def _delete_file_from_disk(self, technical_name: str) -> None:
        # Удаляет файл с диска, если он существует
        if not technical_name:
            return
        
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], technical_name)

        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
        
    def add_model_to_project(
        self,
        project_id: int,
        name: str,
        file=None,
        is_primary: bool = False,
        technical_name: str = None
    ) -> Models:
        project = Project.query.get(project_id)
        if not project:
            raise ProjectNotFoundError()

        if file:
            technical_name = self._save_file(file)

        if is_primary:
            Models.query.filter_by(
                project_id=project_id,
                is_primary=True
            ).update({'is_primary': False})

        model = Models(
            project_id=project_id,
            name=name,
            technical_name=technical_name, 
            is_primary=is_primary
        )
        db.session.add(model)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            if technical_name and file: 
                self._delete_file_from_disk(technical_name)
            raise FileSaveError(f'Не удалось сохранить запись модели: {str(e)}')

        return model

    def update_model(
        self,
        model_id: int,
        name: str = None,
        file=None,
        is_primary: bool = None
    ) -> Models:
        # Обновляет модель
        model = Models.query.get(model_id)
        if not model:
            raise ModelNotFoundError()

        old_technical_name = None

        if file:
            old_technical_name = model.technical_name
            model.technical_name = self._save_file(file)
            if name is None:
                model.name = file.filename

        if name is not None:
            model.name = name

        if is_primary is not None:
            if is_primary:
                Models.query.filter(
                    Models.project_id == model.project_id,
                    Models.id != model.id,
                    Models.is_primary == True
                ).update({'is_primary': False})
            model.is_primary = is_primary

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            if file and model.technical_name != old_technical_name:
                self._delete_file_from_disk(model.technical_name)
            raise FileSaveError(f'Не удалось обновить модель: {str(e)}')

        return model

    def download_model(self, model_id: int):
        # Возвращает путь к файлу и имя для скачивания
        model = Models.query.get(model_id)
        if not model:
            raise ModelNotFoundError()

        if not model.technical_name:
            raise PhysicalFileNotFoundError()

        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], model.technical_name)

        if not os.path.exists(file_path):
            raise PhysicalFileNotFoundError()

        return file_path, model.name
    

    def delete_model(
        self,
        model_id: int,
    ) -> dict:
        # Удаляет модель и ее файл
        model = Models.query.get(model_id)
        if not model:
            raise ModelNotFoundError()

        file_to_delete = model.technical_name

        try:
            db.session.delete(model)
            db.session.commit()

            self._delete_file_from_disk(file_to_delete)

            return {'success': True, 'model_id': model_id}
        except Exception as e:
            db.session.rollback()
            raise FileSaveError(f'Ошибка при удалении модели: {str(e)}')

    def search_models(self, query: str, project_id: int = None, page: int = 1, per_page: int = 50) -> dict:
        if not query or len(query.strip()) < 2:
            return {'models': [], 'total': 0, 'page': page, 'per_page': per_page}

        search_term = f'%{query.strip()}%'

        stmt = Models.query.filter(
            or_(
                Models.name.ilike(search_term),
                Models.technical_name.ilike(search_term)
            )
        )

        if project_id:
            stmt = stmt.filter(Models.project_id == project_id)

        total = stmt.count()

        models = stmt.order_by(Models.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

        return {
            'models': models,
            'total': total,
            'page': page,
            'per_page': per_page
        }

    def get_model(self, model_id: int) -> Models:
        model = Models.query.get(model_id)
        if not model:
            raise ModelNotFoundError()        
        return model

    def get_models_by_project(self, project_id: int) -> list:
        # Получить Модели по id Проекта
        return Models.query.filter_by(project_id=project_id).all()

    def get_items_by_model_id(self, model_id: int) -> list[Item]:
        # Получить список складских позиций, входящих в состав 3D-модели
        model = Models.query.get(model_id) 
        if not model:
            raise ModelNotFoundError()

        links = ModelSpta.query.filter_by(model_id=model_id).all()
        if not links:
            return []

        # Собираем ID изделий и делаем один запрос к таблице Item
        item_ids = [link.item_id for link in links]
        items = Item.query.filter(Item.id.in_(item_ids)).all()

        return items

model_service = ModelService()