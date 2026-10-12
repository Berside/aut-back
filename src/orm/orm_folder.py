from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, func
from src.db import db
from src.orm.orm_doc import Order, ReceiveTransfer

class DocumentFolder(db.Model):
    # Папка для документов(иерархическая структура)
    __table_args__ = {
        'schema': 'document',
        'comment': 'Папки документов'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор папки')
    name = Column(String(255), nullable=False, comment='Название папки')
    description = Column(Text, comment='Описание папки')
    parent_link = Column(Integer, ForeignKey('document.document_folder.id'), comment='Родительская папка')

    created_at = Column(DateTime, default=func.now(), comment='Дата создания')
    updated_at = Column(DateTime, onupdate=func.now(), comment='Дата обновления')
    is_active = Column(Boolean, default=True, comment='Активность папки')
    sort_order = Column(Integer, default=0, comment='Порядок сортировки')

    parent = relationship(
        "DocumentFolder",
        remote_side=[id],
        back_populates='children',
        foreign_keys=[parent_link]
    )

    children = relationship(
        "DocumentFolder",
        back_populates='parent',
        foreign_keys=[parent_link]
    )


class Document(db.Model):
    # Общая таблица документов для привязки к папкам
    __table_args__ = {
        'schema': 'document',
        'comment': 'Документы в папках'
    }

    id = Column(Integer, primary_key=True, comment='Идентификатор документа')
    folder_link = Column(Integer, ForeignKey('document.document_folder.id'), comment='Папка')
    project_link = Column(Integer, ForeignKey('sapr.projects.id'), comment='Проект')

    doc_type_link = Column(Integer, comment='Тип документа(из классификатора)')

    name = Column(String(255), nullable=False, comment='Название документа')
    number = Column(String(100), comment='номер документа')
    date_doc = Column(DateTime, comment='Дата документа')
    description = Column(Text, comment='Описание/примечание')

    order_link = Column(Integer, ForeignKey(Order.id), comment='Наряд')
    act_link = Column(Integer, ForeignKey(ReceiveTransfer.id), comment='Акт')

    file_link = Column(Integer, ForeignKey('storage.task_file.id'), comment='Файл')

    created_at = Column(DateTime, default=func.now(), comment='Дата создания')
    updated_at = Column(DateTime, default=func.now(), comment='Дата обновления')
    created_by = Column(Integer, comment='ID пользователя, создавшего документ')

    folder = relationship('DocumentFolder', back_populates='documents')
    Order = relationship('Order', foreign_keys=[order_link])
    act = relationship('ReceiveTransfer', foreign_keys=[act_link])
    file = relationship('TaskFile', foreign_keys=[file_link])

    

DocumentFolder.documents = relationship('Document', back_populates='folder')


