# coding: utf-8
from src.db import db
from src.orm import orm_cls, orm_list, orm_task
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean, func, UniqueConstraint


class UtilizationAct(db.Model):
    __table_args__ = {'schema': 'res',
                    'comment': 'Акт утилизации' #Документ
                    }

    id = Column(Integer, comment='Идентификатор', primary_key=True)
    number_act = Column(Integer, comment='Номер акта утилизации')
    input_employee_link = Column(ForeignKey(orm_list.ListEmployee.id), comment='Утвердивший сотрудник')
    output_employee_link = Column(ForeignKey(orm_list.ListEmployee.id), comment='Старший бухгалтер')
    task_link = Column(ForeignKey(orm_task.Task.id), comment='Задача')
    number_order = Column(Integer, comment='Номер приказа-основания')
    pursuant_order = Column(String, comment='Основания для утилизации в приказе') #todo нужен ли отдельный приказ?
    total_cost_repairs = Column(Integer, comment='Ремонтов (капитальных) произведено на сумму $')
    reason_utilization = Column(String, comment='Техническое состояние и причины утилизации (ликвидации)')
    init_cost = Column(Integer, comment='Первоначальная стоимость $')
    depreciation_cost = Column(Integer, comment='Сумма износа $')
    result_cost = Column(Integer, comment='Результаты от утилизации (ликвидации) $')
    summary = Column(String, comment='Заключение коммисии')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    InputEmployee = relationship("ListEmployee", foreign_keys=[input_employee_link])
    OutputEmployee = relationship("ListEmployee", foreign_keys=[output_employee_link])
    Commission = relationship("Commission")
    Task = relationship("Task")


class Commission(db.Model):
    __table_args__ = {'schema': 'res',
                    'comment': 'Состав комиссии в Акте утилизации'
                    }

    id = Column(Integer, comment='Идентификатор', primary_key=True)
    act_link = Column(ForeignKey(UtilizationAct.id), comment='Акт утилизации')
    employee_link = Column(ForeignKey(orm_list.ListEmployee.id), comment='Член комиссии')


    ListEmployee = relationship("ListEmployee")


class ResourcesMovement(db.Model):
    __table_args__ = {'schema': 'res',
                    'comment': 'Движение материальный ценностей' #(вся строка в таблице Учёт ЗИП)
                    }

    id = Column(Integer, comment = 'Идентификатор', primary_key=True)
    date_record = Column(DateTime, comment='Дата записи')
    resource_link = Column(ForeignKey(orm_list.ListResources.id), comment='Материальные ценности')
    increase = db.Column(Float, comment="Прибыло")
    decrease = db.Column(Float, comment="Убыло (расход)")
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')
    #нужна ещё одна таблица соотношения документа и учёта движения

    ListResources = relationship("ListResources")
    DeliveryNoteResources = relationship("DeliveryNoteResources", back_populates='ResourcesMovement')


class UtilizationActResources(db.Model):
    __table_args__ = {'schema': 'res',
                    'comment': 'Материальные ценности в акте утилизации' #TODO Подтянуть колонки
                    }

    id = Column(Integer, comment='Идентификатор', primary_key=True)
    utilization_act_link = Column(ForeignKey(UtilizationAct.id), comment='Акт утилизации')
    resources_movement_link = Column(ForeignKey(ResourcesMovement.id), comment='Движение материальный ценностей')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    ResourcesMovement = relationship("ResourcesMovement")
    UtilizationAct = relationship("UtilizationAct")


