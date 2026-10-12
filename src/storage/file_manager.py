# src/storage/file_manager.py
import os
import uuid
import re
import traceback
from flask import request, jsonify, send_from_directory, abort, current_app, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import event, select
from src.db import db
from src.orm.orm_file import TaskFile, RepairDocumentation
from src.orm.orm_task import Task
import shutil
CURRENT_LOGO_FILE = "Flag.png"


def delete_physical_file(storage_filename):
    """Удаление физического файла с диска"""

    app = current_app
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], storage_filename)
    if os.path.exists(file_path):
        os.remove(file_path)


def secure_filename_russian(filename):
    """Очистка названий файлов от опасных символов и поддержка кириллицы"""
    filename = os.path.basename(filename)
    filename = re.sub(r'[^\w\s.-]', '', filename, flags=re.UNICODE)
    filename = re.sub(r'\s+', ' ', filename).strip()
    return filename


@event.listens_for(Task, 'before_delete', propagate=True)
def cleanup_task_files(mapper, connection, target):
    """Удаление файлов при удалении задачи и их записей из БД"""
    try:
        app = current_app

        for file in target.TaskFile:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'],file.storage_filename)
            if os.path.exists(file_path):
                delete_physical_file(file_path)

        # print(f"Файлы задачи {target.id} удалены с диска.")
    except Exception as e:
        print(f"Ошибка при удалении файлов задачи {target.id}: {e}")
        pass

def upload_file_route(app):
    """Путь загрузки файла"""

    @app.route('/task/upload_files/<int:task_id>', methods=['POST'])
    def upload_file_to_task(task_id):

        #todo Здесь могла быть ваша реклама и проверка прав доступа

        if 'file' not in request.files:
            return jsonify({
                "error": "Файл не найден",
                "message": "По заданному пути не найден файл"
            }), 400

        file = request.files['file']
        # print(file)
        if file.filename == '':
            return jsonify({
                "error": "Имя файла пустое",
                "message": "Имя файла не задано"
            }), 400

        original_name = file.filename
        # print(original_name)

        extension = os.path.splitext(original_name)[1]
        storage_name = f"{uuid.uuid4().hex}{extension}"

        save_path = os.path.join(app.config['UPLOAD_FOLDER'], storage_name)
        file.save(save_path)

        file_size = os.path.getsize(save_path)
        mime_type = file.content_type or 'application/octet-stream'

        new_file = TaskFile(
            task_link=task_id,
            original_name=original_name,
            storage_filename=storage_name,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by=get_current_user_id()
        )
        db.session.add(new_file)
        db.session.commit()

        return jsonify({
            "message": "File uploaded successfully",
            "id": new_file.id,
            "name": new_file.original_name,
            "size": new_file.file_size,
            "mime_type": new_file.mime_type
        }), 201


def get_task_files_route(app):
    """Путь для получения файлов"""

    @app.route('/task/get_files/<int:task_id>', methods=['GET'])
    def get_task_files(task_id):
        #todo Здесь могла быть ваша реклама и проверка прав доступа

        files = TaskFile.query.filter_by(task_link=task_id).all() #todo добавить фильтр по правам доступа

        files_data = []
        for file_record in files:
            files_data.append({
                "id": file_record.id,
                "name": file_record.original_name,
                "upload_date": file_record.upload_date.isoformat() if file_record.upload_date else None,
                "size": file_record.file_size,
                "mime_type": file_record.mime_type
            })

        return jsonify({
            "task_id": task_id,
            "files": files_data
        })


