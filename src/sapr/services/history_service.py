from datetime import datetime
from typing import Optional
from src.db import db
from src.orm.orm_sapr import History
from src.sapr.exceptions import InvalidHistoryFilterError


class HistoryService:
    @staticmethod
    def get_history(
        user_id: Optional[int] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[History]:
        # Получает историю с фильтрацией 
        if limit < 1 or limit > 1000:
            raise InvalidHistoryFilterError('limit должен быть от 1 до 1000')
        
        if offset < 0:
            raise InvalidHistoryFilterError('offset не может быть отрицательным')
        
        if method is not None and method.upper() not in ['GET', 'POST', 'PUT', 'DELETE']:
            raise InvalidHistoryFilterError(f'Недопустимый HTTP метод: {method}')
        
        if start_date and end_date and start_date > end_date:
            raise InvalidHistoryFilterError('start_date не может быть позже end_date')

        query = History.query

        if user_id is not None:
            query = query.filter(History.user_id == user_id)
        
        if endpoint is not None:
            query = query.filter(History.endpoint.like(f'%{endpoint}%'))
        
        if method is not None:
            query = query.filter(History.method == method.upper())
        
        if start_date is not None:
            query = query.filter(History.timestamp >= start_date)
        
        if end_date is not None:
            query = query.filter(History.timestamp <= end_date)

        return query.order_by(History.timestamp.desc()).offset(offset).limit(limit).all()


history_service = HistoryService()
