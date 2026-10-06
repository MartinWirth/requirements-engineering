from app.models import RequirementStatus, UserStory


def test_user_story_model():
    story = UserStory(
        id="US-001",
        title="Export report",
        as_a="project manager",
        i_want="to export the requirements",
        so_that="I can share them",
        acceptance_criteria=["CSV export works"],
        status=RequirementStatus.PROPOSED,
    )
    assert story.i_want
    assert story.status == RequirementStatus.PROPOSED


def test_user_story_defaults():
    story = UserStory(title="Login")
    assert story.id == ""
    assert story.priority == "medium"
    assert story.status == RequirementStatus.DRAFT
