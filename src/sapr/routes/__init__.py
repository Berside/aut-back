from flask import Blueprint, jsonify
import logging
from marshmallow import ValidationError
from src.sapr.exceptions import AppError

sapr_bp = Blueprint('sapr', __name__, url_prefix='/api/sapr')

logger = logging.getLogger(__name__)

# ОБРАБОТЧИКИ ОШИБОК (общие для всех роутов)
@sapr_bp.errorhandler(AppError)
def handle_app_error(error: AppError):
    return jsonify({
        'error_code': error.error_code,
        'message': error.message,
    }), error.http_status


@sapr_bp.errorhandler(ValidationError)
def handle_validation_error(error: ValidationError):
    return jsonify({
        'error_code': 'VALIDATION_ERROR',
        'message': 'Некорректные данные запроса',
        'details': error.messages,
    }), 400


@sapr_bp.errorhandler(Exception)
def handle_generic_exception(error: Exception):
    logger.exception(f'Непредвиденная ошибка: {str(error)}')
    return jsonify({
        'error_code': 'INTERNAL_ERROR',
        'message': 'Произошла непредвиденная ошибка на сервере',
    }), 500

from . import (
    item,
    projects,
    models,
    animation_steps,
    assembly_items,
    categories,
    types,
    parts,
    project_parts,
    legacy,
    instruction,
    tree,
    history,
    structure_routes
    
)