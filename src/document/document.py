import os, uuid, jinja2
import traceback

from flask import jsonify, send_file, request, Blueprint, current_app
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
from docxtpl import DocxTemplate
from src.db import db
from src.orm.orm_file import TaskFile
from src.orm.orm_task import Task
from src.storage.file_manager import get_current_user_id

from src.orm.orm_folder import Document
from src.orm.orm_sapr import Project

from src.sapr.routes import sapr_bp

def upload_generate_document(app):
    """Генерация документа по шаблону"""

    @app.route('/task/generate_document/<int:task_id>/<string:original_name>', methods=['GET'])
    @jwt_required()
    def route_generate_document(task_id, original_name = 'Документ.doc'):
        result = generate_document(app, task_id, original_name)
        return result


def generate_document(app, task_id, original_name = 'Документ.docx'):
    try:
        task = db.session.get(Task, task_id)
        template_path = app.config['TEMPLATE_PATH']
        match task.type_link:
            case 3:
                doc = DocxTemplate(os.path.join(template_path,'1. Наряд.docx'))
            case 2:
                doc = DocxTemplate(os.path.join(template_path,'2. Акт приёма-передачи.docx'))
            case _:
                return jsonify({
                    "error": "Неизвестный тип задачи",
                    "message": f"Тип задачи {task.type_link} не поддерживается"
                }), 400

        extension = os.path.splitext(original_name)[1]
        if extension == '':
            extension = '.docx'
            original_name = original_name + '.docx'
        storage_name = f"{uuid.uuid4().hex}{extension}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], storage_name)

        jinja_env = jinja2.Environment(extensions=['jinja2.ext.loopcontrols'])
        jinja_env.finalize = lambda x: x if x is not None else ""
        doc.render({'task': task}, jinja_env)
        doc.save(save_path)

        file_size = os.path.getsize(save_path)
        mime_type = extension

        # Создаём файл
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
        db.session.close()

        return jsonify({
            "message": "Document created successfully",
            "task_link": task_id,
            "file_name": original_name,
            "file_size": file_size
        })
    except Exception as e:
        db.session.rollback()
        print (traceback.format_exc())
        return jsonify({
            "error": f"{e}",
            "message": "ошибка"
        }), 400



@sapr_bp.route('/task/generate_document/<int:task_id>/<string:original_name>', methods=['GET'])
def route_generate_document(task_id, original_name='Документ.doc'):
    """Генерация документа по шаблону"""
    return generate_document(task_id, original_name)


@sapr_bp.route('/document/<int:doc_id>/download', methods=['GET'])
def download_document(doc_id):
    # Скачать файл документа
    try:
        doc = db.session.get(Document, doc_id)

        if not doc:
            return jsonify({'error': 'Документ не найден'}), 404

        if not doc.file_link:
            return jsonify({'error': 'У документа нет файла'}), 404

        file = db.session.get(TaskFile, doc.file_link)
        if not file:
            return jsonify({'error': 'Файл не найден'}), 404

        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.storage_filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "Файл не найден на диске"}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=file.original_name
        )
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500


@sapr_bp.route('/document/<int:doc_id>/upload', methods=['POST'])
def upload_document(doc_id):
    # Загрузить новую версию файла документа
    try:
        doc = db.session.get(Document, doc_id)

        if not doc:
            return jsonify({'error': 'Документ не найден'}), 404

        if 'file' not in request.files:
            return jsonify({'error': 'Файл не передан'}), 400

        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            return jsonify({'error': 'Пустое имя файла'}), 400

        # Удаляем старый файл, если он есть
        if doc.file_link:
            old_file = TaskFile.query.get(doc.file_link)
            if old_file:
                old_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_file.storage_filename)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
                db.session.delete(old_file)

        extension = os.path.splitext(uploaded_file.filename)[1]
        storage_name = f"{uuid.uuid4().hex}{extension}"
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], storage_name)
        uploaded_file.save(save_path)

        file_size = os.path.getsize(save_path)

        new_file = TaskFile(
            task_link=None,
            original_name=uploaded_file.filename,
            storage_filename=storage_name,
            file_size=file_size,
            mime_type=extension,
            uploaded_by=get_current_user_id()
        )

        db.session.add(new_file)
        db.session.flush()

        doc.file_link = new_file.id
        db.session.commit()

        return jsonify({
            'message': 'Файл успешно загружен',
            'document_id': doc_id,
            'file_id': new_file.id,
            'file_name': uploaded_file.filename,
            'file_size': file_size
        }), 200

    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': str(e)}), 500
    

