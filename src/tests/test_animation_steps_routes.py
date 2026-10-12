#!/usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
import pytest
import json
from src.db import db
from src.orm.orm_sapr import Project, AnimationStep
from src.tests.util_test import UtilTest, app_context
from src.sapr.routes import sapr_bp

utilTest = UtilTest(write_data_file=False)

if not any(rule.endpoint.startswith('sapr.') for rule in utilTest.app.url_map.iter_rules()):
    utilTest.app.register_blueprint(sapr_bp)


@pytest.mark.usefixtures('app_context')
class TestAnimationStep(unittest.TestCase):
    def setUp(self):
        # Создаем тестовый проект с привязкой шагов анимации
        self.project = Project(name='Тестовый проект для анимации', description='Описание')
        db.session.add(self.project)
        db.session.commit()
        self.project_id = self.project.id

    def tearDown(self):
        AnimationStep.query.delete()
        Project.query.delete()
        db.session.commit()

    def test_create_animation_step_success(self):
        # Успешное создание шага анимации
        response = utilTest.client.post(f'/api/sapr/projects/{self.project_id}/animation-steps',
            json={
                'name': 'Шаг 1: Вращение',
                'duration': 2.5,
                'order': 1,
                'is_active': True,
                'camera_position': {'x': 0, 'y': 0, 'z': 0},
                'camera_target': {'x': 0, 'y': 0, 'z': 0},
                'animation_ids': [1, 2]
            }
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'Шаг 1: Вращение'
        assert data['duration'] == 2.5
        assert data['is_active'] == True
        assert data['project_id'] == self.project_id

    def test_create_animation_step_project_not_found(self):
        # Создание шага анимации с привязкой к несуществующему проекту
        response = utilTest.client.post('/api/sapr/projects/999999/animation-steps',
            json={'name': 'Шаг', 'duration': 1.0})

        assert response.status_code == 404

    def test_create_animation_step_auto_order(self):
        # Проверка автоматического расчета order, если передан 0 или не передан
        step1 = AnimationStep(project_id=self.project_id, name='Первый шаг', order=5, duration=1.0)
        db.session.add(step1)
        db.session.commit()

        response = utilTest.client.post(f'/api/sapr/projects/{self.project_id}/animation-steps',
            json={
                'name': 'Второй шаг',
                'duration': 1.0,
                'order': 0  
            }
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['order'] == 6
        assert data['name'] == 'Второй шаг'

    def test_get_animation_steps_by_project_success(self):
        # Успешное получение списка шагов анимации проекта
        step1 = AnimationStep(project_id=self.project_id, name='Шаг 2', order=2, duration=1.0)
        step2 = AnimationStep(project_id=self.project_id, name='Шаг 1', order=1, duration=1.0)
        step3 = AnimationStep(project_id=self.project_id, name='Шаг 3', order=3, duration=1.0)
        db.session.add_all([step1, step2, step3])
        db.session.commit()

        response = utilTest.client.get(f'/api/sapr/projects/{self.project_id}/animation-steps')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 3
        
    def test_get_animation_steps_by_project_empty(self):
        # Проект существует, но шагов анимации в нем нет
        response = utilTest.client.get(f'/api/sapr/projects/{self.project_id}/animation-steps')
        assert response.status_code == 404

    def test_get_animation_steps_by_project_not_found(self):
        # Запрос шагов для несуществующего проекта
        response = utilTest.client.get('/api/sapr/projects/999999/animation-steps')
        assert response.status_code == 404

    def test_update_animation_step_success(self):
        # Обновление существующего шага анимации
        step = AnimationStep(
            project_id=self.project_id,
            name='Старое имя',
            duration=1.0,
            order=1,
            is_active=True
        )
        db.session.add(step)
        db.session.commit()
        step_id = step.id

        response = utilTest.client.put(f'/api/sapr/animation-steps/{step_id}',
            json={
                'name': 'Новое имя',
                'duration': 5.0,
                'is_active': False
            })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Новое имя'
        assert data['duration'] == 5.0
        assert data['is_active'] == False

    def test_update_animation_step_not_found(self):
        # Обновление несуществующего шага анимации
        response = utilTest.client.put('/api/sapr/animation-steps/999999',
            json={'name': 'Тест'})
        assert response.status_code == 404

    def test_delete_animation_step(self):
        # Успешное удаление шага анимации
        step = AnimationStep(
            project_id=self.project_id,
            name='Старое имя',
            duration=1.0,
            order=1,
            is_active=True
        )
        db.session.add(step)
        db.session.commit()
        step_id = step.id

        response = utilTest.client.delete(f'/api/sapr/animation-steps/{step_id}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Шаг анимации удален'

        deleted_step = db.session.query(AnimationStep).filter_by(id=step_id).first()
        assert deleted_step is None
    
    def test_delete_animation_step_not_found(self):
        # Удаление несуществующего шага анимации
        response = utilTest.client.delete('/api/sapr/animation-steps/999999')
        assert response.status_code == 404