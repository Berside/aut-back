# coding: utf-8
from src.db import db
from src.orm import orm_cls, orm_list
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean, func, UniqueConstraint
from src.orm.orm_cls import DictResource, DictOkei, DictKindRepair
from src.orm.orm_task import Task

class EmployeeAbsence(db.Model):
    __table_args__ = { 'schema': 'employee',  'comment': 'Даты отсутствия сотрудников'}

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    date_output = Column(DateTime, comment='Дата начала отсутствия')
    date_input = Column(DateTime, comment='Дата окончания отсутствия') #TODO Как это сформулировать адекватно?
    employee_link = Column(ForeignKey(orm_list.ListEmployee.id), comment='Отсутствующий сотрудник')
    absence_link = Column(ForeignKey(orm_cls.DictAbsenceCause.id), comment='Основание для отсутствия')
    note = Column(String, comment='Примечание')

    DictAbsenceCause = relationship("DictAbsenceCause")
    ListEmployee = relationship("ListEmployee")


class WorkTimeLabel(db.Model):
    __table_args__ = { 'schema': 'employee',  'comment': 'Графики рабочего времени'}

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    date_output = Column(DateTime, comment='Дата начала рабочего времени')
    date_input = Column(DateTime, comment='Дата окончания рабочего времени') #TODO Как это сформулировать адекватно?
    employee_link = Column(ForeignKey(orm_list.ListEmployee.id), comment='Сотрудник')
    note = Column(String, comment='Примечание')

    ListEmployee = relationship("ListEmployee")


class ProductionSchedule(db.Model):
    __table_args__ = { 'schema': 'employee',  'comment': 'Производственный календарь'}

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    date_output = Column(DateTime, comment='Дата начала рабочего времени')
    date_input = Column(DateTime, comment='Дата окончания рабочего времени')
    note = Column(String, comment='Примечание')


class Positions(db.Model):
    __table_args__ = { 'schema': 'employee',  'comment': 'Производственный календарь'}

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    Positions = Column(String, comment='Штатная должность')
    note = Column(String, comment='Примечание')

    EmployeePositions = relationship("EmployeePositions")


class EmployeePositions(db.Model):
    __table_args__ = { 'schema': 'employee',  'comment': 'Связь штата и реестра сотрудников'}

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    parent_link = Column(ForeignKey(id), comment='Вышестоящая должность')
    positions_link = Column(ForeignKey(Positions.id), comment='Штатная должность')
    employee_link = Column(ForeignKey(orm_list.ListEmployee.id), comment='Сотрудник')
    note = Column(String, comment='Примечание')

    ListEmployee = relationship("ListEmployee")




