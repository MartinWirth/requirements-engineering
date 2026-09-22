from app.models import Requirement, RequirementType, UseCase


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
        alternative_flows=[{"name": "Invalid credentials", "steps": ["Show error"]}],
    )
    assert item.main_success_scenario
    assert item.alternative_flows[0].name == "Invalid credentials"
