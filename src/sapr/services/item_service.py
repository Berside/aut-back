from typing import Optional
from sqlalchemy import or_
from src.db import db
from src.orm.orm_sapr import Item, BomLine, RepairTool, AssemblyItem
from src.sapr.exceptions import ItemAlredyExists, ItemDeletionError, ItemNotFoundError, CyclicDependencyError


class ItemService:

    @staticmethod
    def _is_ancestor(potential_ancestor_id: int, descendant_id: int) -> bool:
        # Проверяет является ли potential_ancestor_id предком descendant_id в BOM
        current_id = descendant_id
        while current_id is not None:
            if current_id == potential_ancestor_id:
                return True
            parent_link = BomLine.query.filter_by(child_item_id=current_id).first()
            current_id = parent_link.parent_item_id if parent_link else None
        return False

    @staticmethod
    def get_item(item_id: int) -> Item:
        # Получить инструмент по id
        item = Item.query.get(item_id)
        if not item:
            raise ItemNotFoundError()
        return item

    @staticmethod
    def get_all_items(page: int = 1, per_page: int = 20) -> dict:
        # Получает список инструментов с пагинацией
        pagination = Item.query.order_by(Item.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {
            'items': pagination.items,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }

    @staticmethod
    def create_item(
        article: str,
        name: str,
        standard: Optional[str] = None,
        unit: str = 'шт',
        description: Optional[str] = None,
        note: Optional[str] = None,
        photo_path: Optional[str] = None,
        stock_quantity: int = 0
    ) -> Item:
        # Создает новый инструмент
        existing = Item.query.filter_by(article=article).first()
        if existing:
            raise ItemAlredyExists()

        item = Item(
            article=article,
            name=name,
            standard=standard,
            unit=unit,
            description=description,
            note=note,
            photo_path=photo_path,
            stock_quantity=stock_quantity
        )

        db.session.add(item)
        db.session.commit()

        return item
    @staticmethod
    def update_item(
        item_id: int,
        article: Optional[str] = None,
        name: Optional[str] = None,
        standard: Optional[str] = None,
        unit: Optional[str] = None,
        description: Optional[str] = None,
        note: Optional[str] = None,
        photo_path: Optional[str] = None,
        stock_quantity: Optional[int] = None
    ) -> Item:
        item = Item.query.get(item_id)
        if not item:
            raise ItemNotFoundError()

        if article is not None:
            existing = Item.query.filter(Item.article == article, Item.id != item_id).first()
            if existing:
                raise ItemAlredyExists()
            item.article = article

        if name is not None:
            item.name = name

        if standard is not None:
            item.standard = standard
        
        if unit is not None:
            item.unit = unit

        if note is not None:
            item.note = note

        if photo_path is not None:
            item.photo_path = photo_path

        if description is not None:
            item.description = description

        if stock_quantity is not None:
            item.stock_quantity = stock_quantity

        db.session.commit()
        return item

    @staticmethod
    def delete_item(item_id: int) -> bool:
        # Удаляет инструмент
        item = Item.query.get(item_id)
        if not item:
            raise ItemNotFoundError()

        try:
            db.session.delete(item)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise ItemDeletionError(f'Ошибка при удалении инструмента: {str(e)}')

    @staticmethod
    def create_bom_line(parent_item_id: int, child_item_id: int, quantity: float) -> BomLine: 
        parent_item = Item.query.get(parent_item_id)
        if not parent_item:
            raise ItemNotFoundError()

        child_item = Item.query.get(child_item_id)
        if not child_item:
            raise ItemNotFoundError()

        if ItemService._is_ancestor(child_item_id, parent_item_id):
            raise CyclicDependencyError()


        existing = BomLine.query.filter_by(
            parent_item_id=parent_item_id,
            child_item_id=child_item_id
        ).first()
        if existing:
            raise ItemAlredyExists()

        bom_line = BomLine(
            parent_item_id=parent_item_id,
            child_item_id=child_item_id,
            quantity=quantity
        )
        db.session.add(bom_line)
        db.session.commit()

        return bom_line

    @staticmethod
    def get_bom_tree(item_id: int) -> dict:
        # Получает дерево спецификации (BOM) для изделия
        root_item = Item.query.get(item_id)
        if not root_item:
            raise ItemNotFoundError()
        
        def build_node(current_item: Item) -> dict:
            # Базовая структура узла
            node = {
                'id': current_item.id,
                'article': current_item.article,
                'name': current_item.name,
                'quantity': None,
                'children': []
            }

            bom_lines = BomLine.query.filter_by(parent_item_id=current_item.id).all()

            for line in bom_lines:
                child_item = Item.query.get(line.child_item_id)
                if child_item:
                    child_node = build_node(child_item)
                    child_node['quantity'] = float(line.quantity)
                    node['children'].append(child_node)

            return node
        

        tree_data = build_node(root_item)
        tree_data['quantity'] = 1.0

        return tree_data

    @staticmethod
    def get_repair_tools_for_item(item_id: int) -> list[dict]:
        # Получить список инструментов, необходимых для ремонта изделия
        item = Item.query.get(item_id)
        if not item:
            raise ItemNotFoundError()

        # Ищем все связи ремонта для этого изделия 
        repair_links = RepairTool.query.filter_by(for_item_id=item_id).all()
        if not repair_links:
            return []

        tool_ids = [link.tool_item_id for link in repair_links]
        quantities = {link.tool_item_id: float(link.quantity) for link in repair_links}

        tools = Item.query.filter(Item.id.in_(tool_ids)).all()

        result = []
        for tool in tools:
            result.append({
                'tool_id': tool.id,
                'article': tool.article,
                'name': tool.name,
                'quantity': quantities[tool.id],
                'stock_quantity': tool.stock_quantity
            })

        return result

    @staticmethod
    def search_items(query: str, project_id: int = None, page: int = 1, per_page: int = 50) -> dict:
        if not query or not query.strip():
            return {'items': [], 'total': 0, 'page': page, 'per_page': per_page}

        search_term = f'%{query.strip()}%'

        # Базовый запрос
        stmt = Item.query.filter(
            or_(
                Item.name.ilike(search_term),
                Item.article.ilike(search_term),
                Item.standard.ilike(search_term)
            )
        )

        total = stmt.count()

        # Пагинация
        offset = (page - 1) * per_page
        items = stmt.offset(offset).limit(per_page).all()

        linked_item_ids = set()
        if project_id and items:
            item_ids_on_page = [i.id for i in items]
            linked_rows = db.session.query(AssemblyItem.item_id).filter(
                AssemblyItem.project_id == project_id,
                AssemblyItem.item_id.isnot(None),
                AssemblyItem.item_id.in_(item_ids_on_page)
            ).all()
            linked_item_ids = {row[0] for row in linked_rows if row[0] is not None}

        return {
            'items': [
                {
                    'id': i.id,
                    'article': i.article,
                    'name': i.name,
                    'standard': i.standard,
                    'unit': i.unit,
                    'stock_quantity': i.stock_quantity,
                    'is_linked': i.id in linked_item_ids,
                }
                for i in items
            ],
            'total': total,
            'page': page,
            'per_page': per_page,
        }



item_service = ItemService()
        
        
        
