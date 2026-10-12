from src.db import db
from src.orm.orm_sapr import ProjectPart, Project, Part, Item
from src.sapr.exceptions import (
    ProjectNotFoundError,
    PartNotFoundError,
    ProjectPartAlreadyExistsError,
    InsufficientStockError
)


class ProjectPartService:
    def add_to_project_batch(self, project_id: int, parts_data: list) -> tuple[list[ProjectPart], list[dict]]:
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

    @staticmethod
    def add_part_to_project_with_stock_check(
        project_id: int, 
        part_id: int, 
        quantity: int, 
        custom_parameters: dict = None,
        added_by: int = None
        ) -> tuple[ProjectPart, int | None, str | None]:
        # Добавить деталь в проект с проверкой наличия на складе
        project = Project.query.get(project_id)
        if not project:
            raise ProjectNotFoundError()

        part = Part.query.get(part_id)
        if not part:
            raise PartNotFoundError()

        remaining_stock = None
        warning = None

        # Проверяем, привязана ли деталь к складу
        if part.item_id:
            item = Item.query.get(part.item_id)

            if item.stock_quantity < quantity:
                raise InsufficientStockError(
                    message=f'Недостаточно на складе. Есть: {item.stock_quantity}, нужно: {quantity}'
                )

            item.stock_quantity -= quantity
            remaining_stock = item.stock_quantity
        else:
            warning = 'Деталь не учтена на складе, добавляем ее без проверки остатков'

        project_part = ProjectPart(
            project_id=project_id,
            part_id=part_id,
            quantity=quantity,
            custom_parameters=custom_parameters or {},
            added_by=added_by
        )
        db.session.add(project_part)
        db.session.commit()

        return project_part, remaining_stock, warning


project_part_service = ProjectPartService()