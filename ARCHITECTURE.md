# Architecture

## Components

- `insightmesh/api.py`: FastAPI application factory and HTTP routes.
- `insightmesh/storage.py`: SQLite-backed project and artifact persistence.
- `insightmesh/agents.py`: transparent planner, context analyst, critic and optional LLM draft.
- `insightmesh/profiling.py`: CSV/JSONL profiling without heavyweight data dependencies.
- `insightmesh/evidence.py`: SHA-256 fingerprint and verification utilities.
- `insightmesh/reporting.py`: Markdown export.
- `insightmesh/cli.py`: command-line entry points.
- `web/`: responsive HTML/CSS/JavaScript dashboard served by the API.

## Security boundary

No authentication is included. Bind to localhost by default. User-supplied source links are stored as text; the backend does not fetch them. LLM endpoints require HTTPS except for localhost. Frontend output is HTML-escaped. SQLite parameter binding is used for values.

## Next milestones

Authentication and roles, asynchronous job execution, source ingestion with permissions and citations, agent tool isolation, observability, structured LLM output, and deployment templates.
