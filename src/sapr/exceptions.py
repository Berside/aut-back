# Базовый класс для ошибок приложения
class AppError(Exception):
    http_status = 500
    message = 'Внутренняя ошибка сервера'
    error_code = 'INTERNAL_ERROR'

    def __init__(self, message=None, error_code=None, http_status=None):
        self.message = message or self.message
        self.error_code = error_code or self.error_code
        self.http_status = http_status or self.http_status
        super().__init__(self.message)


# ОШИБКИ ПРОЕКТОВ
class ProjectNotFoundError(AppError):
    http_status = 404
    message = 'Проект не найден'
    error_code = 'PROJECT_NOT_FOUND'


class ProjectAlreadyExistsError(AppError):
    http_status = 409
    message = 'Проект с таким именем уже существует'
    error_code = 'PROJECT_ALREADY_EXISTS'


class ProjectDeletionError(AppError):
    http_status = 500
    message = 'Ошибка при удалении проекта'
    error_code = 'PROJECT_DELETION_ERROR'


# ОШИБКИ 3D-МОДЕЛЕЙ
class ModelNotFoundError(AppError):
    http_status = 404
    message = '3D модель не найдена'
    error_code = 'MODEL_NOT_FOUND'


class ModelUploadError(AppError):
    http_status = 400
    message = 'Ошибка загрузки файла модели'
    error_code = 'MODEL_UPLOAD_ERROR'


class PhysicalFileNotFoundError(AppError):
    http_status = 404
    message = 'Файл модели не найден на диске'
    error_code = 'PHYSICAL_FILE_NOT_FOUND'


# ОШИБКИ ДЕТАЛЕЙ
class PartNotFoundError(AppError):
    http_status = 404
    message = 'Деталь не найдена'
    error_code = 'PART_NOT_FOUND'


class PartNumberExistsError(AppError):
    http_status = 409
    message = 'Деталь с таким артикулом уже существует'
    error_code = 'PART_NUMBER_EXISTS'


class PartDeletionError(AppError):
    http_status = 500
    message = 'Ошибка при удалении детали'
    error_code = 'PART_DELETION_ERROR'


class InsufficientStockError(AppError):
    http_status = 400
    message = 'Недостаточно деталей на складе'
    error_code = 'INSUFFICIENT_STOCK'

# ОШИБКИ СБОРКИ
class AssemblyItemNotFoundError(AppError):
    http_status = 404
    message = 'Элемент сборки не найден'
    error_code = 'ASSEMBLY_ITEM_NOT_FOUND'


class CyclicDependencyError(AppError):
    http_status = 400
    message = 'Обнаружена циклическая зависимость в дереве сборки'
    error_code = 'CYCLIC_DEPENDENCY'


class InvalidParentError(AppError):
    http_status = 400
    message = 'Указан невалидный родительский элемент'
    error_code = 'INVALID_PARENT'


class CrossProjectReferenceError(AppError):
    http_status = 400
    message = 'Нельзя ссылаться на элементы из другого проекта'
    error_code = 'CROSS_PROJECT_REFERENCE'


# ОШИБКИ КАТЕГОРИЙ И ТИПОВ
class CategoryNotFoundError(AppError):
    http_status = 404
    message = 'Категория не найдена'
    error_code = 'CATEGORY_NOT_FOUND'


class CategoryCycleError(AppError):
    http_status = 400
    message = 'Категория не может быть родителем самой себя'
    error_code = 'CATEGORY_CYCLE'


class CategoryHasChildrenError(AppError):
    http_status = 409
    message = 'Нельзя удалить категорию с дочерними элементами'
    error_code = 'CATEGORY_HAS_CHILDREN'


class TypeNotFoundError(AppError):
    http_status = 404
    message = 'Тип детали не найден'
    error_code = 'TYPE_NOT_FOUND'


# ОШИБКИ ФАЙЛОВ
class FileSaveError(AppError):
    http_status = 500
    message = 'Не удалось сохранить файл на диск'
    error_code = 'FILE_SAVE_ERROR'


