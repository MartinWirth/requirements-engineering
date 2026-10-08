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

Copy `.env.example` to `.env` and fill in the values required for AI execution and GitHub publication.

### Windows PowerShell

```powershell
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
Copy-Item .env.example .env

# Load .env manually, or set the variables in the PowerShell session:
# $env:AI_API_URL="https://your-provider.example/v1/chat/completions"
# $env:AI_API_KEY="..."
# $env:AI_MODEL="your-model"
# $env:GITHUB_TOKEN="..."
# $env:GITHUB_REPOSITORY="MartinWirth/requirements-engineering"
# $env:GITHUB_BASE_BRANCH="main"

uvicorn app.main:app --reload
```

### Environment variables

Required for AI development execution:

- `AI_API_URL`
- `AI_API_KEY`
- `AI_MODEL`

Required for GitHub **Publish PR**:

- `GITHUB_TOKEN`
- `GITHUB_REPOSITORY`
- `GITHUB_BASE_BRANCH` (defaults to `main`)

Optional:

- `GITHUB_API_URL` (defaults to `https://api.github.com`)

The local `.env` file is ignored by Git. Never commit real API keys or GitHub tokens.

API documentation: http://127.0.0.1:8000/docs

## IREB reference

This project is an independent software implementation and is not an IREB-certified product. IREB's official CPRE Foundation syllabus and Requirements Modeling material are the authoritative references for terminology and learning scope.

- https://cpre.ireb.org/en/downloads-and-resources/downloads
- https://cpre.ireb.org/en/concept/requirements-modeling

## Development and testing workflow

Requirements are now connected to implementation work and verification:

`Requirement -> Issue/Task -> Subtask -> Test Case -> Passed/Failed`

- **Work Items** provides Jira-style `Issue`, `Task` and `Subtask` types.
- A **Subtask** requires a `parent_id`; work items can link to one or more `requirement_ids`.
- **Test Cases** link requirements and work items and record steps, expected results, status and actual results.
- Use **Traceability** for explicit `satisfies` and `verifies` relationships.
- The API endpoints are `/api/work-items` and `/api/test-cases`.

This gives a compact development loop: select a requirement, create implementation work, split it into subtasks, implement it, then create and execute a linked test case. Work Items can also be executed by a configured AI API; the AI returns file changes and test commands, which the backend applies inside the repository and verifies locally. After a successful AI execution, **Publish PR** pushes the dedicated branch to GitHub and creates a pull request against the configured base branch.

**Publish PR is idempotent:** if the branch was already pushed and an open pull request for the same branch/base exists, retrying publication returns that existing pull request instead of creating a duplicate.
