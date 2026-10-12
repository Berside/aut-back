# coding: utf-8
from src.db import db
from src.orm import orm_cls, orm_list, orm_task
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean, func, UniqueConstraint

from src.orm.orm_task import Task


class TaskRemDoc(db.Model):
    __table_args__ = { 'schema': 'rem_doc',  'comment': 'Связь задачи и ремонтной документации'}

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    task_link = Column(ForeignKey(Task.id), comment='Задача')
    rem_doc_link = Column(ForeignKey(orm_list.ListRepairDocumentation.id), comment='Ремонтная документация')

    ListRepairDocumentation = relationship("ListRepairDocumentation")


class TemplateTaskRemDoc(db.Model):
    __table_args__ = { 'schema': 'rem_doc',  'comment': 'Связь типовой задачи и ремонтной документации'}

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    task_link = Column(ForeignKey(orm_task.TemplateTask.id), comment='Типовая задача')
    rem_doc_link = Column(ForeignKey(orm_list.ListRepairDocumentation.id), comment='Ремонтная документация')

    ListRepairDocumentation = relationship("ListRepairDocumentation")


class RemDocTask(db.Model):
    __table_args__ = { 'schema': 'rem_doc',  'comment': 'Связь типа задач и ремонтной документации'}

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    type_link = Column(ForeignKey(orm_cls.DictTypeTask.id), comment='Типы задач')
    rem_doc_link = Column(ForeignKey(orm_list.ListRepairDocumentation.id), comment='Ремонтная документация')

    DictTypeTask = relationship("DictTypeTask")
    ListRepairDocumentation = relationship("ListRepairDocumentation")



