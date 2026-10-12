from flask import Blueprint, request, jsonify
from src.db import db
from src.auth.decorators import jwt_required_mock
from src.orm.orm_auth import PermissionMatrix



matr_api = Blueprint("admin_permissions_matrix", __name__, url_prefix="/api/admin/matrix")

PERMISSIONS_CODES = {
    0: "GET",
    1: "POST",
    2: "DELETE",
    3: "PUT",
}

## Декодирует код в понятный для пользователя вид.
def decode(code):
    if code is None:
        return ""

    result = []

    for bit, permissions in PERMISSIONS_CODES.items():
        if code & (1 << bit):
            result.append(permissions)

    return " ".join(result)

## Проверяет верно ли заполнены поле групп
def validate_ad_groups(value):

    if value is None:
        return []

    if not isinstance(value, list):
        raise ValueError("ad_groups должен быть массивом")

    result = []

    for row in value:

        if not isinstance(row, list):
            raise ValueError(
                "Каждый элемент ad_groups должен быть массивом"
            )

        if not all(isinstance(item, str) for item in row):
            raise ValueError(
                "Все элементы ad_groups должны быть строками"
            )

        result.append(row)

    if result:

        max_len = max(len(row) for row in result)

        for row in result:
            row.extend([""] * (max_len - len(row)))

    return result

## Возврат данных из модели в виде словаря 
def permission_matrix_to_dict(model):
    return {
        "id": model.id,
        "table_name": model.table_name,
        "permissions": model.permissions,
        "permissions_decode": decode(model.permissions),
        "ad_groups": model.ad_groups,
    }

## Получение матрицы доступа
@matr_api.get("/")
@jwt_required_mock
def get_permission_matrix():

    rows = PermissionMatrix.query.all()

    return jsonify([
        permission_matrix_to_dict(row)
        for row in rows
    ]), 200


## Получение конкретной строчки
@matr_api.get("/<int:permission_matrix_id>")
@jwt_required_mock
def get_permission_matrix_by_id(permission_matrix_id):

    row = PermissionMatrix.query.get(permission_matrix_id)

    if row is None:
        return jsonify({
            "error": "permission_matrix не найден"
        }), 404

    return jsonify(
        permission_matrix_to_dict(row)
    ), 200

## Добавления новой строчки в матрицу
@matr_api.post("/")
@jwt_required_mock
def create_permission_matrix():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "JSON body обязателен"
        }), 400

    try:
        ad_groups = validate_ad_groups(data.get("ad_groups", []))
    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    row = PermissionMatrix(
        table_name=data.get("table_name"),
        permissions=data.get("permissions", 0),
        ad_groups=ad_groups
    )
    db.session.add(row)
    try:
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        return jsonify({
            "error": str(error)
        }), 500
    return jsonify(
        permission_matrix_to_dict(row)
    ), 201

## Изменение по id
@matr_api.put("/<int:permission_matrix_id>")
@jwt_required_mock
def update_permission_matrix(permission_matrix_id):

    row = PermissionMatrix.query.get(permission_matrix_id)

    if row is None:
        return jsonify({
            "error": "permission_matrix не найден"
        }), 404

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "JSON body обязателен"
        }), 400

    try:

        if "table_name" in data:
            row.table_name = data["table_name"]

        if "permissions" in data:
            row.permissions = data["permissions"]

        if "ad_groups" in data:
            row.ad_groups = validate_ad_groups(
                data["ad_groups"]
            )

        db.session.commit()

    except ValueError as error:

        db.session.rollback()

        return jsonify({
            "error": str(error)
        }), 400

    except Exception as error:

        db.session.rollback()

        return jsonify({
            "error": str(error)
        }), 500

    return jsonify(
        permission_matrix_to_dict(row)
    ), 200


## Удаление по id
@matr_api.delete("/<int:permission_matrix_id>")
@jwt_required_mock
def delete_permission_matrix(permission_matrix_id):

    row = PermissionMatrix.query.get(permission_matrix_id)

    if row is None:
        return jsonify({
            "error": "permission_matrix не найден"
        }), 404

    try:

        db.session.delete(row)
        db.session.commit()

    except Exception as error:

        db.session.rollback()

        return jsonify({
            "error": str(error)
        }), 500

    return "", 204