def download_file_route(app):
    """Путь скачивания файла (с поддержкой предпросмотра inline)"""

    @app.route('/task/download_files/<int:file_id>')
    def download_task_file(file_id):
        try:
            file_record = db.session.get(TaskFile, file_id)
        except Exception as e:
            return jsonify({"error": "Файл не найден"},
                           {"message": f"Запись о файле отсутствует в базе данных или файла не существует вовсе, ошибка: {e}"}), 404
        #todo Здесь могла быть ваша реклама и проверка прав доступа

        try:
            safe_name = secure_filename_russian(file_record.original_name)

            if not safe_name or len(safe_name.strip()) == 0:
                safe_name = file_record.storage_filename

            # Проверяем параметр запроса ?preview=true
            is_preview = request.args.get('preview', 'false').lower() == 'true'

            # Если это предпросмотр, отключаем as_attachment и явно передаем mimetype из БД
            return send_from_directory(
                directory=app.config['UPLOAD_FOLDER'],
                path=file_record.storage_filename,
                as_attachment=not is_preview,
                download_name=safe_name,
                mimetype=file_record.mime_type  # Передаем оригинальный MIME-тип
            ), 200
        except Exception as e:
            print (traceback.format_exc())
            return jsonify({
                "error": f"Файл не найден, ошибка: {str(e)}",
                "message": "Файл физически отсутствует на сервере",
                "file_id": file_id
            }), 404


def delete_file_route(app):
    """Путь удаления файла"""

    @app.route('/task/delete_files/<int:file_id>', methods=['DELETE'])
    def delete_task_file(file_id):
        try:
            # file_record = TaskFile.session.get_or_404(file_id)
            file_record = db.session.get(TaskFile, file_id)
            #todo Здесь могла быть ваша реклама и проверка прав доступа

            delete_physical_file(file_record.storage_filename)


            db.session.delete(file_record)
            db.session.commit()

            return jsonify({"message": "Файл успешно удален"}), 200
        except Exception as e:
            return jsonify({
                "error": f"Ошибка удаления файла либо файл не найден",
                "message": str(e),
                "file_id": file_id
                }), 400


def get_current_user_id():
    """ID текущего пользователя из access-токена"""
    try:
        identity = get_jwt_identity()
    except RuntimeError:
        return None

    if identity is None:
        return None

    try:
        return int(identity)
    except (TypeError, ValueError):
        return identity


def init_logo_routes(app):
    """Инициализация путей для работы с логотипом"""

    # Гарантируем, что папка для загрузок внутри Flask существует
    # Обычно это 'static/uploads'
    UPLOAD_FOLDER = os.path.join(app.config['SRC_PATH'], '../asutg_frontend/public')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # При старте сервера проверяем, есть ли уже загруженный ранее кастомный логотип
    global CURRENT_LOGO_FILE
    if os.path.exists(os.path.join(UPLOAD_FOLDER, 'custom_logo.png')):
        CURRENT_LOGO_FILE = 'custom_logo.png'
    elif os.path.exists(os.path.join(UPLOAD_FOLDER, 'custom_logo.jpg')):
        CURRENT_LOGO_FILE = 'custom_logo.jpg'
    elif os.path.exists(os.path.join(UPLOAD_FOLDER, 'custom_logo.svg')):
        CURRENT_LOGO_FILE = 'custom_logo.svg'
    else:
        CURRENT_LOGO_FILE = 'Flag.png' # Если ничего нет, то дефолтный


    @app.route('/get_logo', methods=['GET'])
    def get_logo():
        """Эндпоинт, который фронтенд будет вызывать при загрузке страницы"""
        global CURRENT_LOGO_FILE
        return jsonify({
            "logo_url": f"/{CURRENT_LOGO_FILE}"
        }), 200


    @app.route('/upload_logo', methods=['POST'])
    def upload_logo():
        global CURRENT_LOGO_FILE
        # todo: проверка прав доступа

        if 'file' not in request.files:
            return jsonify({
                "error": "Файл не найден",
                "message": "По заданному пути не найден файл"
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "error": "Имя файла пустое",
                "message": "Имя файла не задано"
            }), 400

        # 1. Получаем расширение оригинального файла (.png, .jpg, .svg и т.д.)
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ['.png', '.jpg', '.jpeg', '.svg']:
            return jsonify({
                "error": "Неверный формат",
                "message": "Разрешены только PNG, JPG, JPEG и SVG"
            }), 400

        # 2. Очищаем старые кастомные логотипы, чтобы они не занимали место
        for old_ext in ['.png', '.jpg', '.jpeg', '.svg']:
            old_file = os.path.join(UPLOAD_FOLDER, f'custom_logo{old_ext}')
            if os.path.exists(old_file):
                os.remove(old_file)

        # 3. Сохраняем новый файл с его НАСТОЯЩИМ расширением
        filename = f"custom_logo{ext}"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        print(save_path)
        file.save(save_path)

        # 4. Обновляем глобальную переменную пути
        CURRENT_LOGO_FILE = f"{filename}"

        return jsonify({
            "message": "Лого успешно загружено",
            "logo_url": f"{CURRENT_LOGO_FILE}"
        }), 200


    @app.route('/reset_logo', methods=['GET'])
    def reset_logo():
        global CURRENT_LOGO_FILE
        # todo: проверка прав доступа

        # При сбросе просто удаляем сохраненные кастомные файлы
        for old_ext in ['.png', '.jpg', '.jpeg', '.svg']:
            old_file = os.path.join(UPLOAD_FOLDER, f'custom_logo{old_ext}')
            if os.path.exists(old_file):
                os.remove(old_file)

        # Возвращаем указатель на дефолтный Flag.svg (он должен лежать в папочке static сервера Flask)
        CURRENT_LOGO_FILE = "Flag.png"

        return jsonify({
            "message": "Лого успешно сброшено",
            "logo_url": f"{CURRENT_LOGO_FILE}"
        }), 200



