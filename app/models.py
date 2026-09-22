from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


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


class UseCaseFlow(BaseModel):
    name: str
    steps: list[str] = Field(default_factory=list)


class UseCase(BaseModel):
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


class Requirement(BaseModel):
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


class Actor(BaseModel):
    id: str
    name: str
    description: str = ""
    kind: str = "person"
    parent_actor: str | None = None


class TraceLink(BaseModel):
    source_id: str
    target_id: str
    relation: str
