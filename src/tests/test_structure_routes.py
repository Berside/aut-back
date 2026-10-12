#!/usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
import pytest
from src.db import db
from src.orm.orm_sapr import Project, Models, ModelStructureNode
from src.tests.util_test import UtilTest, app_context

utilTest = UtilTest(write_data_file=False)


@pytest.mark.usefixtures('app_context')
class TestStructureRoutes(unittest.TestCase):
    
    def setUp(self):
        self.tearDown()
        self.project = Project(name='Тестовый проект', description='Описание')
        db.session.add(self.project)
        db.session.flush()

        self.model = Models(
            project_id=self.project.id,
            name='Тестовая модель',
            is_primary=True
        )
        db.session.add(self.model)
        db.session.commit()
        self.model_id = self.model.id

    def tearDown(self):
        ModelStructureNode.query.delete()
        Models.query.delete()
        Project.query.delete()
        db.session.commit()

    def test_create_structure_node_success(self):
        response = utilTest.client.post('/api/sapr/model-structure', json={
            'name': 'Двигатель',
            'code': '536.3902150 РЭ',
            'model_id': self.model_id
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == 'Двигатель'
        assert data['code'] == '536.3902150 РЭ'
        assert 'id' in data

    def test_create_structure_node_duplicate_code(self):
        utilTest.client.post('/api/sapr/model-structure', json={
            'name': 'Двигатель',
            'code': '536.3902150 РЭ',
            'model_id': self.model_id
        })
        response = utilTest.client.post('/api/sapr/model-structure', json={
            'name': 'Двигатель 2',
            'code': '536.3902150 РЭ',
            'model_id': self.model_id
        })
        assert response.status_code == 409
        data = response.get_json()
        assert data['error_code'] == 'STRUCTURE_NODE_ALREADY_EXISTS'

    def test_get_structure_tree(self):
        root_resp = utilTest.client.post('/api/sapr/model-structure', json={
            'name': 'Двигатель',
            'code': '536.3902150 РЭ',
            'model_id': self.model_id
        })
        root_id = root_resp.get_json()['id']

        utilTest.client.post('/api/sapr/model-structure', json={
            'name': 'Поршень',
            'code': '536.3902150-01',
            'parent_id': root_id,
            'model_id': self.model_id
        })
        utilTest.client.post('/api/sapr/model-structure', json={
            'name': 'Клапан',
            'code': '536.3902150-02',
            'parent_id': root_id,
            'model_id': self.model_id
        })

        response = utilTest.client.get(f'/api/sapr/model-structure/tree/{self.model_id}')
        assert response.status_code == 200

        data = response.get_json()
        assert len(data) == 1
        assert data[0]['name'] == 'Двигатель'
        assert data[0]['has_children'] is True
        assert len(data[0]['children']) == 2

    def test_get_structure_tree_empty(self):
        response = utilTest.client.get(f'/api/sapr/model-structure/tree/{self.model_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 0

    def test_get_structure_node_by_id(self):
        create_resp = utilTest.client.post('/api/sapr/model-structure', json={
            'name': 'Двигатель',
            'code': '536.3902150 РЭ',
            'model_id': self.model_id
        })
        node_id = create_resp.get_json()['id']

        response = utilTest.client.get(f'/api/sapr/model-structure/{node_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Двигатель'

    def test_get_structure_node_not_found(self):
        response = utilTest.client.get('/api/sapr/model-structure/nonexistent-id')
        assert response.status_code == 404

    def test_update_structure_node(self):
        create_resp = utilTest.client.post('/api/sapr/model-structure', json={
            'name': 'Двигатель',
            'code': '536.3902150 РЭ',
            'model_id': self.model_id
        })
        node_id = create_resp.get_json()['id']

        response = utilTest.client.put(f'/api/sapr/model-structure/{node_id}', json={
            'name': 'Двигатель обновленный'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Двигатель обновленный'

    def test_delete_structure_node_without_children(self):
        create_resp = utilTest.client.post('/api/sapr/model-structure', json={
            'name': 'Двигатель',
            'code': '536.3902150 РЭ',
            'model_id': self.model_id
        })
        node_id = create_resp.get_json()['id']

        response = utilTest.client.delete(f'/api/sapr/model-structure/{node_id}')
        assert response.status_code == 200

        get_resp = utilTest.client.get(f'/api/sapr/model-structure/{node_id}')
        assert get_resp.status_code == 404

    def test_delete_structure_node_with_children_fails(self):
        root_resp = utilTest.client.post('/api/sapr/model-structure', json={
            'name': 'Двигатель',
            'code': '536.3902150 РЭ',
            'model_id': self.model_id
        })
        root_id = root_resp.get_json()['id']

        utilTest.client.post('/api/sapr/model-structure', json={
            'name': 'Поршень',
            'code': '536.3902150-01',
            'parent_id': root_id,
            'model_id': self.model_id
        })

        response = utilTest.client.delete(f'/api/sapr/model-structure/{root_id}')
        assert response.status_code == 500

    def test_delete_structure_node_with_cascade(self):
        root_resp = utilTest.client.post('/api/sapr/model-structure', json={
            'name': 'Двигатель',
            'code': '536.3902150 РЭ',
            'model_id': self.model_id
        })
        root_id = root_resp.get_json()['id']

        utilTest.client.post('/api/sapr/model-structure', json={
            'name': 'Поршень',
            'code': '536.3902150-01',
            'parent_id': root_id,
            'model_id': self.model_id
        })

        response = utilTest.client.delete(f'/api/sapr/model-structure/{root_id}?cascade=true')
        assert response.status_code == 200

        get_resp = utilTest.client.get(f'/api/sapr/model-structure/{root_id}')
        assert get_resp.status_code == 404