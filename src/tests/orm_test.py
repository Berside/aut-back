#!/usr/bin/python3
# -*- coding: utf-8 -*-

from src.db import db

class ClassifierTest(db.Model):
    __classifier__ = True
    __description_ru__ = "name_ru"
    __description_en__ = "name_en"
    __table_args__ = {
        'schema': 'test',
        'comment': u'Тестовый классификатор'
    }
    id = db.Column(db.Integer, primary_key = True, comment = u'Идентификатор')
    name_ru = db.Column(db.String, unique = True, comment = u'Наименование')
    name_en = db.Column(db.String, unique = True, comment = u'Наименование английское')


class ClassFieldsTest(db.Model):
    __table_args__ = {
        'schema': 'test',
        'comment': u'Тестовый класс с разными полями'
    }
    id = db.Column(db.Integer, primary_key = True, comment = u'Идентификатор')
    text = db.Column(db.String, comment = u'Текст')
    int = db.Column(db.Integer, comment = u'Целое цисло')
    float = db.Column(db.Float, comment = u'Число с плавающей запятой')
    date = db.Column(db.Date, comment = u'Дата')
    datetime = db.Column(db.DateTime, info='Дата и время')
    bool = db.Column(db.Boolean, info='Бинарное поле')
    classifier_link = db.Column(db.ForeignKey(ClassifierTest.id), comment = u'Ссылка на классификатор')

    ClassifierTest = db.relationship('ClassifierTest')
    ClassManyToOneTest = db.relationship('ClassManyToOneTest', back_populates = 'ClassFieldsTest')


class ClassManyToOneTest(db.Model):
    __table_args__ = {
        'schema': 'test',
        'comment': u'Тестовый класс с relationship'
    }
    id = db.Column(db.Integer, primary_key = True, comment = u'Идентификатор')
    class_link = db.Column(db.ForeignKey(ClassFieldsTest.id), comment = u'Ссылка на классификаторв')

    ClassFieldsTest = db.relationship('ClassFieldsTest', back_populates = 'ClassManyToOneTest')


class ClassifierTestTwo(db.Model):
    __classifier__ = True
    __classifier_description__ = "name_one"
    __table_args__ = {
        'schema': 'test',
    }
    id = db.Column(db.Integer, primary_key = True, comment = u'Идентификатор')
    name_one = db.Column(db.String, comment = u'Наименование 1')
    name_two = db.Column(db.String, comment = u'Наименование 2')
    classifier_link = db.Column(db.ForeignKey(ClassifierTest.id), comment = u'Ссылка на классификатор')

    ClassifierTest = db.relationship('ClassifierTest')


class ClassJoinTest(db.Model):
    __table_args__ = {
        'schema': 'test',
    }
    id = db.Column(db.Integer, primary_key = True, comment = u'Идентификатор')
    text = db.Column(db.String, comment = u'Текст')
    classifier_two_link = db.Column(db.ForeignKey(ClassifierTestTwo.id), comment = u'Ссылка на классификатор')

    ClassifierTestTwo = db.relationship('ClassifierTestTwo')


