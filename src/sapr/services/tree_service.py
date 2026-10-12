from src.db import db
from src.orm.orm_sapr import SaprTree, TreeItemType
from src.sapr.exceptions import TreeItemHasChildrenError, TreeItemNotFoundError


class TreeService:
    @staticmethod
    def get_tree(project_id: int) -> list:
        # Получить все дерево для проекта
        nodes = SaprTree.query.filter_by(
            project_id=project_id
        ).order_by(SaprTree.position).all()

        return TreeService._build_tree(nodes, parent_link=None)

    @staticmethod
    def _build_tree(nodes: list, parent_link: int) -> list:
        # Рекурсивно собирает словарь дерева
        result = []
        for node in nodes:
            if node.parent_link == parent_link:
                node_dict = {
                    'id': node.id,
                    'name': node.name,
                    'item_type': node.item_type,
                    'parent_link': node.parent_link,
                    'project_id': node.project_id,
                    'instruction_id': node.instruction_id,
                    'model_id': node.model_id,
                    'position': node.position,
                    'has_children': any(n.parent_link == node.id for n in nodes),
                    'children': TreeService._build_tree(nodes, node.id)
                }
                result.append(node_dict)
        return result

    @staticmethod
    def create_item(
        name: str,
        item_type: str,
        project_id: int,
        parent_link: int = None,
        instruction_id: int = None,
        model_id: int = None,
        position: int = None
    ) -> SaprTree:
        # Создает новый узел дерева
        if position is None:
            max_pos = db.session.query(db.func.max(SaprTree.position)).filter_by(
                project_id=project_id,
                parent_link=parent_link
            ).scalar() or -1
            position = max_pos + 1

        tree_item = SaprTree(
            name=name,
            item_type=item_type,
            project_id=project_id,
            parent_link=parent_link,
            instruction_id=instruction_id,
            model_id=model_id,
            position=position
        )

        db.session.add(tree_item)
        db.session.commit()
        return tree_item

    @staticmethod
    def update_item(item_id: int, name: str = None, position: int = None) -> SaprTree:
        # Обновляет узел дерева
        item = db.session.get(SaprTree, item_id)
        if not item:
            raise TreeItemNotFoundError()

        if name is not None:
            item.name = name
        if position is not None:
            item.position = position

        db.session.commit()
        return item

    @staticmethod
    def delete_item(item_id: int, cascade: bool = False):
        # Удаляет узел. Если cascade=False, запрещает удаление при наличии детей
        item = db.session.get(SaprTree, item_id)

        if not item:
            raise TreeItemNotFoundError()

        children = SaprTree.query.filter_by(parent_link=item_id).all()

        if children and not cascade:
            raise TreeItemHasChildrenError()

        if cascade:
            TreeService._cascade_delete(item_id)
        else:
            db.session.delete(item)

        db.session.commit()

    @staticmethod
    def _cascade_delete(item_id: int):
        # Рекурсивное удаление всех вложенных элементов
        children = SaprTree.query.filter_by(parent_link=item_id).all()
        for child in children:
            TreeService._cascade_delete(child.id)
        
        item = db.session.get(SaprTree, item_id)
        if item:
            db.session.delete(item)

    @staticmethod
    def move_item(item_id: int, new_parent_link: int = None, new_position: int = None) -> SaprTree:
        # Перемещает узел в другую часть дерева
        item = db.session.get(SaprTree, item_id)
        if not item:
            raise TreeItemNotFoundError()

        if new_parent_link is not None:
            item.parent_link = new_parent_link
        if new_position is not None:
            item.position = new_position

        db.session.commit()
        return item


tree_service = TreeService()