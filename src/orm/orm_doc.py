#!/usr/bin/python3
# -*- coding: utf-8 -*-
from src.db import db
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float, Text, Boolean, func, DateTime, Time

from src.orm.orm_task import Task
from src.orm.orm_list import ListEmployee, ListDepartment, ListArticle, ListRepairDocumentation
from src.orm.orm_cls import DictOkei, DictKindRepair, DictTypeDocument
from enum import Enum as Enum

#todo переделать
# class FluidLeak(Enum):
#     """Перечисление отсутствует - имеется """
#     ABSENT = "отсутствует"
#     PRESENT = "имеется"
#
#
# class SystemStatus(Enum):
#     """Перечисление исправна - неисправна """
#     FUNCTIONAL = "исправна"
#     NOT_FUNCTIONAL = "неисправна"
#
#
# class TransmissionShift(Enum):
#     """Переключение передач"""
#     STABLE = "стабильно"
#     DIFFICULT = "затруднено"
#
#
# class Efficiency(Enum):
#     """Эффективность"""
#     TIMELY = "своевременно"
#     DELAYED = "с задержкой"
#
#
# class TechnicalCondition(Enum):
#     """Определение перечисления для технического состояния"""
#     GOOD = "годное"
#     NOT_GOOD = "не годное"
#     REQUIRES_REPAIR = "требует ремонта"


