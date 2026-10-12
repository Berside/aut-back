#!/usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
import pytest
import json
from src.db import db
from src.orm.orm_sapr import Project, AssemblyItem, Part, Item
from src.tests.util_test import UtilTest, app_context
from src.sapr.routes import sapr_bp

utilTest = UtilTest(write_data_file=False)

if not any(rule.endpoint.startswith('sapr.') for rule in utilTest.app.url_map.iter_rules()):
    utilTest.app.register_blueprint(sapr_bp)


@pytest.mark.usefixtures('app_context')
class TestAssemblyItem(unittest.TestCase):
    def setUp(self):
        self.project = Project(name='Тестовый проект', description='Описание')
        db.session.add(self.project)
        db.session.commit()
        self.project_id = self.project.id

        self.part = Part(name='Тестовая деталь', description='TEST_001')
        db.session.add(self.part)
        db.session.commit()
        self.part_id = self.part.id

        self.item = Item(article='ART-TEST-001', name='Тестовое изделие', unit='шт', stock_quantity=10)
        db.session.add(self.item)
        db.session.commit()
        self.item_id = self.item.id

    def tearDown(self):
        AssemblyItem.query.delete()
        Item.query.delete()
        Part.query.delete()
        Project.query.delete()
        db.session.commit()

    def test_create_assembly_item_success(self):
        # Создание элемента сборки
        response = utilTest.client.post(f'/api/sapr/projects/{self.project_id}/assembly-items',
            json={
            'name': 'Корпус двигателя',
            'order': 1,
            'part_id': self.part_id 
        })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'Корпус двигателя'
        assert data['project_id'] == self.project_id
        assert data['part_id'] == self.part_id

    def test_create_assembly_item_project_not_found(self):
        # Создание элемента сборки для несуществующего проекта
        response = utilTest.client.post('/api/sapr/projects/999999/assembly-items',
            json={'name': 'Тест', 'order': 1}
        )
        
        assert response.status_code == 404

    def test_update_assembly_item_success(self):
        # Обновление существующего элемента сборки
        item = AssemblyItem(
            project_id=self.project_id,
            name='Старое название',
            order=1
        )
        db.session.add(item)
        db.session.commit()
        item_id = item.id

        response = utilTest.client.put(f'/api/sapr/assembly-items/{item_id}',
            json={
                'name': 'Новое название',
                'order': 5
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Новое название'
        assert data['order'] == 5

    def test_update_assembly_item_not_found(self):
        # Обновление несуществующего элемента
        response = utilTest.client.put('/api/sapr/assembly-items/999999',
            json={'name': 'Тест'}
        )
        assert response.status_code == 404

    def test_delete_assembly_item_success(self):
        # Удаление элемента сборки
        item = AssemblyItem(
            project_id=self.project_id,
            name='Элемент на удаление',
            order=1
        )
        db.session.add(item)
        db.session.commit()
        item_id = item.id

        response = utilTest.client.delete(f'/api/sapr/assembly-items/{item_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Элемент сборки удалён'

        deleted_item = db.session.query(AssemblyItem).filter_by(id=item_id).first()
        assert deleted_item is None

    def test_delete_assembly_item_not_found(self):
        # Удаление несуществующего элемента
        response = utilTest.client.delete('/api/sapr/assembly-items/999999')
        assert response.status_code == 404

    def test_import_part_to_assembly(self):
        # Импорт детали в сборку

        response = utilTest.client.post('/api/sapr/assembly/import-part',
            json= {
            'project_id': self.project_id,
            'part_id': self.part_id,
            'quantity': 2,
            'position': {'x': 10, 'y': 20, 'z': 30},
            'rotation': {'x': 0, 'y': 90, 'z': 0}
        })

        assert response.status_code == 201
        data = json.loads(response.data)

        assert data['success'] is True
        assert 'assembly_item' in data
        assert 'link' in data
        assert data['link']['quantity'] == 2
        assert data['link']['position']['x'] == 10

    def test_import_part_to_assembly_part_not_found(self):
        # Импорт несуществующей детали
        response = utilTest.client.post('/api/sapr/assembly/import-part',
            json={
                'project_id': self.project_id,
                'part_id': 999999
            })
        assert response.status_code == 404

    def test_link_item_to_assembly_item_success(self):
        item = AssemblyItem(project_id=self.project_id, name='Без изделия', order=1)
        db.session.add(item)
        db.session.commit()
        
        response = utilTest.client.post(f'/api/sapr/assembly-items/{item.id}/link-item',
            json={'item_id': self.item_id}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['item_id'] == self.item_id
        assert data['item'] is not None
        assert data['item']['article'] == 'ART-TEST-001'
        
        db_item = db.session.query(AssemblyItem).filter_by(id=item.id).first()
        assert db_item.item_id == self.item_id

    def test_unlink_item_from_assembly_item_success(self):
        item = AssemblyItem(project_id=self.project_id, name='С изделием', order=1, item_id=self.item_id)
        db.session.add(item)
        db.session.commit()
        
        response = utilTest.client.delete(f'/api/sapr/assembly-items/{item.id}/link-item')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['item_id'] is None
        assert data['item'] is None
        
        db_item = db.session.query(AssemblyItem).filter_by(id=item.id).first()
        assert db_item.item_id is None

    def test_link_non_existent_item(self):
        item = AssemblyItem(project_id=self.project_id, name='Тест', order=1)
        db.session.add(item)
        db.session.commit()
        
        response = utilTest.client.post(f'/api/sapr/assembly-items/{item.id}/link-item',
            json={'item_id': 999999}
        )
        assert response.status_code == 404

    def test_get_assembly_tree_with_item(self):
        item = AssemblyItem(
            project_id=self.project_id,
            name='Корень с изделием',
            order=1,
            item_id=self.item_id
        )
        db.session.add(item)
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/projects/{self.project_id}/assembly-tree')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['item_id'] == self.item_id
        assert data[0]['item'] is not None
        assert data[0]['item']['article'] == 'ART-TEST-001'
        assert data[0]['item']['name'] == 'Тестовое изделие'

    def test_get_linked_item_success(self):
    
        item = Item(article='ART-LINK-01', name='Привязанная деталь', unit='шт', stock_quantity=10)
        db.session.add(item)
        db.session.commit()

        # Создаем AssemblyItem с привязкой к этому Item
        assembly_item = AssemblyItem(
            project_id=self.project_id,
            name='Элемент с привязкой',
            item_id=item.id
        )
        db.session.add(assembly_item)
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/assembly-items/{assembly_item.id}/item')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data is not None
        assert data['id'] == item.id
        assert data['article'] == 'ART-LINK-01'
        assert data['name'] == 'Привязанная деталь'
        assert data['stock_quantity'] == 10

    def test_get_linked_item_no_link(self):
        # Создаем AssemblyItem БЕЗ привязки к Item (item_id=None)
        assembly_item = AssemblyItem(
            project_id=self.project_id,
            name='Элемент без привязки',
            item_id=None
        )
        db.session.add(assembly_item)
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/assembly-items/{assembly_item.id}/item')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data is None

    def test_get_linked_item_assembly_not_found(self):
        # Пытаемся получить Item для несуществующего элемента сборки
        response = utilTest.client.get('/api/sapr/assembly-items/999999/item')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error_code' in data
        assert data['error_code'] == 'ASSEMBLY_ITEM_NOT_FOUND'
        assert data['message'] == 'Элемент сборки не найден'

    def test_get_project_assembly_tree_recursive(self):
        root = AssemblyItem(project_id=self.project_id, name='Корневой узел', order=1)
        db.session.add(root)
        db.session.commit()

        child = AssemblyItem(project_id=self.project_id, name='Дочерний узел', parent_id=root.id, order=1)
        db.session.add(child)
        db.session.commit()

        item = Item(article='ART-TEST-999', name='Тестовая деталь', unit='шт', stock_quantity=10)
        db.session.add(item)
        db.session.commit()

        grandchild = AssemblyItem(
            project_id=self.project_id, 
            name='Внучатый узел', 
            parent_id=child.id, 
            order=1, 
            item_id=item.id
        )
        db.session.add(grandchild)
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/projects/{self.project_id}/assembly-tree')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert len(data) == 1
        assert data[0]['name'] == 'Корневой узел'
        assert data[0]['item_id'] is None
        
        assert len(data[0]['children']) == 1
        assert data[0]['children'][0]['name'] == 'Дочерний узел'
        
        assert len(data[0]['children'][0]['children']) == 1
        assert data[0]['children'][0]['children'][0]['name'] == 'Внучатый узел'
        assert data[0]['children'][0]['children'][0]['item_id'] == item.id
        
        assert data[0]['children'][0]['children'][0]['item']['article'] == 'ART-TEST-999'
        assert data[0]['children'][0]['children'][0]['item']['name'] == 'Тестовая деталь'

    def test_get_project_assembly_tree_empty(self):
        # Проверяем ответ для проекта без элементов сборки
        response = utilTest.client.get(f'/api/sapr/projects/{self.project_id}/assembly-tree')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data == []

    def test_get_project_assembly_tree_multiple_roots(self):
        # Проверяем проект с несколькими корневыми элементами
        root1 = AssemblyItem(project_id=self.project_id, name='Корень 1', order=1)
        root2 = AssemblyItem(project_id=self.project_id, name='Корень 2', order=2)
        db.session.add_all([root1, root2])
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/projects/{self.project_id}/assembly-tree')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert len(data) == 2
        assert data[0]['name'] == 'Корень 1'
        assert data[1]['name'] == 'Корень 2'
        assert data[0]['children'] == []
        assert data[1]['children'] == []