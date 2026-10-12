from marshmallow import Schema, fields, validate, validates, ValidationError, post_load, EXCLUDE
from typing import Optional, List, Dict, Any


# PROJECTS
class ProjectCreateRequestDTO(Schema):
    name = fields.String(required=True, validate=[validate.Length(min=1, max=255)])
    description = fields.String(load_default="")

    class Meta:
        unknown = EXCLUDE


class ProjectResponseDTO(Schema):
    id = fields.Integer()
    name = fields.String()
    description = fields.String()
    created_at = fields.DateTime(allow_none=True)
    instructions = fields.Nested(lambda: InstructionListItemDTO(), many=True, load_default=[])


    class Meta:
        unknown = EXCLUDE


# MODELS
class ModelCreateRequestDTO(Schema):
    name = fields.String(required=True, validate=[validate.Length(min=1, max=255)])
    technical_name = fields.String(allow_none=True, load_default=None)
    is_primary = fields.Boolean(load_default=False)

    class Meta:
        unknown = EXCLUDE


class ModelUpdateRequestDTO(Schema):
    name = fields.String(allow_none=True, load_default=None, validate=[validate.Length(min=1, max=255)])
    is_primary = fields.Boolean(allow_none=True, load_default=None)

    class Meta:
        unknown = EXCLUDE


class ModelResponseDTO(Schema):
    id = fields.Integer()
    name = fields.String()
    technical_name = fields.String(allow_none=True)
    is_primary = fields.Boolean()
    created_at = fields.DateTime(allow_none=True)

    class Meta:
        unknown = EXCLUDE


# ANIMATION_STEPS
class AnimationStepCreateRequestDTO(Schema):
    project_id = fields.Integer(required=True, validate=validate.Range(min=1))
    name = fields.String(required=True, validate=[validate.Length(min=1, max=255)])
    model_id = fields.Integer(allow_none=True, load_default=None)
    duration = fields.Float(load_default=1.0, validate=validate.Range(min=0))
    order = fields.Integer(load_default=0, validate=validate.Range(min=0))
    is_active = fields.Boolean(load_default=True)
    camera_position = fields.Dict(keys=fields.String(), values=fields.Float(), load_default={"x": 0.0, "y": 0.0, "z": 0.0})
    camera_target = fields.Dict(keys=fields.String(), values=fields.Float(), load_default={"x": 0.0, "y": 0.0, "z": 0.0})
    animation_ids = fields.List(fields.Integer(), load_default=[])

    class Meta:
        unknown = EXCLUDE


class AnimationStepUpdateRequestDTO(Schema):
    name = fields.String(allow_none=True, load_default=None, validate=[validate.Length(min=1, max=255)])
    model_id = fields.Integer(allow_none=True, load_default=None)
    duration = fields.Float(allow_none=True, load_default=None, validate=validate.Range(min=0))
    order = fields.Integer(allow_none=True, load_default=None, validate=validate.Range(min=0))
    is_active = fields.Boolean(allow_none=True, load_default=None)
    camera_position = fields.Dict(keys=fields.String(), values=fields.Float(), allow_none=True, load_default=None)
    camera_target = fields.Dict(keys=fields.String(), values=fields.Float(), allow_none=True, load_default=None)
    animation_ids = fields.List(fields.Integer(), allow_none=True, load_default=None)

    class Meta:
        unknown = EXCLUDE


class AnimationStepResponseDTO(Schema):
    id = fields.Integer()
    project_id = fields.Integer()
    model_id = fields.Integer(allow_none=True)
    name = fields.String()
    duration = fields.Float()
    order = fields.Integer()
    is_active = fields.Boolean()
    camera_position = fields.Dict(keys=fields.String(), values=fields.Float())
    camera_target = fields.Dict(keys=fields.String(), values=fields.Float())
    animation_ids = fields.List(fields.Integer())
    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)

    class Meta:
        unknown = EXCLUDE


# CATEGORIES
class CategoryCreateRequestDTO(Schema):
    name = fields.String(required=True, validate=[validate.Length(min=1, max=255)])
    parent_id = fields.Integer(allow_none=True, load_default=None)
    sort_order = fields.Integer(load_default=0, validate=validate.Range(min=0))

    class Meta:
        unknown = EXCLUDE


class CategoryUpdateRequestDTO(Schema):
    name = fields.String(allow_none=True, load_default=None, validate=[validate.Length(min=1, max=255)])
    parent_id = fields.Integer(allow_none=True, load_default=None)
    sort_order = fields.Integer(allow_none=True, load_default=None, validate=validate.Range(min=0))

    class Meta:
        unknown = EXCLUDE