def register_storage_routes(app):
    """Регистрация всех маршрутов файлового менеджера"""
    upload_file_route(app)
    get_task_files_route(app)
    download_file_route(app)
    delete_file_route(app)
    init_logo_routes(app)
    get_task_documentation_route(app)
    download_documentation_route(app)


def get_task_documentation_route(app):
    ##Получение файлов документации

    @app.route('/task/get_documentation/<int:task_id>', methods=['GET'])
    def et_task_documentation(task_id):
        task = db.session.get(Task, task_id)
        if not task.TaskRepairDocumentation and task.Parent:
            task = task.Parent
        files_data = []
        for task_documentation in task.TaskRepairDocumentation:
            if task_documentation.RepairDocumentation:
                files_data.append({
                    "id": task_documentation.RepairDocumentation.id,
                    "name": task_documentation.RepairDocumentation.original_name,
                    "upload_date": task_documentation.RepairDocumentation.upload_date.isoformat() if task_documentation.RepairDocumentation.upload_date else None,
                    "size": task_documentation.RepairDocumentation.file_size,
                    "mime_type": task_documentation.RepairDocumentation.mime_type
                })

        return jsonify({
            "task_id": task_id,
            "files": files_data
        })


def download_documentation_route(app):
    """Путь скачивания файла (с поддержкой предпросмотра inline)"""

    @app.route('/task/download_documentation/<int:file_id>')
    def download_documentation_file(file_id):
        try:
            file_record = db.session.get(RepairDocumentation, file_id)
        except Exception as e:
            return jsonify({"error": "File not found"},
                           {"message": f"File not found: {e}"}), 404
        #todo Здесь могла быть ваша реклама и проверка прав доступа

        try:
            safe_name = secure_filename_russian(file_record.original_name)

            if not safe_name or len(safe_name.strip()) == 0:
                safe_name = file_record.storage_filename

            # Проверяем параметр запроса ?preview=true
            is_preview = request.args.get('preview', 'false').lower() == 'true'

            # Если это предпросмотр, отключаем as_attachment и явно передаем mimetype из БД
            return send_from_directory(
                directory=app.config['UPLOAD_FOLDER'],
                path=file_record.storage_filename,
                as_attachment=not is_preview,
                download_name=safe_name,
                mimetype=file_record.mime_type  # Передаем оригинальный MIME-тип
            ), 200
        except Exception as e:
            print (traceback.format_exc())
            return jsonify({
                "error": f"Файл не найден, ошибка: {str(e)}",
                "message": "Файл физически отсутствует на сервере",
                "file_id": file_id
            }), 404
