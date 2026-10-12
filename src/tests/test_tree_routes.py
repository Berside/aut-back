#!/usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
import pytest
from src.db import db
from src.orm.orm_sapr import Project, SaprTree
from src.tests.util_test import UtilTest, app_context

utilTest = UtilTest(write_data_file=False)


@pytest.mark.usefixtures('app_context')
class TestSaprTreeRoutes(unittest.TestCase):
    
    def setUp(self):
        self.tearDown()
        # Создаем базовый проект для тестов
        self.project = Project(name='Тестовый проект для дерева', description='Описание')
        db.session.add(self.project)
        db.session.commit()
        self.project_id = self.project.id

    def tearDown(self):
        # Очищаем данные
        SaprTree.query.delete()
        Project.query.delete()
        db.session.commit()

    def test_create_tree_item_success(self):
        # Успешное создание
        response = utilTest.client.post('/api/sapr/tree', json={
            'name': 'Корневая папка',
            'item_type': 'folder',
            'project_id': self.project_id
        })
        assert response.status_code == 201

    def test_create_tree_item_validation_error(self):
        # Неуспешное создание(недопустимый item_type)
        response = utilTest.client.post('/api/sapr/tree', json={
            'name': 'Неверный тип',
            'item_type': 'invalid_type',
            'project_id': self.project_id
        })
        assert response.status_code == 400

    def test_project_tree(self):
        root = SaprTree(name='Root', item_type='folder', project_id=self.project_id, position=0)
        db.session.add(root)
        db.session.commit()

        child = SaprTree(name='Child', item_type='file', project_id=self.project_id, parent_link=root.id, position=0)
        db.session.add(child)
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/projects/{self.project_id}/tree')
        assert response.status_code == 200

        data = response.get_json()

        assert len(data) == 1
        assert data[0]['name'] == 'Root'
        assert data[0]['has_children'] is True
        assert len(data[0]['children']) == 1
        assert data[0]['children'][0]['name'] == 'Child'
        assert data[0]['children'][0]['has_children'] is False

    def test_update_tree_item(self):
        # Успешное обновление дерева
        item = SaprTree(name='Old Name', item_type='folder', project_id=self.project_id, position=0)
        db.session.add(item)
        db.session.commit()

        response = utilTest.client.put(f'/api/sapr/tree/{item.id}', json={
            'name': 'New Name',
            'position': 5
        })
        assert response.status_code == 200
        
        updated = db.session.get(SaprTree, item.id)
        assert updated.name == 'New Name'
        assert updated.position == 5

    def test_delete_tree_item_with_children_fails(self):
        parent = SaprTree(name='Parent', item_type='folder', project_id=self.project_id, position=0)
        db.session.add(parent)
        db.session.commit()
        
        child = SaprTree(name='Child', item_type='file', project_id=self.project_id, parent_link=parent.id, position=0)
        db.session.add(child)
        db.session.commit()

        response = utilTest.client.delete(f'/api/sapr/tree/{parent.id}')
        assert response.status_code == 409
        
        data = response.get_json()
        assert data['error_code'] == 'TREE_ITEM_HAS_CHILDREN'
        assert 'message' in data

    def test_delete_tree_item_with_cascade_success(self):
        parent = SaprTree(name='Parent', item_type='folder', project_id=self.project_id, position=0)
        db.session.add(parent)
        db.session.commit()
        
        child = SaprTree(name='Child', item_type='file', project_id=self.project_id, parent_link=parent.id, position=0)
        db.session.add(child)
        db.session.commit()

        response = utilTest.client.delete(f'/api/sapr/tree/{parent.id}?cascade=true')
        assert response.status_code == 200
        
        assert db.session.get(SaprTree, parent.id) is None
        assert db.session.get(SaprTree, child.id) is None

    def test_move_tree_item(self):
        folder1 = SaprTree(name='Folder 1', item_type='folder', project_id=self.project_id, position=0)
        folder2 = SaprTree(name='Folder 2', item_type='folder', project_id=self.project_id, position=1)
        db.session.add_all([folder1, folder2])
        db.session.commit()

        file_item = SaprTree(name='File', item_type='file', project_id=self.project_id, parent_link=folder1.id, position=0)
        db.session.add(file_item)
        db.session.commit()

        response = utilTest.client.post(f'/api/sapr/tree/{file_item.id}/move', json={
            'new_parent_link': folder2.id,
            'new_position': 10
        })
        assert response.status_code == 200
        
        moved_item = db.session.get(SaprTree, file_item.id)
        assert moved_item.parent_link == folder2.id
        assert moved_item.position == 10
