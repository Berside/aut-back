# coding: utf-8
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.schema import FetchedValue
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean, func
from src.db import db
from src.orm.orm_cls import DictJobTitle, DictResource
from src.orm.orm_list import ListEmployee, ListDepartment


class DataVersion(db.Model):
    __table_args__ = {'schema': 'sys', 'comment': 'Загруженные файлы данных' }

    id = Column(Integer, primary_key=True, comment='Индификатор')
    name_version = Column(String, nullable=False, comment='Название загруженных файлов')
    date_upload = Column(Date, server_default=FetchedValue(), comment='Время загрузки файла данных')


class User(db.Model):
    __table_args__ = {'schema': 'sys',
                    'comment': 'Пользователи'
                    }

    id = Column(Integer, comment = 'Идентификатор', primary_key=True)
    name_ru = Column(String,  comment='Наименование русское')
    name_en = Column(String, comment='Наименование английское')
    employee_link = Column(ForeignKey(ListEmployee.id), comment='Сотдруник')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    ListEmployee = relationship("ListEmployee")


class FileType(db.Model):
    __table_args__ = {'schema': 'sys',
                'comment': 'Типы файлов'
                }
    id = Column(Integer, primary_key=True, comment='Идентификатор')
    name = Column(String, nullable=False, comment='Наименование типа')
    note = Column(String, comment='Примечание')
    config_path = Column(String, nullable=False, comment='Путь к JSON-правилам')
    parser_class = Column(String, nullable=False, comment='Класс')


class Notification(db.Model):
    __table_args__ = { 'schema': 'sys',  'comment': 'Оповещения пользователя'}

    id = Column(Integer, primary_key=True, comment='Ключ')
    title = Column(String, comment='Заголовок оповещения')
    text = Column(String, comment='Оповещение')
    datetime = Column(DateTime, comment='Дата/время')
    task_link = Column(Integer, comment='Задача')
    user_link = Column(ForeignKey(User.id), comment='Пользователь')
    read = Column(Boolean, comment='Прочитано')

    User = relationship("User")
