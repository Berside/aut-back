#!/usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
import pytest
import io
import json
from src.db import db
from src.orm.orm_sapr import Project, Models, Item, ModelSpta
from src.tests.util_test import UtilTest, app_context
from src.sapr.routes import sapr_bp

utilTest = UtilTest(write_data_file=False)

if not any(rule.endpoint.startswith('sapr.') for rule in utilTest.app.url_map.iter_rules()):
    utilTest.app.register_blueprint(sapr_bp)


@pytest.mark.usefixtures('app_context')
class TestModel(unittest.TestCase):
    def setUp(self):
        # Создаем тестовый проект, чтобы привязать тестовые модели
        self.project = Project(name='Тестовый проект для моделей', description='Описание')
        db.session.add(self.project)
        db.session.commit()
        self.project_id = self.project.id

    def tearDown(self):
        # Удаляем все проекты и модели
        ModelSpta.query.delete() 
        Item.query.delete()
        Models.query.delete()
        Project.query.delete()
        db.session.commit()

    def test_add_model_to_project_json(self):
        # Добавление модели в проект через json
        response = utilTest.client.post(f'/api/sapr/projects/{self.project_id}/models',
            json={'name': 'Модель из json', 'is_primary': True}
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'Модель из json'
        assert data['is_primary'] == True

    def test_add_model_to_project_with_file(self):
        # Добавление модели в проект с загрузкой файла
        file_content = b'binary glb data'
        file_name = 'test_model.glb'

        data = {
            'name': 'Модель с файлом',
            'is_primary': 'true',
            'file': (io.BytesIO(file_content), file_name)
        }

        response = utilTest.client.post(f'/api/sapr/projects/{self.project_id}/models',
            content_type='multipart/form-data',
            data=data
        )

        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data['name'] == 'Модель с файлом'

        model = db.session.query(Models).filter_by(name='Модель с файлом').first()
        assert model is not None
        assert model.is_primary == True

    def test_update_model_success(self):
        # Успешное обновление существующей модели
        model = Models(project_id=self.project_id, name='Старое имя', technical_name='old.glb', is_primary=False)
        db.session.add(model)
        db.session.commit()
        model_id = model.id

        response = utilTest.client.put(f'/api/sapr/models/{model_id}',
            json={'name': 'Новое имя', 'is_primary': True}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Новое имя'
        assert data['is_primary'] == True

    def test_update_model_not_found(self):
        # Обновление несуществующей модели
        response = utilTest.client.put('/api/sapr/models/999999',
            json={'name': 'Тест'})
        assert response.status_code == 404

    def test_delete_model_success(self):
        # Удаление модели
        model = Models(
            project_id=self.project_id,
            name='model.glb',
            technical_name='test123.glb',
            is_primary=True
        )
        db.session.add(model)
        db.session.commit()

        model_id = model.id
        response = utilTest.client.delete(f'/api/sapr/models/{model_id}')

        assert response.status_code == 200

    def test_delete_model_not_found(self):
        # Удаление несуществующей модели
        response = utilTest.client.delete('/api/sapr/models/999999')
        assert response.status_code == 404


    def test_search_models_by_name(self):
        # Создаем несколько тестовых моделей
        m1 = Models(project_id=self.project_id, name='Корпус редуктора', technical_name='a.glb', is_primary=False)
        m2 = Models(project_id=self.project_id, name='Крышка подшипника', technical_name='b.glb', is_primary=False)
        m3 = Models(project_id=self.project_id, name='Вал приводной', technical_name='c.glb', is_primary=False)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        response = utilTest.client.get('/api/sapr/models/search?q=корпус')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['name'] == 'Корпус редуктора'

    def test_search_models_case_insensitive(self):
        # Проверка не независимость регистра в поиске
        m1 = Models(project_id=self.project_id, name='Главная шестерня', technical_name='d.glb', is_primary=False)
        db.session.add(m1)
        db.session.commit()

        response = utilTest.client.get('/api/sapr/models/search?q=шестерня')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['name'] == 'Главная шестерня'

    def test_search_models_empty_query(self):
        # Проверка валидации пустого запроса 
        response = utilTest.client.get('/api/sapr/models/search?q=')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Параметр поиска "q" обязателен'

    def test_search_models_no_results(self):
        # Проверка корректного возврата пустого списка, если ничего не найдено
        m1 = Models(project_id=self.project_id, name='Тестовая модель', technical_name='e.glb', is_primary=False)
        db.session.add(m1)
        db.session.commit()

        response = utilTest.client.get('/api/sapr/models/search?q=несуществующее_слово_12345')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 0

    def test_get_model_items_success(self):
        model = Models(project_id=self.project_id, name='Тестовая сборка', is_primary=True)
        db.session.add(model)
        db.session.commit()

        item1 = Item(article='ART-BOLT', name='Болт М10', stock_quantity=100)
        item2 = Item(article='ART-NUT', name='Гайка М10', stock_quantity=200)
        db.session.add_all([item1, item2])
        db.session.commit()

        link1 = ModelSpta(model_id=model.id, item_id=item1.id)
        link2 = ModelSpta(model_id=model.id, item_id=item2.id)
        db.session.add_all([link1, link2])
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/models/{model.id}/items')

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        
        articles = [item['article'] for item in data]
        assert 'ART-BOLT' in articles
        assert 'ART-NUT' in articles
        
        assert data[0]['stock_quantity'] >= 0
        assert 'id' in data[0]
        assert 'name' in data[0]

    def test_get_model_items_empty(self):
        model = Models(project_id=self.project_id, name='Пустая модель', is_primary=False)
        db.session.add(model)
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/models/{model.id}/items')

        assert response.status_code == 200
        data = response.get_json()
        assert data == []

    def test_get_model_items_not_found(self):
        response = utilTest.client.get('/api/sapr/models/999999/items')

        assert response.status_code == 404
        data = response.get_json()
        assert 'error_code' in data
        assert data['error_code'] == 'MODEL_NOT_FOUND'
