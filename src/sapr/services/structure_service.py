from typing import Optional, List
from src.db import db
from src.orm.orm_sapr import ModelStructureNode
from src.sapr.exceptions import (
    StructureNodeNotFoundError,
    StructureNodeAlreadyExistsError,
    StructureNodeDeletionError
)


class StructureService:
    @staticmethod
    def get_node(node_id: str) -> ModelStructureNode:
        # Получает узел по ID
        node = ModelStructureNode.query.get(node_id)
        if not node:
            raise StructureNodeNotFoundError()
        return node

    @staticmethod
    def get_tree(model_id: str) -> list:
        # Получает дерево структуры для модели
        nodes = db.session.query(ModelStructureNode).filter_by(
            model_id=model_id
        ).order_by(ModelStructureNode.position).all()

        return StructureService._build_tree(nodes, parent_id=None)

    @staticmethod
    def _build_tree(nodes: list, parent_id: Optional[int]) -> list:
        # Рекурсивно собирает дерево в памяти
        result = []
        for node in nodes:
            if node.parent_id == parent_id:
                node_dict = {
                    'id': node.id,
                    'name': node.name,
                    'description': node.description,
                    'code': node.code,
                    'parent_id': node.parent_id,
                    'model_id': node.model_id,
                    'part_id': node.part_id,
                    'position': node.position,
                    'has_children': any(n.parent_id == node.id for n in nodes),
                    'children': StructureService._build_tree(nodes, node.id)
                }
                result.append(node_dict)
        return result

    @staticmethod
    def create_node(
        name: str,
        code: str,
        parent_id: Optional[int] = None,
        description: Optional[str] = None,
        model_id: Optional[int] = None,
        part_id: Optional[int] = None,
        position: int = 0
    ) -> ModelStructureNode:
        # Создаёт новый узел структуры
        existing = db.session.query(ModelStructureNode).filter_by(code=code).first()
        if existing:
            raise StructureNodeAlreadyExistsError()

        if position is None:
            max_pos = db.session.query(db.func.max(ModelStructureNode.position)).filter_by(
                parent_id=parent_id
            ).scalar() or -1
            position = max_pos + 1

        node = ModelStructureNode(
            name=name,
            code=code,
            parent_id=parent_id,
            description=description,
            model_id=model_id,
            part_id=part_id,
            position=position
        )

        db.session.add(node)
        db.session.commit()
        return node

    @staticmethod
    def update_node(
        node_id: str,
        name: Optional[str] = None,
        code: Optional[str] = None,
        description: Optional[str] = None,
        parent_id: Optional[int] = None,
        model_id: Optional[int] = None,
        part_id: Optional[int] = None,
        position: Optional[int] = None
    ) -> ModelStructureNode:
        # Обновляет узел структуры
        node = db.session.get(ModelStructureNode, node_id)
        if not node:
            raise StructureNodeNotFoundError()

        if code is not None:
            existing = db.session.query(ModelStructureNode).filter(
                ModelStructureNode.code == code,
                ModelStructureNode.id != node_id
            ).first()
            if existing:
                raise StructureNodeAlreadyExistsError()
            node.code = code

        if name is not None:
            node.name = name

        if description is not None:
            node.description = description

        if parent_id is not None:
            node.parent_id = parent_id

        if model_id is not None:
            node.model_id = model_id

        if part_id is not None:
            node.part_id = part_id

        if position is not None:
            node.position = position

        db.session.commit()
        return node

    @staticmethod
    def delete_node(node_id: str, cascade: bool = False) -> bool:
        # Удаляет узел. cascade=True удаляет всех потомков
        node = db.session.get(ModelStructureNode, node_id)
        if not node:
            raise StructureNodeNotFoundError()

        children = db.session.query(ModelStructureNode).filter_by(parent_id=node_id).all()

        if children and not cascade:
            raise StructureNodeDeletionError('Нельзя удалить узел с дочерними элементами')

        if cascade:
            StructureService._cascade_delete(node_id)
        else:
            db.session.delete(node)

        db.session.commit()
        return True

    @staticmethod
    def _cascade_delete(node_id: str):
        # Рекурсивное удаление всех потомков
        children = db.session.query(ModelStructureNode).filter_by(parent_id=node_id).all()
        for child in children:
            StructureService._cascade_delete(child.id)

        node = db.session.get(ModelStructureNode, node_id)
        if node:
            db.session.delete(node)


structure_service = StructureService()