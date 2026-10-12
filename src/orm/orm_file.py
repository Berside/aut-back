from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func, Boolean
from src.db import db
from src.orm.orm_task import Task
from src.orm.orm_list import DictResource


class TaskFile(db.Model):
    __table_args__ = {
        'schema': 'storage',
        'comment': 'Файлы задач'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор файла')
    task_link = Column(Integer, ForeignKey(Task.id), comment='Задача')
    original_name = Column(String(255), nullable=False, comment='Оригинальное имя файла')
    storage_filename = Column(String(255), nullable=False, comment='Имя файла на диске')
    file_size = Column(Integer, comment='Размер файла в байтах')
    mime_type = Column(String(100), comment='MIME тип файла')
    upload_date = Column(DateTime, default=func.now(), comment='Дата загрузки файла')
    uploaded_by = Column(Integer, comment='ID пользователя, загрузившего файл')
    access_groups = Column(String(255), comment='Группы, имеющие доступ к файлу') # TODO: сделать нормально через связь

    Task = relationship('Task', back_populates='TaskFile')


class RepairDocumentation(db.Model):
    __table_args__ = {
        'schema': 'storage',
        'comment': 'Ремонтная документация'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор файла')
    name = Column(Text, comment='Наименование изделия')
    original_name = Column(String(255), nullable=False, comment='Оригинальное имя файла')
    storage_filename = Column(String(255), nullable=False, comment='Имя файла на диске')
    file_size = Column(Integer, comment='Размер файла в байтах')
    mime_type = Column(String(100), comment='MIME тип файла')
    upload_date = Column(DateTime, default=func.now(), comment='Дата загрузки файла')
    uploaded_by = Column(Integer, comment='ID пользователя, загрузившего файл')
    access_groups = Column(String(255), comment='Группы, имеющие доступ к файлу')


class TaskRepairDocumentation(db.Model):
    __table_args__ = {
        'schema': 'storage',
        'comment': 'Информационная поддержка'
    }
    id = Column(Integer, primary_key=True, comment='Идентификатор файла')
    task_link = Column(Integer, ForeignKey(Task.id), comment='Задача')
    documentation_link = Column(Integer, ForeignKey(RepairDocumentation.id), comment='Задача')

    RepairDocumentation = relationship('RepairDocumentation')


class FormalizedDocuments(db.Model):
    __table_args__ = {
        'schema': 'storage',
        'comment': 'Формализованные документы'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор файла')
    original_name = Column(String(255), nullable=False, comment='Оригинальное имя файла')
    language = Column(Text, comment='Язык')
    storage_filename = Column(String(255), nullable=False, comment='Имя файла на диске')
    file_size = Column(Integer, comment='Размер файла в байтах')
    mime_type = Column(String(100), comment='MIME тип файла')
    upload_date = Column(DateTime, default=func.now(), comment='Дата загрузки файла')
    uploaded_by = Column(Integer, comment='ID пользователя, загрузившего файл')
    access_groups = Column(String(255), comment='Группы, имеющие доступ к файлу')

class TechDocumentation(db.Model):
    __table_args__ = {
        'schema': 'storage',
        'comment': 'Техническая документация'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор файла')
    dict_resource_link = Column(ForeignKey(DictResource.id), comment='Ссылка на материальные ценности')

    prizn = Column(Integer, comment='Признак документа')
    original_name = Column(String(255), nullable=False, comment='Оригинальное имя файла')
    storage_filename = Column(String(255), nullable=False, comment='Имя файла на диске')
    file_size = Column(Integer, comment='Размер файла в байтах')
    mime_type = Column(String(100), comment='MIME тип файла')
    upload_date = Column(DateTime, default=func.now(), comment='Дата загрузки файла')
    uploaded_by = Column(Integer, comment='ID пользователя, загрузившего файл')
    access_groups = Column(String(255), comment='Группы, имеющие доступ к файлу') # TODO: сделать нормально через связь

    DictResource = relationship('DictResource')
