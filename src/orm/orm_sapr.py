from src.db import db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float, func, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import text as sa_text
from datetime import datetime
from uuid import uuid4


class Project(db.Model):
    __tablename__ = 'projects'
    __table_args__ = {'schema': 'sapr', 'comment': 'Проекты САПР'}
    
    id = Column(Integer, primary_key=True, comment='ID проекта')
    name = Column(String(255), nullable=False, comment='Имя проекта')
    description = Column(Text, comment='Описание')
    model_path = Column(String(500), comment='Путь к основной 3D модели')
    created_at = Column(DateTime, server_default=func.now(), comment='Дата создания проекта')

    models = relationship('Models', back_populates='project', cascade='all, delete-orphan', passive_deletes=True)
    assembly_items = relationship('AssemblyItem', back_populates='project', cascade='all, delete-orphan', passive_deletes=True)
    project_parts = relationship('ProjectPart', back_populates='project', cascade='all, delete-orphan', passive_deletes=True)
    animation_steps = relationship('AnimationStep', back_populates='project', cascade='all, delete-orphan', passive_deletes=True)
    sapr_tree = relationship('SaprTree', back_populates='project', cascade='all, delete-orphan', passive_deletes=True)
    instructions = relationship('Instruction', back_populates='project', cascade='all, delete-orphan', passive_deletes=True)


class Models(db.Model):
    __tablename__ = 'models'
    __table_args__ = {'schema': 'sapr', 'comment': '3D модели проектов'}

    id = Column(Integer, primary_key=True, comment='ID модели')
    project_id = Column(Integer, ForeignKey(Project.id, ondelete='CASCADE'), nullable=False, comment='ID проекта')
    name = Column(String(255), primary_key=False, comment='Имя модели')
    technical_name = Column(Text, nullable=True, comment='Техническое имя файла модели')
    is_primary = Column(Boolean, default=False, comment='Флаг основной модели')
    created_at = Column(DateTime, server_default=func.now(), comment='Дата создания')

    project = relationship('Project', back_populates='models')
    assembly_items = relationship('AssemblyItem', back_populates='model')


class AnimationStep(db.Model):
    __tablename__ = 'animation_steps'
    __table_args__ = {'schema': 'sapr', 'comment': 'Шаги анимации сборки'}

    id = Column(Integer, primary_key=True, comment='ID шага анимации')
    project_id = Column(Integer, ForeignKey(Project.id, ondelete='CASCADE'), nullable=True, comment='ID проекта')
    model_id = Column(Integer, ForeignKey(Models.id, ondelete='SET NULL'), nullable=True, comment='ID модели')
    name = Column(String(255), nullable=False, comment='Название шага')
    duration = Column(Float, default=1.0, comment='Длительность шага в секундах')
    order = Column(Integer, default=0, comment='Порядок шага')
    is_active = Column(Boolean, default=True, comment='Флаг активности')

    camera_position = Column(JSONB, server_default=sa_text("'{}'::jsonb"), default={"x": 0, "y": 0, "z": 0}, comment='Позиция камеры')
    camera_target = Column(JSONB, server_default=sa_text("'{}'::jsonb"), default={"x": 0, "y": 0, "z": 0}, comment='Цель камеры')
    animation_ids = Column(JSONB, server_default=sa_text("'[]'::jsonb"), default=[], comment='ID анимаций')

    created_at = Column(DateTime, server_default=func.now(), comment='Дата создания')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='Дата обновления')

    project = relationship('Project', back_populates='animation_steps')
    model = relationship('Models', backref='animation_steps')


