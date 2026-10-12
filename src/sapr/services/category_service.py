from datetime import datetime
from src.db import db
from src.orm.orm_sapr import PartCategory
from src.sapr.exceptions import (
    CategoryNotFoundError,
    CategoryCycleError,
    CategoryHasChildrenError,
)


class CategoryService:
    def _has_cycle(self, category_id: int, parent_id: int) -> bool:
        # Проверяет, станет ли parent_id потомком category_id
        if category_id == parent_id:
            return True

        current = PartCategory.query.get(parent_id)
        while current:
            if current.id == category_id:
                return True
            current = PartCategory.query.get(current.parent_id) if current.parent_id else None

        return False

    def create_category(
        self,
        name: str,
        parent_id: int = None,
        sort_order: int = 0
    ) -> PartCategory:
        # Создаёт категорию
        if parent_id is not None:
            parent = PartCategory.query.get(parent_id)
            if not parent:
                raise CategoryNotFoundError()
        
        category = PartCategory(
            name=name,
            parent_id=parent_id,
            sort_order=sort_order
        )
        db.session.add(category)
        db.session.commit()
        return category

    def update_category(
        self,
        category_id: int,
        name: str = None,
        parent_id: int = None,
        sort_order: int = None
    ) -> PartCategory:
        # Обновляет категорию
        category = PartCategory.query.get(category_id)
        if not category:
            raise CategoryNotFoundError()

        if parent_id is not None and parent_id != category.parent_id:
            if self._has_cycle(category_id, parent_id):
                raise CategoryCycleError()
            parent = PartCategory.query.get(parent_id)
            if not parent:
                raise CategoryNotFoundError()

        if name is not None:
            category.name = name
        if parent_id is not None:
            category.parent_id = parent_id
        if sort_order is not None:
            category.sort_order = sort_order

        category.updated_at = datetime.utcnow()
        db.session.commit()
        return category

    def delete_category(self, category_id: int) -> dict:
        # Удаляет категорию 
        category = PartCategory.query.get(category_id)
        if not category:
            raise CategoryNotFoundError()

        children_count = PartCategory.query.filter_by(parent_id=category_id).count()
        if children_count > 0:
            raise CategoryHasChildrenError()

        db.session.delete(category)
        db.session.commit()
        return {'success': True, 'category_id': category_id}

    def get_tree(self, parent_id: int = None) -> list:
        # Возвращает дерево категорий
        categories = PartCategory.query.order_by(PartCategory.sort_order).all()
        nodes_by_id = {}

        for cat in categories:
            nodes_by_id[cat.id] = {
                'id': cat.id,
                'name': cat.name,
                'parent_id': cat.parent_id,
                'sort_order': cat.sort_order,
                'created_at': cat.created_at.isoformat() if cat.created_at else None,
                'updated_at': cat.updated_at.isoformat() if cat.updated_at else None,
                'children': []
            }

        roots = []
        for cat in categories:
            node = nodes_by_id[cat.id]
            if cat.parent_id is None:
                roots.append(node)
            else:
                parent_node = nodes_by_id.get(cat.parent_id)
                if parent_node:
                    parent_node['children'].append(node)

        if parent_id is not None:
            subtree = nodes_by_id.get(parent_id)
            return [subtree] if subtree else []
        
        return roots


category_service = CategoryService()