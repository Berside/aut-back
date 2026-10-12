# type_service.py
from src.db import db
from src.orm.orm_sapr import PartType, PartCategory
from src.sapr.exceptions import TypeNotFoundError, CategoryNotFoundError


class TypeService:
    def get_types(self, category_id: int = None) -> list[PartType]:
        query = PartType.query
        if category_id:
            query = query.filter(PartType.category_id == category_id)
        return query.all()

    def create_type(self, name: str, category_id: int = None) -> PartType:
        if category_id:
            category = PartCategory.query.get(category_id)
            if not category:
                raise CategoryNotFoundError()
        
        part_type = PartType(name=name, category_id=category_id)
        db.session.add(part_type)
        db.session.commit()
        return part_type

    def update_type(self, type_id: int, name: str = None, category_id: int = None) -> PartType:
        part_type = PartType.query.get(type_id)
        if not part_type:
            raise TypeNotFoundError()
        
        if category_id is not None:
            category = PartCategory.query.get(category_id)
            if not category:
                raise CategoryNotFoundError()
            part_type.category_id = category_id
        
        if name is not None:
            part_type.name = name
        
        db.session.commit()
        return part_type

    def delete_type(self, type_id: int) -> dict:
        part_type = PartType.query.get(type_id)
        if not part_type:
            raise TypeNotFoundError()
        
        db.session.delete(part_type)
        db.session.commit()
        return {'success': True, 'type_id': type_id}


type_service = TypeService()