from flask import request, jsonify
from datetime import datetime
from . import sapr_bp
from src.sapr.services.history_service import history_service
from src.sapr.dto import HistoryResponseDTO
from src.sapr.exceptions import InvalidHistoryFilterError


@sapr_bp.route('/history', methods=['GET'])
def get_history():
    # Получить историю действий с фильтрацией
    user_id = request.args.get('user_id', type=int)
    endpoint = request.args.get('endpoint', type=str)
    method = request.args.get('method', type=str)
    limit = request.args.get('limit', default=100, type=int)
    offset = request.args.get('offset', default=0, type=int)

    start_date_str = request.args.get('start_date', type=str)
    end_date_str = request.args.get('end_date', type=str)

    try:
        start_date = datetime.fromisoformat(start_date_str) if start_date_str else None
        end_date = datetime.fromisoformat(end_date_str) if end_date_str else None
    except ValueError as e:
        raise InvalidHistoryFilterError(f'Неккоректный формат даты: {str(e)}')

    history = history_service.get_history(
        user_id=user_id,
        endpoint=endpoint,
        method=method,
        limit=limit,
        offset=offset,
        start_date=start_date,
        end_date=end_date   
    )

    schema = HistoryResponseDTO(many=True)
    return jsonify(schema.dump(history)), 200