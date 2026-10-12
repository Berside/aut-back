import os
import uuid
from flask import Blueprint, jsonify, request, current_app

from . import sapr_bp

ALLOWED_EXTENSIONS = {'glb', 'gltf', 'obj', 'stl'}


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@sapr_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username == 'admin' and password == 'admin123':
        return jsonify({
            'success': True,
            'token': 'fake-jwt-token-12345',
            'user': {'id': 1, 'username': username}
        })
    
    return jsonify({'success': False, 'error': 'Неправильный логин или пароль'}), 401


@sapr_bp.route('/upload-model', methods=['POST'])
def upload_model():
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'Файл не передан'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'Пустое имя файла'
        }), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': f'Допустимые форматы: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400

    extension = os.path.splitext(file.filename)[1].lower()
    storage_name = f"{uuid.uuid4().hex}{extension}"
    
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        upload_folder = os.path.join(current_app.config['SRC_PATH'], 'file_storage')
    
    os.makedirs(upload_folder, exist_ok=True)
    
    filepath = os.path.join(upload_folder, storage_name)
    file.save(filepath)
    
    return jsonify({
        'success': True,
        'technical_name': storage_name,
        'original_name': file.filename
    }), 200