class RepairAct(db.Model):
    __table_args__ = {
        'schema': 'doc',
        'comment': 'Акт на сдачу в ремонт'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    department_link = Column(ForeignKey(ListDepartment.id), comment='Структурное подразделение')
    approved_employee_link = Column(ForeignKey(ListEmployee.id), nullable=True, comment='Утверждающий сотрудник (Глав. инженер)')
    act_number = Column(String, nullable=False, unique=True, comment='Номер акта')
    date_of_act = Column(Date, comment='Дата акта')
    storage_representative_employee_link = Column(ForeignKey(ListEmployee.id), comment='Представитель отдела хранения')
    repair_representative_employee_link = Column(ForeignKey(ListEmployee.id), comment='Представитель ремонтного подразделения')
    task_link = Column(ForeignKey(Task.id), comment='Задачу')
    ntd_document = Column(ForeignKey(ListRepairDocumentation.id), comment='Ремонтный документ')
    conclusion = Column(String, comment='Заключение')
    date_repair = Column(Date, comment='Дата приёмки')
    rejection_reason = Column(String, comment='Причины отказа')
    date_deletion = Column(DateTime, comment='Дата удаления')
    # created_at = Column(Date, default=func.now())
    # updated_at = Column(Date, default=func.now(), onupdate=func.now())

    ListDepartment = relationship("ListDepartment", foreign_keys = [department_link])
    Approver = relationship('ListEmployee', foreign_keys=[approved_employee_link])
    StoragePosition = relationship("ListEmployee", foreign_keys=[storage_representative_employee_link])
    RepairPosition = relationship("ListEmployee", foreign_keys=[repair_representative_employee_link])
    Task = relationship("Task", foreign_keys = [task_link], back_populates='RepairAct')
    ListRepairDocumentation = relationship('ListRepairDocumentation')

    def __repr__(self): #TODO нафига?
        return f"<RepairAct {self.act_number}>"


class ReceiveTransfer(db.Model):
    __table_args__ = {
        'schema': 'doc',
        'comment': 'Акт приема-передачи'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    department_link = Column(ForeignKey(ListDepartment.id), comment='Структурное подразделение')
    approved_employee_link = Column(ForeignKey(ListEmployee.id), comment='Утверждающий сотрудник (Глав. инженер)')
    act_number = Column(String, nullable=False, unique=True, comment='Номер акта')
    task_link = Column(ForeignKey(Task.id), comment='Задача')
    date_of_act = Column(Date, comment='Дата акта')
    storage_representative_employee_link = Column(ForeignKey(ListEmployee.id), comment='Представитель отдела хранения')
    sender_unit = Column(String, comment='Номер воинской части заказчика')
    sender = Column(String, comment='Представитель заказчика (воинской части)')
    annex = Column(String, comment='Приложение') #todo здесь должна быть ссылка на промежуточную таблицу
    date_deletion = Column(DateTime, comment='Дата удаления')

    ListDepartment = relationship("ListDepartment", foreign_keys=[department_link])
    Approver = relationship('ListEmployee', foreign_keys=[approved_employee_link])
    Task = relationship("Task", foreign_keys=[task_link], back_populates='ReceiveTransfer')
    StoragePosition = relationship("ListEmployee", foreign_keys=[storage_representative_employee_link])


class AppendixReceiveTransfer(db.Model):
    __table_args__ = {
        'schema': 'doc',
        'comment': 'Приложение к акту приема-передачи'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    receive_transfer_link = Column(ForeignKey(ReceiveTransfer.id), comment='Акт приёма/передачи')
    id_document = Column(Integer, comment='Id документа, который прилагается к акту')
    class_document = Column(String, comment='Название класса документа, который прилагается к акту')


class InitialReadingsReport(db.Model):
    __table_args__ = {
        'schema': 'doc',
        'comment': 'Акт технического состояния'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    act_number = Column(String, nullable=False, unique=True, comment='Номер акта')
    date_of_act = Column(Date, comment='Дата акта')
    department_link = Column(ForeignKey(ListDepartment.id), comment='Структурное подразделение')
    approved_employee_link = Column(ForeignKey(ListEmployee.id), comment='Утверждающий сотрудник (Глав. инженер)')
    completeness = Column(String, comment='Комплектность')
    technical_condition = Column(String, comment='Техническое состояние')
    reasons_for_early_wear = Column(String, comment='Причины досрочного износа или повреждения')
    conclusion = Column(String, comment='Заключение комиссии')
    senior_officer_conclusion = Column(String, comment='Заключение старшего начальника')

    ListDepartment = relationship("ListDepartment", foreign_keys = [department_link])
    Approver = relationship('ListEmployee', foreign_keys=[approved_employee_link])
    Commission = relationship("CommissionInitialReadingsReport")
    StatusInitialReadings = relationship("StatusInitialReadings")


class StatusInitialReadings(db.Model):
    __table_args__ = {
        'schema': 'doc',
        'comment': 'Таблица "Сведения о состоянии материальных ценностей"'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    readings_report_link = Column(ForeignKey(InitialReadingsReport.id), comment='Акт технического состояния')
    article_link = Column(ForeignKey(ListArticle.id), comment='Изделие')

    ListArticle = relationship("ListArticle", foreign_keys=[article_link])


class CommissionInitialReadingsReport(db.Model):
    __table_args__ = {
        'schema': 'doc',
        'comment': 'Члены комиссии акта тех состояния'
    }

    id = Column(Integer, comment='Идентификатор', primary_key=True)
    act_link = Column(ForeignKey(InitialReadingsReport.id), comment='Акт технического состояния')
    employee_link = Column(ForeignKey(ListEmployee.id), comment='Сотрудников')

    ListEmployee = relationship("ListEmployee")


class Order(db.Model):
    __table_args__ = {
        'schema': 'doc',
        'comment': 'Наряд'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    order_number = Column(String, nullable=False, unique=True, comment='Номер акта')
    date_order = Column(Date, comment='Дата акта')
    task_link = Column(ForeignKey(Task.id), comment='Задачу')
    issuing_authority = Column(String, comment='Наименование довольствующего органа')
    valid_until_date = Column(Date, comment='Действителен по')
    operation_purpose = Column(String, comment='Цель операции')
    operation_basis = Column(String, comment='Основание для совершения операции')
    shipper_name = Column(String, comment='Грузоотправитель и его почтовый адрес')
    consignee_name = Column(String, comment='Грузополучатель и его почтовый адрес')
    transport = Column(String, comment='Вид и номер транспорта')
    transport_document_name = Column(String, comment='Наименование транспортного документа')
    total = Column(String, comment='Итого')
    shipment_order = Column(String, comment='Порядок отправки')
    arrival_period = Column(String, comment='Срок прибытия караула с приемщиком')

    OrderContent = relationship("OrderContent", back_populates='Order', lazy='dynamic')


    # @property  Это не правильно, вы можете выдать несколько одинаковых изделий
    # def total_order_contents(self):
    #     """Подсчет общего количества позиций"""
    #     return self.order_contents.count()


class OrderContent(db.Model):
    __table_args__ = {
        'schema': 'doc',
        'comment': 'Материальные ценности в наряде'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    sequence_number = Column(Integer, comment='№ п/п')
    material_link = Column(ForeignKey(ListArticle.id), comment='Изделие')
    order_link = Column(ForeignKey(Order.id), comment='Наряд')
    increase = db.Column(Float, comment="Выдать (передать)")
    decrease = db.Column(Float, comment="Выдано (передано)")
    repair_type_link = Column(ForeignKey(DictKindRepair.id), comment='Вид ремонта (обработки)')
    execution_period = Column(DateTime, comment='Срок исполнения')
    work_completion_note = Column(String, comment='Отметка о выполненных работах')

    Order = relationship('Order', back_populates='OrderContent', foreign_keys = [order_link])
    ListArticle = relationship("ListArticle", foreign_keys = [material_link])
    DictKindRepair = relationship("DictKindRepair", foreign_keys = [repair_type_link])


class ScannedDocument(db.Model):
    __table_args__ = {
        'schema': 'doc',
        'comment': 'Сканированный документ'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    task_link = Column(ForeignKey(Task.id), comment='Задача')
    dict_type_documents_link = Column(ForeignKey(DictTypeDocument.id), comment='Тип документа')

    DictTypeDocument = relationship("DictTypeDocument", foreign_keys=[dict_type_documents_link])