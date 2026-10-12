from __future__ import annotations

import io
import logging
from dataclasses import asdict
from functools import wraps

from flask import Blueprint, Response, jsonify, request, send_file

from minio.error import S3Error

from src.s3.s3_client import ObjectInfo, S3Client, UploadResult, VersionInfo

logger = logging.getLogger(__name__)


def _handle_errors(view_func):

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        try:
            return view_func(*args, **kwargs)
        except FileNotFoundError as e:
            logger.warning("Файл не найден: %s", e)
            return jsonify({"error": "Not Found", "message": str(e)}), 404
        except S3Error as e:
            logger.error("Ошибка MinIO: %s", e)
            status = 404 if e.code in ("NoSuchKey", "NoSuchBucket", "NoSuchVersion") else 502
            return jsonify({"error": "S3Error", "code": e.code, "message": str(e)}), status
        except Exception as e:  # noqa: BLE001
            logger.exception("Внутренняя ошибка сервера")
            return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

    return wrapper


def _obj_info_to_dict(info: ObjectInfo) -> dict:
    return asdict(info)


def _upload_result_to_dict(result: UploadResult) -> dict:
    return asdict(result)


def _version_info_to_dict(v: VersionInfo) -> dict:
    return asdict(v)


class S3Blueprint:

    def __init__(self, client: S3Client, url_prefix: str = "/s3", name: str = "s3_api"):
        self.client = client
        self.blueprint = Blueprint(name, __name__, url_prefix=url_prefix)
        self._register_routes()

    # ──────────────────────────────────────────
    # Регистрация маршрутов
    # ──────────────────────────────────────────

    def _register_routes(self) -> None:
        bp = self.blueprint

        # Bucket
        bp.add_url_rule("/bucket", view_func=self.ensure_bucket, methods=["POST"])
        bp.add_url_rule("/bucket/exists", view_func=self.bucket_exists, methods=["GET"])

        # Versioning — bucket
        bp.add_url_rule("/bucket/versioning", view_func=self.get_versioning, methods=["GET"])
        bp.add_url_rule("/bucket/versioning", view_func=self.set_versioning, methods=["PUT"])

        # Upload
        bp.add_url_rule("/objects/<path:key>/upload-path", view_func=self.upload_file, methods=["POST"])
        bp.add_url_rule("/objects/<path:key>", view_func=self.upload_bytes, methods=["PUT"])
        bp.add_url_rule("/objects/<path:key>/upload-form", view_func=self.upload_fileobj, methods=["POST"])

        # Download
        bp.add_url_rule("/objects/<path:key>/download", view_func=self.download_bytes, methods=["GET"])
        bp.add_url_rule("/objects/<path:key>/download-to", view_func=self.download_file, methods=["POST"])
        bp.add_url_rule("/objects/<path:key>/stream", view_func=self.stream, methods=["GET"])

        # Metadata & listing
        bp.add_url_rule("/objects/<path:key>/info", view_func=self.info, methods=["GET"])
        bp.add_url_rule("/objects/<path:key>/exists", view_func=self.exists, methods=["GET"])
        bp.add_url_rule("/objects", view_func=self.list_objects, methods=["GET"])

        # Delete
        bp.add_url_rule("/objects/<path:key>", view_func=self.delete, methods=["DELETE"])
        bp.add_url_rule("/objects", view_func=self.delete_many, methods=["DELETE"])

        # Presigned URLs
        bp.add_url_rule("/objects/<path:key>/presigned-url", view_func=self.presigned_url, methods=["GET"])
        bp.add_url_rule("/objects/<path:key>/presigned-put-url", view_func=self.presigned_put_url, methods=["GET"])

        # Copy
        bp.add_url_rule("/objects/<path:key>/copy", view_func=self.copy, methods=["POST"])

        # ── Versioning — object versions ──
        bp.add_url_rule("/objects/versions", view_func=self.list_versions, methods=["GET"])
        bp.add_url_rule("/objects/<path:key>/versions", view_func=self.list_key_versions, methods=["GET"])
        bp.add_url_rule("/objects/<path:key>/versions/<version_id>/info", view_func=self.version_info, methods=["GET"])
        bp.add_url_rule("/objects/<path:key>/versions/<version_id>/exists", view_func=self.version_exists, methods=["GET"])
        bp.add_url_rule("/objects/<path:key>/versions/<version_id>/download", view_func=self.version_download, methods=["GET"])
        bp.add_url_rule("/objects/<path:key>/versions/<version_id>", view_func=self.delete_version, methods=["DELETE"])
        bp.add_url_rule("/objects/<path:key>/versions/<version_id>/restore", view_func=self.restore_version, methods=["POST"])
        bp.add_url_rule("/objects/<path:key>/versions/<version_id>/presigned-url", view_func=self.presigned_version_url_route, methods=["GET"])

    # ──────────────────────────────────────────
    # Bucket
    # ──────────────────────────────────────────

    @_handle_errors
    def ensure_bucket(self):
        self.client.ensure_bucket()
        return jsonify({"bucket": self.client.bucket, "status": "ready"}), 200

    @_handle_errors
    def bucket_exists(self):
        exists = self.client.bucket_exists()
        return jsonify({"bucket": self.client.bucket, "exists": exists}), 200

    # ──────────────────────────────────────────
    # Versioning — bucket
    # ──────────────────────────────────────────

    @_handle_errors
    def get_versioning(self):
        status = self.client.get_versioning_status()
        return jsonify({"bucket": self.client.bucket, "status": status.status}), 200

    @_handle_errors
    def set_versioning(self):
        payload = request.get_json(silent=True) or {}
        if "enabled" not in payload:
            return jsonify({"error": "Bad Request", "message": "Поле 'enabled' (bool) обязательно"}), 400
        status = self.client.set_versioning(bool(payload["enabled"]))
        return jsonify({"bucket": self.client.bucket, "status": status.status}), 200

    # ──────────────────────────────────────────
    # Upload
    # ──────────────────────────────────────────

    @_handle_errors
    def upload_file(self, key: str):
        #Загружает файл, уже лежащий на сервере, по локальному пути
        payload = request.get_json(silent=True) or {}
        source_path = payload.get("source_path")
        if not source_path:
            return jsonify({"error": "Bad Request", "message": "Поле 'source_path' обязательно"}), 400

        content_type = payload.get("content_type")
        presigned = bool(payload.get("presigned", False))

        result = self.client.upload_file(
            key, source_path, content_type=content_type, presigned=presigned
        )
        return jsonify(_upload_result_to_dict(result)), 201

    @_handle_errors
    def upload_bytes(self, key: str):
        #Загружает содержимое тела запроса как есть (raw upload)
        data = request.get_data()
        if data is None:
            return jsonify({"error": "Bad Request", "message": "Тело запроса пустое"}), 400

        content_type = request.content_type or "application/octet-stream"
        presigned = request.args.get("presigned", "false").lower() == "true"

        result = self.client.upload_bytes(
            key, data, content_type=content_type, presigned=presigned
        )
        return jsonify(_upload_result_to_dict(result)), 201

    @_handle_errors
    def upload_fileobj(self, key: str):
        #Загружает файл, присланный через multipart/form-data (поле 'file')
        if "file" not in request.files:
            return jsonify({"error": "Bad Request", "message": "Поле формы 'file' обязательно"}), 400

        file_storage = request.files["file"]
        content_type = file_storage.mimetype or "application/octet-stream"
        presigned = request.args.get("presigned", "false").lower() == "true"

        file_storage.stream.seek(0, io.SEEK_END)
        length = file_storage.stream.tell()
        file_storage.stream.seek(0)

        result = self.client.upload_fileobj(
            key,
            file_storage.stream,
            length=length,
            content_type=content_type,
            presigned=presigned,
        )
        return jsonify(_upload_result_to_dict(result)), 201

    # ──────────────────────────────────────────
    # Download
    # ──────────────────────────────────────────

    @_handle_errors
    def download_bytes(self, key: str):
        #Скачивает файл из S3 и отдаёт его клиенту
        file_info = self.client.info(key)
        content_type = file_info.content_type or "application/octet-stream"
        file_data = self.client.download_bytes(key)
        filename = key.rsplit("/", 1)[-1]

        return send_file(
            io.BytesIO(file_data),
            mimetype=content_type,
            as_attachment=True,
            download_name=filename,
        )

    @_handle_errors
    def download_file(self, key: str):
        #Скачивает объект в файл на сервере по указанному пути назначения
        payload = request.get_json(silent=True) or {}
        destination = payload.get("destination")
        if not destination:
            return jsonify({"error": "Bad Request", "message": "Поле 'destination' обязательно"}), 400

        saved_path = self.client.download_file(key, destination)
        return jsonify({"key": key, "saved_to": str(saved_path)}), 200

    @_handle_errors
    def stream(self, key: str):
        #Отдаёт файл потоково
        file_info = self.client.info(key)
        content_type = file_info.content_type or "application/octet-stream"
        chunk_size = int(request.args.get("chunk_size", 8 * 1024))
        filename = key.rsplit("/", 1)[-1]

        return Response(
            self.client.stream(key, chunk_size=chunk_size),
            mimetype=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(file_info.size),
            },
        )

    # ──────────────────────────────────────────
    # Metadata & listing
    # ──────────────────────────────────────────

    @_handle_errors
    def info(self, key: str):
        object_info = self.client.info(key)
        return jsonify(_obj_info_to_dict(object_info)), 200

    @_handle_errors
    def exists(self, key: str):
        return jsonify({"key": key, "exists": self.client.exists(key)}), 200

    @_handle_errors
    def list_objects(self):
        prefix = request.args.get("prefix", "")
        recursive = request.args.get("recursive", "true").lower() == "true"
        objects = self.client.list_objects(prefix=prefix, recursive=recursive)
        return jsonify([_obj_info_to_dict(o) for o in objects]), 200

    # ──────────────────────────────────────────
    # Delete
    # ──────────────────────────────────────────

    @_handle_errors
    def delete(self, key: str):
        self.client.delete(key)
        return jsonify({"key": key, "deleted": True}), 200

    @_handle_errors
    def delete_many(self):
        payload = request.get_json(silent=True) or {}
        keys = payload.get("keys")
        if not keys or not isinstance(keys, list):
            return jsonify({"error": "Bad Request", "message": "Поле 'keys' должно быть непустым списком"}), 400

        failed = self.client.delete_many(keys)
        return jsonify({
            "requested": keys,
            "failed": failed,
            "deleted": [k for k in keys if k not in failed],
        }), 200

    # ──────────────────────────────────────────
    # Presigned URLs
    # ──────────────────────────────────────────

    @_handle_errors
    def presigned_url(self, key: str):
        expiry = request.args.get("expiry", type=int)
        url = self.client.presigned_url(key, expiry=expiry)
        return jsonify({"key": key, "url": url}), 200

    @_handle_errors
    def presigned_put_url(self, key: str):
        expiry = request.args.get("expiry", type=int)
        url = self.client.presigned_put_url(key, expiry=expiry)
        return jsonify({"key": key, "url": url}), 200

    # ──────────────────────────────────────────
    # Copy
    # ──────────────────────────────────────────

    @_handle_errors
    def copy(self, key: str):
        payload = request.get_json(silent=True) or {}
        dst_key = payload.get("dst_key")
        dst_bucket = payload.get("dst_bucket")
        if not dst_key:
            return jsonify({"error": "Bad Request", "message": "Поле 'dst_key' обязательно"}), 400

        self.client.copy(key, dst_key, dst_bucket=dst_bucket)
        return jsonify({
            "src_key": key,
            "dst_key": dst_key,
            "dst_bucket": dst_bucket or self.client.bucket,
        }), 200

    # ──────────────────────────────────────────
    # Versioning — object versions
    # ──────────────────────────────────────────

    @_handle_errors
    def list_versions(self):
        #Список всех версий объектов в бакете
        prefix = request.args.get("prefix", "")
        include_markers = request.args.get("include_delete_markers", "false").lower() == "true"
        versions = self.client.list_versions(prefix=prefix, include_delete_markers=include_markers)
        return jsonify([_version_info_to_dict(v) for v in versions]), 200

    @_handle_errors
    def list_key_versions(self, key: str):
        #Список версий конкретного объекта
        versions = self.client.list_versions(prefix=key)
        filtered = [v for v in versions if v.key == key]
        return jsonify([_version_info_to_dict(v) for v in filtered]), 200

    @_handle_errors
    def version_info(self, key: str, version_id: str):
        #Метаданные конкретной версии
        info = self.client.get_version_info(key, version_id)
        return jsonify(_obj_info_to_dict(info)), 200

    @_handle_errors
    def version_exists(self, key: str, version_id: str):
        #Проверка существования конкретной версии
        return jsonify({"key": key, "version_id": version_id, "exists": self.client.exists_version(key, version_id)}), 200

    @_handle_errors
    def version_download(self, key: str, version_id: str):
        #Скачивание конкретной версии файла
        file_info = self.client.get_version_info(key, version_id)
        content_type = file_info.content_type or "application/octet-stream"
        file_data = self.client.get_version(key, version_id)
        filename = key.rsplit("/", 1)[-1]

        return send_file(
            io.BytesIO(file_data),
            mimetype=content_type,
            as_attachment=True,
            download_name=filename,
        )

    @_handle_errors
    def delete_version(self, key: str, version_id: str):
        #Физическое удаление конкретной версии
        self.client.delete_version(key, version_id)
        return jsonify({"key": key, "version_id": version_id, "deleted": True}), 200

    @_handle_errors
    def restore_version(self, key: str, version_id: str):
        #Восстановление указанной версии как последней
        result = self.client.restore_version(key, version_id)
        return jsonify({
            "key": key,
            "restored_version_id": version_id,
            "new_version_id": result.version_id,
            "etag": result.etag,
        }), 200

    @_handle_errors
    def presigned_version_url_route(self, key: str, version_id: str):
        #Presigned GET URL для конкретной версии
        expiry = request.args.get("expiry", type=int)
        url = self.client.presigned_version_url(key, version_id, expiry=expiry)
        return jsonify({"key": key, "version_id": version_id, "url": url}), 200