class CategoryResponseDTO(Schema):
    id = fields.Integer()
    name = fields.String()
    parent_id = fields.Integer(allow_none=True)
    sort_order = fields.Integer()
    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)
    children = fields.Nested(lambda: CategoryResponseDTO(), many=True, load_default=[])

    class Meta:
        unknown = EXCLUDE


# TYPES
class TypeCreateRequestDTO(Schema):
    name = fields.String(required=True, validate=[validate.Length(min=1, max=255)])
    category_id = fields.Integer(allow_none=True, load_default=None)

    class Meta:
        unknown = EXCLUDE


class TypeUpdateRequestDTO(Schema):
    name = fields.String(allow_none=True, load_default=None, validate=[validate.Length(min=1, max=255)])
    category_id = fields.Integer(allow_none=True, load_default=None)

    class Meta:
        unknown = EXCLUDE


class TypeResponseDTO(Schema):
    id = fields.Integer()
    name = fields.String()
    category_id = fields.Integer(allow_none=True)
    category_name = fields.String(allow_none=True)
    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)

    class Meta:
        unknown = EXCLUDE


# PARTS 
class PartCreateRequestDTO(Schema):
    name = fields.String(required=True, validate=[validate.Length(min=1, max=255)])
    part_number = fields.String(allow_none=True, load_default=None, validate=validate.Length(max=100))
    description = fields.String(allow_none=True, load_default=None)
    category_id = fields.Integer(allow_none=True, load_default=None)
    type_id = fields.Integer(allow_none=True, load_default=None)
    parameters = fields.Dict(keys=fields.String(), values=fields.Raw(), load_default={})
    model_id = fields.Integer(allow_none=True, load_default=None)
    technical_name = fields.String(allow_none=True, load_default=None)
    preview_image = fields.String(allow_none=True, load_default=None)
    unit = fields.String(load_default="шт", validate=validate.Length(max=20))
    is_standard = fields.Boolean(load_default=True)
    is_active = fields.Boolean(load_default=True)
    created_by = fields.Integer(allow_none=True, load_default=None)
    item_id = fields.Integer(allow_none=True, load_default=None)

    project_id = fields.Integer(allow_none=True, load_default=None)
    quantity = fields.Integer(allow_none=True, load_default=1, validate=validate.Range(min=1))
    custom_parameters = fields.Dict(keys=fields.String(), values=fields.Raw(), allow_none=True, load_default={})


    class Meta:
        unknown = EXCLUDE


class PartUpdateRequestDTO(Schema):
    name = fields.String(allow_none=True, load_default=None, validate=[validate.Length(min=1, max=255)])
    part_number = fields.String(allow_none=True, load_default=None, validate=validate.Length(max=100))
    description = fields.String(allow_none=True, load_default=None)
    category_id = fields.Integer(allow_none=True, load_default=None)
    type_id = fields.Integer(allow_none=True, load_default=None)
    parameters = fields.Dict(keys=fields.String(), values=fields.Raw(), allow_none=True, load_default=None)
    model_id = fields.Integer(allow_none=True, load_default=None)
    technical_name = fields.String(allow_none=True, load_default=None)
    preview_image = fields.String(allow_none=True, load_default=None)
    unit = fields.String(allow_none=True, load_default=None, validate=validate.Length(max=20))
    is_standard = fields.Boolean(allow_none=True, load_default=None)
    is_active = fields.Boolean(allow_none=True, load_default=None)
    item_id = fields.Integer(allow_none=True, load_default=None)

    class Meta:
        unknown = EXCLUDE


class PartResponseDTO(Schema):
    id = fields.Integer()
    name = fields.String()
    part_number = fields.String(allow_none=True)
    description = fields.String(allow_none=True)
    category_id = fields.Integer(allow_none=True)
    category_name = fields.String(allow_none=True)
    type_id = fields.Integer(allow_none=True)
    type_name = fields.String(allow_none=True)
    parameters = fields.Dict(keys=fields.String(), values=fields.Raw(), load_default={})
    model_id = fields.Integer(allow_none=True)
    technical_name = fields.String(allow_none=True)
    preview_image = fields.String(allow_none=True)
    unit = fields.String(load_default="шт")
    is_standard = fields.Boolean(load_default=True)
    is_active = fields.Boolean(load_default=True)
    created_by = fields.Integer(allow_none=True)
    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)
    item_id = fields.Integer(allow_none=True)

    class Meta:
        unknown = EXCLUDE


