from enum import Enum
from typing import Any, get_args, get_origin, get_type_hints

from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from .models import Actor, Requirement, TestCase, TraceLink, UseCase, UserStory, WorkItem


IREB_GLOSSARY = "https://cpre.ireb.org/en/downloads-and-resources/glossary"
IREB_DOWNLOADS = "https://cpre.ireb.org/en/downloads-and-resources/downloads"
IREB_MODELING = "https://cpre.ireb.org/en/concept/requirements-modeling"

FIELD_HELP: dict[str, tuple[str, str]] = {
    "action": ("Workbench action for editing the element.", IREB_GLOSSARY),
    "id": ("Unique identifier of the model element.", IREB_GLOSSARY),
    "title": ("Short, precise title identifying the requirement or user story.", IREB_GLOSSARY),
    "statement": ("Textual formulation of what is required.", IREB_GLOSSARY),
    "type": ("Requirement classification.", IREB_GLOSSARY),
    "status": ("Lifecycle status: draft, proposed, validated, approved, implemented or retired.", IREB_DOWNLOADS),
    "priority": ("Relative priority for planning and implementation.", IREB_DOWNLOADS),
    "source": ("Origin or source of the requirement.", IREB_DOWNLOADS),
    "rationale": ("Reason for the requirement or decision.", IREB_GLOSSARY),
    "acceptance_criteria": ("Criteria used to verify fulfillment.", IREB_GLOSSARY),\n    "ai_summary": ("Summary returned by the AI development execution.", IREB_DOWNLOADS),\n    "ai_executed_at": ("Timestamp of the latest AI development execution.", IREB_DOWNLOADS),
    "ai_branch": ("Git branch created for the AI implementation.", IREB_DOWNLOADS),
    "ai_commit": ("Git commit created for the AI implementation.", IREB_DOWNLOADS),
    "related_use_cases": ("Use cases related to this element.", IREB_MODELING),
    "related_requirements": ("Requirements related to this element.", IREB_DOWNLOADS),
    "depends_on": ("Elements on which this element depends.", IREB_DOWNLOADS),
    "conflicts_with": ("Elements with a documented conflict.", IREB_DOWNLOADS),
    "name": ("Name of the use case or actor.", IREB_GLOSSARY),
    "goal": ("Goal achieved by the use case.", IREB_GLOSSARY),
    "description": ("Additional description of the element.", IREB_GLOSSARY),
    "actors": ("External actors interacting with the system or use case.", IREB_MODELING),
    "actor": ("Primary actor of the user story.", IREB_MODELING),
    "as_a": ("Role or persona in the user-story formulation.", IREB_GLOSSARY),
    "i_want": ("Desired capability in the user-story formulation.", IREB_GLOSSARY),
    "so_that": ("Expected benefit or value of the user story.", IREB_GLOSSARY),
    "trigger": ("Event that starts the use case.", IREB_MODELING),
    "preconditions": ("Conditions that must hold before the use case starts.", IREB_MODELING),
    "postconditions": ("States or results that apply after the use case.", IREB_MODELING),
    "main_success_scenario": ("Normal successful sequence of use-case steps.", IREB_MODELING),
    "alternative_flows": ("Alternative use-case flows.", IREB_MODELING),
    "exception_flows": ("Exception or error flows.", IREB_MODELING),
    "includes": ("Use cases included by this use case.", IREB_MODELING),
    "extends": ("Use cases extending this use case.", IREB_MODELING),
    "generalizes": ("Use-case generalization relationships.", IREB_MODELING),
    "kind": ("Actor kind, such as person or system.", IREB_MODELING),
    "parent_actor": ("Parent actor in an actor generalization.", IREB_MODELING),
    "source_id": ("Source element of a traceability link.", IREB_DOWNLOADS),
    "target_id": ("Target element of a traceability link.", IREB_DOWNLOADS),
    "relation": ("Semantics of the traceability relationship.", IREB_DOWNLOADS),
    "parent_id": ("Parent Issue or Task for a Subtask.", IREB_DOWNLOADS),
    "requirement_ids": ("Requirements implemented or verified by this element.", IREB_DOWNLOADS),
    "work_item_ids": ("Development work items covered by this test.", IREB_DOWNLOADS),
    "assignee": ("Person responsible for implementation.", IREB_DOWNLOADS),
    "steps": ("Actions performed during the test.", IREB_DOWNLOADS),
    "expected_results": ("Expected result for each test step.", IREB_DOWNLOADS),
    "actual_result": ("Observed result from the latest test execution.", IREB_DOWNLOADS),
    "executed_at": ("Timestamp of the latest test execution.", IREB_DOWNLOADS),
    "execution_command": ("Command arguments executed for automated verification.", IREB_DOWNLOADS),
}

MODEL_DEFINITIONS = {
    "Requirements": (Requirement, "/api/requirements"),
    "User Stories": (UserStory, "/api/user-stories"),
    "Use Cases": (UseCase, "/api/use-cases"),
    "Actors": (Actor, "/api/actors"),
    "Traceability": (TraceLink, "/api/traceability"),
    "Work Items": (WorkItem, "/api/work-items"),
    "Test Cases": (TestCase, "/api/test-cases"),
}


def _field_schema(annotation: Any) -> dict[str, Any]:
    origin = get_origin(annotation)
    args = get_args(annotation)

    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return {"kind": "enum", "values": [member.value for member in annotation]}

    if origin is list:
        item_type = args[0] if args else Any
        return {"kind": "json", "data_type": "list", "item_type": getattr(item_type, "__name__", str(item_type))}

    if origin is dict:
        return {"kind": "json", "data_type": "dict"}

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
            summary, documentation_url = FIELD_HELP.get(name, ("Attribute of the requirements model.", IREB_GLOSSARY))
            schema.update({
                "name": name,
                "required": field.is_required(),
                "default": default,
                "summary": summary,
                "documentation_url": documentation_url,
            })
            fields.append(schema)
        result[display_name] = {"endpoint": endpoint, "fields": fields}
    return result
