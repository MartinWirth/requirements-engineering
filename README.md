# Requirements Engineering

A practical Requirements Engineering workbench aligned with the IREB CPRE curriculum.

## Goal

The application supports the core IREB requirements-engineering work products and techniques, with a particular focus on **use-case engineering** and traceability.

The current foundation is based on the current IREB CPRE material. IREB's Foundation Level covers elicitation, documentation, validation, negotiation/conflict handling, process adaptation and requirements management; the Requirements Modeling specialization explicitly includes use-case modeling, scenario modeling, activity/data-flow diagrams and state machines. [IREB Download Center](https://cpre.ireb.org/en/downloads-and-resources/downloads)

## Planned IREB coverage

### Requirements
- Functional requirements
- Quality requirements
- Constraints
- User requirements
- System requirements
- Stakeholders and sources
- Acceptance criteria

### Use cases
- Actors
- System boundary
- Use-case identification
- Main success scenario
- Alternative flows
- Exception flows
- Preconditions
- Postconditions
- Trigger
- Business value / goal
- Includes / extends relationships
- Generalization
- Use-case diagrams
- Detailed use-case specifications
- Traceability to requirements and test cases

### Modeling
- Context models
- Information/class models
- Activity diagrams
- Data-flow diagrams
- State machines
- Sequence diagrams
- Communication diagrams

### Requirements management
- IDs and versioning
- Status and lifecycle
- Priority
- Risk
- Dependencies
- Conflicts
- Traceability
- Change requests
- Baselines
- Review/validation records

## Architecture

- Python 3.12+
- FastAPI
- Pydantic
- SQLite for the initial local implementation
- REST API first; UI follows

## Start

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

API documentation: http://127.0.0.1:8000/docs

## IREB reference

This project is an independent software implementation and is not an IREB-certified product. IREB's official CPRE Foundation syllabus and Requirements Modeling material are the authoritative references for terminology and learning scope.

- https://cpre.ireb.org/en/downloads-and-resources/downloads
- https://cpre.ireb.org/en/concept/requirements-modeling
