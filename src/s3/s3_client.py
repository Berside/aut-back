from __future__ import annotations

import io
import logging
import mimetypes
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import BinaryIO, Iterator
import urllib3
import socket
from urllib3.exceptions import MaxRetryError, NewConnectionError, TimeoutError as URLLib3TimeoutError

from minio import Minio
from minio.commonconfig import COPY, CopySource
from minio.api import VersioningConfig
from minio.deleteobjects import DeleteObject
from minio.error import S3Error

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class S3Config:
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    secure: bool = False
    presigned_url_expiry: int = 3600    # seconds


# ──────────────────────────────────────────────
# Result types
# ──────────────────────────────────────────────

@dataclass(slots=True)
class UploadResult:
    key: str
    bucket: str
    etag: str
    url: str | None = None
    version_id: str | None = None


@dataclass(slots=True)
class ObjectInfo:
    key: str
    size: int                           # bytes
    last_modified: str
    etag: str
    content_type: str | None = None
    version_id: str | None = None


@dataclass(slots=True)
class VersionInfo:
    key: str
    version_id: str
    is_latest: bool
    size: int
    last_modified: str
    etag: str
    content_type: str | None = None
    is_delete_marker: bool = False


@dataclass(frozen=True, slots=True)
class VersioningStatus:
    status: str  # "Enabled" | "Suspended" | "Off"


# ──────────────────────────────────────────────
# Client
# ──────────────────────────────────────────────