# PROJECT PARTS
class ProjectPartCreateRequestDTO(Schema):
    project_id = fields.Integer(required=True, validate=validate.Range(min=1))
    part_id = fields.Integer(required=True, validate=validate.Range(min=1))
    quantity = fields.Integer(load_default=1, validate=validate.Range(min=1))
    custom_parameters = fields.Dict(keys=fields.String(), values=fields.Raw(), load_default={})
    added_by = fields.Integer(allow_none=True, load_default=None)

    class Meta:
        unknown = EXCLUDE


class ProjectPartUpdateRequestDTO(Schema):
    quantity = fields.Integer(allow_none=True, load_default=None, validate=validate.Range(min=1))
    custom_parameters = fields.Dict(keys=fields.String(), values=fields.Raw(), allow_none=True, load_default=None)

    class Meta:
        unknown = EXCLUDE


class ProjectPartResponseDTO(Schema):
    id = fields.Integer()
    project_id = fields.Integer()
    part_id = fields.Integer()
    quantity = fields.Integer()
    custom_parameters = fields.Dict(keys=fields.String(), values=fields.Raw(), load_default={})
    added_at = fields.DateTime(allow_none=True)
    added_by = fields.Integer(allow_none=True)

    class Meta:
        unknown = EXCLUDE


class ProjectPartWithStockCheckResponseDTO(Schema):
    success = fields.Boolean()
    message = fields.String()
    project_part = fields.Nested(ProjectPartResponseDTO, allow_none=True)
    remaining_stock = fields.Integer(allow_none=True)
    warning = fields.String(allow_none=True)

    class Meta:
        unknown = EXCLUDE


