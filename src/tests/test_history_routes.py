#!/usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
import pytest
from datetime import datetime, timedelta
from src.db import db
from src.orm.orm_sapr import History
from src.tests.util_test import UtilTest, app_context

utilTest = UtilTest(write_data_file=False)


@pytest.mark.usefixtures('app_context')
class TestHistoryRoutes(unittest.TestCase):
    def setUp(self):
        self.tearDown()

        self.history_entries = [
            History(
                user_id=1,
                endpoint='/api/sapr/models/1',
                method='GET',
                timestamp=datetime.utcnow() - timedelta(days=5)
            ),
            History(
                user_id=1,
                endpoint='/api/sapr/models/2',
                method='GET',
                timestamp=datetime.utcnow() - timedelta(days=3)
            ),
            History(
                user_id=2,
                endpoint='/api/sapr/projects/1',
                method='POST',
                timestamp=datetime.utcnow() - timedelta(days=1)
            ),
            History(
                user_id=1,
                endpoint='/api/sapr/tree',
                method='POST',
                timestamp=datetime.utcnow()
            ),
        ]

        for entry in self.history_entries:
            db.session.add(entry)

        db.session.commit()

    def tearDown(self):
        History.query.delete()
        db.session.commit()
    def test_get_history_all(self):
        # Получить все записи истории
        response = utilTest.client.get('/api/sapr/history')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data) == 4
        assert data[0]['endpoint'] == '/api/sapr/tree'

    def test_get_history_filter_by_user_id(self):
        # Фильтрация по user_id
        response = utilTest.client.get('/api/sapr/history?user_id=1')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data) == 3
        
        for entry in data:
            assert entry['user_id'] == 1

    def test_get_history_filter_by_endpoint(self):
        # Фильтрация по endpoint
        response = utilTest.client.get('/api/sapr/history?endpoint=/api/sapr/models')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data) == 2
        
        for entry in data:
            assert '/api/sapr/models' in entry['endpoint']

    def test_get_history_filter_by_method(self):
        # Фильтрация по method
        response = utilTest.client.get('/api/sapr/history?method=POST')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data) == 2
        
        for entry in data:
            assert entry['method'] == 'POST'

    def test_get_history_filter_by_date_range(self):
        # Фильтрация по периоду дат
        start_date = (datetime.utcnow() - timedelta(days=4)).isoformat()
        end_date = (datetime.utcnow() - timedelta(days=2)).isoformat()
        
        response = utilTest.client.get(f'/api/sapr/history?start_date={start_date}&end_date={end_date}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data) == 1 

    def test_get_history_pagination(self):
        # Пагинация
        response = utilTest.client.get('/api/sapr/history?limit=2&offset=1')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data) == 2 
        assert data[0]['endpoint'] == '/api/sapr/projects/1'

    def test_get_history_invalid_limit(self):
        # Некорректный limit
        response = utilTest.client.get('/api/sapr/history?limit=9999')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['error_code'] == 'INVALID_HISTORY_FILTER'

    def test_get_history_invalid_offset(self):
        # Отрицательный offset
        response = utilTest.client.get('/api/sapr/history?offset=-1')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['error_code'] == 'INVALID_HISTORY_FILTER'

    def test_get_history_invalid_method(self):
        # Некорректный HTTP метод
        response = utilTest.client.get('/api/sapr/history?method=INVALID')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['error_code'] == 'INVALID_HISTORY_FILTER'

    def test_get_history_invalid_date_format(self):
        # Некорректный формат даты
        response = utilTest.client.get('/api/sapr/history?start_date=invalid_date')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['error_code'] == 'INVALID_HISTORY_FILTER'

    def test_get_history_start_date_after_end_date(self):
        # start_date позже end_date
        start_date = datetime.utcnow().isoformat()
        end_date = (datetime.utcnow() - timedelta(days=10)).isoformat()
        
        response = utilTest.client.get(f'/api/sapr/history?start_date={start_date}&end_date={end_date}')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['error_code'] == 'INVALID_HISTORY_FILTER'
    
        