class S3Client:

    http_client = urllib3.PoolManager(
        timeout=urllib3.Timeout(connect=5, read=10),
        retries=urllib3.Retry(
            total=3,
            backoff_factor=0.2,
            status_forcelist=[500, 502, 503, 504],
        ),
    )

    def __init__(self, config: S3Config) -> None:
        self._cfg = config
        self._client = Minio(
            config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.secure,
            http_client=self.http_client
        )

    @property
    def bucket(self) -> str:
        return self._cfg.bucket

    # ──────────────────────────────────────────
    # Bucket
    # ──────────────────────────────────────────

    def ensure_bucket(self) -> bool:
        #Создаёт бакет, если он не существует. Возвращает True если успешно
        try:
            if self._client.bucket_exists(self.bucket):
                logger.debug("Бакет '%s' уже существует.", self.bucket)
                return True
            self._client.make_bucket(self.bucket)
            logger.info("Бакет '%s' создан.", self.bucket)
            return True
        except (MaxRetryError, NewConnectionError, URLLib3TimeoutError, socket.gaierror, socket.timeout) as e:
            logger.error("Проблема с сетью/DNS при подключении к MinIO: %s", e)
            return False
        except S3Error as e:
            logger.error("Ошибка MinIO при создании бакета '%s': %s", self.bucket, e)
            return False
        except Exception as e:
            logger.error("Неожиданная ошибка: %s", e)
            return False

    def bucket_exists(self) -> bool:
        #Проверяет существование бакета
        try:
            return self._client.bucket_exists(self.bucket)
        except S3Error as e:
            logger.error("Ошибка MinIO при проверке бакета '%s': %s", self.bucket, e)
            raise

    # ──────────────────────────────────────────
    # Upload
    # ──────────────────────────────────────────

    def upload_file(
        self,
        key: str,
        source: str | Path,
        *,
        content_type: str | None = None,
        presigned: bool = False,
    ) -> UploadResult:
        #Загружает локальный файл в MinIO
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"Файл не найден: '{source}'")

        ct = content_type or _guess_mime(source) or "application/octet-stream"
        try:
            result = self._client.fput_object(
                self.bucket, key, str(source), content_type=ct
            )
            logger.debug("Загружен файл '%s' → s3://%s/%s", source, self.bucket, key)
            return self._make_result(key, result.etag, presigned, version_id=result.version_id)
        except S3Error as e:
            logger.error("Ошибка MinIO при загрузке файла '%s': %s", key, e)
            raise

    def upload_bytes(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        presigned: bool = False,
    ) -> UploadResult:
        #Загружает bytes-объект в MinIO
        try:
            result = self._client.put_object(
                self.bucket, key,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            logger.debug("Загружены байты → s3://%s/%s (%d Б)", self.bucket, key, len(data))
            return self._make_result(key, result.etag, presigned, version_id=result.version_id)
        except S3Error as e:
            logger.error("Ошибка MinIO при загрузке байтов в '%s': %s", key, e)
            raise

    def upload_fileobj(
        self,
        key: str,
        fileobj: BinaryIO,
        *,
        length: int = -1,
        content_type: str = "application/octet-stream",
        presigned: bool = False,
    ) -> UploadResult:
        #Загружает file-like object (стрим) в MinIO
        #Если размер неизвестен, length=-1 — MinIO использует multipart upload
        
        try:
            result = self._client.put_object(
                self.bucket, key,
                data=fileobj,
                length=length,
                content_type=content_type,
            )
            logger.debug("Загружен файловый объект → s3://%s/%s", self.bucket, key)
            return self._make_result(key, result.etag, presigned, version_id=result.version_id)
        except S3Error as e:
            logger.error("Ошибка MinIO при загрузке файлового объекта в '%s': %s", key, e)
            raise

    # ──────────────────────────────────────────
    # Download
    # ──────────────────────────────────────────

    def download_bytes(self, key: str) -> bytes:
        #Скачивает объект и возвращает содержимое как bytes
        response = None
        try:
            response = self._client.get_object(self.bucket, key)
            return response.read()
        except S3Error as e:
            logger.error("Ошибка MinIO при скачивании '%s': %s", key, e)
            raise
        finally:
            if response:
                response.close()
                response.release_conn()

    def download_file(self, key: str, destination: str | Path) -> Path:
        #Скачивает объект в локальный файл
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._client.fget_object(self.bucket, key, str(destination))
            logger.debug("Скачан s3://%s/%s → '%s'", self.bucket, key, destination)
            return destination
        except S3Error as e:
            logger.error("Ошибка MinIO при скачивании '%s' в '%s': %s", key, destination, e)
            raise

    def stream(self, key: str, chunk_size: int = 8 * 1024) -> Iterator[bytes]:
        #Возвращает генератор чанков для стриминга большого файла
        response = None
        try:
            response = self._client.get_object(self.bucket, key)
            yield from response.stream(chunk_size)
        except S3Error as e:
            logger.error("Ошибка MinIO при стриминге '%s': %s", key, e)
            raise
        finally:
            if response:
                response.close()
                response.release_conn()

    # ──────────────────────────────────────────
    # Metadata & listing
    # ──────────────────────────────────────────

    def info(self, key: str) -> ObjectInfo:
        #Возвращает метаданные объекта
        try:
            meta = self._client.stat_object(self.bucket, key)
            return ObjectInfo(
                key=key,
                size=meta.size,
                last_modified=str(meta.last_modified),
                etag=meta.etag,
                content_type=meta.content_type,
            )
        except S3Error as e:
            logger.error("Ошибка MinIO при получении метаданных '%s': %s", key, e)
            raise

    def exists(self, key: str) -> bool:
        try:
            self._client.stat_object(self.bucket, key)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            raise

    def list_objects(self, prefix: str = "", recursive: bool = True) -> list[ObjectInfo]:
        #Возвращает список объектов с опциональным префиксом
        try:
            objects = self._client.list_objects(
                self.bucket, prefix=prefix, recursive=recursive
            )
            return [
                ObjectInfo(
                    key=obj.object_name,
                    size=obj.size,
                    last_modified=str(obj.last_modified),
                    etag=obj.etag or "",
                )
                for obj in objects
            ]
        except S3Error as e:
            logger.error("Ошибка MinIO при получении списка объектов (префикс='%s'): %s", prefix, e)
            raise

    # ──────────────────────────────────────────
    # Delete
    # ──────────────────────────────────────────

    def delete(self, key: str) -> None:
        #Удаляет один объект (создаёт delete marker, если версионирование включено)
        try:
            self._client.remove_object(self.bucket, key)
            logger.debug("Удалён s3://%s/%s", self.bucket, key)
        except S3Error as e:
            logger.error("Ошибка MinIO при удалении '%s': %s", key, e)
            raise

    def delete_many(self, keys: list[str]) -> list[str]:
        #Удаляет список объектов за один запрос.
        #Возвращает ключи, которые не удалось удалить.
        
        delete_objects = [DeleteObject(key) for key in keys]
        failed: list[str] = []
        try:
            errors = self._client.remove_objects(self.bucket, iter(delete_objects))
            for err in errors:
                logger.warning("Не удалось удалить '%s': %s", err.name, err.message)
                failed.append(err.name)
        except S3Error as e:
            logger.error("Ошибка MinIO при массовом удалении: %s", e)
            raise
        return failed

    # ──────────────────────────────────────────
    # Presigned URLs
    # ──────────────────────────────────────────

    def presigned_url(self, key: str, *, expiry: int | None = None) -> str:
        #Генерирует presigned GET URL
        try:
            return self._client.presigned_get_object(
                self.bucket, key,
                expires=timedelta(seconds=expiry or self._cfg.presigned_url_expiry),
            )
        except S3Error as e:
            logger.error("Ошибка MinIO при генерации presigned GET URL для '%s': %s", key, e)
            raise

    def presigned_put_url(self, key: str, *, expiry: int | None = None) -> str:
        #Генерирует presigned PUT URL (для загрузки прямо с клиента)
        try:
            return self._client.presigned_put_object(
                self.bucket, key,
                expires=timedelta(seconds=expiry or self._cfg.presigned_url_expiry),
            )
        except S3Error as e:
            logger.error("Ошибка MinIO при генерации presigned PUT URL для '%s': %s", key, e)
            raise

    # ──────────────────────────────────────────
    # Copy
    # ──────────────────────────────────────────

    def copy(self, src_key: str, dst_key: str, *, dst_bucket: str | None = None) -> None:
        #Копирует объект внутри бакета или в другой бакет
        try:
            self._client.copy_object(
                dst_bucket or self.bucket,
                dst_key,
                CopySource(self.bucket, src_key),
                metadata_directive=COPY,
            )
            logger.debug(
                "Скопирован s3://%s/%s → s3://%s/%s",
                self.bucket, src_key, dst_bucket or self.bucket, dst_key,
            )
        except S3Error as e:
            logger.error("Ошибка MinIO при копировании '%s' в '%s': %s", src_key, dst_key, e)
            raise

    # ──────────────────────────────────────────
    # Versioning
    # ──────────────────────────────────────────

    def get_versioning_status(self) -> VersioningStatus:
        #Возвращает текущий статус версионирования бакета
        try:
            result = self._client.get_bucket_versioning(self.bucket)
            return VersioningStatus(status=result.status)
        except S3Error as e:
            logger.error("Ошибка MinIO при получении статуса версионирования: %s", e)
            raise

    def set_versioning(self, enabled: bool) -> VersioningStatus:
        #Включает (enabled=True) или приостанавливает (enabled=False) версионирование
        #S3 не позволяет полностью отключить — только suspend

        try:
            config = VersioningConfig(status="Enabled" if enabled else "Suspended")
            self._client.set_bucket_versioning(self.bucket, config)
            logger.info(
                "Версионирование бакета '%s': %s",
                self.bucket,
                "Enabled" if enabled else "Suspended",
            )
            return self.get_versioning_status()
        except S3Error as e:
            logger.error("Ошибка MinIO при изменении версионирования: %s", e)
            raise

    def list_versions(
            self,
            prefix: str = "",
            include_delete_markers: bool = False,
    ) -> list[VersionInfo]:
        #Возвращает список версий объектов (опционально по префиксу)"""
        try:
            objects = self._client.list_objects(
                self.bucket,
                prefix=prefix or None,
                include_version=True,
            )
            return [
                VersionInfo(
                    key=obj.object_name,
                    version_id=obj.version_id or "",
                    is_latest=obj.is_latest,
                    size=obj.size or 0,
                    last_modified=str(obj.last_modified),
                    etag=obj.etag or "",
                    content_type=obj.content_type,
                    is_delete_marker=obj.is_delete_marker,
                )
                for obj in objects
                if include_delete_markers or not obj.is_delete_marker
            ]
        except S3Error as e:
            logger.error("Ошибка MinIO при получении списка версий: %s", e)
            raise

    def get_version(self, key: str, version_id: str) -> bytes:
        #Скачивает конкретную версию объекта
        response = None
        try:
            response = self._client.get_object(self.bucket, key, version_id=version_id)
            return response.read()
        except S3Error as e:
            logger.error("Ошибка MinIO при скачивании версии '%s' (v=%s): %s", key, version_id, e)
            raise
        finally:
            if response:
                response.close()
                response.release_conn()

    def get_version_info(self, key: str, version_id: str) -> ObjectInfo:
        #Возвращает метаданные конкретной версии
        try:
            meta = self._client.stat_object(self.bucket, key, version_id=version_id)
            return ObjectInfo(
                key=key,
                size=meta.size,
                last_modified=str(meta.last_modified),
                etag=meta.etag,
                content_type=meta.content_type,
                version_id=version_id,
            )
        except S3Error as e:
            logger.error("Ошибка MinIO при получении метаданных версии '%s' (v=%s): %s", key, version_id, e)
            raise

    def exists_version(self, key: str, version_id: str) -> bool:
        #Проверяет существование конкретной версии
        try:
            self._client.stat_object(self.bucket, key, version_id=version_id)
            return True
        except S3Error as e:
            if e.code in ("NoSuchKey", "NoSuchVersion"):
                return False
            raise

    def delete_version(self, key: str, version_id: str) -> None:
        #Физически удаляет конкретную версию (не создаёт delete marker)
        try:
            self._client.remove_object(self.bucket, key, version_id=version_id)
            logger.debug("Удалена версия s3://%s/%s (v=%s)", self.bucket, key, version_id)
        except S3Error as e:
            logger.error("Ошибка MinIO при удалении версии '%s' (v=%s): %s", key, version_id, e)
            raise

    def restore_version(self, key: str, version_id: str) -> UploadResult:
        #Восстанавливает указанную версию как последнюю
        #Реализация: copy_object с version_id → создаёт новую версию
        try:
            source = CopySource(self.bucket, key, version_id=version_id)
            result = self._client.copy_object(self.bucket, key, source)
            new_version_id = result.version_id
            logger.info(
                "Восстановлена версия s3://%s/%s (v=%s) → новая v=%s",
                self.bucket, key, version_id, new_version_id,
            )
            return UploadResult(
                key=key,
                bucket=self.bucket,
                etag=result.etag.strip('"'),
                version_id=new_version_id,
            )
        except S3Error as e:
            logger.error("Ошибка MinIO при восстановлении версии '%s' (v=%s): %s", key, version_id, e)
            raise

    def presigned_version_url(
        self,
        key: str,
        version_id: str,
        *,
        expiry: int | None = None,
    ) -> str:
        #Генерирует presigned GET URL для конкретной версии
        try:
            return self._client.presigned_get_object(
                self.bucket, key,
                expires=timedelta(seconds=expiry or self._cfg.presigned_url_expiry),
                version_id=version_id,
            )
        except S3Error as e:
            logger.error(
                "Ошибка MinIO при генерации presigned URL версии '%s' (v=%s): %s",
                key, version_id, e,
            )
            raise

    # ──────────────────────────────────────────
    # Private
    # ──────────────────────────────────────────

    def _make_result(
        self,
        key: str,
        etag: str,
        presigned: bool,
        version_id: str | None = None,
    ) -> UploadResult:
        url = self.presigned_url(key) if presigned else None
        return UploadResult(
            key=key,
            bucket=self.bucket,
            etag=etag.strip('"'),
            url=url,
            version_id=version_id,
        )


# ──────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────

def _guess_mime(path: Path) -> str | None:
    mime, _ = mimetypes.guess_type(path.name)
    return mime
