from __future__ import annotations

import re
from enum import Enum
from typing import Iterable, Self

from pydantic import BaseModel, Field


class _NextIDModel(BaseModel):
    @classmethod
    def nextID(cls, instances: Iterable[Self]) -> int:
        """Return the next numeric ID for instances of this model.

        Returns 1 when there are no instances with a numeric ID; otherwise
        returns max(id) + 1. IDs such as "REQ-001" are supported by using
        their trailing numeric part.
        """
        ids: list[int] = []

        for instance in instances:
            value = getattr(instance, "id", None)
            if value is None:
                continue

            match = re.search(r"(\d+)$", str(value))
            if match:
                ids.append(int(match.group(1)))

        return max(ids, default=0) + 1


class RequirementType(str, Enum):
    FUNCTIONAL = "functional"
    QUALITY = "quality"
    CONSTRAINT = "constraint"
    USER = "user"
    SYSTEM = "system"


class RequirementStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    VALIDATED = "validated"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    RETIRED = "retired"


class UseCaseFlow(_NextIDModel):
    id: str = ""
    name: str
    steps: list[str] = Field(default_factory=list)


class UseCase(_NextIDModel):
    id: str
    name: str
    goal: str = ""
    description: str = ""
    actors: list[str] = Field(default_factory=list)
    trigger: str = ""
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    main_success_scenario: list[str] = Field(default_factory=list)
    alternative_flows: list[UseCaseFlow] = Field(default_factory=list)
    exception_flows: list[UseCaseFlow] = Field(default_factory=list)
    includes: list[str] = Field(default_factory=list)
    extends: list[str] = Field(default_factory=list)
    generalizes: list[str] = Field(default_factory=list)
    related_requirements: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    priority: str = "medium"
    status: RequirementStatus = RequirementStatus.DRAFT


class Requirement(_NextIDModel):
    id: str
    title: str
    statement: str
    type: RequirementType
    status: RequirementStatus = RequirementStatus.DRAFT
    priority: str = "medium"
    source: str = ""
    rationale: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    related_use_cases: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    conflicts_with: list[str] = Field(default_factory=list)


class Actor(_NextIDModel):
    id: str
    name: str
    description: str = ""
    kind: str = "person"
    parent_actor: str | None = None


class TraceLink(_NextIDModel):
    id: str = ""
    source_id: str
    target_id: str
    relation: str
