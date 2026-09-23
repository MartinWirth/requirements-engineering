from app.database import SQLiteStore
from app.models import Requirement, RequirementType


def test_objects_are_persisted_and_loaded(tmp_path):
    database = SQLiteStore(tmp_path / "requirements.db")
    item = Requirement(
        id="REQ-001",
        title="Login",
        statement="The system shall authenticate users.",
        type=RequirementType.FUNCTIONAL,
    )

    database.insert("requirements", item)

    reopened = SQLiteStore(tmp_path / "requirements.db")
    loaded = reopened.get("requirements", Requirement, "REQ-001")

    assert loaded == item


def test_next_id_uses_persisted_objects(tmp_path):
    database = SQLiteStore(tmp_path / "requirements.db")
    database.insert(
        "requirements",
        Requirement(
            id="REQ-007",
            title="Seventh",
            statement="Seventh requirement",
            type=RequirementType.FUNCTIONAL,
        ),
    )

    reopened = SQLiteStore(tmp_path / "requirements.db")

    assert reopened.next_id("requirements", Requirement) == 8


def test_list_returns_persisted_objects(tmp_path):
    database = SQLiteStore(tmp_path / "requirements.db")
    for number in (1, 3):
        database.insert(
            "requirements",
            Requirement(
                id=f"REQ-{number:03d}",
                title=f"Requirement {number}",
                statement=f"Statement {number}",
                type=RequirementType.FUNCTIONAL,
            ),
        )

    reopened = SQLiteStore(tmp_path / "requirements.db")

    assert [item.id for item in reopened.list("requirements", Requirement)] == [
        "REQ-001",
        "REQ-003",
    ]
