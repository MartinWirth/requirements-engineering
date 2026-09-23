from enum import Enum
from typing import Any, get_args, get_origin, get_type_hints

from pydantic import BaseModel

from .models import Actor, Requirement, TraceLink, UseCase


MODEL_DEFINITIONS = {
    "Requirements": (Requirement, "/requirements"),
    "Use Cases": (UseCase, "/use-cases"),
    "Actors": (Actor, "/actors"),
    "Trace Links": (TraceLink, "/traceability"),
}


def _field_schema(annotation: Any) -> dict[str, Any]:
    origin = get_origin(annotation)
    args = get_args(annotation)

    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return {
            "kind": "enum",
            "values": [member.value for member in annotation],
        }

    if origin is list:
        item_type = args[0] if args else Any
        return {
            "kind": "json",
            "data_type": "list",
            "item_type": getattr(item_type, "__name__", str(item_type)),
        }

    if origin is dict:
        return {"kind": "json", "data_type": "dict"}

    if origin is type(None):
        return {"kind": "text", "data_type": "null"}

    if origin is not None and type(None) in args:
        non_none = next((arg for arg in args if arg is not type(None)), Any)
        result = _field_schema(non_none)
        result["optional"] = True
        return result

    if annotation is bool:
        return {"kind": "text", "data_type": "bool"}
    if annotation is int:
        return {"kind": "text", "data_type": "int"}
    if annotation is float:
        return {"kind": "text", "data_type": "float"}
    if annotation is str:
        return {"kind": "text", "data_type": "str"}

    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return {"kind": "json", "data_type": annotation.__name__}

    return {"kind": "text", "data_type": "str"}


def model_schema() -> dict[str, Any]:
    result: dict[str, Any] = {}

    for display_name, (model, endpoint) in MODEL_DEFINITIONS.items():
        hints = get_type_hints(model)
        fields = []

        for name, field in model.model_fields.items():
            schema = _field_schema(hints[name])
            default = field.default
            if isinstance(default, Enum):
                default = default.value

            schema.update({
                "name": name,
                "required": field.is_required(),
                "default": None if default is None else default,
            })
            fields.append(schema)

        result[display_name] = {
            "endpoint": endpoint,
            "fields": fields,
        }

    return result
