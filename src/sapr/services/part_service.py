import os
from datetime import datetime
from flask import current_app
from sqlalchemy import or_, func
from src.db import db
from src.orm.orm_sapr import (
    Part, PartCategory, PartType, ProjectPart, 
    AssemblyPartLink, AssemblyItem, Models, Project, Item
)
from src.sapr.exceptions import (
    PartNotFoundError,
    PartNumberExistsError,
    PartDeletionError,
    ProjectNotFoundError,
    ProjectPartNotFoundError,
    ProjectPartAlreadyExistsError,
    CategoryNotFoundError,
    TypeNotFoundError,
    ModelNotFoundError,
    PhysicalFileNotFoundError,
    ItemNotFoundError
)


class PartService:
    def _serialize_part(self, part: Part, full: bool = True) -> dict:
        # Сериализует деталь в словарь
        data = {
            'id': part.id,
            'name': part.name,
            'part_number': part.part_number,
            'description': part.description,
            'category_id': part.category_id,
            'category_name': part.category.name if part.category else None,
            'type_id': part.type_id,
            'type_name': part.type.name if part.type else None,
            'parameters': part.parameters,
            'model_id': part.model_id,
            'unit': part.unit,
            'is_standard': part.is_standard,
            'is_active': part.is_active,
        }
        
        if full:
            data.update({
                'technical_name': part.technical_name,
                'preview_image': part.preview_image,
                'created_by': part.created_by,
                'created_at': part.created_at.isoformat() if part.created_at else None,
                'updated_at': part.updated_at.isoformat() if part.updated_at else None,
            })
        
        return data

    def get_part(self, part_id: int, project_id: int = None) -> Part:
        # Получает одну деталь по ID
        part = Part.query.get(part_id)
        if not part:
            raise PartNotFoundError()

        if project_id:
            project_part = ProjectPart.query.filter_by(
                project_id=project_id,
                part_id=part_id
            ).first()
            if not project_part:
                raise PartNotFoundError('Деталь не принадлежит этому проекту')

        return part

    @staticmethod
    def get_part_item(part_id: int) -> Item:
        # Получить складскую позицию, связанную с деталью из библиотеки
        part = Part.query.get(part_id)
        if not part:
            raise PartNotFoundError()

        if part.item_id is None:
            raise ItemNotFoundError(message='Деталь не привязана к складской позиции')

        item = Item.query.get(part.item_id)
        if not item:
            raise ItemNotFoundError(message='Связанная складская позиия не найдена')
        
        return item

        

    def search_parts(self, query: str, category_id: int = None, page: int = 1, per_page = 50) -> dict:
        # Поиск деталей по строке
        if not query or len(query.strip()) < 2:
            return {'parts': [], 'total': 0, 'page': page, 'per_page': per_page}

        search_term = f'%{query.strip()}%'

        stmt = Part.query.filter(
            or_(
                Part.name.ilike(search_term),
                Part.part_number.ilike(search_term),                
                Part.description.ilike(search_term)
            )
        )

        if category_id:
            stmt = stmt.filter(Part.category_id == category_id)

        total = stmt.count()

        parts = stmt.order_by(Part.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

        return {
            'parts': [self._serialize_part(p, full=False) for p in parts],
            'total': total,
            'page': page,
            'per_page': per_page
        }

    def get_parts_list(
        self,
        page: int = 1,
        limit: int = 20,
        category_id: int = None,
        type_id: int = None,
        is_standard: bool = None,
        search: str = None,
        project_id: int = None
    ) -> tuple[list[Part], int]:
        # Получает список деталей с фильтрацией
        if limit > 1000:
            limit = 1000

        query = Part.query

        if project_id:
            query = query.join(ProjectPart, ProjectPart.part_id == Part.id).filter(
                ProjectPart.project_id == project_id
            )

        if category_id:
            query = query.filter(Part.category_id == category_id)
        if type_id:
            query = query.filter(Part.type_id == type_id)
        if is_standard is not None:
            query = query.filter(Part.is_standard == is_standard)
        if search:
            query = query.filter(
                or_(
                    Part.name.ilike(f'%{search}%'),
                    Part.part_number.ilike(f'%{search}%'),
                )
            )
        total = query.count()
        parts = query.order_by(Part.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

        return parts, total

    def create_part(
        self,
        name: str,
        project_id: int = None,
        part_number: str = None,
        description: str = None,
        category_id: int = None,
        type_id: int = None,
        parameters: dict = None,
        model_id: int = None,
        technical_name: str = None,
        preview_image: str = None,
        unit: str = "шт",
        is_standard: bool = True,
        is_active: bool = True,
        created_by: int = None,
        quantity: int = 1,
        custom_parameters: dict = None,
    ) -> Part:
        # Создаёт деталь и привязывает к проекту
        if part_number:
            existing = Part.query.filter_by(part_number=part_number).first()
            if existing:
                raise PartNumberExistsError(f'part_number {part_number} уже существует')

        if category_id and not PartCategory.query.get(category_id):
            raise CategoryNotFoundError()
        if type_id and not PartType.query.get(type_id):
            raise TypeNotFoundError()
        if model_id and not Models.query.get(model_id):
            raise ModelNotFoundError()

        if project_id:
            project = Project.query.get(project_id)
            if not project:
                raise ProjectNotFoundError()

        part = Part(
            name=name,
            part_number=part_number,
            description=description,
            category_id=category_id,
            type_id=type_id,
            parameters=parameters or {},
            model_id=model_id,
            technical_name=technical_name,
            preview_image=preview_image,
            unit=unit,
            is_standard=is_standard,
            is_active=is_active,
            created_by=created_by
        )
        db.session.add(part)
        db.session.flush()

        if project_id:
            project_part = ProjectPart(
                project_id=project_id,
                part_id=part.id,
                quantity=quantity,
                custom_parameters=custom_parameters or {}
            )
            db.session.add(project_part)
            
        db.session.commit()
        
        return part

    def update_part(self, part_id: int, **kwargs) -> Part:
        # Обновляет деталь
        part = Part.query.get(part_id)
        if not part:
            raise PartNotFoundError()

        if 'part_number' in kwargs and kwargs['part_number']:
            existing = Part.query.filter(
                Part.part_number == kwargs['part_number'],
                Part.id != part_id
            ).first()
            if existing:
                raise PartNumberExistsError(f"part_number {kwargs['part_number']} уже существует")

        for key, val in kwargs.items():
            if val is not None and hasattr(part, key):
                setattr(part, key, val)

        part.updated_at = datetime.utcnow()
        db.session.commit()
        return part

    def delete_part(self, part_id: int) -> dict:
        # Удаляет деталь и её файлы
        part = Part.query.get(part_id)
        if not part:
            raise PartNotFoundError()

        files_to_delete = []
        if part.technical_name:
            files_to_delete.append(
                os.path.join(current_app.config['UPLOAD_FOLDER'], part.technical_name)
            )
        if part.preview_image:
            files_to_delete.append(
                os.path.join(current_app.config['UPLOAD_FOLDER'], part.preview_image)
            )

        try:
            ProjectPart.query.filter_by(part_id=part_id).delete()
            AssemblyPartLink.query.filter_by(part_id=part_id).delete()
            db.session.delete(part)
            db.session.commit()

            for filepath in files_to_delete:
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except OSError:
                        pass

            return {'success': True, 'part_id': part_id}
        except Exception as e:
            db.session.rollback()
            raise PartDeletionError(f"Ошибка при удалении: {str(e)}")

    def download_file(self, part_id: int) -> tuple[str, str]:
        # Возвращает путь к файлу детали и mimetype
        part = Part.query.get(part_id)
        if not part:
            raise PartNotFoundError()
        
        if not part.technical_name:
            raise PhysicalFileNotFoundError("У детали нет файла")
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        if not upload_folder:
            upload_folder = os.path.join(current_app.config['SRC_PATH'], 'file_storage')
        
        filepath = os.path.join(upload_folder, part.technical_name)
        
        if not os.path.exists(filepath):
            raise PhysicalFileNotFoundError("Файл не найден на диске")
        
        return filepath, 'model/gltf-binary'

    def batch_create(self, parts_data: list) -> tuple[list[Part], list[dict]]:
        # Массовое создание деталей
        created_parts = []
        project_parts_data = []
        errors = []
        
        for idx, part_data in enumerate(parts_data):
            try:
                if not part_data.get('name'):
                    errors.append({'index': idx, 'error': 'name обязателен'})
                    continue
                
                project_id = part_data.get('project_id')
                if not project_id:
                    errors.append({'index': idx, 'error': 'project_id обязателен'})
                    continue
                
                project = Project.query.get(project_id)
                if not project:
                    errors.append({'index': idx, 'error': f'project_id {project_id} не найден'})
                    continue

                if part_data.get('part_number'):
                    existing = Part.query.filter_by(part_number=part_data['part_number']).first()
                    if existing:
                        errors.append({'index': idx, 'error': f"part_number '{part_data['part_number']}' уже существует"})
                        continue
                
                part = Part(
                    name=part_data['name'],
                    part_number=part_data.get('part_number'),
                    description=part_data.get('description'),
                    category_id=part_data.get('category_id'),
                    type_id=part_data.get('type_id'),
                    parameters=part_data.get('parameters', {}),
                    model_id=part_data.get('model_id'),
                    technical_name=part_data.get('technical_name'),
                    unit=part_data.get('unit', 'шт'),
                    is_standard=part_data.get('is_standard', True)
                )
                db.session.add(part)
                created_parts.append(part)
                
                project_parts_data.append({
                    'project_id': project_id,
                    'part': part,
                    'quantity': part_data.get('quantity', 1),
                    'custom_parameters': part_data.get('custom_parameters', {})
                })
                
            except Exception as e:
                errors.append({'index': idx, 'error': str(e)})
        
        if created_parts:
            db.session.flush()
            
            for pp_data in project_parts_data:
                project_part = ProjectPart(
                    project_id=pp_data['project_id'],
                    part_id=pp_data['part'].id,
                    quantity=pp_data['quantity'],
                    custom_parameters=pp_data['custom_parameters']
                )
                db.session.add(project_part)
                
            db.session.commit()
        
        return created_parts, errors

    def batch_delete(self, part_ids: list) -> tuple[int, list[dict]]:
        # Массовое удаление деталей
        deleted_count = 0
        errors = []

        for part_id in part_ids:
            part = Part.query.get(part_id)
            if part:
                ProjectPart.query.filter_by(part_id=part_id).delete()
                AssemblyPartLink.query.filter_by(part_id=part_id).delete()
                db.session.delete(part)
                deleted_count += 1
            else:
                errors.append({'id': part_id, 'error': 'Деталь не найдена'})

        db.session.commit()
        return deleted_count, errors

    def add_to_project_batch(self, project_id: int, parts_data: list) -> tuple[list[ProjectPart], list[dict]]:
        # Массовое добавление деталей в проект
        project = Project.query.get(project_id)
        if not project:
            raise ProjectNotFoundError()
        
        added_parts = []
        errors = []

        for idx, part_data in enumerate(parts_data):
            try: 
                if not part_data.get('part_id'):
                    errors.append({'index': idx, 'error': 'part_id обязателен'})
                    continue

                part = Part.query.get(part_data['part_id'])
                if not part:
                    errors.append({'index': idx, 'error': f"part_id {part_data['part_id']} не найден"})
                    continue
                
                existing = ProjectPart.query.filter_by(
                    project_id=project_id,
                    part_id=part_data['part_id']
                ).first()

                if existing:
                    errors.append({'index': idx, 'error': 'деталь уже добавлена в проект'})
                    continue

                project_part = ProjectPart(
                    project_id=project_id,
                    part_id=part_data['part_id'],
                    quantity=part_data.get('quantity', 1),
                    custom_parameters=part_data.get('custom_parameters', {})
                )

                db.session.add(project_part)
                added_parts.append(project_part)

            except Exception as e:
                errors.append({'index': idx, 'error': str(e)})
        
        if added_parts:
            db.session.commit()

        return added_parts, errors

    def remove_from_project_batch(self, project_id: int, part_ids: list) -> tuple[int, list[dict]]:
        # Массовое удаление деталей из проекта
        deleted_count = 0
        errors = []

        for part_id in part_ids:
            project_part = ProjectPart.query.filter_by(
                project_id=project_id,
                part_id=part_id,
            ).first()

            if project_part:
                db.session.delete(project_part)
                deleted_count += 1
            else:
                errors.append({'part_id': part_id, 'error': 'Деталь проекта не найдена'})
        
        db.session.commit()
        return deleted_count, errors

part_service = PartService()