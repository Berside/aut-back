#!/usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
import pytest
from src.db import db
from src.orm.orm_sapr import Item, BomLine, RepairTool, AssemblyItem, Project
from src.tests.util_test import UtilTest, app_context

utilTest = UtilTest(write_data_file=False)


@pytest.mark.usefixtures('app_context')
class TestItemRoutes(unittest.TestCase):
    
    def setUp(self):
        self.tearDown()

    def tearDown(self):
        RepairTool.query.delete()
        BomLine.query.delete()
        Item.query.delete()
        db.session.commit()

    def test_create_Item_success(self):
        response = utilTest.client.post('/api/sapr/items', json={
            'article': 'ART-001',
            'name': 'Отвертка',
            'description': 'Крестовая отвертка',
            'note': 'Использовать осторожно',
            'photo_path': '/photos/screwdriver.jpg',
            'stock_quantity': 10
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == 'Отвертка'
        assert data['stock_quantity'] == 10
        assert 'id' in data

    def test_create_Item_duplicate_article(self):
        utilTest.client.post('/api/sapr/items', json={'article': 'ART-DUP', 'name': 'Молоток', 'stock_quantity': 5})
        response = utilTest.client.post('/api/sapr/items', json={'article': 'ART-DUP', 'name': 'Молоток другой', 'stock_quantity': 3})
        assert response.status_code == 409
        data = response.get_json()
        assert data['error_code'] == 'ITEM_ALREADY_EXISTS'


    def test_get_Items_with_pagination(self):
        for i in range(25):
            utilTest.client.post('/api/sapr/items', json={
                'article': f'ART-{i:03d}',
                'name': f'Инструмент {i}', 
                'stock_quantity': i}
            )
        
        response = utilTest.client.get('/api/sapr/items?page=1&per_page=10')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['items']) == 10
        assert data['total'] == 25
        assert data['page'] == 1
        assert data['per_page'] == 10

    def test_get_Item_by_id(self):
        create_response = utilTest.client.post('/api/sapr/items', json={
            'article': 'ART-DUP',
            'name': 'Ключ', 
            'stock_quantity': 3
        })
        Item_id = create_response.get_json()['id']
        
        response = utilTest.client.get(f'/api/sapr/items/{Item_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Ключ'

    def test_get_Item_not_found(self):
        response = utilTest.client.get('/api/sapr/items/999999')
        assert response.status_code == 404

    def test_update_Item(self):
        create_response = utilTest.client.post('/api/sapr/items', json={
            'article': 'ART-DUP',
            'name': 'Пила', 
            'stock_quantity': 2})
        Item_id = create_response.get_json()['id']
        
        response = utilTest.client.put(f'/api/sapr/items/{Item_id}', json={
            'article': 'ART-DUP',
            'name': 'Пила обновленная',
            'stock_quantity': 5
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Пила обновленная'
        assert data['stock_quantity'] == 5

    def test_delete_Item(self):
        create_response = utilTest.client.post('/api/sapr/items', json={
            'article': 'ART-DUP',
            'name': 'Дрель', 
            'stock_quantity': 1
        })
        Item_id = create_response.get_json()['id']
        
        response = utilTest.client.delete(f'/api/sapr/items/{Item_id}')
        assert response.status_code == 200
        
        get_response = utilTest.client.get(f'/api/sapr/items/{Item_id}')
        assert get_response.status_code == 404

    def test_get_item_bom_tree_success(self):
        root_item = Item(article='ASM-001', name='Сборка Двигатель', stock_quantity=10)
        child_1 = Item(article='PRT-001', name='Поршень', stock_quantity=50)
        child_2 = Item(article='PRT-002', name='Болт М10', stock_quantity=100)
        db.session.add_all([root_item, child_1, child_2])
        db.session.commit()

        link_1 = BomLine(parent_item_id=root_item.id, child_item_id=child_1.id, quantity=4.0)
        link_2 = BomLine(parent_item_id=root_item.id, child_item_id=child_2.id, quantity=12.0)
        db.session.add_all([link_1, link_2])
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/items/{root_item.id}/bom-tree')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['id'] == root_item.id
        assert data['article'] == 'ASM-001'
        assert data['quantity'] == 1.0  
        assert len(data['children']) == 2

        child_articles = [c['article'] for c in data['children']]
        assert 'PRT-001' in child_articles
        assert 'PRT-002' in child_articles

        bolt_data = next(c for c in data['children'] if c['article'] == 'PRT-002')
        assert bolt_data['quantity'] == 12.0

    def test_get_item_bom_tree_leaf_node(self):
        item = Item(article='PRT-999', name='Одиночная гайка', stock_quantity=500)
        db.session.add(item)
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/items/{item.id}/bom-tree')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == item.id
        assert data['quantity'] == 1.0
        assert data['children'] == []


    def test_get_item_bom_tree_not_found(self):
        response = utilTest.client.get('/api/sapr/items/999999/bom-tree')
        assert response.status_code == 404
        data = response.get_json()
        assert 'error_code' in data 
        assert data['error_code'] == 'ITEM_NOT_FOUND'

    def test_get_item_repair_tools_success(self):
        device = Item(article='DEV-001', name='Насос центробежный', stock_quantity=5)
        wrench = Item(article='TOOL-WRENCH', name='Ключ гаечный 10мм', stock_quantity=15)
        screwdriver = Item(article='TOOL-SCREW', name='Отвертка крестовая', stock_quantity=8)
        db.session.add_all([device, wrench, screwdriver])
        db.session.commit()

        db.session.add(RepairTool(for_item_id=device.id, tool_item_id=wrench.id, quantity=1.0))
        db.session.add(RepairTool(for_item_id=device.id, tool_item_id=screwdriver.id, quantity=2.0))
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/items/{device.id}/repair-tools')

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2

        articles = [t['article'] for t in data]
        assert 'TOOL-WRENCH' in articles
        assert 'TOOL-SCREW' in articles

        wrench_data = next(t for t in data if t['article'] == 'TOOL-WRENCH')
        assert wrench_data['quantity'] == 1.0
        assert wrench_data['stock_quantity'] == 15
        assert wrench_data['name'] == 'Ключ гаечный 10мм'

        screwdriver_data = next(t for t in data if t['article'] == 'TOOL-SCREW')
        assert screwdriver_data['quantity'] == 2.0
        assert screwdriver_data['stock_quantity'] == 8

    def test_get_item_repair_tools_empty(self):
        device = Item(article='DEV-002', name='Простая деталь', stock_quantity=10)
        db.session.add(device)
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/items/{device.id}/repair-tools')

        assert response.status_code == 200
        data = response.get_json()
        assert data == []

    def test_get_item_repair_tools_not_found(self):
        response = utilTest.client.get('/api/sapr/items/999999/repair-tools')
        assert response.status_code == 404
        data = response.get_json()
        assert 'error_code' in data

    def test_get_item_repair_tools_fractional_quantity(self):
        device = Item(article='DEV-003', name='Сложный механизм', stock_quantity=1)
        tool = Item(article='TOOL-SPECIAL', name='Спец-инструмент', stock_quantity=3)
        db.session.add_all([device, tool])
        db.session.commit()

        db.session.add(RepairTool(for_item_id=device.id, tool_item_id=tool.id, quantity=0.5))
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/items/{device.id}/repair-tools')

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['quantity'] == 0.5
        assert data[0]['article'] == 'TOOL-SPECIAL'

    def test_search_items_by_name(self):
        item1 = Item(article='ART-001', name='Корпус насоса', unit='шт', stock_quantity=10)
        item2 = Item(article='ART-002', name='Вал двигателя', unit='шт', stock_quantity=5)
        item3 = Item(article='ART-003', name='Крышка корпуса', unit='шт', stock_quantity=20)
        
        db.session.add_all([item1, item2, item3])
        db.session.commit()

        response = utilTest.client.get('/api/sapr/items/search?q=корпус')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['total'] == 2
        assert len(data['items']) == 2
        
        names = [item['name'] for item in data['items']]
        assert 'Корпус насоса' in names
        assert 'Крышка корпуса' in names

    def test_search_items_by_article(self):
        item1 = Item(article='ART-001', name='Корпус насоса', unit='шт', stock_quantity=10)
        item2 = Item(article='ART-002', name='Вал двигателя', unit='шт', stock_quantity=5)
        
        db.session.add_all([item1, item2])
        db.session.commit()

        response = utilTest.client.get('/api/sapr/items/search?q=ART-001')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['total'] == 1
        assert data['items'][0]['article'] == 'ART-001'

    def test_search_items_empty_query(self):
        response = utilTest.client.get('/api/sapr/items/search?q=')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_search_items_no_results(self):
        response = utilTest.client.get('/api/sapr/items/search?q=несуществующий')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['total'] == 0
        assert len(data['items']) == 0

    def test_search_items_with_pagination(self):
        items = [
            Item(article=f'ART-{i:03d}', name=f'Деталь {i}', unit='шт', stock_quantity=i)
            for i in range(1, 11)
        ]
        db.session.add_all(items)
        db.session.commit()

        response = utilTest.client.get('/api/sapr/items/search?q=деталь&page=1&per_page=3')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['total'] == 10
        assert data['page'] == 1
        assert data['per_page'] == 3
        assert len(data['items']) == 3

    def test_search_items_with_project_filter(self):
        project = Project(name='Тестовый проект', description='Тест')
        db.session.add(project)
        db.session.commit()

        item1 = Item(article='ART-001', name='Корпус', unit='шт', stock_quantity=10)
        item2 = Item(article='ART-002', name='Вал', unit='шт', stock_quantity=5)
        db.session.add_all([item1, item2])
        db.session.commit()

        assembly = AssemblyItem(
            project_id=project.id,
            name='Узел 1',
            item_id=item1.id
        )
        db.session.add(assembly)
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/items/search?q=корпус&project_id={project.id}')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['total'] == 1
        assert data['items'][0]['is_linked'] == True

    def test_search_items_is_linked_flag(self):
        project = Project(name='Тестовый проект', description='Тест')
        db.session.add(project)
        db.session.commit()

        item1 = Item(article='ART-001', name='Деталь 1', unit='шт', stock_quantity=10)
        item2 = Item(article='ART-002', name='Деталь 2', unit='шт', stock_quantity=5)
        db.session.add_all([item1, item2])
        db.session.commit()

        assembly = AssemblyItem(
            project_id=project.id,
            name='Узел 1',
            item_id=item1.id
        )
        db.session.add(assembly)
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/items/search?q=деталь&project_id={project.id}')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Проверяем флаги is_linked
        items_dict = {item['id']: item for item in data['items']}
        assert items_dict[item1.id]['is_linked'] == True
        assert items_dict[item2.id]['is_linked'] == False
