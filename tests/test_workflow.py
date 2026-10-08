from pydantic import ValidationError
import pytest

from app.models import TestCase, TestCaseStatus, WorkItem, WorkItemType


def test_work_item_hierarchy():
    task = WorkItem(id="WI-1", title="Implement", type=WorkItemType.TASK)
    subtask = WorkItem(id="WI-2", title="Code", type=WorkItemType.SUBTASK, parent_id=task.id)
    assert task.type == WorkItemType.TASK
    assert subtask.parent_id == task.id


def test_subtask_requires_parent():
    with pytest.raises(ValidationError):
        WorkItem(id="WI-1", title="Code", type=WorkItemType.SUBTASK)


def test_test_case_traces_requirement_and_work():
    case = TestCase(id="TEST-1", title="Verify", status=TestCaseStatus.READY,
                    requirement_ids=["FR-1"], work_item_ids=["WI-1"])
    assert case.requirement_ids == ["FR-1"]
    assert case.work_item_ids == ["WI-1"]\n\n\ndef test_work_item_ai_fields():\n    item = WorkItem(id="WI-1", title="AI task", ai_summary="implemented", ai_executed_at="2026-10-08T00:00:00+00:00")\n    assert item.ai_summary == "implemented"\n    assert item.ai_executed_at
