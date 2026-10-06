from .api import Resource
from .models import Actor, Requirement, TraceLink, UseCase

RESOURCES = [
    Resource("/api/requirements", "requirements", Requirement, "REQ"),
    Resource("/api/use-cases", "use_cases", UseCase, "UC"),
    Resource("/api/actors", "actors", Actor, "ACT"),
    Resource("/api/traceability", "trace_links", TraceLink, "TRACE"),
]
