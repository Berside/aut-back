#!/usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
import pytest
import json
from src.db import db
from src.orm.orm_sapr import Project, PartCategory, PartType, Part, ProjectPart, Item
from src.tests.util_test import UtilTest, app_context
from src.sapr.routes import sapr_bp

utilTest = UtilTest(write_data_file=False)

if not any(rule.endpoint.startswith('sapr.') for rule in utilTest.app.url_map.iter_rules()):
    utilTest.app.register_blueprint(sapr_bp)


@pytest.mark.usefixtures('app_context')
class TestProjectPart(unittest.TestCase):
    
    def setUp(self):
        self.tearDown()

        self.project = Project(name='Тестовый проект', description='Описание')
        db.session.add(self.project)
        db.session.commit()
        self.project_id = self.project.id

        self.category = PartCategory(name='Тестовая категория', sort_order=1)
        db.session.add(self.category)
        db.session.commit()
        
        self.part_type = PartType(name='Тестовый тип')
        db.session.add(self.part_type)
        db.session.commit()

        self.item1 = Item(name='Складская деталь 1', article='ART-001', stock_quantity=10)
        self.item2 = Item(name='Складская деталь 2', article='ART-002', stock_quantity=2)
        db.session.add_all([self.item1, self.item2])
        db.session.commit()

        self.part1 = Part(
            name='Деталь 1', 
            part_number='P-001', 
            category_id=self.category.id, 
            type_id=self.part_type.id,
            item_id=self.item1.id
        )
        self.part2 = Part(
            name='Деталь 2', 
            part_number='P-002', 
            category_id=self.category.id, 
            type_id=self.part_type.id,
            item_id=self.item2.id
        )

        db.session.add_all([self.part1, self.part2])
        db.session.commit()

    def tearDown(self):
        ProjectPart.query.delete()
        Part.query.delete()
        Item.query.delete()
        PartType.query.delete()
        PartCategory.query.delete()
        Project.query.delete()
        db.session.commit()

    def test_add_parts_to_project_batch_success(self):
        # Массовое добавление деталей в проект
        response = utilTest.client.post(f'/api/sapr/projects/{self.project_id}/parts/batch',
            json={
                'parts': [
                    {'part_id': self.part1.id, 'quantity': 2},
                    {'part_id': self.part2.id, 'quantity': 5},
                ]
            })
        assert response.status_code == 201

    def test_add_parts_to_project_batch_project_not_found(self):
        # Массовое добавление с отсутствующим ключом ('parts')
        response = utilTest.client.post('/api/sapr/projects/999999/parts/batch',
            json={'parts': [{'part_id': self.part1.id, 'quantity': 1}]})
        assert response.status_code == 404

    def test_remove_parts_from_project_batch_success(self):
        # Массовое удаление деталей из проекта
        link1 = ProjectPart(project_id=self.project_id, part_id=self.part1.id, quantity=2)
        link2 = ProjectPart(project_id=self.project_id, part_id=self.part2.id, quantity=5)
        db.session.add_all([link1, link2])
        db.session.commit()

        response = utilTest.client.delete(f'/api/sapr/projects/{self.project_id}/parts/batch',
            json={
                'part_ids': [self.part1.id, self.part2.id]
            })
        assert response.status_code == 200

    def test_remove_parts_from_projects_batch_invalid_key(self):
        # Массовое удаление с отсутствующим ключем part_ids
        response = utilTest.client.delete(f'/api/sapr/projects/{self.project_id}/parts/batch',
            json={'wrong_key': [self.part1.id]})
        assert response.status_code == 400

    def test_add_part_to_project_with_succifient_stock(self):
        # Добавляем 3 шт, на складе 10, остаток 7
        response = utilTest.client.post(
            f'/api/sapr/projects/{self.project_id}/parts', json={
                'part_id': self.part1.id,
                'quantity': 3
            }
        )


        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['remaining_stock'] == 7
        assert data['warning'] is None
        assert data['project_part']['part_id'] == self.part1.id
        
        db.session.refresh(self.item1)
        assert self.item1.stock_quantity == 7

    def test_add_part_to_project_with_insufficient_stock(self):
        # Пытаемся добавить 5 штук, хотя на складе всего 2
        response = utilTest.client.post(f'/api/sapr/projects/{self.project_id}/parts', json={
            'part_id': self.part2.id,
            'quantity': 5
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Есть: 2, нужно: 5' in data['error']
        
        link = ProjectPart.query.filter_by(project_id=self.project_id, part_id=self.part2.id).first()
        assert link is None
        
        db.session.refresh(self.item2)
        assert self.item2.stock_quantity == 2

    def test_add_part_to_project_without_stock_binding(self):
        # Создаем деталь, которая Не привязана к складу
        part_no_stock = Part(name='Деталь без склада', part_number='P-NO-STOCK', category_id=self.category.id)
        db.session.add(part_no_stock)
        db.session.commit()

        response = utilTest.client.post(f'/api/sapr/projects/{self.project_id}/parts', json={
            'part_id': part_no_stock.id,
            'quantity': 100
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['remaining_stock'] is None
        assert 'не учтена на складе' in data['warning']

    def test_add_part_to_project_exact_stock_amount(self):
        # Запрашиваем ровно столько, сколько есть на складе 
        response = utilTest.client.post(f'/api/sapr/projects/{self.project_id}/parts', json={
            'part_id': self.part2.id,
            'quantity': 2
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['remaining_stock'] == 0
        
        db.session.refresh(self.item2)
        assert self.item2.stock_quantity == 0
