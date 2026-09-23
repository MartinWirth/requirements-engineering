from app.models import (
    Actor,
    Requirement,
    RequirementType,
    TraceLink,
    UseCase,
    UseCaseFlow,
)


def test_requirement_model():
    item = Requirement(
        id="REQ-001",
        title="Login",
        statement="The system shall authenticate users.",
        type=RequirementType.FUNCTIONAL,
    )
    assert item.id == "REQ-001"


def test_use_case_supports_ireb_core_fields():
    item = UseCase(
        id="UC-001",
        name="Authenticate user",
        actors=["ACT-USER"],
        trigger="User submits credentials",
        preconditions=["User has an account"],
        main_success_scenario=["Validate credentials", "Create session"],
        alternative_flows=[
            {"name": "Invalid credentials", "steps": ["Show error"]}
        ],
    )
    assert item.main_success_scenario
    assert item.alternative_flows[0].name == "Invalid credentials"


def test_next_id_returns_one_for_no_instances():
    assert Requirement.nextID([]) == 1
    assert UseCase.nextID([]) == 1
    assert Actor.nextID([]) == 1
    assert UseCaseFlow.nextID([]) == 1
    assert TraceLink.nextID([]) == 1


def test_next_id_returns_max_plus_one():
    requirements = [
        Requirement(
            id="REQ-001",
            title="First",
            statement="First requirement",
            type=RequirementType.FUNCTIONAL,
        ),
        Requirement(
            id="REQ-007",
            title="Seventh",
            statement="Seventh requirement",
            type=RequirementType.FUNCTIONAL,
        ),
        Requirement(
            id="REQ-003",
            title="Third",
            statement="Third requirement",
            type=RequirementType.FUNCTIONAL,
        ),
    ]

    assert Requirement.nextID(requirements) == 8


def test_next_id_uses_numeric_suffix():
    actors = [
        Actor(id="ACT-002", name="User"),
        Actor(id="ACT-009", name="Administrator"),
    ]

    assert Actor.nextID(actors) == 10


def test_main_models_can_be_created_without_an_id():
    assert Requirement(
        title="Login",
        statement="The system shall authenticate users.",
        type=RequirementType.FUNCTIONAL,
    ).id == ""

    assert UseCase(name="Authenticate user").id == ""
    assert Actor(name="User").id == ""
    assert TraceLink(source_id="REQ-001", target_id="UC-001", relation="satisfies").id == ""
