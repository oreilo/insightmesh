"""OREiLO InsightMesh HTTP API and dashboard."""
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Depends, Request, UploadFile, File
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .intelligence import summarize, query_data
from .webresearch import retrieve
from .documents import extract
from .exports import pdf_export, docx_export
from .workflows import execute
from pydantic import BaseModel, Field
import os
import hmac
from .agents import run_research
from .evidence import digest, verify
from .models import DatasetRequest, EvidenceCreate, ProjectCreate, ResearchRequest
from .profiling import profile
from .reporting import markdown_report
from .settings import get_settings
from .storage import Store

WEB = Path(__file__).resolve().parent.parent / "web"


def require_key(x_oreilo_key: str | None = Header(default=None)):
        configured = os.getenv("INSIGHTMESH_API_KEY", "")
        if configured and not hmac.compare_digest(x_oreilo_key or "", configured):
            raise HTTPException(401, "Valid OREiLO API key required")

def create_app(store: Store | None = None) -> FastAPI:
    app = FastAPI(title="OREiLO InsightMesh", version=__version__,
                  description="Research and data intelligence workspace by OREiLO")
    app.state.store = store or Store(get_settings().database)
    app.add_middleware(CORSMiddleware, allow_origins=[], allow_methods=["GET", "POST"],
                       allow_headers=["Content-Type"])

    def ensure(project_id: str):
        if not app.state.store.get_project(project_id):
            raise HTTPException(404, "Project not found")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "product": "OREiLO InsightMesh", "version": __version__}

    @app.get("/api/projects", dependencies=[Depends(require_key)])
    def projects():
        return app.state.store.list_projects()

    @app.post("/api/projects", status_code=201, dependencies=[Depends(require_key)])
    def create_project(body: ProjectCreate):
        return app.state.store.create_project(body.name, body.description)

    @app.get("/api/projects/{project_id}", dependencies=[Depends(require_key)])
    def project(project_id: str):
        ensure(project_id)
        return app.state.store.get_project(project_id)

    @app.post("/api/projects/{project_id}/research", status_code=201, dependencies=[Depends(require_key)])
    async def research(project_id: str, body: ResearchRequest):
        ensure(project_id)
        try:
            result = await run_research(body.question, body.context, body.sources, get_settings())
        except (ValueError, KeyError) as exc:
            raise HTTPException(422, str(exc)) from exc
        except Exception as exc:
            raise HTTPException(502, "Configured model provider request failed") from exc
        item = app.state.store.save("research", project_id,
                                    {"question": body.question, "result": json.dumps(result)})
        item["result"] = result
        return item

    @app.get("/api/projects/{project_id}/research", dependencies=[Depends(require_key)])
    def research_history(project_id: str):
        ensure(project_id)
        return app.state.store.list_items("research", project_id)

    @app.get("/api/projects/{project_id}/research/{research_id}/report.md", dependencies=[Depends(require_key)])
    def report(project_id: str, research_id: str):
        ensure(project_id)
        for item in app.state.store.list_items("research", project_id):
            if item["id"] == research_id:
                return PlainTextResponse(markdown_report(item["result"]),
                                         media_type="text/markdown")
        raise HTTPException(404, "Research record not found")

    @app.post("/api/projects/{project_id}/evidence", status_code=201, dependencies=[Depends(require_key)])
    def add_evidence(project_id: str, body: EvidenceCreate):
        ensure(project_id)
        return app.state.store.save("evidence", project_id,
                                    {**body.model_dump(), "sha256": digest(body.content)})

    @app.get("/api/projects/{project_id}/evidence", dependencies=[Depends(require_key)])
    def evidence(project_id: str):
        ensure(project_id)
        return app.state.store.list_items("evidence", project_id)

    @app.get("/api/projects/{project_id}/evidence/{evidence_id}/verify", dependencies=[Depends(require_key)])
    def verify_evidence(project_id: str, evidence_id: str):
        ensure(project_id)
        for item in app.state.store.list_items("evidence", project_id):
            if item["id"] == evidence_id:
                return {"verified": verify(item["content"], item["sha256"]),
                        "sha256": item["sha256"]}
        raise HTTPException(404, "Evidence not found")

    @app.post("/api/projects/{project_id}/datasets", status_code=201, dependencies=[Depends(require_key)])
    def add_dataset(project_id: str, body: DatasetRequest):
        ensure(project_id)
        try:
            result = profile(body.filename, body.content)
        except (ValueError, json.JSONDecodeError) as exc:
            raise HTTPException(422, str(exc)) from exc
        item = app.state.store.save("datasets", project_id,
                                    {"filename": body.filename, "profile": json.dumps(result)})
        item["profile"] = result
        return item

    @app.get("/api/projects/{project_id}/datasets", dependencies=[Depends(require_key)])
    def datasets(project_id: str):
        ensure(project_id)
        return app.state.store.list_items("datasets", project_id)


    class DataOperation(BaseModel):
        filename: str = Field(min_length=1, max_length=255)
        content: str = Field(min_length=1, max_length=2_000_000)
        group_by: str = ""
        metric: str = ""
        sql: str = ""

    class WebSource(BaseModel):
        url: str = Field(max_length=2048)

    class WorkflowRequest(BaseModel):
        steps: list[dict] = Field(min_length=1, max_length=20)

    @app.post("/api/intelligence/group", dependencies=[Depends(require_key)])
    def group(body: DataOperation):
        try: return summarize(body.filename, body.content, body.group_by, body.metric)
        except ValueError as exc: raise HTTPException(422, str(exc)) from exc

    @app.post("/api/intelligence/sql", dependencies=[Depends(require_key)])
    def sql(body: DataOperation):
        try: return query_data(body.filename, body.content, body.sql)
        except (ValueError, __import__("sqlite3").DatabaseError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/api/research/fetch", dependencies=[Depends(require_key)])
    async def fetch(body: WebSource):
        try: return await retrieve(body.url)
        except (ValueError, __import__("httpx").HTTPError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/api/documents/extract", dependencies=[Depends(require_key)])
    async def document(file: UploadFile = File(...)):
        content = await file.read(8_000_001)
        try: text = extract(file.filename or "", content)
        except (ValueError, ImportError) as exc: raise HTTPException(422, str(exc)) from exc
        return {"filename": file.filename, "text": text, "characters": len(text)}

    @app.post("/api/workflows/execute", dependencies=[Depends(require_key)])
    async def workflow(body: WorkflowRequest):
        try: return await execute(body.steps)
        except (ValueError, KeyError, TypeError) as exc: raise HTTPException(422, str(exc)) from exc

    @app.get("/api/projects/{project_id}/research/{research_id}/report.{fmt}", dependencies=[Depends(require_key)])
    def exported_report(project_id: str, research_id: str, fmt: str):
        ensure(project_id)
        for item in app.state.store.list_items("research", project_id):
            if item["id"] == research_id:
                report = markdown_report(item["result"])
                if fmt == "pdf":
                    return Response(pdf_export("OREiLO InsightMesh Research Report", report), media_type="application/pdf",
                                    headers={"Content-Disposition": "attachment; filename=insightmesh-report.pdf"})
                if fmt == "docx":
                    return Response(docx_export("OREiLO InsightMesh Research Report", report),
                                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    headers={"Content-Disposition": "attachment; filename=insightmesh-report.docx"})
                raise HTTPException(422, "Supported formats: pdf, docx")
        raise HTTPException(404, "Research record not found")

    @app.get("/")
    def index():
        return FileResponse(WEB / "index.html")

    @app.get("/app.css")
    def css():
        return FileResponse(WEB / "app.css", media_type="text/css")

    @app.get("/app.js")
    def js():
        return FileResponse(WEB / "app.js", media_type="text/javascript")

    return app


app = create_app()
