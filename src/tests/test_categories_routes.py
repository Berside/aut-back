#!/usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
import pytest
import json
from src.db import db
from src.orm.orm_sapr import PartCategory
from src.tests.util_test import UtilTest, app_context
from src.sapr.routes import sapr_bp

utilTest = UtilTest(write_data_file=False)

if not any(rule.endpoint.startswith('sapr.') for rule in utilTest.app.url_map.iter_rules()):
    utilTest.app.register_blueprint(sapr_bp)


@pytest.mark.usefixtures('app_context')
class TestPartCategory(unittest.TestCase):
    
    def setUp(self):
        self.tearDown()

    def tearDown(self):
        PartCategory.query.delete()
        db.session.commit()

    def test_create_PartCategory_success(self):
        # Создание категории
        response = utilTest.client.post('/api/sapr/parts/categories',
            json={
                'name': 'Двигатели',
                'sort_order': 1
            })

        assert response.status_code == 201

    def test_create_PartCategory_with_parent(self):
        # Создание дочерней категории
        parent = PartCategory(name='Родительская категория', sort_order=0)
        db.session.add(parent)
        db.session.commit()

        response = utilTest.client.post('/api/sapr/parts/categories',
            json={
                'name': 'Дочерняя категория',
                'parent_id': parent.id,
                'sort_order': 1
            })
        assert response.status_code == 201

    def test_get_categories_tree(self):
        # Получение дерева категорий
        parent = PartCategory(name='Родитель', sort_order=0)
        db.session.add(parent)
        db.session.commit()

        child = PartCategory(name='Ребенок', sort_order=1)
        db.session.add(child)
        db.session.commit()

        response = utilTest.client.get('/api/sapr/parts/categories')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data['categories'], list)

    def test_update_PartCategory_success(self):
        # Обновление категории
        category = PartCategory(name='Старое имя', sort_order=0)
        db.session.add(category)
        db.session.commit()
        category_id = category.id

        response = utilTest.client.put(f'/api/sapr/parts/categories/{category_id}',
            json={
                'name': 'Новое имя',
                'sort_order': 5
            })
        
        assert response.status_code == 200

    def test_update_PartCategory_not_found(self):
        # Обновление несуществующей категории
        response = utilTest.client.put('/api/sapr/parts/categories/999999',
            json={'name': 'Тест'})
        assert response.status_code == 404

    def test_delete_PartCategory_success(self):
        # Удаление категории
        category = PartCategory(name='Категория для удаления', sort_order=0)
        db.session.add(category)
        db.session.commit()
        category_id = category.id

        response = utilTest.client.delete(f'/api/sapr/parts/categories/{category_id}')
        assert response.status_code == 200

    def test_delete_PartCategory_not_found(self):
        # Удаление несуществующей категории
        response = utilTest.client.delete('/api/sapr/parts/categories/999999')
        assert response.status_code == 404

    def test_delete_PartCategory_with_children_fails(self):
        # Удаление категории, у которой есть наследники
        parent = PartCategory(name='Родитель', sort_order=0)
        db.session.add(parent)
        db.session.commit()

        child = PartCategory(name='Наследник', parent_id=parent.id, sort_order=1)
        db.session.add(child)
        db.session.commit()

        response = utilTest.client.delete(f'/api/sapr/parts/categories/{parent.id}')

        assert response.status_code == 409

    def test_create_PartCategory_cycle_fails(self):
        # Попытка сделать категорию родителем самой себя 
        category = PartCategory(name='Тестовая категория', sort_order=0)
        db.session.add(category)
        db.session.commit()
        category_id = category.id

        response = utilTest.client.put(f'/api/sapr/parts/categories/{category_id}',
            json={'parent_id': category_id}
        )
        
        assert response.status_code == 400                                                                                      