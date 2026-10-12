# coding: utf-8
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, String, Boolean, func, UniqueConstraint, Text
from src.db import db


class ClassifiersList(db.Model):
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"
    __table_args__ = {'schema': 'cls',
                    'comment': 'Список НСИ' # (служебная таблица)
                    }

    id = Column(Integer, comment = 'Идентификатор', primary_key=True)
    name_ru = Column(String,  comment='Наименование русское')
    name_en = Column(String, comment='Наименование английское')
    class_path = Column(String(255), comment = 'Путь к классу таблицы')
    table_name = Column(String(255), comment = 'Название таблицы в БД (латиница)')
    schema = Column(String(255), comment = 'Название схемы для таблицы')
    parent_link = Column(Integer, ForeignKey(id), comment = 'Вышестоящая таблица')
    date_employment = Column(DateTime, comment='Дата трудоустройства')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    # parent = relationship("ClassifiersList", remote_side=[id], back_populates="children")
    # children = relationship("ClassifiersList", back_populates="parent")


class DictTypeTask(db.Model):
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"
    __table_args__ = {
        'schema': 'cls',
        'comment': 'Справочник типов задач' # (шаблон, работы по изделию, мойка...)
    }
    id = Column(Integer, primary_key = True, comment = 'Идентификатор')
    name_ru = Column(String,  comment='Наименование русское')
    name_en = Column(String, comment='Наименование английское')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')


class DictStatusTask(db.Model):
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"
    __table_args__ = {
        'schema': 'cls',
        'comment': 'Справочник статусов задач'
    }
    id = Column(Integer, primary_key = True, comment = 'Идентификатор')
    name_ru = Column(String,  comment='Наименование русское')
    name_en = Column(String, comment='Наименование английское')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')


class DictKindRepair(db.Model):
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"
    __table_args__ = {
    'schema': 'cls', 'comment': 'Справочник видов ремонтных работ' # (ТОиР)
    }

    id = Column(Integer, primary_key=True, comment='Ключ')
    name_ru = Column(String,  comment='Наименование русское')
    name_en = Column(String, comment='Наименование английское')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')


class DictMilitaryRank(db.Model):
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"
    __table_args__ = {
    'schema': 'cls', 'comment': 'Справочник воинских званий'
    }

    id = Column(Integer, primary_key=True, comment='Ключ')
    name_ru = Column(String,  comment='Наименование русское')
    name_en = Column(String, comment='Наименование английское')
    date_deletion = Column(DateTime, comment='Дата удаления', info={"hidden": True})
    note = Column(String, comment='Примечание')


class DictTypeDocument(db.Model):
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"
    __table_args__ = {
    'schema': 'cls', 'comment': 'Справочник типов документов'
    }

    id = Column(Integer, primary_key=True, comment='Ключ')
    name_ru = Column(String,  comment='Наименование русское')
    name_en = Column(String, comment='Наименование английское ')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')


class DictJobTitle(db.Model):
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"
    __table_args__ = {
    'schema': 'cls', 'comment': 'Справочник должностей'
    }

    id = Column(Integer, primary_key=True, comment='Ключ')
    name_ru = Column(String,  comment='Наименование русское')
    name_en = Column(String, comment='Наименование английское ')
    parent_link = Column(ForeignKey(id), comment='Начальник')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    Parent = relationship("DictJobTitle", remote_side=[id], back_populates="Children")
    Children = relationship("DictJobTitle", back_populates="Parent")


class DictLocationType(db.Model):
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"
    __table_args__ = {
    'schema': 'cls', 'comment': 'Справочник типов мест содержания' # (стеллаж, полка, место, укладка)
    }

    id = Column(Integer, primary_key=True, comment='Ключ')
    name_ru = Column(String,  comment='Наименование русское')
    name_en = Column(String, comment='Наименование английское ')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')


class DictOkei(db.Model):
    __description_ru__ = "name"
    __description_en__ = "intenat_designation"
    __table_args__ = {
    'schema': 'cls', 'comment': ' Общероссийский классификатор единиц измерения (ОКЕИ)'
    }

    id = Column(String, primary_key=True, comment='Код')
    name = Column(String, comment='Название единицы измерения')
    nat_designation = Column(String, comment='Национальное условное обозначение')
    intenat_designation = Column(String, comment='Международное условное обозначение')
    nat_code_designation = Column(String, comment='Национальное кодовое обозначение')
    intenat_code_designation = Column(String, comment='Международное кодовое обозначение')



class DictResourceType(db.Model):
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"
    __table_args__ = {
    'schema': 'cls', 'comment': ' Справочник типов материальных ценностей'
    }

    id = Column(Integer, primary_key=True, comment='Ключ')
    name_ru = Column(String,  comment='Тип русский')
    name_en = Column(String, comment='Тип английский ')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')


class DictResourceCategory(db.Model):
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"
    __table_args__ = {
    'schema': 'cls', 'comment': ' Справочник категорий материальных ценностей'
    }

    id = Column(Integer, primary_key=True, comment='Ключ')
    name_ru = Column(String,  comment='Категория русская')
    name_en = Column(String, comment='Категория английская ')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')


class DictResource(db.Model):
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"
    __table_args__ = {
    'schema': 'cls', 'comment': ' Справочник материальных ценностей'
    }

    id = Column(Integer, primary_key=True, comment='Ключ')
    name_ru = Column(String,  comment='Наименование русское')
    name_en = Column(String, comment='Наименование английское ')
    type_link = Column(ForeignKey(DictResourceType.id), comment='Тип')
    designation_ru = Column(String, comment='Обозначение русское')
    designation_en = Column(String, comment='Обозначение английское')
    category_link = Column(ForeignKey(DictResourceCategory.id), comment='Категория')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    DictResourceType = relationship('DictResourceType')
    DictResourceCategory = relationship('DictResourceCategory')
    DeliveryNoteResources = relationship('DeliveryNoteResources', back_populates='DictResource')
    DictArticle = relationship(
        "DictArticleStructure",
        back_populates='ArticleLink',
        foreign_keys='DictArticleStructure.article_link'
    )
    DictPart = relationship(
        "DictArticleStructure",
        back_populates='PartLink',
        foreign_keys='DictArticleStructure.part_link'
    )



class DictArticleStructure(db.Model):
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"
    __table_args__ = {
    'schema': 'cls', 'comment': ' Справочник состава изделий'
    }

    id = Column(Integer, primary_key=True, comment='Ключ')
    name_ru = Column(String,  comment='Наименование русское')
    name_en = Column(String, comment='Наименование английское ')
    part_link = Column(ForeignKey(DictResource.id), comment='Составная часть изделия')
    article_link = Column(ForeignKey(DictResource.id), comment='Изделие')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')

    ArticleLink = relationship(
        'DictResource',
        back_populates='DictArticle',
        foreign_keys=[article_link]
    )
    PartLink = relationship(
        'DictResource',
        back_populates='DictPart',
        foreign_keys=[part_link]
    )


class DictAbsenceCause(db.Model):
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"
    __table_args__ = {
    'schema': 'cls', 'comment': ' Справочник основания отсутствия'
    }

    id = Column(Integer, primary_key=True, comment='Ключ')
    name_ru = Column(String,  comment='Наименование русское')
    name_en = Column(String, comment='Наименование английское ')
    date_deletion = Column(DateTime, comment='Дата удаления')
    note = Column(String, comment='Примечание')