class PhysicalFileNotFoundError(AppError):
    http_status = 404
    message = 'Файл не найден на диске'
    error_code = 'PHYSICAL_FILE_NOT_FOUND'


# ОШИБКИ ШАГОВ АНИМАЦИИ
class AnimationStepNotFoundError(AppError):
    http_status = 404
    message = 'Шаг анимации не найден'
    error_code = 'ANIMATION_STEP_NOT_FOUND'


# ОШИБКИ СВЯЗЕЙ ПРОЕКТ-ДЕТАЛЬ
class ProjectPartNotFoundError(AppError):
    http_status = 404
    message = 'Связь проект-деталь не найдена'
    error_code = 'PROJECT_PART_NOT_FOUND'


class ProjectPartAlreadyExistsError(AppError):
    http_status = 409
    message = 'Деталь уже добавлена в проект'
    error_code = 'PROJECT_PART_ALREADY_EXISTS'


# ОШИБКИ ДЕРЕВЬЕВ
class TreeItemNotFoundError(AppError):
    http_status = 404
    message = 'Элемент дерева не найден'
    error_code = 'TREE_PART_NOT_FOUND'


class TreeItemHasChildrenError(AppError):
    http_status = 409
    message = 'Нельзя удалить. Есть дочерние элементы'
    error_code = 'TREE_ITEM_HAS_CHILDREN'


# ОШИБКИ ИСТОРИИ
class InvalidHistoryFilterError(AppError):
    http_status = 400
    message = 'Неккоректные параметры фильтрации истории'
    error_code = 'INVALID_HISTORY_FILTER'


# ОШИБКИ ИНСТРУМЕНТОВ
class ItemNotFoundError(AppError):
    http_status = 404
    message = 'Инструмент не найден'
    error_code = 'ITEM_NOT_FOUND'


class ItemAlredyExists(AppError):
    http_status = 409
    message = 'Инструмент с таким наименованием уже существует'
    error_code = 'ITEM_ALREADY_EXISTS'


class ItemDeletionError(AppError):
    http_status = 500
    message = 'Ошибка при удалении инструмента'
    error_code = 'ITEM_DELETION_ERROR'


# ОШИБКИ СТРУКТУРЫ МОДЕЛИ
class StructureNodeNotFoundError(AppError):
    http_status = 404
    message = 'Узел структуры не найден'
    error_code = 'STRUCTURE_NODE_NOT_FOUND'


class StructureNodeAlreadyExistsError(AppError):
    http_status = 409
    message = 'Узел с таким кодом уже существует'
    error_code = 'STRUCTURE_NODE_ALREADY_EXISTS'


class StructureNodeDeletionError(AppError):
    http_status = 500
    message = 'Ошибка при удалении узла структуры'
    error_code = 'STRUCTURE_NODE_DELETION_ERROR'


class InvalidStructureNodeError(AppError):
    http_status = 400
    message = 'Некорректные данные узла структуры'
    error_code = 'INVALID_STRUCTURE_NODE'


# ОШИБКИ ИНСТРУКЦИЙ 
class InstructionNotFoundError(AppError):
    http_status=404
    message='Инструкция не найдена'
    error_code='INSTRUCTION_NOT_FOUND_ERROR'


class InstructionValidationError(AppError):
    http_status = 400
    message = 'Невалидный TipTap JSON'
    error_code = 'INSTRUCTION_VALIDATION_ERROR'


class MissingFileError(AppError):
    http_status = 400
    message = 'Файл не выбран'
    error_code = 'MISSING_FILE'


class InvalidFileFormatError(AppError):
    http_status = 400
    message = 'Разрешены только файлы с расширением .tap'
    error_code = 'INVALID_FILE_FORMAT'


class InvalidAnimationStepError(AppError):
    http_status = 400
    message = 'Шаг анимации не принадлежит проекту'
    error_code = 'INVALID_ANIMATION_STEP'