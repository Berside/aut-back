# coding: utf-8
from src.db import db
from src.orm import orm_cls
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean, func, UniqueConstraint, Interval, Date, event
from src.orm.orm_cls import DictResource, DictOkei, DictKindRepair
# from src.orm.orm_task import Task

class ListDepartment(db.Model):
    __table_args__ = { 'schema': 'list',  'comment': 'Реестр подразделений'}
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    name_ru = Column(String,  comment='Наименование русское')
    name_en = Column(String, comment='Наименование английское ')
    parent_link = Column(ForeignKey(id), comment='Вышестоящее подразделение')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    Parent = relationship("ListDepartment", remote_side=[id], back_populates="Children")
    Children = relationship("ListDepartment", back_populates="Parent")
    ListEmployee = relationship("ListEmployee", back_populates="ListDepartment")


class ListEmployee(db.Model):
    __table_args__ = { 'schema': 'list',  'comment': 'Реестр сотрудников'}

    id = Column(Integer, primary_key=True, comment='Ключ')
    fio = Column(String, comment='ФИО сотрудника')
    first_name = Column(String, comment='Имя')
    middle_name = Column(String, comment='Отчество')
    last_name = Column(String, comment='Фамилия')
    job_title_link = Column(ForeignKey(orm_cls.DictJobTitle.id), comment='Должность')
    rank_link = Column(ForeignKey(orm_cls.DictMilitaryRank.id), comment='Воинское звание')
    parent_link = Column(ForeignKey(id), comment='Руководитель')
    department_link = Column(ForeignKey(ListDepartment.id), comment='Подразделение')
    date_employment = Column(DateTime, comment='Дата трудоустройства')
    date_brith = Column(DateTime, comment='Дата рождения')
    date_termination = Column(DateTime, comment='Дата увольнения сострудника')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    DictJobTitle = relationship('DictJobTitle')
    DictMilitaryRank = relationship('DictMilitaryRank')
    Parent = relationship("ListEmployee", remote_side=[id], back_populates="Children", foreign_keys = [parent_link])
    Children = relationship("ListEmployee", back_populates="Parent")
    ListDepartment = relationship("ListDepartment", back_populates="ListEmployee")


class ListResourceLocation(db.Model):
    __table_args__ = { 'schema': 'list',  'comment': 'Реестр мест содержания материальных ценностей'}

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    location = Column(String, comment='Местосодержание')
    rack = Column(String, comment='Стеллаж')
    shelf = Column(String, comment='Полка')
    place = Column(String, comment='Место')
    placement = Column(String, comment='Укладка')
    department_link = Column(ForeignKey(ListDepartment.id), comment='Подразделение')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    ListDepartment = relationship("ListDepartment")


class ListMilitaryUnit(db.Model):
    __table_args__ = { 'schema': 'list',  'comment': 'Реестр ВФ'} #(воинских формирований)
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    name_ru = Column(String,  comment='Наименование русское')
    name_en = Column(String, comment='Наименование английское ')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')


class ListTechnologicalEquipment(db.Model):
    __table_args__ = { 'schema': 'list',  'comment': 'Реестр технологического оборудования'}
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    name_ru = Column(String,  comment='Наименование русское')
    name_en = Column(String, comment='Наименование английское ')
    serial_number = Column(String, comment='Заводской номер')
    production_year = Column(Integer, comment="Год выпуска")
    total_operating = Column(String, comment='Наработка с начала эксплуатации (последнего ремонта) м/ч')
    component = Column(String, comment='Составная часть, шкаф, блок')
    res_location_link = Column(ForeignKey(ListResourceLocation.id), comment='Местоположений мат. ценностей')
    employee_link = Column(ForeignKey(ListEmployee.id), comment='Ответственный за технологическое оборудование')
    dict_okei_link = Column(ForeignKey(DictOkei.id), comment='Единица измерения')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    ListResourceLocation = relationship("ListResourceLocation")
    DictOkei = relationship("DictOkei")
    ListEmployee = relationship("ListEmployee")


class ListArticle(db.Model):
    __table_args__ = { 'schema': 'list',  'comment': 'Реестр изделий'}
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    name_ru = Column(String,  comment='Наименование русское')
    name_en = Column(String, comment='Наименование английское ')
    serial_number = Column(String, comment='Заводской номер')
    production_index = Column(String, comment='Индекс изделия')
    production_designation = Column(String, comment='Обозначение изделия')
    production_year = Column(Integer, comment = "Год выпуска")
    passport_number = Column(String, comment='Номер паспорта')
    form_number = Column(String, comment='Номер формуляр')
    manufacturer = Column(String, comment='Завод-изготовитель')
    component = Column(String, comment='Составная часть, шкаф, блок')
    res_location_link = Column(ForeignKey(ListResourceLocation.id), comment='Местоположений мат. ценностей')
    parent_link = Column(ForeignKey(id), comment='Вышестоящее изделие')
    resource_link = Column(ForeignKey(DictResource.id), comment='Справочник мат. ценностей')
    military_unit_link = Column (ForeignKey(ListMilitaryUnit.id), comment='Воинское формирование')
    dict_okei_link = Column(ForeignKey(orm_cls.DictOkei.id), comment='Единица измерения')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    ListResourceLocation = relationship("ListResourceLocation")
    DictResource = relationship("DictResource")
    Parent = relationship("ListArticle", remote_side=[id], back_populates="Children", foreign_keys = [parent_link])
    Children = relationship("ListArticle", back_populates="Parent")
    SpecificationsArticle = relationship("ListSpecificationsArticle")
    DictOkei = relationship("DictOkei")