def populate_test_tables():
    db.session.query(ClassJoinTest).delete()
    db.session.query(ClassifierTestTwo).delete()
    db.session.query(ClassManyToOneTest).delete()
    db.session.query(ClassFieldsTest).delete()
    db.session.query(ClassifierTest).delete()
    db.session.commit()
    db.session.add_all([ClassifierTest(id = 1, name_ru = 'спам', name_en = 'spam'),
                        ClassifierTest(id = 2, name_ru = 'тест', name_en = 'test'),
                        ClassifierTest(id = 3, name_ru = 'Спам', name_en = 'Spam'),
                        ClassifierTest(id = 4, name_ru = 'ТЕСТ4', name_en = 'TEST4')])
    db.session.execute(db.text("select setval(pg_get_serial_sequence('test.classifier_test', 'id'), 4);"))
    db.session.commit()
    db.session.add_all([ClassFieldsTest(id = 1, text = "тест1", int = 1, float = 1, date = "2026-02-18", datetime = "2026-02-18 00:00",
                                        bool = True, classifier_link = 1),
                        ClassFieldsTest(id = 2, text = "тест2", int = 2, float = 0.5, date = "2026-02-19", datetime = "2026-02-19 01:00",
                                        bool = False, classifier_link = 1),
                        ClassFieldsTest(id = 3, text = "тест3", int = 3, float = 1.2, date = "2026-02-20", datetime = "2026-02-20 02:00",
                                        bool = True, classifier_link = 1),
                        ClassFieldsTest(id = 4, text = "тест4", int = 4, float = 1.8, date = "2026-02-21", datetime = "2026-02-21 03:00",
                                        bool = False, classifier_link = 2),
                        ClassFieldsTest(id = 5, text = "тест5", int = 5, float = 3.1, date = "2026-02-22", datetime = "2026-02-22 04:00",
                                        bool = True, classifier_link = 2),
                        ClassFieldsTest(id = 6, text = "тест6", int = 6, float = 4.1, date = "2026-02-23", datetime = "2026-02-23 05:00",
                                        bool = False, classifier_link = 2),
                        ClassFieldsTest(id = 7, text = "тест7", int = 7, float = 10.1, date = "2026-02-24", datetime = "2026-02-24 06:00",
                                        bool = True, classifier_link = 4),
                        ClassFieldsTest(id = 8, text = "тест8", int = 8, float = 11.5, date = "2026-02-25", datetime = "2026-02-25 07:00",
                                        bool = False, classifier_link = 4),
                        ClassFieldsTest(id = 9, text = "тест9", int = 9, float = .1, date = "2026-02-26", datetime = "2026-02-26 08:00",
                                        bool = True, classifier_link = 4),
                        ClassFieldsTest(id = 10, text = "тест10", int = 10, float = 11, date = "2026-02-27", datetime = "2026-02-27 09:00",
                                        bool = False, classifier_link = 4)])
    db.session.execute(db.text("select setval(pg_get_serial_sequence('test.class_fields_test', 'id'), 10);"))
    db.session.commit()
    db.session.add_all([ClassManyToOneTest(id=1, class_link=1),
                        ClassManyToOneTest(id=2, class_link=1),
                        ClassManyToOneTest(id=3, class_link=1),
                        ClassManyToOneTest(id=4, class_link=2),
                        ClassManyToOneTest(id=5, class_link=2),
                        ClassManyToOneTest(id=6, class_link=3),
                        ClassManyToOneTest(id=7, class_link=3),
                        ClassManyToOneTest(id=8, class_link=3),
                        ClassManyToOneTest(id=9, class_link=3),
                        ClassManyToOneTest(id=10, class_link=4)])
    db.session.execute(db.text("select setval(pg_get_serial_sequence('test.class_many_to_one_test', 'id'), 10);"))
    db.session.commit()


def populate_join_test_tables():
    populate_test_tables()
    db.session.commit()
    db.session.add_all([ClassifierTestTwo(id = 1, name_one = 'boo1', name_two = 'проверка1', classifier_link=1),
                        ClassifierTestTwo(id = 2, name_one = 'boo2', name_two = 'проверка2', classifier_link=2),
                        ClassifierTestTwo(id = 3, name_one = 'boo3', name_two = 'проверка3', classifier_link=3)])
    db.session.execute(db.text("select setval(pg_get_serial_sequence('test.classifier_test_two', 'id'), 3);"))
    db.session.add_all([ClassJoinTest(id = 1, text = 'foo1', classifier_two_link=1),
                        ClassJoinTest(id = 2, text = 'foo2', classifier_two_link=1),
                        ClassJoinTest(id = 3, text = 'foo3', classifier_two_link=2),
                        ClassJoinTest(id = 4, text = 'foo4', classifier_two_link=2),
                        ClassJoinTest(id = 5, text = 'foo5', classifier_two_link=3)])
    db.session.execute(db.text("select setval(pg_get_serial_sequence('test.class_join_test', 'id'), 5);"))
    db.session.commit()
