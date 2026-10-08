from .api import Resource
from .models import Actor, Requirement, TraceLink, TestCase, UseCase, UserStory, WorkItem

RESOURCES = [
    Resource("/api/requirements", "requirements", Requirement, "REQ"),
    Resource("/api/user-stories", "user_stories", UserStory, "US"),
    Resource("/api/use-cases", "use_cases", UseCase, "UC"),
    Resource("/api/actors", "actors", Actor, "ACT"),
    Resource("/api/traceability", "trace_links", TraceLink, "TRACE"),
    Resource("/api/work-items", "work_items", WorkItem, "WI"),
    Resource("/api/test-cases", "test_cases", TestCase, "TEST"),
]
