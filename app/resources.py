from .models import Actor, Requirement, TraceLink, UseCase
from .api import Resource

RESOURCES = [
    Resource("/requirements", "requirements", Requirement, "REQ"),
    Resource("/use-cases", "use_cases", UseCase, "UC"),
    Resource("/actors", "actors", Actor, "ACT"),
    Resource("/traceability", "trace_links", TraceLink, "TRACE"),
]