class ListSpecificationsArticle(db.Model):
    __table_args__ = { 'schema': 'list',  'comment': 'Технико-эксплуатационные показатели изделия'}

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    article_link = Column(ForeignKey(ListArticle.id), comment='Изделие')
    operation_date = Column(Date, comment='Дата введения в эксплуатацию')
    operation_period = Column(Interval, comment='Находится в эксплуатации (лет, месяцев)') #Вычисляемое
    operating_work = Column(Float, comment='Наработка с начала эксплуатации (циклов, ч, км пробега)')

    resource_work = Column(Float, comment='Ресурс работы (циклов, ч, км пробега)')
    resource_period = Column(Interval, comment='Ресурс эксплуатации (лет, месяцев)')
    guarantee_resource_work = Column(Float, comment='Гарантийный ресурс работы (циклов, ч, км пробега)')
    guarantee_period = Column(Interval, comment='Гарантийный срок (лет, месяцев)')

    repaired_type_link = Column(ForeignKey(DictKindRepair.id), comment='Вид произведённого ремонта')
    repaired_date = Column(Date, comment='Дата произведённого ремонта')
    repaired_period = Column(Interval, comment='Находится в эксплуатации с последнего ремонта(лет, месяцев)') #Вычисляемое
    repaired_operating = Column(Float, comment='Наработка с последнего ремонта (циклов, ч, км пробега)')

    different_resource_work = Column(Integer, comment='Разница между ресурсом работы и фактической наработка с начала эксплуатации (циклов, ч, км пробега)') #Вычисляемое
    different_resource_period = Column(Interval, comment='Разница между ресурсом эксплуатации и фактической эксплуатацией (лет, месяцев)') #Вычисляемое
    different_guarantee_resource = Column(Float, comment='Разница между гарантийным ресурсом работы и фактической наработкой с начала эксплуатации(циклов, ч, км пробега)') #Вычисляемое
    different_guarantee_period = Column(Interval, comment='Разница между гарантийным сроком и фактической эксплуатацией (лет, месяцев)') #Вычисляемое
    note = Column(String, comment='Примечание')

    DictKindRepair = relationship("DictKindRepair")

#TODO переделать! должно рассчитываться при запросе
@event.listens_for(ListSpecificationsArticle, 'before_insert')
def calculate_on_postgres_side(mapper, connection, target):
    if target.operation_date:
        target.operation_period = func.now() - target.operation_date
    if target.repaired_date:
        target.repaired_period = func.now() - target.repaired_date
    if target.resource_work and target.operating_work:
        target.different_resource_work = target.resource_work - target.operating_work
    if target.resource_period and target.operation_period:
        target.different_resource_period = target.resource_period - target.operation_period
    if target.guarantee_resource_work and target.operating_work:
        target.different_guarantee_resource = target.guarantee_resource_work - target.operating_work
    if target.guarantee_period and target.operation_period:
        target.different_guarantee_period = target.guarantee_period - target.operation_period


class ListRepairDocumentation(db.Model):
    __table_args__ = { 'schema': 'list',  'comment': 'Реестр ремонтной документации'}
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"

    id = Column(Integer, primary_key=True, comment='Идентификатор')
    name_ru = Column(String,  comment='Наименование русское')
    name_en = Column(String, comment='Наименование английское ')
    resource_link = Column(ForeignKey(DictResource.id), comment='Справочник мат. ценностей')
    file_path = Column(String, comment='Путь к файлу/документу') # todo Возможно стоит сделать отдельную таблицу файлов типо TaskFile
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    DictResource = relationship("DictResource")


class ListResources(db.Model):
    __table_args__ = {'schema': 'list',
                    'comment': 'Реестр ЗИП'} #(строка в таблице Учет ЗИП-Р до Убыло, "Мешок ЗИП")
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"

    id = Column(Integer, comment = 'Идентификатор', primary_key=True)
    date_created = Column(DateTime, comment='Дата записи')
    dict_resource_link = Column(ForeignKey(orm_cls.DictResource.id), comment='Справочник материальных ценностей')  # Наименование из справочника
    resource_location_link = Column(ForeignKey(ListResourceLocation.id), comment='Реестр местоположения материальных ценностей')
    article = Column (String, comment='Применяемость, изделие, СЧ') # здесь как будто бы должна быть ссылка на изделие, но её нет модели
    count_in_article = Column(Integer, comment='Количество в изделии, шт')
    count_norm = Column(Integer, comment='Положено содержать по норме, шт')
    current_stock = Column(Integer, comment='Имеется в наличии, шт')
    dict_okei_link = Column(ForeignKey(orm_cls.DictOkei.id), comment='Единица измерения')
    date_deletion = Column(DateTime, comment='Дата удаления')

    DictResource = relationship("DictResource")
    ListResourceLocation = relationship("ListResourceLocation")
    DictOkei = relationship("DictOkei")