# ASSEMBLY ITEMS
class AssemblyItemCreateRequestDTO(Schema):
    project_id = fields.Integer(required=True, validate=validate.Range(min=1))
    name = fields.String(required=True)
    model_id = fields.Integer(allow_none=True, load_default=None)
    part_id = fields.Integer(allow_none=True, load_default=None)
    parent_id = fields.Integer(allow_none=True, load_default=None)
    order = fields.Integer(load_default=0, validate=validate.Range(min=0))

    @validates('name')
    def validate_name(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError('Название не может состоять только из пробелов')

    @post_load
    def strip_name(self, data, **kwargs):
        if 'name' in data and isinstance(data['name'], str):
            data['name'] = data['name'].strip()
        return data

    class Meta:
        unknown = EXCLUDE


class AssemblyItemUpdateRequestDTO(Schema):
    name = fields.String(allow_none=True, load_default=None)
    model_id = fields.Integer(allow_none=True, load_default=None)
    part_id = fields.Integer(allow_none=True, load_default=None)
    parent_id = fields.Integer(allow_none=True, load_default=None)
    order = fields.Integer(allow_none=True, load_default=None, validate=validate.Range(min=0))

    @validates('name')
    def validate_name(self, value, **kwargs):
        if value is not None and not value.strip():
            raise ValidationError('Название не может состоять только из пробелов')

    @post_load
    def strip_name(self, data, **kwargs):
        if 'name' in data and isinstance(data['name'], str):
            data['name'] = data['name'].strip()
        return data

    class Meta:
        unknown = EXCLUDE


class AssemblyItemResponseDTO(Schema):
    id = fields.Integer()
    project_id = fields.Integer()
    name = fields.String()
    model_id = fields.Integer(allow_none=True)
    part_id = fields.Integer(allow_none=True)
    parent_id = fields.Integer(allow_none=True)
    order = fields.Integer()
    created_at = fields.DateTime(allow_none=True)

    class Meta:
        unknown = EXCLUDE


class AssemblyPartLinkResponseDTO(Schema):
    id = fields.Integer()
    part_id = fields.Integer()
    quantity = fields.Integer()
    position = fields.Dict(allow_none=True)
    rotation = fields.Dict(allow_none=True)
    created_at = fields.DateTime(format="%Y-%m-%dT%H:%M:%S")

    class Meta:
        unknown = EXCLUDE


class AssemblyItemLinkRequestDTO(Schema):
    item_id = fields.Integer(required=True, validate=validate.Range(min=1))

    class Meta:
        unknown = EXCLUDE


class AssemblyItemLinkResponseDTO(Schema):
    id = fields.Integer()
    name = fields.String()
    item_id = fields.Integer(allow_none=True)
    item = fields.Nested('ItemResponseDTO', allow_none=True) 


    class Meta:
        unknown = EXCLUDE


class AssemblyTreeItemDTO(Schema):
    id = fields.Integer()
    name = fields.String()
    model_id = fields.Integer(allow_none=True)
    part_id = fields.Integer(allow_none=True)
    item_id = fields.Integer(allow_none=True) 
    order = fields.Integer()
    item = fields.Nested('ItemResponseDTO', allow_none=True)
    children = fields.Nested(lambda: AssemblyTreeItemDTO(), many=True, load_default=[])

    class Meta:
        unknown = EXCLUDE


# INSTRUCTIONS
class InstructionCreateRequestDTO(Schema):
    dmc = fields.String(required=True, validate=[validate.Length(min=1, max=64)])
    project_id = fields.Integer(required=True)
    title = fields.String(required=True, validate=[validate.Length(min=1, max=255)])
    content = fields.Raw(required=True)
    part_id = fields.Integer(allow_none=True, load_default=None)
    animation_step_id = fields.Integer(allow_none=True, load_default=None)

    class Meta:
        unknown = EXCLUDE

class InstructionUpdateRequestDTO(Schema):
    dmc = fields.String(required=True, validate=[validate.Length(min=1, max=64)])
    project_id = fields.Integer(required=True)
    title = fields.String(required=True, validate=[validate.Length(min=1, max=255)])
    content = fields.Raw(required=True)
    part_id = fields.Integer(allow_none=True, load_default=None)
    animation_step_id = fields.Integer(allow_none=True, load_default=None)

    class Meta:
        unknown = EXCLUDE



class InstructionListItemDTO(Schema):
    dmc = fields.String()
    title = fields.String()

    class Meta:
        unknown = EXCLUDE


class InstructionResponseDTO(Schema):
    id = fields.Integer()
    dmc = fields.String()
    project_id = fields.Integer()
    title = fields.String()
    content = fields.Dict(keys=fields.String(), values=fields.Raw(), allow_none=True)
    part_id = fields.Integer(allow_none=True)
    animation_step_id = fields.Integer(allow_none=True)
    file_path = fields.String(allow_none=True)
    is_current = fields.Boolean()
    created_at = fields.DateTime(allow_none=True)

    class Meta:
        unknown = EXCLUDE


# SAPR TREE
class SaprTreeNodeDTO(Schema):
    id = fields.Integer()
    name = fields.String()
    item_type = fields.String()
    parent_link = fields.Integer(allow_none=True)
    project_id = fields.Integer()
    instruction_id = fields.Integer(allow_none=True)
    model_id = fields.Integer(allow_none=True)
    position = fields.Integer()
    has_children = fields.Boolean(load_default=False)
    children = fields.Nested(lambda: SaprTreeNodeDTO(), many=True, load_default=[])

    class Meta:
        unknown = EXCLUDE


class SaprTreeCreateRequestDTO(Schema):
    name = fields.String(required=True, validate=[validate.Length(min=1, max=255)])
    item_type = fields.String(required=True, validate=validate.OneOf(['folder', 'file', 'model']))
    parent_link = fields.Integer(allow_none=True, load_default=None)
    project_id = fields.Integer(required=True, validate=validate.Range(min=1))
    instruction_id = fields.Integer(allow_none=True, load_default=None)
    model_id = fields.Integer(allow_none=True, load_default=None)
    position = fields.Integer(allow_none=True, load_default=None)

    class Meta:
        unknown = EXCLUDE


class SaprTreeUpdateRequestDTO(Schema):
    name = fields.String(allow_none=True, load_default=None, validate=[validate.Length(min=1, max=255)])
    position = fields.Integer(allow_none=True, load_default=None)

    class Meta:
        unknown = EXCLUDE


# HISTORY
class HistoryResponseDTO(Schema):
    id = fields.Integer()
    user_id = fields.Integer(allow_none=True)
    endpoint = fields.String()
    method = fields.String()
    timestamp = fields.DateTime(allow_none=True)

    class Meta:
        unknown = EXCLUDE


# ITEM
class ItemCreateRequestDTO(Schema):
    article = fields.String(required=True, validate=[validate.Length(min=1, max=100)])
    name = fields.String(required=True, validate=[validate.Length(min=1, max=255)])
    standard = fields.String(allow_none=True, load_default=None)
    unit = fields.String(load_default='шт', validate=[validate.Length(min=1, max=20)])
    description = fields.String(allow_none=True, load_default=None)
    note = fields.String(allow_none=True, load_default=None)
    photo_path = fields.String(allow_none=True, load_default=None)
    stock_quantity = fields.Integer(load_default=0, validate=validate.Range(min=0))

    class Meta:
        unknown = EXCLUDE


class ItemUpdateRequestDTO(Schema):
    article = fields.String(allow_none=True, load_default=None, validate=[validate.Length(min=1, max=100)])
    name = fields.String(allow_none=True, load_default=None, validate=[validate.Length(min=1, max=255)])
    standard = fields.String(allow_none=True, load_default=None)
    unit = fields.String(load_default='шт', validate=[validate.Length(min=1, max=20)])
    description = fields.String(allow_none=True, load_default=None)
    note = fields.String(allow_none=True, load_default=None)
    photo_path = fields.String(allow_none=True, load_default=None)
    stock_quantity = fields.Integer(load_default=0, validate=validate.Range(min=0))

    class Meta:
        unknown = EXCLUDE


class ItemResponseDTO(Schema):
    id = fields.Integer()
    article = fields.String()
    name = fields.String()
    standard = fields.String(allow_none=True)
    unit = fields.String()
    description = fields.String(allow_none=True)
    note = fields.String(allow_none=True)
    photo_path = fields.String(allow_none=True)
    stock_quantity = fields.Integer()
    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)

    class Meta:
        unknown = EXCLUDE