class DeliveryNote(db.Model):
    __table_args__ = {'schema': 'res',
                    'comment': 'Накладная' #Документ
                    }

    id = Column(Integer, comment='Идентификатор', primary_key=True)
    number_delivery_note = Column(String, comment='Номер накладной')
    date_delivery_note = Column(DateTime, comment='Дата накладной')
    reason = Column(String, comment='Основания для выдачи')
    power_attorney = Column(String, comment='Доверенность, приказ, распоряжение, указание, номер, дата')
    total_issue = Column(Integer, comment='Общее количество выданных наименований')
    department_input_link = Column(ForeignKey(orm_list.ListDepartment.id), comment='Подразделение принимающее')
    department_output_link = Column(ForeignKey(orm_list.ListDepartment.id), comment='Передающее подразделение')
    head_employee_link = Column(ForeignKey(orm_list.ListEmployee.id), comment='Утвердивший выдачу сотрудник')
    input_employee_link = Column(ForeignKey(orm_list.ListEmployee.id), comment='Принявший сотрудник')
    output_employee_link = Column(ForeignKey(orm_list.ListEmployee.id), comment='Передавший сотрудник')
    task_link = Column(ForeignKey(orm_task.Task.id), comment='Задачу')
    military_unit_link = Column(ForeignKey(orm_list.ListMilitaryUnit.id), comment='Воинское формирование')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    InputListDepartment = relationship("ListDepartment",foreign_keys=[department_input_link] )
    OutputListDepartment = relationship("ListDepartment",foreign_keys=[department_output_link] )
    HeadEmployee = relationship("ListEmployee", foreign_keys=[head_employee_link])
    InputEmployee = relationship("ListEmployee", foreign_keys=[input_employee_link])
    OutputEmployee = relationship("ListEmployee", foreign_keys=[output_employee_link])
    Task = relationship("Task", back_populates='DeliveryNote')
    ListMilitaryUnit = relationship("ListMilitaryUnit")
    DeliveryNoteResources = relationship("DeliveryNoteResources", back_populates='DeliveryNote')


class DeliveryNoteResources(db.Model):
    __table_args__ = {'schema': 'res',
                    'comment': 'Материальные ценности в накладной' #TODO Подтянуть колонки
                    }

    id = Column(Integer, comment='Идентификатор', primary_key=True)
    delivery_note = Column (ForeignKey(DeliveryNote.id), comment='Накладная')
    resources_movement_link = Column(ForeignKey(ResourcesMovement.id), comment='Движение материальный ценностей')
    okei_link = Column(ForeignKey(orm_cls.DictOkei.id), comment='Еденица измерения')
    location_link = Column(ForeignKey(orm_list.ListResourceLocation.id), comment='Место содержание материальных ценностей')
    resource_link = Column(ForeignKey(orm_cls.DictResource.id), comment='Справочник материальных ценностей')
    quantity = Column(Integer, comment='Количество')
    note = Column(String, comment='Примечание')
    date_deletion = Column(DateTime, comment='Дата удаления')

    DictResource = relationship("DictResource", back_populates='DeliveryNoteResources')
    ListResourceLocation = relationship("ListResourceLocation")
    DictOkei = relationship("DictOkei")
    ResourcesMovement = relationship("ResourcesMovement", back_populates='DeliveryNoteResources')
    DeliveryNote = relationship("DeliveryNote", back_populates='DeliveryNoteResources')


class Request(db.Model):
    __table_args__ = {'schema': 'res',
                    'comment': 'Заявка на ЗИП материалы' #Документ
                    }

    id = Column(Integer, comment='Идентификатор', primary_key=True)
    name = Column(String, comment='Название')
    department_link = Column(ForeignKey(orm_list.ListDepartment.id), comment='Подразделение')
    input_employee_link = Column(ForeignKey(orm_list.ListEmployee.id), comment='Получатель (Начальник подразделения)')
    output_employee_link = Column(ForeignKey(orm_list.ListEmployee.id), comment='Отправитель (Начальник/старший)')
    task_link = Column(ForeignKey(orm_task.Task.id), comment='Задачу')
    military_unit_link = Column(ForeignKey(orm_list.ListMilitaryUnit.id), comment='Воинское формирование')
    date_deletion = Column(DateTime, comment='Дата удаления')

    ListDepartment = relationship("ListDepartment")
    InputEmployee = relationship("ListEmployee", foreign_keys=[input_employee_link])
    OutputEmployee = relationship("ListEmployee", foreign_keys=[output_employee_link])
    Task = relationship("Task")
    ListMilitaryUnit = relationship("ListMilitaryUnit")
    RequestResources = relationship("RequestResources", back_populates="Request")


