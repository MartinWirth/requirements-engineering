from enum import Enum
from typing import Any, get_args, get_origin, get_type_hints

from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from .models import Actor, Requirement, TraceLink, UseCase


IREB_GLOSSARY = "https://cpre.ireb.org/en/downloads-and-resources/glossary"
IREB_DOWNLOADS = "https://cpre.ireb.org/en/downloads-and-resources/downloads"
IREB_MODELING = "https://cpre.ireb.org/en/concept/requirements-modeling"

FIELD_HELP: dict[str, tuple[str, str]] = {
    "id": ("Eindeutige Kennung des Elements innerhalb des Modells.", IREB_GLOSSARY),
    "title": ("Kurzer, prägnanter Titel zur Identifikation der Anforderung.", IREB_GLOSSARY),
    "statement": ("Textuelle Formulierung dessen, was gefordert wird.", IREB_GLOSSARY),
    "type": ("Klassifikation der Anforderung, z. B. funktional oder qualitativ.", IREB_GLOSSARY),
    "status": ("Lebenszyklusstatus der Anforderung bzw. des Elements.", IREB_DOWNLOADS),
    "priority": ("Relative Priorität, mit der eine Anforderung behandelt werden soll.", IREB_DOWNLOADS),
    "source": ("Quelle oder Ursprung der Anforderung.", IREB_DOWNLOADS),
    "rationale": ("Begründung für die Existenz oder Formulierung der Anforderung.", IREB_GLOSSARY),
    "acceptance_criteria": ("Kriterien, anhand derer die Erfüllung der Anforderung überprüft werden kann.", IREB_GLOSSARY),
    "related_use_cases": ("Use Cases, die mit dieser Anforderung in Beziehung stehen.", IREB_MODELING),
    "depends_on": ("Anforderungen, von denen diese Anforderung abhängig ist.", IREB_DOWNLOADS),
    "conflicts_with": ("Anforderungen, zu denen ein dokumentierter Konflikt besteht.", IREB_DOWNLOADS),
    "name": ("Bezeichnung des Elements, z. B. eines Use Cases oder Actors.", IREB_GLOSSARY),
    "goal": ("Das durch den Use Case angestrebte Nutzer- oder Systemziel.", IREB_GLOSSARY),
    "description": ("Zusätzliche Beschreibung des Elements.", IREB_GLOSSARY),
    "actors": ("Externe Akteure, die mit dem System bzw. Use Case interagieren.", IREB_MODELING),
    "trigger": ("Ereignis oder Situation, die den Use Case startet.", IREB_MODELING),
    "preconditions": ("Bedingungen, die vor Beginn des Use Cases erfüllt sein müssen.", IREB_MODELING),
    "postconditions": ("Zustände oder Ergebnisse, die nach dem Use Case gelten.", IREB_MODELING),
    "main_success_scenario": ("Normaler erfolgreicher Ablauf des Use Cases als Folge von Schritten.", IREB_MODELING),
    "alternative_flows": ("Alternative Abläufe eines Use Cases für abweichende Situationen.", IREB_MODELING),
    "exception_flows": ("Abläufe für Ausnahme- oder Fehlersituationen.", IREB_MODELING),
    "includes": ("Verknüpfte Use Cases, deren Verhalten in diesen Use Case eingeschlossen wird.", IREB_MODELING),
    "extends": ("Use Cases, die diesen Use Case unter definierten Bedingungen erweitern.", IREB_MODELING),
    "generalizes": ("Generalisierungsbeziehungen zu allgemeineren oder spezielleren Use Cases.", IREB_MODELING),
    "kind": ("Art des Actors, beispielsweise Person oder System.", IREB_MODELING),
    "parent_actor": ("Übergeordneter Actor in einer Actor-Generalisation.", IREB_MODELING),
    "source_id": ("ID des Ausgangselements einer Traceability-Beziehung.", IREB_DOWNLOADS),
    "target_id": ("ID des Zielelements einer Traceability-Beziehung.", IREB_DOWNLOADS),
    "relation": ("Semantik der Beziehung zwischen zwei verknüpften Elementen.", IREB_DOWNLOADS),
}


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
            default = None if field.default is PydanticUndefined else field.default

            if isinstance(default, Enum):
                default = default.value

            summary, documentation_url = FIELD_HELP.get(
                name,
                ("Attribut des IREB-orientierten Modells.", IREB_GLOSSARY),
            )

            schema.update({
                "name": name,
                "required": field.is_required(),
                "default": default,
                "summary": summary,
                "documentation_url": documentation_url,
            })
            fields.append(schema)

        result[display_name] = {
            "endpoint": endpoint,
            "fields": fields,
        }

    return result
