#!/usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
import pytest
import io
import json
from src.db import db
from src.orm.orm_sapr import Project, Models, Instruction
from src.tests.util_test import UtilTest, app_context
from src.sapr.routes import sapr_bp

utilTest = UtilTest(write_data_file=False)

if not any(rule.endpoint.startswith('sapr.') for rule in utilTest.app.url_map.iter_rules()):
    utilTest.app.register_blueprint(sapr_bp)


@pytest.mark.usefixtures('app_context')
class TestProjectService(unittest.TestCase):
    global utilTest

    def setUp(self):
        self.tearDown()

    def tearDown(self):
        # Удаляем все проекты и связанные модели
        Instruction.query.delete()
        Models.query.delete()
        Project.query.delete()
        db.session.commit()

    def test_get_all_projects_empty(self):
        # Получение списка проектов, когда их нет
        response = utilTest.client.get('/api/sapr/projects/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 0

    def test_get_all_projects_with_data(self):
        # Получение списка проектов с данными
        db.session.add(Project(name='Тестовый проект 1', description='Описание 1'))
        db.session.add(Project(name='Тестовый проект 2', description='Описание 2'))
        db.session.commit()

        response = utilTest.client.get('/api/sapr/projects/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2

    def test_get_project_success(self):
        # Успешное получение проекта по ID
        project = Project(name='Проект для GET', description='Описание')
        db.session.add(project)
        db.session.commit()
        project_id = project.id

        response = utilTest.client.get(f'/api/sapr/projects/{project_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == project_id
        assert data['name'] == 'Проект для GET'

    def test_get_project_not_found(self):
        # Получение несуществующего проекта
        response = utilTest.client.get('/api/sapr/projects/999999')
        assert response.status_code == 404

    def test_create_project_without_file(self):
        # Создание проекта без файла
        response = utilTest.client.post('/api/sapr/projects/',
            headers={"Content-Type": "application/json"},
            data=json.dumps({"name": "Новый проект", "description": "Тестовое описание"})
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'Новый проект'
        assert data['description'] == 'Тестовое описание'

        project = db.session.query(Project).filter_by(name='Новый проект').first()
        assert project is not None
        assert len(project.models) == 0

    def test_create_project_duplicate_name(self):
        # Создание проекта с дублирующимся именем
        db.session.add(Project(name='Уникальное имя', description='Первый'))
        db.session.commit()

        response = utilTest.client.post('/api/sapr/projects/',
            headers={"Content-Type": "application/json"},
            data=json.dumps({"name": "Уникальное имя", "description": "Второй"}))
        
        assert response.status_code == 409

    def test_create_project_with_file(self):
        # Создание проекта с файлом модели
        file_content = b'test model content'
        file_name = 'test_model.glb'
        
        data = {
            'name': 'Проект с файлом',
            'description': 'С моделью',
            'primary_model': (io.BytesIO(file_content), file_name)
        }
        
        response = utilTest.client.post('/api/sapr/projects/',
            content_type='multipart/form-data',
            data=data)
        
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data['name'] == 'Проект с файлом'

        project = db.session.query(Project).filter_by(name='Проект с файлом').first()
        assert project is not None
        assert len(project.models) == 1
        assert project.models[0].is_primary == True
        assert project.models[0].name == file_name

    def test_delete_project_success(self):
        # Успешное удаление проекта
        project = Project(name="Проект на удаление", description="Описание")
        db.session.add(project)
        db.session.commit()
        project_id = project.id

        response = utilTest.client.delete(f'/api/sapr/projects/{project_id}')
        assert response.status_code == 200

        deleted_project = db.session.query(Project).filter_by(id=project_id).first()
        assert deleted_project is None

    def test_delete_project_not_found(self):
        # Удаление несуществующего проекта
        response = utilTest.client.delete('/api/sapr/projects/999999')
        assert response.status_code == 404

    def test_delete_project_with_model(self):
        # Удаление проекта с моделью
        project = Project(name="Проект с моделью", description="Описание")
        db.session.add(project)
        db.session.commit()
        
        model = Models(
            project_id=project.id,
            name="model.glb",
            technical_name="test123.glb",
            is_primary=True
        )
        db.session.add(model)
        db.session.commit()
        project_id = project.id

        response = utilTest.client.delete(f'/api/sapr/projects/{project_id}')
        assert response.status_code == 200

        assert db.session.query(Project).filter_by(id=project_id).first() is None
        assert db.session.query(Models).filter_by(project_id=project_id).count() == 0

    def test_get_project_instructions_success(self):
        # Успешное получение списка инструкций проекта
        project = Project(name='Проект с инструкциями', description='Описание')
        db.session.add(project)
        db.session.commit()

        inst1 = Instruction(dmc='DMC-001', project_id=project.id, title='Инструкция 1', is_current=True)
        inst2 = Instruction(dmc='DMC-002', project_id=project.id, title='Инструкция 2', is_current=True)
        inst_old = Instruction(dmc='DMC-001', project_id=project.id, title='Инструкция 1 (старая)', is_current=False)
        
        db.session.add_all([inst1, inst2, inst_old])
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/projects/{project.id}/instructions')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert len(data) == 2
        
        for item in data:
            assert 'dmc' in item
            assert 'title' in item
            assert 'content' not in item 
            assert 'file_path' not in item

    def test_get_project_instructions_empty(self):
        # Получение инструкций для проекта, у которого их нет
        project = Project(name='Пустой проект', description='Описание')
        db.session.add(project)
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/projects/{project.id}/instructions')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []

    def test_get_project_instructions_not_found(self):
        # Попытка получить инструкции несуществующего проекта
        response = utilTest.client.get('/api/sapr/projects/999999/instructions')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error_code'] == 'PROJECT_NOT_FOUND'



if __name__ == '__main__':
    unittest.main()