class RequestResources(db.Model):
    __table_args__ = {'schema': 'res',
                    'comment': 'Материальные ценности в Заявке на ЗИП' #TODO Подтянуть колонки
                    }

    id = Column(Integer, comment='Идентификатор', primary_key=True)
    resource_link = Column(ForeignKey(orm_cls.DictResource.id), comment='Наименование, обозначение индекс материальных средств')
    okei_link = Column(ForeignKey(orm_cls.DictOkei.id), comment='Единицы измерения')
    quantity = Column(Integer, comment='Количество')
    request_link = Column(ForeignKey(Request.id), comment='Заявка на ЗИП материалы')
    department_link = Column(ForeignKey(orm_list.ListDepartment.id), comment='Подразделение')
    location_link = Column(ForeignKey(orm_list.ListResourceLocation.id), comment='Место содержания материальных ценностей')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    DictResource = relationship("DictResource")
    ListResourceLocation = relationship("ListResourceLocation")
    ListDepartment = relationship("ListDepartment")
    DictOkei = relationship("DictOkei")
    Request = relationship("Request", back_populates="RequestResources")


class SupplyPermission(db.Model):
    __table_args__ = {'schema': 'res',
                    'comment': 'Ведомость израс. ЗИП и мат.' #Документ
                    }

    id = Column(Integer, comment='Идентификатор', primary_key=True)
    name = Column(String, comment='Название')
    input_employee_link = Column(ForeignKey(orm_list.ListEmployee.id), comment='Начальник подразделения')
    output_employee_link = Column(ForeignKey(orm_list.ListEmployee.id), comment='Начальник/старшего')
    task_link = Column(ForeignKey(orm_task.Task.id), comment='Задача')
    military_unit_link = Column(ForeignKey(orm_list.ListMilitaryUnit.id), comment='Воинское формирование')
    date_deletion = Column(DateTime, comment='Дата удаления')

    InputEmployee = relationship("ListEmployee", foreign_keys=[input_employee_link])
    OutputEmployee = relationship("ListEmployee", foreign_keys=[output_employee_link])
    Task = relationship("Task")
    ListMilitaryUnit = relationship("ListMilitaryUnit")


class SupplyPermissionResources(db.Model):
    __table_args__ = {'schema': 'res',
                    'comment': 'Материальные ценности в ведомости израс. ЗИП и мат.'  # TODO Подтянуть колонки
                    }

    id = Column(Integer, comment='Идентификатор', primary_key=True)
    supply_permission_link = Column(ForeignKey(SupplyPermission.id), comment='Ведомость израс. ЗИП и мат.')
    resources_movement_link = Column(ForeignKey(ResourcesMovement.id), comment='Движение материальный ценностей')
    okei_link = Column(ForeignKey(orm_cls.DictOkei.id), comment='Единица измерения')
    quantity = Column(Integer, comment='Количество')
    total_quantity = Column(Integer, comment='Всего израсходовано при проведении ремонтных работ')
    department_link = Column(ForeignKey(orm_list.ListDepartment.id), comment='Подразделение')
    location_link = Column(ForeignKey(orm_list.ListResourceLocation.id), comment='Место содержание материальных ценностей')
    resource_link = Column(ForeignKey(orm_cls.DictResource.id), comment='Справочник материальных ценностей')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    DictResource = relationship("DictResource")
    ListResourceLocation = relationship("ListResourceLocation")
    ListDepartment = relationship("ListDepartment")
    DictOkei = relationship("DictOkei")
    ResourcesMovement = relationship("ResourcesMovement")


class TechnologicalEquipmentCharacteristic(db.Model):
    __table_args__ = {'schema': 'res',
                    'comment': 'Характеристики технологического оборудования'
                    }

    id = Column(Integer, comment='Идентификатор', primary_key=True)
    okei_link = Column(ForeignKey(orm_cls.DictOkei.id), comment='Единицы измерения')
    equipment_link = Column(ForeignKey(orm_list.ListTechnologicalEquipment.id), comment='Технологическое оборудование')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    DictOkei = relationship("DictOkei")
    ListTechnologicalEquipment = relationship("ListTechnologicalEquipment")