class PartCategory(db.Model):
    __tablename__ = 'part_categories'
    __table_args__ = {'schema': 'sapr', 'comment': 'Категории деталей'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID категории')
    name = Column(String(255), nullable=False, comment='Название категории')
    parent_id = Column(Integer, ForeignKey(id, ondelete='CASCADE'), nullable=True, comment='ID родительской категории')
    sort_order = Column(Integer, default=0, comment='Порядок сортировки')
    created_at = Column(DateTime, default=datetime.utcnow, comment='Дата создания')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Дата обновления')

    parent = relationship('PartCategory', remote_side=[id], backref='children')


class PartType(db.Model):
    __tablename__ = 'part_types'
    __table_args__ = {'schema': 'sapr', 'comment': 'Типы деталей'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID типа')
    name = Column(String(255), nullable=False, comment='Название типа')
    category_id = Column(Integer, ForeignKey(PartCategory.id, ondelete='CASCADE'), nullable=True, comment='ID категории')
    created_at = Column(DateTime, default=datetime.utcnow, comment='Дата создания')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Дата обновления')

    category = relationship('PartCategory', backref='types')


class Item(db.Model):
    __tablename__ = 'item'
    __table_args__ = {
        'schema': 'sapr',
        'comment': 'Базовый справочник изделий'
    }

    id = Column(Integer, primary_key=True, comment='ID изделия')
    article = Column(String(100), unique=True, nullable=False, comment='Артикул')
    standard = Column(Text, nullable=True, comment='Стандарт/ГОСТ')
    name = Column(String(255), nullable=False, comment='Наименование')
    unit = Column(String(20), default='шт', comment='Единица измерения')

    description = Column(Text, nullable=True, comment='Описание')
    note = Column(Text, nullable=True, comment='Примечание')
    photo_path = Column(String(500), nullable=True, comment='Путь к изображению')
    stock_quantity = Column(Integer, default=0, comment='Количество на складе')

    model_spta = relationship('ModelSpta', back_populates='item')
    assembly_item_spta = relationship('AssemblyItemSpta', back_populates='item')
    bom_lines_as_parent = relationship('BomLine', foreign_keys='BomLine.parent_item_id', back_populates='parent_item')
    bom_lines_as_child = relationship('BomLine', foreign_keys='BomLine.child_item_id', back_populates='child_item')
    repair_tools_as_target = relationship('RepairTool', foreign_keys='RepairTool.for_item_id', back_populates='for_item')
    repair_tools_as_tool = relationship('RepairTool', foreign_keys='RepairTool.tool_item_id', back_populates='tool_item')


class Part(db.Model):
    __tablename__ = 'parts'
    __table_args__ = {'schema': 'sapr', 'comment': 'Библиотека деталей'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID детали')
    name = Column(String(255), nullable=False, comment='Название детали')
    part_number = Column(String(100), unique=True, nullable=True, comment='Артикул детали')
    description = Column(Text, nullable=True, comment='Описание детали')
    category_id = Column(Integer, ForeignKey(PartCategory.id, ondelete='SET NULL'), nullable=True, comment='ID категории')
    type_id = Column(Integer, ForeignKey(PartType.id, ondelete='SET NULL'), nullable=True, comment='ID типа')
    parameters = Column(JSONB, server_default='{}', comment='Параметры детали')
    model_id = Column(Integer, ForeignKey(Models.id, ondelete='SET NULL'), nullable=True, comment='ID 3D модели')
    technical_name = Column(String(500), nullable=True, comment='Техническое имя файла в хранилище')
    preview_image = Column(String(500), nullable=True, comment='Путь к превью')
    unit = Column(String(20), server_default="'шт'", comment='Единица измерения')
    is_standard = Column(Boolean, server_default=sa_text('true'), comment='Флаг стандартной детали')
    is_active = Column(Boolean, server_default=sa_text('true'), comment='Флаг активности')
    created_by = Column(Integer, nullable=True, comment='ID создателя')
    created_at = Column(DateTime, default=datetime.utcnow, comment='Дата создания')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Дата обновления')

    item_id = Column(Integer, ForeignKey(Item.id, ondelete='SET NULL'), nullable=True, comment='ID складской позиции')

    category = relationship('PartCategory', backref='parts')
    type = relationship('PartType', backref='parts')
    model = relationship('Models', backref='parts')
    item = relationship('Item', backref='parts')


class ProjectPart(db.Model):
    __tablename__ = 'project_parts'
    __table_args__ = {'schema': 'sapr', 'comment': 'Связь проектов и деталей'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID связи')
    project_id = Column(Integer, ForeignKey(Project.id, ondelete='CASCADE'), nullable=False, comment='ID проекта')
    part_id = Column(Integer, ForeignKey(Part.id, ondelete='CASCADE'), nullable=False, comment='ID детали')
    quantity = Column(Integer, default=1, comment='Количество')
    custom_parameters = Column(JSONB, server_default='{}', comment='Кастомные параметры')
    added_at = Column(DateTime, default=datetime.utcnow, comment='Дата добавления')
    added_by = Column(Integer, nullable=True, comment='ID добавившего')

    project = relationship('Project', back_populates='project_parts')
    part = relationship('Part', backref='project_parts')


class AssemblyItem(db.Model):
    __tablename__ = 'assembly_items'
    __table_args__ = {'schema': 'sapr', 'comment': 'Элементы сборки (дерево конструкции)'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID элемента')
    project_id = Column(Integer, ForeignKey(Project.id, ondelete='CASCADE'), nullable=False, comment='ID проекта')
    name = Column(String(255), nullable=False, comment='Название элемента')
    model_id = Column(Integer, ForeignKey(Models.id, ondelete='CASCADE'), nullable=True, comment='ID 3D модели')
    part_id = Column(Integer, ForeignKey(Part.id, ondelete='SET NULL'), nullable=True, comment='ID детали')
    item_id = Column(Integer, ForeignKey(Item.id, ondelete='SET NULL'), nullable=True, comment='ID складской позиции')
    parent_id = Column(Integer, ForeignKey(id, ondelete='CASCADE'), nullable=True, comment='ID родительского элемента')
    order = Column(Integer, default=0, nullable=False, comment='Порядок сортировки')
    created_at = Column(DateTime, server_default=func.now(), comment='Дата создания')

    item = relationship('Item', backref='assembly_items')
    project = relationship('Project', back_populates='assembly_items')
    model = relationship('Models', back_populates='assembly_items')
    part = relationship('Part', backref='assembly_items')
    parent = relationship('AssemblyItem', remote_side=[id], backref='children', foreign_keys=[parent_id])


class AssemblyPartLink(db.Model):
    __tablename__ = 'assembly_part_links'
    __table_args__ = {'schema': 'sapr', 'comment': 'Связь элементов сборки и деталей'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID связи')
    assembly_item_id = Column(Integer, ForeignKey(AssemblyItem.id, ondelete='CASCADE'), nullable=False, comment='ID элемента сборки')
    part_id = Column(Integer, ForeignKey(Part.id, ondelete='CASCADE'), nullable=False, comment='ID детали')
    quantity = Column(Integer, default=1, comment='Количество')
    position = Column(JSONB, server_default='{"x": 0, "y": 0, "z": 0}', comment='Позиция')
    rotation = Column(JSONB, server_default='{"x": 0, "y": 0, "z": 0}', comment='Поворот')
    created_at = Column(DateTime, default=datetime.utcnow, comment='Дата создания')

    assembly_item = relationship('AssemblyItem', backref='part_links')
    part = relationship('Part', backref='assembly_links')


class Instruction(db.Model):
    __tablename__ = 'instructions'
    __table_args__ = {'schema': 'sapr', 'comment': 'Интерактивные инструкции (Data Modules)'}

    id = Column(Integer, primary_key=True, autoincrement=True)

    dmc = Column(String(64), nullable=False, comment='Data Module Code')
    project_id = Column(Integer, ForeignKey(Project.id, ondelete='CASCADE'), nullable=False, comment='ID проекта')
    part_id = Column(Integer, ForeignKey(Part.id, ondelete='SET NULL'), nullable=True, comment='ID детали')

    animation_step_id = Column(Integer, ForeignKey(AnimationStep.id, ondelete='SET NULL'), nullable=True, comment='ID шага анимации')

    title = Column(String(255), nullable=False, comment='Название инструкции')
    content = Column(JSONB, nullable=True, comment='Содержание инструкции в формате TipTap JSON')

    file_path = Column(String(255), nullable=True, comment='Путь к .tiptap файлу')

    is_current = Column(Boolean, server_default=sa_text('true'), comment='Флаг версии')

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship('Project', back_populates='instructions')
    part = relationship('Part', backref='instructions')


class TreeItemType:
    FOLDER = 'folder'
    FILE = 'file'
    MODEL = 'model'


class SaprTree(db.Model):
    __tablename__ = 'sapr_tree'
    __table_args__ = {
        'schema': 'sapr',
        'comment': 'Древовидная структура проекта САПР'
    }

    id = Column(Integer, primary_key=True, comment='ID элемента дерева')
    name = Column(String(255), nullable=False, comment='Название элемента')
    item_type = Column(String(20), nullable=False, comment='Тип элемента (folder/file/model)')
    parent_link = Column(Integer, ForeignKey(id, ondelete='CASCADE'), nullable=True, comment='ID родительского элемента')
    project_id = Column(Integer, ForeignKey(Project.id, ondelete='CASCADE'), nullable=False, comment='ID проекта')

    instruction_id = Column(Integer, ForeignKey(Instruction.id, ondelete='SET NULL'), nullable=True, comment='ID связанной инструкции')
    model_id = Column(Integer, ForeignKey(Models.id, ondelete='SET NULL'), nullable=True, comment='ID связанной 3D модели')

    position = Column(Integer, default=0, comment='Позиция для сортировки')

    parent = relationship('SaprTree', remote_side=[id], backref='children', overlaps='children')
    project = relationship('Project', back_populates='sapr_tree')
    instruction = relationship('Instruction', backref='tree_items')
    model = relationship('Models', backref='tree_items')


class History(db.Model):
    __tablename__ = 'history'
    __table_args__ = {
        'schema': 'sapr',
        'comment': 'История действий пользователя'
    }

    id = Column(Integer, primary_key=True, comment='ID записи')
    user_id = Column(Integer, nullable=True, comment='ID пользователя')
    endpoint = Column(String(255), nullable=False, comment='Вызванный эндпоинт')
    method = Column(String(10), nullable=False, comment='HTTP метод')
    timestamp = Column(DateTime, server_default=func.now(), comment='Время доступа')


class ModelStructureNode(db.Model):
    __tablename__ = 'model_structure_nodes'
    __table_args__ = {
        'schema': 'sapr',
        'comment': 'Иерархия декомпозиции модели(сборки и детали)'
    }

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()), comment='UUID узла структуры')
    parent_id = Column(String(36), ForeignKey(id, ondelete='CASCADE'), nullable=True, comment='ID родительского узла')

    name = Column(String(255), nullable=False, comment='Название узла')
    description = Column(Text, nullable=True, comment='Описание')
    code = Column(String(100), unique=True, nullable=False, comment='Код изделия (например, 536.3902150 РЭ)')

    model_id = Column(Integer, ForeignKey(Models.id, ondelete='SET NULL'), nullable=True, comment='ID связанной модели (если это сборка)')
    part_id = Column(Integer, ForeignKey(Part.id, ondelete='SET NULL'), nullable=True, comment='ID связанной детали (если это конечный элемент)')

    position = Column(Integer, default=0, comment='Позиция для сортировки')
    created_at = Column(DateTime, server_default=func.now(), comment='Дата создания')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='Дата обновления')

    parent = relationship('ModelStructureNode', remote_side=[id], backref='children', foreign_keys=[parent_id])
    model = relationship('Models', backref='structure_nodes')
    part = relationship('Part', backref='structure_nodes')


class BomLine(db.Model):
    __tablename__ = 'bom_line'
    __table_args__ = {
        'schema': 'sapr',
        'comment': 'Ведомость материалов'
    }

    id = Column(Integer, primary_key=True, comment='ID строки спецификации')
    parent_item_id = Column(Integer, ForeignKey(Item.id, ondelete='CASCADE'), nullable=False, comment='ID родительского изделия')
    child_item_id = Column(Integer, ForeignKey(Item.id, ondelete='CASCADE'), nullable=False, comment='ID дочернего изделия')
    quantity = Column(Float, default=1, comment='Количество')

    parent_item = relationship('Item', foreign_keys=[parent_item_id], back_populates='bom_lines_as_parent')
    child_item = relationship('Item', foreign_keys=[child_item_id], back_populates='bom_lines_as_child')


class ModelSpta(db.Model):
    __tablename__ = 'model_spta'
    __table_args__ = {
        'schema': 'sapr',
        'comment': 'Состав 3D модели'
    }

    model_id = Column(Integer, ForeignKey(Models.id, ondelete='CASCADE'), primary_key=True, comment='ID модели')
    item_id = Column(Integer, ForeignKey(Item.id, ondelete='CASCADE'), primary_key=True, comment='ID изделия в составе модели')

    model = relationship('Models', backref='spta_items')
    item = relationship('Item', back_populates='model_spta')


class AssemblyItemSpta(db.Model):
    __tablename__ = 'assembly_item_spta'
    __table_args__ = {
        'schema': 'sapr',
        'comment': 'Состав узла сборки'
    }

    assembly_item_id = Column(Integer, ForeignKey(AssemblyItem.id, ondelete='CASCADE'), primary_key=True, comment='ID узла сборки')
    item_id = Column(Integer, ForeignKey(Item.id, ondelete='CASCADE'), primary_key=True, comment='ID изделия в составе узла')

    assembly_item = relationship('AssemblyItem', backref='spta_items')
    item = relationship('Item', back_populates='assembly_item_spta')


class RepairTool(db.Model):
    __tablename__ = 'repair_tool'
    __table_args__ = {
        'schema': 'sapr',
        'comment': 'Связь изделия и инструмента для ремонта'
    }

    id = Column(Integer, primary_key=True, comment='ID записи')
    for_item_id = Column(Integer, ForeignKey(Item.id, ondelete='CASCADE'), nullable=False, comment='ID ремонтируемого изделия')
    tool_item_id = Column(Integer, ForeignKey(Item.id, ondelete='CASCADE'), nullable=False, comment='ID используемого инструмента')
    quantity = Column(Float, default=1, comment='Кол-во инструментов для ремонта')

    for_item = relationship('Item', foreign_keys=[for_item_id], back_populates='repair_tools_as_target')
    tool_item = relationship('Item', foreign_keys=[tool_item_id], back_populates='repair_tools_as_tool')

    
