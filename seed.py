# from app import create_app, db
# from app.models import FileType

from src.db import db
from src.app import app

def seed():
    # app = create_app()
    with app.app_context():
        if FileType.query.first():
            print('Таблица уже содержит записи')
            return
        types = [
            FileType(
                name = 'Склад',
                note = 'Загрузка',
                config_path = 'configs/config1.json',
                parser_class = 'XlsxParser',
                target_model = 'Table'
            )
        ]

        db.session.add_all(types)
        db.session.commit()
        print("Начальные данные добавлены")
    
if __name__ == '__main__':
    seed()
