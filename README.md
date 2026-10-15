# OREiLO InsightMesh v3.0

**OREiLO** - Original research and data intelligence workspace. Copyright (c) 2026 OREiLO. MIT licensed.

## Features

- Research workspace with planner, context analyst, critic and report composer
- Optional OpenAI-compatible LLM draft generation (requires configured provider)
- Source explorer for public HTTPS pages, with private-network blocking and no redirect following
- Document extraction: TXT, MD, CSV, JSON, JSONL, PDF and DOCX
- Data profiling, numeric aggregation by category and read-only SQL on uploaded CSV/JSON datasets
- Evidence records with SHA-256 integrity verification
- Bounded multi-step workflows (plan, analyze, review, profile)
- Research reports: Markdown, PDF and DOCX
- SQLite-backed projects, research history and datasets
- REST API with optional API-key protection and responsive OREiLO dashboard
- Command-line utility and automated tests

## Windows setup

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
insightmesh serve
```

Open **http://127.0.0.1:8000**. REST API reference: **http://127.0.0.1:8000/docs**.

## Optional model configuration

Set `INSIGHTMESH_LLM_URL` to an OpenAI-compatible `/chat/completions` HTTPS endpoint (or localhost HTTP), `INSIGHTMESH_LLM_MODEL` to the model name and `INSIGHTMESH_LLM_KEY` to the provider key. Without configuration, research runs in transparent offline mode. No sources are invented.

## API access control

Set `INSIGHTMESH_API_KEY` to require an `X-OREILO-KEY` header for API calls. **The bundled dashboard does not implement an API-key login screen**, so use this option for API-only deployments or put the dashboard behind your own trusted gateway. By default, bind to `127.0.0.1` only. Do not expose the development server directly to the public internet.

## Example workflow

```json
{"steps":[{"action":"plan","args":{"question":"Evaluate a research hypothesis"}},{"action":"analyze","args":{"question":"Evaluate a research hypothesis","context":"A supplied observation.","sources":[]}}]}
```

POST to `/api/workflows/execute`.

## Limitations

This is a functional developer release, **not a fully autonomous web research platform or enterprise-ready service**. Source retrieval requires an explicit URL; it does not crawl the web or verify external claims. Workflow steps are sequential and are not a durable background scheduler. AI provider connectivity and browser operation require validation in your deployment. Authentication is a single optional shared API key, not multi-user RBAC. The public-source fetcher uses DNS filtering but should additionally be isolated at the network layer before internet-facing deployment.

## Project identity

Original OREiLO codebase; no upstream DataGen source is included. Third-party packages are dependencies governed by their respective licenses. Website: https://oreilo.com. Contact: contact@oreilo.com.
