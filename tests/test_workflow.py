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
    case = TestCase(
        id="TEST-1",
        title="Verify",
        status=TestCaseStatus.READY,
        requirement_ids=["FR-1"],
        work_item_ids=["WI-1"],
    )
    assert case.requirement_ids == ["FR-1"]
    assert case.work_item_ids == ["WI-1"]


def test_work_item_ai_fields():
    item = WorkItem(
        id="WI-1",
        title="AI task",
        ai_summary="implemented",
        ai_executed_at="2026-10-08T00:00:00+00:00",
        ai_branch="ai/WI-1-ai-task",
        ai_commit="abc123",
        ai_pr_url="https://github.com/MartinWirth/requirements-engineering/pull/1",
        ai_pushed_at="2026-10-08T00:00:00+00:00",
    )
    assert item.ai_summary == "implemented"
    assert item.ai_executed_at
    assert item.ai_branch == "ai/WI-1-ai-task"
    assert item.ai_commit == "abc123"
    assert item.ai_pr_url.endswith("/pull/1")
    assert item.ai_pushed_at
