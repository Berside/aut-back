#!/usr/bin/python3
# -*- coding: utf-8 -*-
import unittest
import pytest
from src.db import db
from src.orm.orm_sapr import Project, AnimationStep, Instruction
from src.orm.orm_sapr import Project
from src.tests.util_test import UtilTest, app_context
from src.sapr.routes import sapr_bp

utilTest = UtilTest(write_data_file=False)

if not any(rule.endpoint.startswith('sapr.') for rule in utilTest.app.url_map.iter_rules()):
    utilTest.app.register_blueprint(sapr_bp)


@pytest.mark.usefixtures('app_context')
class TestInstruction(unittest.TestCase):
    
    def setUp(self):
        self.tearDown()
        self.project = Project(name='Тестовый проект', description='Описание')
        db.session.add(self.project)
        db.session.commit()
        self.project_id = self.project.id

        self.animation_step = AnimationStep(project_id=self.project_id, name='Тестовый шаг')
        db.session.add(self.animation_step)
        db.session.commit()
        self.animation_step_id = self.animation_step.id

    def tearDown(self):
        Instruction.query.delete()
        AnimationStep.query.delete()
        Project.query.delete()
        db.session.commit()

    def test_create_instruction_success(self):
        response = utilTest.client.post('/api/sapr/instructions', json={
            'dmc': 'DMC-001', 'project_id': self.project_id, 'title': 'Инструкция по монтажу',
            'content': {'type': 'doc', 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Тестовый текст'}]}]},
            'animation_step_id': self.animation_step_id
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['dmc'] == 'DMC-001'
        assert data['is_current'] is True

    def test_create_instruction_with_forbidden_content(self):
        response = utilTest.client.post('/api/sapr/instructions', json={
            'dmc': 'DMC-002', 'project_id': self.project_id, 'title': 'Инструкция с таблицей',
            'content': {'type': 'doc', 'content': [{'type': 'table', 'content': [{'type': 'tableRow', 'content': [{'type': 'tableCell', 'content': [{'type': 'text', 'text': 'Ячейка'}]}]}]}]}
        })
        assert response.status_code == 400

    def test_create_instruction_version_update(self):
        utilTest.client.post('/api/sapr/instructions', json={'dmc': 'DMC-003', 'project_id': self.project_id, 'title': 'Версия 1', 'content': {'type': 'doc', 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Текст 1'}]}]}})
        response = utilTest.client.post('/api/sapr/instructions', json={'dmc': 'DMC-003', 'project_id': self.project_id, 'title': 'Версия 2', 'content': {'type': 'doc', 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Текст 2'}]}]}})
        
        assert response.status_code == 201
        old_instruction = Instruction.query.filter_by(dmc='DMC-003', is_current=False).first()
        assert old_instruction is not None and old_instruction.title == 'Версия 1'
        new_instruction = Instruction.query.filter_by(dmc='DMC-003', is_current=True).first()
        assert new_instruction is not None and new_instruction.title == 'Версия 2'

    def test_get_instruction_by_id(self):
        instruction = Instruction(dmc='DMC-004', project_id=self.project_id, title='Тестовая инструкция', content={'type': 'doc', 'content': []}, is_current=True)
        db.session.add(instruction)
        db.session.commit()
        response = utilTest.client.get(f'/api/sapr/instructions/{instruction.id}')
        assert response.status_code == 200
        assert response.get_json()['dmc'] == 'DMC-004'

    def test_get_instruction_not_found(self):
        response = utilTest.client.get('/api/sapr/instructions/999999')
        assert response.status_code == 404

    def test_get_current_instruction_by_dmc(self):
        instruction = Instruction(dmc='DMC-005', project_id=self.project_id, title='Актуальная версия', content={'type': 'doc', 'content': []}, is_current=True)
        db.session.add(instruction)
        db.session.commit()
        response = utilTest.client.get('/api/sapr/instructions/dmc/DMC-005')
        assert response.status_code == 200
        assert response.get_json()['is_current'] is True

    def test_get_current_instruction_by_dmc_not_found(self):
        response = utilTest.client.get('/api/sapr/instructions/dmc/NONEXISTENT')
        assert response.status_code == 404

    def test_delete_instruction_success(self):
        instruction = Instruction(dmc='DMC-006', project_id=self.project_id, title='Инструкция для удаления', content={'type': 'doc', 'content': []}, is_current=True)
        db.session.add(instruction)
        db.session.commit()
        response = utilTest.client.delete(f'/api/sapr/instructions/{instruction.id}')
        assert response.status_code == 200
        assert db.session.get(Instruction, instruction.id) is None

    def test_delete_instruction_not_found(self):
        response = utilTest.client.delete('/api/sapr/instructions/999999')
        assert response.status_code == 404

    def test_create_instruction_invalid_dto(self):
        response = utilTest.client.post('/api/sapr/instructions', json={'project_id': self.project_id, 'title': 'Без DMC'})
        assert response.status_code == 400

    def test_get_instructions_list(self):
        inst1 = Instruction(dmc='DMC-LIST-1', project_id=self.project_id, title='Инструкция 1', is_current=True)
        inst2 = Instruction(dmc='DMC-LIST-2', project_id=self.project_id, title='Инструкция 2', is_current=True)
        db.session.add_all([inst1, inst2])
        db.session.commit()
        response = utilTest.client.get('/api/sapr/instructions')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2

    def test_get_instructions_list_filtered(self):
        inst1 = Instruction(dmc='DMC-FILTER-1', project_id=self.project_id, title='Фильтр 1', is_current=True)
        db.session.add(inst1)
        db.session.commit()
        response = utilTest.client.get(f'/api/sapr/instructions?project_id={self.project_id}')
        assert response.status_code == 200
        assert len(response.get_json()) == 1

    def test_get_instruction_versions(self):
        old_inst = Instruction(dmc='DMC-VER-TEST', project_id=self.project_id, title='Версия 1', is_current=False)
        new_inst = Instruction(dmc='DMC-VER-TEST', project_id=self.project_id, title='Версия 2', is_current=True)
        db.session.add_all([old_inst, new_inst])
        db.session.commit()
        response = utilTest.client.get('/api/sapr/instructions/dmc/DMC-VER-TEST/versions')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2

    def test_get_instruction_versions_not_found(self):
        response = utilTest.client.get('/api/sapr/instructions/dmc/NONEXISTENT-DMC/versions')
        assert response.status_code == 404

    def test_create_instruction_invalid_project_id(self):
        # Попытка создать инструкцию для несуществующего проекта
        response = utilTest.client.post('/api/sapr/instructions', json={
            'dmc': 'DMC-ERR-1',
            'project_id': 99999,
            'title': 'Тестовая инструкция',
            'content': {'type': 'doc', 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Текст'}]}]}
        })

        assert response.status_code == 404

    def test_create_instruction_invalid_animation_step_id(self):
        # Попытка создать инструкцию с несуществующим шагом анимации
        response = utilTest.client.post('/api/sapr/instructions', json={
            'dmc': 'DMC-ERR-2',
            'project_id': self.project_id,
            'animation_step_id': 99999,
            'title': 'Тестовая инструкция',
            'content': {'type': 'doc', 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Текст'}]}]}
        })
        assert response.status_code == 404

    def test_create_instruction_animation_step_wrong_project(self):
        # Попытка привязать шаг анимации другого проекта
        other_project = Project(name='Другой проект', description='Описание')
        db.session.add(other_project)
        db.session.commit()

        other_step = AnimationStep(project_id=other_project.id, name='Чужой шаг', duration=1.0)
        db.session.add(other_step)
        db.session.commit()

        response = utilTest.client.post('/api/sapr/instructions', json={
            'dmc': 'DMC-ERR-3',
            'project_id': self.project_id,
            'animation_step_id': other_step.id, 
            'title': 'Тестовая инструкция',
            'content': {'type': 'doc', 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Текст'}]}]}
           
        })

        assert response.status_code == 400

    def test_search_instructions_by_title(self):
        inst1 = Instruction(dmc='DMC-SEARCH-1', project_id=self.project_id, title='Инструкция по монтажу насоса', is_current=True)
        inst2 = Instruction(dmc='DMC-SEARCH-2', project_id=self.project_id, title='Руководство по демонтажу', is_current=True)
        inst3 = Instruction(dmc='DMC-SEARCH-3', project_id=self.project_id, title='Схема электрическая', is_current=True)
        db.session.add_all([inst1, inst2, inst3])
        db.session.commit()

        response = utilTest.client.get('/api/sapr/instructions/search?q=монтаж')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        assert any('насоса' in item['title'] for item in data)
        assert any('демонтажу' in item['title'] for item in data)

    def test_search_instructions_empty_query(self):
        response = utilTest.client.get('/api/sapr/instructions/search?q=')
        assert response.status_code == 400

    def test_instruction_by_dmc(self):
        # Проверка поиска инструкции по части DMC-кода
        inst = Instruction(
            dmc='DMC-TEST-AIRCRAFT-001',
            project_id=self.project_id,
            title='Тестовая инструкция по самолету',
            is_current=True
        )
        db.session.add(inst)
        db.session.commit()

        response = utilTest.client.get('/api/sapr/instructions/search?q=AIRCRAFT')
        assert response.status_code == 200

    def test_search_instructions_by_content(self):
        # Проверка поиска инструкции по слову из содержимого 
        inst = Instruction(
            dmc='DMC-CONTENT-TEST',
            project_id=self.project_id,
            title='Техническое обслуживание',
            content={
                'type': 'doc',
                'content': [{
                    'type': 'paragraph',
                    'content': [{'type': 'text', 'text': 'Необходимо регулярно наносить смазку на все движущиеся части'}]
                }]
            },
            is_current=True
        )
        db.session.add(inst)
        db.session.commit()

        response = utilTest.client.get('/api/sapr/instructions/search?q=смазка')

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 1
        assert any(item['dmc'] == 'DMC-CONTENT-TEST' for item in data)

    def test_get_instructions_list_restricted_fields(self):
        # Список должен возвращать ТОЛЬКО dmc и title
        inst = Instruction(
            dmc='DMC-LIST-RESTRICTED',
            project_id=self.project_id,
            title='Тестовая инструкция',
            content={'type': 'doc', 'content': []},
            file_path='DMC-LIST-RESTRICTED.tiptap',
            is_current=True
        )
        db.session.add(inst)
        db.session.commit()

        response = utilTest.client.get('/api/sapr/instructions')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        
        item = data[0]
        assert 'dmc' in item
        assert 'title' in item
        assert 'content' not in item
        assert 'file_path' not in item
        assert item['dmc'] == 'DMC-LIST-RESTRICTED'

    def test_create_instruction_saves_file_to_disk(self):
        # При создании инструкции JSON сохраняется как .tiptap файл
        import unittest.mock as mock
        
        payload = {
            'dmc': 'DMC-FILE-SAVE-TEST',
            'project_id': self.project_id,
            'title': 'Инструкция с файлом',
            'content': {'type': 'doc', 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Тест'}]}]}
        }
        
        with mock.patch('builtins.open', mock.mock_open()) as mock_file:
            response = utilTest.client.post('/api/sapr/instructions', json=payload)
            
            assert response.status_code == 201
            data = response.get_json()
            
            assert data['file_path'] == 'DMC-FILE-SAVE-TEST.tiptap'
            
            mock_file.assert_called_once()
            call_args = mock_file.call_args
            assert call_args[0][1] == 'w'
            assert call_args[1].get('encoding') == 'utf-8'

    def test_get_instruction_file_success(self):
        # Получение содержимого инструкции 
        import unittest.mock as mock
        import json
        
        inst = Instruction(
            dmc='DMC-FILE-GET-TEST',
            project_id=self.project_id,
            title='Инструкция для получения файла',
            file_path='DMC-FILE-GET-TEST.tiptap',
            is_current=True
        )
        db.session.add(inst)
        db.session.commit()

        mock_file_content = {
            "type": "doc",
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Тестовый текст из файла"}]}]
        }

        with mock.patch('os.path.exists', return_value=True), \
             mock.patch('builtins.open', mock.mock_open(read_data=json.dumps(mock_file_content))):
            
            response = utilTest.client.get(f'/api/sapr/instructions/{inst.id}/file')
            
            assert response.status_code == 200
            
            assert response.content_type == 'application/json'
            assert response.get_json() == mock_file_content

    def test_get_instruction_file_not_found_on_disk(self):
        # Запись в БД есть, но файла на диске нет
        import unittest.mock as mock
        
        inst = Instruction(
            dmc='DMC-FILE-MISSING',
            project_id=self.project_id,
            title='Инструкция без файла на диске',
            file_path='DMC-FILE-MISSING.tiptap',
            is_current=True
        )
        db.session.add(inst)
        db.session.commit()

        with mock.patch('os.path.exists', return_value=False):
            response = utilTest.client.get(f'/api/sapr/instructions/{inst.id}/file')
            
            assert response.status_code == 404
            data = response.get_json()
            assert data['error_code'] == 'PHYSICAL_FILE_NOT_FOUND'

    def test_update_instruction_success(self):
        response = utilTest.client.post('/api/sapr/instructions', json={
            'dmc': 'DMC-UPD-001', 'project_id': self.project_id, 'title': 'Версия 1',
            'content': {'type': 'doc', 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Текст 1'}]}]}
        })
        assert response.status_code == 201
        old_data = response.get_json()
        old_id = old_data['id']

        response = utilTest.client.put(f'/api/sapr/instructions/{old_id}', json={
            'dmc': 'DMC-UPD-001',
            'project_id': self.project_id,
            'title': 'Версия 2 (Обновленная)',
            'content': {'type': 'doc', 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Текст 2'}]}]},
            'part_id': None,
            'animation_step_id': None
        })

        assert response.status_code == 200
        new_data = response.get_json()

        old_inst = db.session.get(Instruction, old_id)
        assert old_inst is not None
        assert old_inst.is_current is False
        assert old_inst.title == 'Версия 1'

        new_inst = db.session.get(Instruction, new_data['id'])
        assert new_inst is not None
        assert new_inst.is_current is True
        assert new_inst.title == 'Версия 2 (Обновленная)'
        assert new_inst.file_path == f'DMC-UPD-001_v{old_id}.tiptap'

    def test_update_instruction_dmc_mismatch(self):
        # Создаем инструкцию
        response = utilTest.client.post('/api/sapr/instructions', json={
            'dmc': 'DMC-UPD-002', 'project_id': self.project_id, 'title': 'Тест',
            'content': {'type': 'doc', 'content': []}
        })
        inst_id = response.get_json()['id']

        response = utilTest.client.put(f'/api/sapr/instructions/{inst_id}', json={
            'dmc': 'DMC-WRONG', 
            'project_id': self.project_id,
            'title': 'Новое название',
            'content': {'type': 'doc', 'content': []}
        })
        assert response.status_code == 400

    def test_update_instruction_project_mismatch(self):
        response = utilTest.client.post('/api/sapr/instructions', json={
            'dmc': 'DMC-UPD-003', 'project_id': self.project_id, 'title': 'Тест',
            'content': {'type': 'doc', 'content': []}
        })
        inst_id = response.get_json()['id']

        other_project = Project(name='Другой проект', description='Описание')
        db.session.add(other_project)
        db.session.commit()

        response = utilTest.client.put(f'/api/sapr/instructions/{inst_id}', json={
            'dmc': 'DMC-UPD-003',
            'project_id': other_project.id,
            'title': 'Новое название',
            'content': {'type': 'doc', 'content': []}
        })
        assert response.status_code == 400

    def test_update_instruction_not_found(self):
        response = utilTest.client.put('/api/sapr/instructions/999999', json={
            'dmc': 'DMC-UPD-004',
            'project_id': self.project_id,
            'title': 'Тест',
            'content': {'type': 'doc', 'content': []}
        })
        assert response.status_code == 404

    def test_update_instruction_saves_versioned_file(self):
        import unittest.mock as mock
        
        response = utilTest.client.post('/api/sapr/instructions', json={
            'dmc': 'DMC-UPD-FILE', 'project_id': self.project_id, 'title': 'Версия 1',
            'content': {'type': 'doc', 'content': []}
        })
        inst_id = response.get_json()['id']

        new_content = {'type': 'doc', 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Обновлено'}]}]}

        with mock.patch('builtins.open', mock.mock_open()) as mock_file:
            response = utilTest.client.put(f'/api/sapr/instructions/{inst_id}', json={
                'dmc': 'DMC-UPD-FILE',
                'project_id': self.project_id,
                'title': 'Версия 2',
                'content': new_content
            })
            
            assert response.status_code == 200
            
            mock_file.assert_called()
            call_args = mock_file.call_args
            
            assert f'_v{inst_id}.tiptap' in call_args[0][0]
            assert call_args[0][1] == 'w'
            assert call_args[1].get('encoding') == 'utf-8'
        

@pytest.mark.parametrize("complex_content, expected_status, test_name", [
    (
        {
            "type": "doc",
            "content": [
                {
                    "type": "bulletList",
                    "content": [{
                        "type": "listItem",
                        "content": [{
                            "type": "paragraph",
                            "attrs": {"textAlign": "left"},
                            "content": [
                                {"type": "text", "text": "Начало текста. "},
                                {"type": "text", "marks": [{"type": "bold"}], "text": "Жирный "},
                                {"type": "text", "marks": [{"type": "bold"}, {"type": "italic"}], "text": "курсив внутри жирного"},
                                {"type": "text", "marks": [{"type": "code"}], "text": "код внутри жирного"}
                            ]
                        }]
                    }],
                },
                {
                    "type": "orderedList",
                    "attrs": {"start": 1},
                    "content": [{
                        "type": "listItem",
                        "content": [{
                            "type": "paragraph",
                            "attrs": {"textAlign": "left"},
                            "content": [
                                {"type": "text", "text": "После этого верхний индекс x² и "},
                                {"type": "text", "marks": [{"type": "underline"}], "text": "нижний H₂O"},
                                {"type": "text", "marks": [{"type": "superscript"}], "text": "м"},
                                {"type": "text", "marks": [{"type": "subscript"}], "text": "че"}
                            ]
                        }]
                    }]
                }
            ]
        },
        201,
        "Смешанные списки и стили"
    ),
    (
        {
            "type": "doc",
            "content": [{
                "type": "heading",
                "attrs": {"textAlign": "center", "level": 1},
                "content": [
                    {"type": "text", "marks": [{"type": "bold"}], "text": "E = mc² + Σ"},
                    {"type": "text", "text": "(xᵢ - x̄)² / (n-1) г"},
                    {"type": "text", "marks": [{"type": "strike"}], "text": "де i=1...N, а H₂O"},
                    {"type": "text", "text": " — это "},
                    {"type": "text", "marks": [{"type": "underline"}], "text": "вода, но не"},
                    {"type": "text", "text": " H₂SO₄! Проверь: a^"},
                    {"type": "text", "marks": [{"type": "subscript"}], "text": "(b^c) ≠"},
                    {"type": "text", "marks": [{"type": "superscript"}], "text": "c и ∫f(x"},
                    {"type": "text", "marks": [{"type": "italic"}, {"type": "subscript"}], "text": "и Δx→0"}
                ]
            }]
        },
        201,
        "Заголовок с математикой и сложными стилями"
    ),
    (
        {
            "type": "doc",
            "content": [
                {"type": "paragraph", "attrs": {"textAlign": "left"}, "content": [{"type": "text", "marks": [{"type": "underline"}], "text": "Уровень 1"}]},
                {"type": "paragraph", "attrs": {"textAlign": "justify"}, "content": [{"type": "text", "marks": [{"type": "strike"}], "text": "Уровень 3"}]},
                {"type": "heading", "attrs": {"textAlign": "left", "level": 1}, "content": [{"type": "text", "text": "Уровень 4"}]},
                {"type": "paragraph", "attrs": {"textAlign": "right"}, "content": [{"type": "text", "marks": [{"type": "italic"}, {"type": "subscript"}], "text": "Уровень 6 (разрешенные стили)"}]},
                {"type": "paragraph", "attrs": {"textAlign": "right"}, "content": [{"type": "text", "marks": [{"type": "superscript"}], "text": "Вернулись на уровень 3"}]}
            ]
        },
        201,
        "Различные выравнивания и комбинации стилей"
    ),
    (
        {
            "type": "doc",
            "content": [{
                "type": "heading",
                "attrs": {"textAlign": "left", "level": 7},
                "content": [{"type": "text", "text": "Слишком высокий уровень заголовка"}]
            }]
        },
        400,
        "Невалидный уровень заголовка (level=7)"
    )
])
def test_complex_tipTap_json_scenarios(complex_content, expected_status, test_name, app_context):
    project = Project(name=f'Проект для теста {test_name}', description='Описание')
    db.session.add(project)
    db.session.commit()
    
    response = utilTest.client.post('/api/sapr/instructions', json={
        'dmc': f'DMC-COMPLEX-{test_name.replace(" ", "-")}',
        'project_id': project.id,
        'title': f'Тест: {test_name}',
        'content': complex_content
    })
    
    assert response.status_code == expected_status, (
        f"Тест '{test_name}' провален. "
        f"Ожидался статус {expected_status}, получен {response.status_code}. "
        f"Ответ сервера: {response.get_json()}"
    )

    Instruction.query.filter_by(project_id=project.id).delete()
    db.session.delete(project)
    db.session.commit()

