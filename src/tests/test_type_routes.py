#!/usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
import pytest
import json
from src.db import db
from src.orm.orm_sapr import PartType, PartCategory
from src.tests.util_test import UtilTest, app_context
from src.sapr.routes import sapr_bp

utilTest = UtilTest(write_data_file=False)

if not any(rule.endpoint.startswith('sapr.') for rule in utilTest.app.url_map.iter_rules()):
    utilTest.app.register_blueprint(sapr_bp)


@pytest.mark.usefixtures('app_context')
class TestType(unittest.TestCase):
    
    def setUp(self):
        self.tearDown()

        self.category = PartCategory(name='Тестовая категория', sort_order=1)
        db.session.add(self.category)
        db.session.commit()
        self.category_id = self.category.id

    def tearDown(self):
        PartType.query.delete()
        PartCategory.query.delete()
        db.session.commit()

    def test_create_type_success(self):
        # Создание типа
        response = utilTest.client.post('/api/sapr/parts/types',
            json={
                'name': 'Стандартная деталь',
                'category_id': self.category_id
            }
        )
        assert response.status_code == 201

    def test_get_types_success(self):
        # Получение списка всех типов
        type1 = PartType(name='Тип 1', category_id=self.category_id)
        type2 = PartType(name='Тип 2', category_id=self.category_id)
        db.session.add_all([type1, type2])
        db.session.commit()

        response = utilTest.client.get('/api/sapr/parts/types')
        
        assert response.status_code == 200

    def test_get_types_filtered_by_category(self):
        # Получение типов с фильтрацией по категории
        category2 = PartCategory(name='Другая категория', sort_order=2)
        db.session.add(category2)
        db.session.commit()
        
        PartType(name='Тип для кат 1', category_id=self.category_id)
        PartType(name='Тип для кат 2', category_id=category2.id)
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/parts/types?category_id={self.category_id}')
        
        assert response.status_code == 200

    def test_update_type_success(self):
        # Обновление типа
        part_type = PartType(name='Старое имя', category_id=self.category_id)
        db.session.add(part_type)
        db.session.commit()
        type_id = part_type.id

        response = utilTest.client.put(f'/api/sapr/parts/types/{type_id}',
            json={'name': 'Новое имя типа'}
        )
        
        assert response.status_code == 200

    def test_update_type_not_found(self):
        # Обновление несуществующего типа
        response = utilTest.client.put('/api/sapr/parts/types/999999',
            json={'name': 'Тест'}
        )
        assert response.status_code == 404

    def test_delete_type_success(self):
        # Удаление типа
        part_type = PartType(name='Тип на удаление', category_id=self.category_id)
        db.session.add(part_type)
        db.session.commit()
        type_id = part_type.id

        response = utilTest.client.delete(f'/api/sapr/parts/types/{type_id}')
        
        assert response.status_code == 200

    def test_delete_type_not_found(self):
        # Удаление несуществующего типа
        response = utilTest.client.delete('/api/sapr/parts/types/999999')
        assert response.status_code == 404