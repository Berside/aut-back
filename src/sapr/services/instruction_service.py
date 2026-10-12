#!/usr/bin/python3
# -*- coding: utf-8 -*-
from src.db import db
from src.orm.orm_sapr import Instruction, Project, AnimationStep
from src.sapr.utils.tip_tap_validator import TipTapValidator
from src.sapr.exceptions import (
    InstructionNotFoundError,
    InstructionValidationError,
    ProjectNotFoundError,
    AnimationStepNotFoundError,
    InvalidAnimationStepError,
    MissingFileError,
    FileSaveError,
    PhysicalFileNotFoundError)

from typing import Optional
from sqlalchemy import func, or_
from flask import current_app
import os
import uuid
import json

class InstructionService:
    # Сервис для работы с инструкциями(Data Modules)

    @staticmethod
    def _validate_content(content: dict) -> None:
        # Валидация TipTap JSON через валидатор
        if content is None:
            return

        validator = TipTapValidator(content, verbose=False)
        is_valid, errors = validator.validate()

        if not is_valid:
            error_message = "; ".join(errors)
            raise InstructionValidationError()

    @staticmethod
    def _get_upload_folder() -> str:
        # Возвращает путь к директории file_storage
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        if not upload_folder:
            src_path = current_app.config.get('SRC_PATH', 'src')
            upload_folder = os.path.join(src_path, 'file_storage')
        return upload_folder

    @staticmethod
    def create_instruction(
        dmc: str,
        project_id: int,
        title: str,
        content: Optional[dict] = None,
        part_id: Optional[int] = None,
        animation_step_id: Optional[int] = None
    ) -> Instruction:
        # Создает новую инструкцию

        project = Project.query.get(project_id)
        if not project:
            raise ProjectNotFoundError()

        if animation_step_id is not None:
            step = AnimationStep.query.get(animation_step_id)
            if not step:
                raise AnimationStepNotFoundError()

            if step.project_id != project_id:
                raise InvalidAnimationStepError()

        version = Instruction.query.filter_by(dmc=dmc).count() + 1
        safe_filename = f'{dmc}_{version}.tiptap'

        upload_folder = InstructionService._get_upload_folder()
        filepath = os.path.join(upload_folder, safe_filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise FileSaveError(f'Не удалось сохранить файл: {str(e)}')

        # Помечаем старые версии с тем же DMC как неактуальные
        Instruction.query.filter_by(dmc=dmc).update({'is_current': False})
        
        new_instruction = Instruction(
            dmc=dmc,
            project_id=project_id,
            title=title,
            content=content,
            part_id=part_id,
            animation_step_id=animation_step_id,
            file_path=safe_filename,
            is_current=True
        )
        db.session.add(new_instruction)
        db.session.commit()

        return new_instruction

    @staticmethod
    def update_instruction(
        instruction_id: int,
        dmc: str,
        project_id: int,
        title: str,
        content: dict,
        part_id: Optional[int] = None,
        animation_step_id: Optional[int] = None
    ) -> Instruction:
        old_instruction = Instruction.query.get(instruction_id)
        if not old_instruction:
            raise InstructionNotFoundError()
        
        if old_instruction.dmc != dmc:
            raise InstructionValidationError("DMC не может быть изменен")

        if old_instruction.project_id != project_id:
            raise InstructionValidationError()

        project = Project.query.get(old_instruction.project_id)
        if not project:
            raise ProjectNotFoundError()

        if animation_step_id is not None:
            step = AnimationStep.query.get(animation_step_id)
            if not step:
                raise AnimationStepNotFoundError()
            if step.project_id != project.id:
                raise InvalidAnimationStepError()

        old_instruction.is_current = False
        db.session.add(old_instruction)

        version = Instruction.query.filter_by(dmc=dmc).count() + 1
        safe_filename = f'{dmc}_{version}.tiptap'

        upload_folder = instruction_service._get_upload_folder()
        filepath = os.path.join(upload_folder, safe_filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
        except Exception as e:
            db.session.rollback()
            old_instruction.is_current = True
            db.session.add(old_instruction)
            db.session.commit()
            raise FileSaveError()

        new_instruction = Instruction(
            dmc=dmc,
            project_id=project.id,
            title=title,
            content=content,
            part_id=part_id if part_id is not None else old_instruction.part_id,
            animation_step_id=animation_step_id if animation_step_id is not None else old_instruction.animation_step_id,
            file_path=safe_filename,
            is_current=True
        )

        db.session.add(new_instruction)
        db.session.commit()

        return new_instruction

    @staticmethod
    def get_by_id(instruction_id: int) -> Instruction:
        # Получить инструкцию по ID 
        instruction = Instruction.query.get(instruction_id)
        if instruction is None:
            raise InstructionNotFoundError()
        return instruction

    @staticmethod
    def get_current_by_dmc(dmc: str) -> Instruction:
        # Получить актуальную версию инструкции по DMC
        instruction = Instruction.query.filter_by(dmc=dmc, is_current=True).first()
        if instruction is None:
            raise InstructionNotFoundError()
        return instruction

    @staticmethod
    def get_all_versions_by_dmc(dmc: str) -> list[Instruction]:
        # Получить все версии инструкции с DMC
        versions = Instruction.query.filter_by(dmc=dmc).order_by(Instruction.created_at.desc()).all()

        if not versions:
            raise InstructionNotFoundError()
        return versions

    @staticmethod
    def delete(instruction_id: int) -> None:
        instruction = InstructionService.get_by_id(instruction_id)

        if instruction.is_current:
            previous_version = Instruction.query.filter(
                Instruction.dmc == instruction.dmc,
                Instruction.id != instruction_id
            ).order_by(Instruction.created_at.desc()).first()

            if previous_version:
                previous_version.is_current = True
                db.session.add(previous_version)
                    
        # Удаляем файл с диска
        if instruction.file_path:
            upload_folder = InstructionService._get_upload_folder()
            filepath = os.path.join(upload_folder, instruction.file_path)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass
        
        db.session.delete(instruction)
        db.session.commit()

    @staticmethod
    def get_instructions_list(project_id: int = None, part_id: int = None) -> list[Instruction]:
        # Получить список инструкций с фильтрами
        query = Instruction.query

        if project_id:
            query = query.filter(Instruction.project_id == project_id)
        if part_id:
            query = query.filter(Instruction.part_id == part_id)

        return query.filter(Instruction.is_current == True).order_by(Instruction.created_at.desc()).all()

    @staticmethod
    def get_instruction_file(instruction_id: int) -> dict:
        # Читает .tiptap файл и возвращает его содержимое как JSON
        
        instruction = Instruction.query.get(instruction_id)
        if not instruction:
            raise InstructionNotFoundError()

        if not instruction.file_path:
            raise PhysicalFileNotFoundError('У инструкции нет сохранённого файла')

        upload_folder = InstructionService._get_upload_folder()
        filepath = os.path.join(upload_folder, instruction.file_path)

        if not os.path.exists(filepath):
            raise PhysicalFileNotFoundError('Файл инструкции не найден на диске')

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            raise FileSaveError('Файл инструкции поврежден или не является валидным JSON')
        except Exception as e:
            raise FileSaveError(f'Не удалось прочитать файл инструкции: {str(e)}')

    @staticmethod
    def search_instructions(query: str, project_id: int = None) -> list[Instruction]:
        if not query or not query.strip():
            return []

        clean_query = query.strip()

        # Вектор для поиска по заголовку
        search_vector_title = func.to_tsvector('russian', func.coalesce(Instruction.title, ''))

        # Вектор для поиска по содержимому
        search_vector_content = func.to_tsvector('russian', func.coalesce(Instruction.content.cast(db.Text), ''))

        search_query = func.plainto_tsquery('russian', clean_query)

        # Полнотекстовое совпадение или нечеткое совпадение по триаграммам
        stmt = Instruction.query.filter(
            or_(
                search_vector_title.op('@@')(search_query),
                search_vector_content.op('@@')(search_query),
                Instruction.title.ilike(f'%{clean_query}%'),
                Instruction.dmc.ilike(f'%{clean_query}%')
            )
        )

        # Фильтр по проекту(если передан)
        if project_id:
            stmt = stmt.filter(Instruction.project_id == project_id)

        # Поиск только актуальных версий
        stmt = stmt.filter(Instruction.is_current == True)
        
        # Сортировка по релевантности 
        stmt = stmt.order_by(
            func.ts_rank(search_vector_title, search_query).desc(),
            func.ts_rank(search_vector_content, search_query).desc()
        )

        return stmt.all()


instruction_service = InstructionService()