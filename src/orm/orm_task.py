#!/usr/bin/python3
# -*- coding: utf-8 -*-
from src.db import db
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean, func

from src.orm import orm_cls
from src.orm.orm_cls import DictJobTitle
from src.orm.orm_list import ListEmployee, ListDepartment, ListArticle, ListTechnologicalEquipment


class Task(db.Model):
    __table_args__ = {
        'schema': 'task',
        'comment': 'Задача'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    name = Column(String, comment = "Наименование задачи", nullable=False)
    status_link = Column(ForeignKey(orm_cls.DictStatusTask.id), comment="Статус", default=1)
    department_link =Column(ForeignKey(ListDepartment.id), comment = "Подразделение")
    job_title_signed_link = Column(ForeignKey(DictJobTitle.id), comment = "Должность принявшего задачу")
    job_title_assignee_link = Column(ForeignKey(DictJobTitle.id), comment = "Должность ответственного за задачу")
    assignee_link = Column(ForeignKey(ListEmployee.id), comment = "Ответственный")
    signed_link = Column(ForeignKey(ListEmployee.id), comment = "Принявший задачу")
    type_link = Column(ForeignKey(orm_cls.DictTypeTask.id), comment = "Тип задачи")
    parent_link = Column(ForeignKey(id, ondelete='CASCADE'), comment = "Родительская задачу")
    labor_costs = Column(Integer, comment = 'Трудозатраты, чел.-ч')
    condition = Column(Boolean, comment = "Условие")
    production_task = Column(Boolean, comment = "Признак участия в производственном задании")
    start_date = Column(DateTime, comment = "Дата/время начала")
    end_date = Column(DateTime, comment = "Дата/время окончания")
    created_at = Column(DateTime, comment = "Дата/время создания задачи", default=func.now())
    updated_at = Column(DateTime, comment = "Дата/время обновления задачи", default=func.now())
    note = Column(String, comment = "Примечание")

    DictTypeTask = relationship("DictTypeTask")
    DictStatusTask = relationship("DictStatusTask")
    Parent = relationship("Task", remote_side=[id], back_populates="Children")
    Children = relationship("Task", back_populates="Parent")
    Assignee = relationship("ListEmployee", foreign_keys=[assignee_link])
    Signed = relationship("ListEmployee", foreign_keys=[signed_link])
    InputJob = relationship("DictJobTitle", foreign_keys=[job_title_signed_link])
    OutputJob = relationship("DictJobTitle", foreign_keys=[job_title_assignee_link])
    PreviousTask = relationship("Task", secondary="task.task_previous_next",
                                primaryjoin="or_(Task.id == TaskPreviousNext.next_link, Task.id == TaskPreviousNext.choice_neg_task_link)",
                                secondaryjoin="Task.id == TaskPreviousNext.previous_link", viewonly=True, uselist=True)
    NextTask = relationship("Task", secondary="task.task_previous_next",
                            primaryjoin="Task.id == TaskPreviousNext.previous_link",
                                secondaryjoin="Task.id == TaskPreviousNext.next_link", viewonly=True, uselist=False)
    ChoiceNegTask = relationship("Task", secondary="task.task_previous_next",
                                primaryjoin="Task.id == TaskPreviousNext.previous_link",
                                secondaryjoin="Task.id == TaskPreviousNext.choice_neg_task_link", viewonly=True, uselist=False)
    TaskFile = relationship('TaskFile', back_populates='Task')

    TaskRepairDocumentation = relationship('TaskRepairDocumentation') #Информационная поддержка
    TaskZip = relationship("TaskZip") #Расход ЗИП
    TaskTool = relationship("TaskTool") #Применяемое оборудование
    TechnologicalEquipmentWork = relationship("TechnologicalEquipmentWork", back_populates='Task') #Работы по технологическому оборудованию
    TaskArticleWork = relationship("TaskArticleWork") #Работы по изделию
    ListDepartment = relationship('ListDepartment') #Подразделение
    TaskDocTypes = relationship('TaskDocTypes') #Типы документов в задаче

    RepairAct = relationship("RepairAct", back_populates='Task') #Акт на сдачу в ремонт
    Order = relationship("Order") #Наряд
    ReceiveTransfer = relationship("ReceiveTransfer", back_populates='Task') #Акт приема-передачи
    DeliveryNote = relationship("DeliveryNote", back_populates='Task') #Накладная


class TaskArticleWork(db.Model):
    __table_args__ = {
        'schema': 'task',
        'comment': 'Работы по изделию'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    work_order = Column(Integer, comment = "Номер производственного задания")
    breakdown_date = Column(DateTime, comment= 'Дата выхода из строя ОР')
    received_date = Column(DateTime, comment= 'Дата поступления ОР в ремонт')
    diagnostic_summary  = Column(String, comment = "Заключение")
    task_link = Column(ForeignKey(Task.id), comment = 'Задача')
    object_link = Column(ForeignKey(ListArticle.id), comment = 'Изделие' )
    type_repair_link = Column(ForeignKey(orm_cls.DictKindRepair.id), comment='Вид ремонта')

    ListArticle = relationship("ListArticle")
    DictKindRepair = relationship("DictKindRepair")


class TaskPreviousNext(db.Model):
    __table_args__ = {
        'schema': 'task',
        'comment': 'Связь задачи с предыдущей и последующей'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    previous_link = Column(ForeignKey(Task.id), comment = "Предыдущая задачу")
    next_link = Column(ForeignKey(Task.id), comment = "Следующая задачу(При положительном условии)")
    choice_neg_task_link = Column(ForeignKey(Task.id), comment = "Следующая задачу(При отрицательном условии)")


class TaskZip(db.Model):
    __table_args__ = {
        'schema': 'task',
        'comment': 'Расход ЗИП'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    task_link = Column(ForeignKey(Task.id), nullable=False, comment = "Задача")
    zip_link = Column(ForeignKey(orm_cls.DictResource.id), nullable=False, comment = "Используемый ЗИП")
    okei_link = Column(ForeignKey(orm_cls.DictOkei.id), comment='Единица измерения')
    kol_pln = db.Column(Float, comment = "Планируемый расход")
    increase = db.Column(Float, comment = "Прибыло")
    decrease = db.Column(Float, comment = "Убыло (расход)")

    DictResource = relationship("DictResource")
    DictOkei = relationship("DictOkei")


class TaskTool(db.Model):
    __table_args__ = {
        'schema': 'task',
        'comment': 'Применяемое оборудование'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    task_link = Column(ForeignKey(Task.id), nullable=False, comment = "Задача")
    tool_link = Column(ForeignKey(orm_cls.DictResource.id), nullable=False, comment = "Используемое оборудование")

    DictResource = relationship("DictResource")


class TaskDocTypes(db.Model):
    __table_args__ = {
        'schema': 'task',
        'comment': 'Типы документов в задаче'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    task_link = Column(ForeignKey(Task.id), comment='Задача')
    document_type_link = Column(ForeignKey(orm_cls.DictTypeDocument.id), comment='Тип документа')
    employee_id = Column(ForeignKey(ListEmployee.id), comment='Сотрудник')

    DictTypeDocument = relationship("DictTypeDocument", foreign_keys=[document_type_link])
    ListEmployee = relationship("ListEmployee", foreign_keys=[employee_id])


class TechnologicalEquipmentWork(db.Model):
    __table_args__ = {'schema': 'task', 'comment': 'Работы по технологическому оборудованию'}

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    work_order = Column(Integer, comment = "Номер производственного задания", nullable=False)
    breakdown_date = Column(DateTime, comment= 'Дата выхода из строя ОР')
    received_date = Column(DateTime, comment= 'Дата поступления ОР в ремонт')
    diagnostic_summary  = Column(String, comment = "Наименование задачи", nullable=False)
    task_link = Column(ForeignKey('task.task.id'), comment = 'Задача')
    equipment_link = Column(ForeignKey(ListTechnologicalEquipment.id), comment='Технологического оборудование')
    kind_repair_link = Column(ForeignKey(orm_cls.DictKindRepair.id), comment='Технологическое оборудование')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    Task = relationship("Task", back_populates="TechnologicalEquipmentWork")
    ListTechnologicalEquipment = relationship("ListTechnologicalEquipment")
    DictKindRepair = relationship("DictKindRepair")

## Template: дальше дороги нет - здесь живут драконы
class TemplateTask(db.Model):
    __table_args__ = {
        'schema': 'task',
        'comment': 'Типовая задача'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    name = Column(String, comment = "Наименование задачи", nullable=False)
    job_title_signed_link = Column(ForeignKey(DictJobTitle.id), comment = "Должность принявшего задачу")
    job_title_assignee_link = Column(ForeignKey(DictJobTitle.id), comment = "Должность ответственного за задачу")
    type_link = Column(ForeignKey(orm_cls.DictTypeTask.id), comment = "Тип задачи")
    department_link =Column(ForeignKey(ListDepartment.id), comment = "Подразделение")
    parent_link = Column(ForeignKey(id, ondelete='CASCADE'), comment = "Родительская задача")
    production_task = Column(Boolean, comment = "Признак участия в производственном задании")
    labor_costs = Column(Integer, comment = 'Трудозатраты, чел.-ч')
    created_at = Column(DateTime, comment = "Дата/время создания задачи", default=func.now())
    updated_at = Column(DateTime, comment = "Дата/время обновления задачи", default=func.now())
    note = Column(String, comment = "Примечание")

    DictTypeTask = relationship("DictTypeTask")
    Parent = relationship("TemplateTask", remote_side=[id], back_populates="Children")
    Children = relationship("TemplateTask", back_populates="Parent")
    InputJob = relationship("DictJobTitle", foreign_keys=[job_title_signed_link])
    OutputJob = relationship("DictJobTitle", foreign_keys=[job_title_assignee_link])
    PreviousTask = relationship("TemplateTask", secondary="task.template_task_previous_next",
                                primaryjoin="or_(TemplateTask.id == TemplateTaskPreviousNext.next_link, TemplateTask.id == TemplateTaskPreviousNext.choice_neg_task_link)",
                                secondaryjoin="TemplateTask.id == TemplateTaskPreviousNext.previous_link", viewonly=True, uselist=True)
    NextTask = relationship("TemplateTask", secondary="task.template_task_previous_next",
                            primaryjoin="TemplateTask.id == TemplateTaskPreviousNext.previous_link",
                                secondaryjoin="TemplateTask.id == TemplateTaskPreviousNext.next_link", viewonly=True, uselist=False)
    ChoiceNegTask = relationship("TemplateTask", secondary="task.template_task_previous_next",
                                primaryjoin="TemplateTask.id == TemplateTaskPreviousNext.previous_link",
                                secondaryjoin="TemplateTask.id == TemplateTaskPreviousNext.choice_neg_task_link", viewonly=True, uselist=False)
    ListDepartment = relationship('ListDepartment')
    TaskZip = relationship("TemplateTaskZip")
    TaskTool = relationship("TemplateTaskTool")
    TemplateTaskArticleWork = relationship("TemplateTaskArticleWork", back_populates="TemplateTask")
    TaskDocTypes = relationship('TemplateTaskDocTypes')


class TemplateTaskPreviousNext(db.Model):
    __table_args__ = {
        'schema': 'task',
        'comment': 'Шаблонная связь задачи шаблона с предыдущей и последующей'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    previous_link = Column(ForeignKey(TemplateTask.id), comment="Предыдущая задача")
    next_link = Column(ForeignKey(TemplateTask.id), comment="Следующая задача шаблона(При положительном условии)")
    choice_neg_task_link = Column(ForeignKey(TemplateTask.id), comment = "Следующая задача шаблона(При отрицательном условии)")


class TemplateTaskZip(db.Model):
    __table_args__ = {
        'schema': 'task',
        'comment': 'Расход ЗИП в типовой задаче'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    task_link = Column(ForeignKey(TemplateTask.id), nullable=False, comment="Типовая задача")
    zip_link = Column(ForeignKey(orm_cls.DictResource.id), nullable=False, comment="Используемое оборудование")
    kol_pln = db.Column(Float, comment="Планируемый расход")
    increase = db.Column(Float, comment="Прибыло")
    decrease = db.Column(Float, comment="Убыло (расход)")

    DictResource = relationship("DictResource")


class TemplateTaskTool(db.Model):
    __table_args__ = {
        'schema': 'task',
        'comment': 'Применяемое оборудование в типовой задаче'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    task_link = Column(ForeignKey(TemplateTask.id), nullable=False, comment="Типовая задачу")
    tool_link = Column(ForeignKey(orm_cls.DictResource.id), nullable=False, comment = "Используемое оборудование")

    DictResource = relationship("DictResource")


class TemplateTaskArticleWork(db.Model):
    __table_args__ = {
        'schema': 'task',
        'comment': 'Типовая работа по изделию'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    task_link = Column(ForeignKey(TemplateTask.id), comment="Задача")
    resource_type_link = Column(ForeignKey(orm_cls.DictResourceType.id), comment="Тип изделия")
    object_link = Column(ForeignKey(orm_cls.DictResource.id), nullable=False, comment="Изделие")

    DictResource = relationship("DictResource")
    TemplateTask = relationship("TemplateTask", back_populates="TemplateTaskArticleWork")


class TemplateTaskDocTypes(db.Model):
    __table_args__ = {
        'schema': 'task',
        'comment': 'Типы документов в типовой задаче'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    template_task_link = Column(ForeignKey(TemplateTask.id), comment='Типовая задачу')
    document_type_link = Column(ForeignKey(orm_cls.DictTypeDocument.id), comment='Тип документа')

    DictTypeDocument = relationship("DictTypeDocument", foreign_keys=[document_type_link])
