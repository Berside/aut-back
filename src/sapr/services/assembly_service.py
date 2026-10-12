from src.db import db
from src.orm.orm_sapr import AssemblyItem, Project, Part, AssemblyPartLink, Item
from src.sapr.exceptions import (
    AssemblyItemNotFoundError,
    ProjectNotFoundError,
    CyclicDependencyError,
    InvalidParentError,
    CrossProjectReferenceError,
    PartNotFoundError,
    ItemNotFoundError
)
from sqlalchemy import func

class AssemblyService():
    def _has_cycle(self, item_id: int, parent_id: int) -> bool:
        # Проверяет, станет ли parent_id потомком item_id

        if item_id == parent_id:
            return True

        stack = [parent_id]
        visited = set()

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)

            current_item = AssemblyItem.query.get(current)

            if not current_item:
                continue
            if current_item.id == item_id:
                return True
            if current_item.parent_id is not None:
                stack.append(current_item.parent_id)

        return False

    def get_project_assembly(self, project_id: int) -> list:
        # Получаем все элементы сборки проекта, отсортированные по порядку
        return AssemblyItem.query.filter_by(project_id=project_id).order_by(
            AssemblyItem.parent_id, AssemblyItem.order
        ).all()

    @staticmethod
    def get_assembly_tree(project_id: int) -> list:
        # Возвращает рекурсивное дерево элементов сборки проекта
        items = AssemblyItem.query.filter_by(project_id=project_id).order_by(
            AssemblyItem.order, AssemblyItem.id
        ).all()

        item_dict = {}
        for item in items:
            node = {
                'id': item.id,
                'name': item.name,
                'model_id': item.model_id,
                'part_id': item.part_id,
                'item_id': item.item_id,
                'order': item.order,
                'children': []
            }
            if item.item:
                node['item'] = {
                    'id': item.item.id,
                    'article': item.item.article,
                    'name': item.item.name,
                    'standard': item.item.standard,
                    'unit': item.item.unit,
                    'stock_quantity': item.item.stock_quantity
                }
            item_dict[item.id] = node

        tree = []
        for item in items:
            node = item_dict[item.id]
            if item.parent_id and item.parent_id in item_dict:
                item_dict[item.parent_id]['children'].append(node)
            else:
                tree.append(node)

        return tree

    def create_item(
        self,
        project_id: int,
        name: str,
        model_id: int = None,
        part_id: int = None,
        parent_id: int = None,
        order: int = 0
    ) -> AssemblyItem:
        # Создает элемент сборки
        project = Project.query.get(project_id)
        if not project:
            raise ProjectNotFoundError()

        if parent_id is not None:
            parent = AssemblyItem.query.get(parent_id)
            if not parent:
                raise InvalidParentError()
            if parent.project_id != project_id:
                raise CrossProjectReferenceError()

        item = AssemblyItem(
            project_id=project_id,
            name=name,
            model_id=model_id,
            part_id=part_id,
            parent_id=parent_id,
            order=order
        )

        db.session.add(item)
        db.session.commit()
        return item

    def update_item(self, item_id: int, **kwargs) -> AssemblyItem:
        # Обновляет элемент сборки с проверкой циклов
        item = AssemblyItem.query.get(item_id)
        if not item:
            raise AssemblyItemNotFoundError()

        new_parent_id = kwargs.get('parent_id')
        if new_parent_id is not None and new_parent_id != item.parent_id:
            parent = AssemblyItem.query.get(new_parent_id)
            if not parent:
                raise InvalidParentError()
            if parent.project_id != item.project_id:
                raise CrossProjectReferenceError()
            if self._has_cycle(item_id, new_parent_id):
                raise CyclicDependencyError()

        for key, val in kwargs.items():
            if val is not None and hasattr(item, key):
                setattr(item, key, val)
        db.session.commit()
        return item

    def delete_item(self, item_id: int) -> dict:
        # Удаляет элемент сборки
        item = AssemblyItem.query.get(item_id)
        if not item:
            raise AssemblyItemNotFoundError()

        try:
            db.session.delete(item)
            db.session.commit()
            return {'success': True, 'item_id': item_id}
        except Exception as e:
            db.session.rollback()
            raise AssemblyItemNotFoundError(f'Ошибка при удалении элемента: {str(e)}')

    def import_part_to_assembly(
        self,
        project_id: int,
        part_id: int,
        parent_id: int = None,
        quantity: int = 1,
        position: dict = None,
        rotation: dict = None,
    ) -> tuple[AssemblyItem, AssemblyPartLink]:
        # Импортирует деталь в сборку
        project = Project.query.get(project_id)
        if not project:
            raise ProjectNotFoundError()
        
        part = Part.query.get(part_id)
        if not part:
            raise PartNotFoundError()
        
        if parent_id:
            parent = AssemblyItem.query.get(parent_id)
            if not parent:
                raise InvalidParentError()
            if parent.project_id != project_id:
                raise CrossProjectReferenceError()

        max_order = db.session.query(func.max(AssemblyItem.order)).filter(
            AssemblyItem.project_id == project_id,
            AssemblyItem.parent_id == parent_id
        ).scalar() or 0

        assembly_item = AssemblyItem(
            project_id=project_id,
            name=part.name,
            model_id=part.model_id,
            part_id=part_id,
            parent_id=parent_id,
            order=max_order + 1
        )
        db.session.add(assembly_item)
        db.session.flush()

        link = AssemblyPartLink(
            assembly_item_id=assembly_item.id,
            part_id=part_id,
            quantity=quantity,
            position=position or {'x': 0, 'y': 0, 'z': 0},
            rotation=rotation or {'x': 0, 'y': 0, 'z': 0},
        )
        db.session.add(link)
        db.session.commit()

        return assembly_item, link

    @staticmethod
    def link_item_to_assembly(assembly_item_id: int, item_id: int) -> AssemblyItem:
        # Привязывает складскую позицию к элементу сборки
        assembly_item = AssemblyItem.query.get(assembly_item_id)
        if not assembly_item:
            raise AssemblyItemNotFoundError()

        item = Item.query.get(item_id)
        if not item:
            raise ItemNotFoundError()

        assembly_item.item_id = item_id
        db.session.commit()

        return assembly_item

    @staticmethod 
    def unlink_item_from_assembly(assembly_item_id: int) -> AssemblyItem:
        # Отвязать складскую позицию от элемента сборки
        assembly_item = AssemblyItem.query.get(assembly_item_id)
        if not assembly_item:
            raise AssemblyItemNotFoundError()
        
        assembly_item.item_id = None
        db.session.commit()

        return assembly_item

    @staticmethod
    def get_linked_item_for_assembly(assembly_item_id: int):
        # Получает складскую позицию Item, привязанную к элементу сборки
        assembly_item = AssemblyItem.query.get(assembly_item_id)
        if not assembly_item:
            raise AssemblyItemNotFoundError()

        return assembly_item.item

    @staticmethod
    def search_assembly_items(project_id: int, query: str, page: int = 1, per_page: int = 50) -> dict:
        # Поиск элементов сборки по названию в рамках проекта
        project = Project.query.get(project_id)
        if not project:
            raise ProjectNotFoundError()

        if not query or len(query.strip()) < 2:
            return {'items': [], 'total': 0, 'page': page, 'per_page': per_page}

        search_term = f'%{query.strip()}%'

        stmt = AssemblyItem.query.filter(
            AssemblyItem.project_id == project_id,
            AssemblyItem.name.ilike(search_term)
        )

        total = stmt.count()

        items = stmt.order_by(AssemblyItem.order, AssemblyItem.id).offset((page - 1) * per_page).limit(per_page).all()

        return {
            'items': [
                {
                    'id': item.id,
                    'name': item.name,
                    'model_id': item.model_id,
                    'part_id': item.part_id,
                    'item_id': item.item_id,
                    'parent_id': item.parent_id,
                    'order': item.order,
                }
                for item in items
            ],
            'total': total,
            'page': page,
            'per_page': per_page
        }


assembly_service = AssemblyService()