class ItemSearchResponseDTO(Schema):
    id = fields.Integer()
    article = fields.String()
    name = fields.String()
    standard = fields.String(allow_none=True)
    unit = fields.String()
    stock_quantity = fields.Integer()
    is_linked = fields.Boolean(load_default=False)

    class Meta:
        unknown = EXCLUDE

# BOM
class BomTreeItemDTO(Schema):
    id = fields.Integer()
    article = fields.String()
    name = fields.String()
    quantity = fields.Float(allow_none=True)
    children = fields.Nested(lambda: BomTreeItemDTO(), many=True, load_default=[])

    class Meta:
        unknown = EXCLUDE


class RepairToolItemDTO(Schema):
    tool_id = fields.Integer()
    article = fields.String()
    name = fields.String()
    quantity = fields.Float()
    stock_quantity = fields.Integer()

    class Meta:
        unknown = EXCLUDE
        


# MODEL STRUCTURE NODE
class ModelStructureNodeCreateRequestDTO(Schema):
    name = fields.String(required=True, validate=[validate.Length(min=1, max=255)])
    description = fields.String(allow_none=True, load_default=None)
    code = fields.String(required=True, validate=[validate.Length(min=1, max=100)])
    parent_id = fields.String(allow_none=True, load_default=None)  
    model_id = fields.Integer(allow_none=True, load_default=None)
    part_id = fields.Integer(allow_none=True, load_default=None)
    position = fields.Integer(load_default=0, validate=validate.Range(min=0))

    class Meta:
        unknown = EXCLUDE


class ModelStructureNodeUpdateRequestDTO(Schema):
    name = fields.String(allow_none=True, load_default=None, validate=[validate.Length(min=1, max=255)])
    description = fields.String(allow_none=True, load_default=None)
    code = fields.String(allow_none=True, load_default=None, validate=[validate.Length(min=1, max=100)])
    parent_id = fields.String(allow_none=True, load_default=None)  
    model_id = fields.Integer(allow_none=True, load_default=None)
    part_id = fields.Integer(allow_none=True, load_default=None)
    position = fields.Integer(allow_none=True, load_default=None, validate=validate.Range(min=0))

    class Meta:
        unknown = EXCLUDE


class ModelStructureNodeResponseDTO(Schema):
    id = fields.String() 
    name = fields.String()
    description = fields.String(allow_none=True)
    code = fields.String()
    parent_id = fields.String(allow_none=True)  
    model_id = fields.Integer(allow_none=True)
    part_id = fields.Integer(allow_none=True)
    position = fields.Integer()
    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)

    class Meta:
        unknown = EXCLUDE


class ModelStructureNodeTreeDTO(Schema):
    id = fields.String()  
    name = fields.String()
    description = fields.String(allow_none=True)
    code = fields.String()
    parent_id = fields.String(allow_none=True)  
    model_id = fields.Integer(allow_none=True)
    part_id = fields.Integer(allow_none=True)
    position = fields.Integer()
    has_children = fields.Boolean(load_default=False)
    children = fields.Nested(lambda: ModelStructureNodeTreeDTO(), many=True, load_default=[])

    class Meta:
        unknown = EXCLUDE