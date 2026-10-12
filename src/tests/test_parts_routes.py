#!/usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
import pytest
import json
from unittest.mock import patch
from src.db import db
from src.orm.orm_sapr import Project, PartCategory, PartType, Part, Item
from src.tests.util_test import UtilTest, app_context
from src.sapr.routes import sapr_bp

utilTest = UtilTest(write_data_file=False)

if not any(rule.endpoint.startswith('sapr.') for rule in utilTest.app.url_map.iter_rules()):
    utilTest.app.register_blueprint(sapr_bp)


@pytest.mark.usefixtures('app_context')
class TestPart(unittest.TestCase):
    
    def setUp(self):
        self.tearDown()

        self.project = Project(name='Тестовый проект', description='Описание')
        db.session.add(self.project)
        db.session.commit()
        self.project_id = self.project.id

        self.category = PartCategory(name='Тестовая категория', sort_order=1)
        db.session.add(self.category)
        db.session.commit()
        self.category_id = self.category.id

        self.part_type = PartType(name='Тестовый тип')
        db.session.add(self.part_type)
        db.session.commit()
        self.type_id = self.part_type.id

    def tearDown(self):
        Part.query.delete()
        Item.query.delete()
        PartType.query.delete()
        PartCategory.query.delete()
        Project.query.delete()
        db.session.commit()
    
    def test_create_part_success(self):
        # Создание детали
        response = utilTest.client.post(f'/api/sapr/parts',
            json={
                'name': 'Тестовая деталь',
                'part_number': 'TEST_001',
                'project_id': self.project_id,
                'category_id': self.category_id,
                'type_id': self.type_id,
                'is_standard': True
            })
        assert response.status_code == 201

    def test_get_parts_list(self):
        # Получение списка деталей с фильтрацией
        part = Part(
            name='Деталь для списка',
            part_number='LIST_001',
            category_id=self.category_id,
            type_id=self.type_id
        )
        db.session.add(part)
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/parts?project_id={self.project_id}')
        assert response.status_code == 200

    def test_get_single_part_by_id(self):
        # Получение одной детали по ID
        part = Part(
            name='Одиночная деталь',
            part_number='SINGLE_001',
            category_id=self.category_id,
            type_id=self.type_id
        )
        db.session.add(part)
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/parts?id={part.id}')
        assert response.status_code == 200

    def test_update_part_success(self):
        # Обновление детали
        part = Part(
            name='Старое имя',
            part_number='UPDATE_001',
            category_id=self.category_id,
            type_id=self.type_id
        )
        db.session.add(part)
        db.session.commit()
        part_id = part.id

        response = utilTest.client.put(f'/api/sapr/parts/{part_id}',
            json={'name': 'Новое имя', 'description': 'Новое описание'})
        assert response.status_code == 200

    def test_delete_part_success(self):
        # Удаление детали
        part = Part(
            name='Деталь на удаление',
            part_number='DEL_001',
            category_id=self.category_id,
            type_id=self.type_id
        )
        db.session.add(part)
        db.session.commit()
        part_id = part.id

        response = utilTest.client.delete(f'/api/sapr/parts/{part_id}')
        assert response.status_code == 200

    @patch('src.sapr.services.part_service.part_service.download_file')
    def test_download_part_file(self, mock_download):
        # Скачивание файла детали с моком сервиса
        part = Part(
            name='Деталь с файлом',
            part_number='FILE_001',
            category_id=self.category_id,
            type_id=self.type_id
        )
        db.session.add(part)
        db.session.commit()

        mock_download.return_value = ('/fake/path/test.stp', 'application/octet-stream')
        response = utilTest.client.get(f'/api/sapr/parts/{part.id}/download')
        assert response.status_code == 500
        mock_download.assert_called_once_with(part.id)

    def test_create_parts_batch_success(self):
        # Массовое создание деталей
        payload = {
            'parts': [
                {'name': 'Деталь 1', 'part_number': 'BATCH-001', 'project_id': self.project_id, 'category_id': self.category_id, 'type_id': self.type_id},
                {'name': 'Деталь 2', 'part_number': 'BATCH-002', 'project_id': self.project_id, 'category_id': self.category_id, 'type_id': self.type_id}
            ]
        }
        
        response = utilTest.client.post('/api/sapr/parts/batch', json=payload)
        
        assert response.status_code == 201

    def test_create_parts_batch_invalid_payload(self):
        # Массовое создание с невалидным ключом
        response = utilTest.client.post('/api/sapr/parts/batch', json={'wrong_key': []})
        
        assert response.status_code == 400

    def test_delete_parts_batch_success(self):
        # Массовое удаление деталей
        part1 = Part(name='P1', part_number='BDEL-1', category_id=self.category_id, type_id=self.type_id)
        part2 = Part(name='P2', part_number='BDEL-2', category_id=self.category_id, type_id=self.type_id)
        db.session.add_all([part1, part2])
        db.session.commit()
        
        response = utilTest.client.delete('/api/sapr/parts/batch', json={'ids': [part1.id, part2.id]})
        
        assert response.status_code == 200

    def test_get_part_item_success(self):
        item = Item(article='ART-BOLT-01', name='Болт М10', stock_quantity=150)
        db.session.add(item)
        db.session.commit()
        
        part = Part(
            name='Болт М10 стандартный',
            part_number='BOLT-M10-STD',
            category_id=self.category_id,
            type_id=self.type_id,
            item_id=item.id
        )
        db.session.add(part)
        db.session.commit()
        
        response = utilTest.client.get(f'/api/sapr/parts/{part.id}/item')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == item.id
        assert data['article'] == 'ART-BOLT-01'
        assert data['name'] == 'Болт М10'
        assert data['stock_quantity'] == 150

    def test_get_part_item_not_linked(self):
        part = Part(
            name='Деталь без склада',
            part_number='NO-STOCK-PART',
            category_id=self.category_id,
            type_id=self.type_id,
            item_id=None
        )
        db.session.add(part)
        db.session.commit()
        
        response = utilTest.client.get(f'/api/sapr/parts/{part.id}/item')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error_code' in data
        assert data['error_code'] == 'ITEM_NOT_FOUND'

    def test_get_part_item_part_not_found(self):
        response = utilTest.client.get('/api/sapr/parts/999999/item')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error_code'] == 'PART_NOT_FOUND'