@sapr_bp.route('/document/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    # Удаление документа

    try:
        doc = db.session.get(Document, doc_id)

        if not doc:
            return jsonify({'error': 'Документ не найден'}), 404
        from src.db import db

        if doc.file_link:
            file = db.session.get(TaskFile, doc.file_link)
            if file:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.storage_filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                db.session.delete(file)

        db.session.delete(doc)
        db.session.commit()

        return jsonify({'message': 'Документ удален'}), 200

    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': str(e)}), 500

@sapr_bp.route('/projects/<int:project_id>/documents', methods=['GET'])
def get_project_documents(project_id):
    # Список документов проекта

    try:
        project = db.session.get(Project, project_id)

        if not project:
            return jsonify({'error': 'Проект не найден'}), 404
        
        documents = db.session.query(Document).filter(
            Document.project_link == project_id
        ).all()

        result = []

        for doc in documents:
            result.append({
                'id': doc.id,
                'name': doc.name,
                'number': doc.number,
                'doc_type': doc.doc_type_link,
                'file_name': doc.file.original_name if doc.file else None,
                'file_size': doc.file.file_size if doc.file else None,
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'description': doc.description
            })

        return jsonify({
            'project_id': project_id,
            'project_name': project.name,
            'documents': result,
            'total': len(result)
        }), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@sapr_bp.route('/document/create', methods=['POST'])
def create_document():
    # Создание документа с файлом

    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не найден'}), 400
        
        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            return jsonify({'error': 'Пустое имя файла'}), 400
        
        project_id = request.form.get('project_id')
        
        if not project_id:
            return jsonify({'error': 'Не указан ID проекта'}), 400
        
        project = db.session.get(Project, int(project_id))
        if not project:
            return jsonify({'error': 'Проект не найден'}), 404
        
        extension = os.path.splitext(uploaded_file.filename)[1]
        storage_name = f"{uuid.uuid4().hex}{extension}"
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], storage_name)
        uploaded_file.save(save_path)

        file_size = os.path.getsize(save_path)

        new_file = TaskFile(
            task_link=None,
            original_name=uploaded_file.filename,
            storage_filename=storage_name,
            file_size=file_size,
            mime_type=extension,
            uploaded_by=get_current_user_id()
        )

        db.session.add(new_file)
        db.session.flush()

        new_document = Document(
            project_link=int(project_id),
            folder_link=None,
            doc_type_link=int(request.form.get('doc_type', 1)),
            name=request.form.get('name', uploaded_file.filename),
            number=request.form.get('number'),
            description=request.form.get('description'),
            file_link=new_file.id,
            created_by=get_current_user_id()
        )

        db.session.add(new_document)
        db.session.commit()

        return jsonify({
            'message': 'Документ создан',
            'document_id': new_document.id,
            'file_id': new_file.id,
            'file_name': uploaded_file.filename
        }), 201
    
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': str(e)}), 500

@sapr_bp.route('/search', methods=['GET'])
def global_search():
    # Глобальный поиск по всем сущностям
    try:
        query = request.args.get('q', '').strip()

        if not query:
            return jsonify({'error': 'Не задан поисковый запрос'}), 400

        limit = int(request.args.get('limit', 20))

        results = {
            'query': query,
            'tasks': [],
            'documents': [],
            'files': [],
            'projects': []
        }

        # Поиск по задачам
        tasks = db.session.query(Task).filter(
            or_(
                Task.title.ilike(f'%{query}%'),
                Task.description.ilike(f'%{query}%')
            )
        ).limit(limit).all()

        for task in tasks:
            results['tasks'].append({
                'id': task.id,
                'type': 'task',
                'title': task.title,
                'description': task.description[:100] if task.description else None,
                'status': task.status_link
            })

        # Поиск по документам
        documents = db.session.query(Document).filter(
            or_(
                Document.name.ilike(f'%{query}%'),
                Document.number.ilike(f'%{query}%'),
                Document.description.ilike(f'%{query}%')
            )
        ).limit(limit).all()

        for doc in documents:
            results['documents'].append({
                'id': doc.id,
                'type': 'document',
                'name': doc.name,
                'number': doc.number,
                'description': doc.description[:100] if doc.description else None,
                'doc_type': doc.doc_type_link
            })

        # Поиск по файлам
        files = db.session.query(TaskFile).filter(
            TaskFile.original_name.ilike(f'%{query}%')
        ).limit(limit).all()

        for file in files:
            results['files'].append({
                'id': file.id,
                'type': 'file',
                'original_name': file.original_name,
                'file_size': file.file_size,
                'upload_date': file.upload_date.isoformat() if file.upload_date else None
            })

        # Поиск по проектам
        projects = db.session.query(Project).filter(
            Project.name.ilike(f'%{query}%')
        ).limit(limit).all()

        for proj in projects:
            results['projects'].append({
                'id': proj.id,
                'type': 'project',
                'name': proj.name,
                'description': proj.description[:100] if proj.description else None
            })

        # Подсчитываем общее количество результатов
        total = (
            len(results['tasks']) +
            len(results['documents']) +
            len(results['files']) +
            len(results['projects'])
        )

        return jsonify({
            'query': query,
            'total': total,
            'results': results
        }), 200

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500


@sapr_bp.route('/search/suggest', methods=['GET'])
def search_suggest():
    # Быстрый поиск для autocomplete (подсказки)
    try:
        query = request.args.get('q', '').strip()

        if len(query) < 2:
            return jsonify({'suggestions': []}), 200

        limit = int(request.args.get('limit', 10))
        suggestions = []

        # Ищем по задачам
        tasks = db.session.query(Task).filter(
            Task.title.ilike(f'%{query}%')
        ).limit(limit).all()

        for task in tasks:
            suggestions.append({
                'id': task.id,
                'type': 'task',
                'value': task.title,
                'label': f'Задача: {task.title}'
            })

        # Ищем по документам
        if len(suggestions) < limit:
            documents = db.session.query(Document).filter(
                Document.name.ilike(f'%{query}%')
            ).limit(limit - len(suggestions)).all()

            for doc in documents:
                suggestions.append({
                    'id': doc.id,
                    'type': 'document',
                    'value': doc.name,
                    'label': f'Документ: {doc.name} ({doc.number})'
                })

        # Ищем по проектам        
        if len(suggestions) < limit:
            projects = db.session.query(Project).filter(
                Project.name.ilike(f'%{query}%')
            ).limit(limit - len(suggestions)).all()

            for proj in projects:
                suggestions.append({
                    'id': proj.id,
                    'type': 'project',
                    'value': proj.name,
                    'label': f'Проект: {proj.name}'
                })

        return jsonify({
            'query': query,
            'suggestions': suggestions
        }), 200

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

