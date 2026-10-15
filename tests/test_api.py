from fastapi.testclient import TestClient
from insightmesh.api import create_app
from insightmesh.storage import Store


def test_project_and_artifacts(tmp_path):
    with TestClient(create_app(Store(str(tmp_path / "api.db")))) as client:
        assert client.get("/api/health").json()["product"] == "OREiLO InsightMesh"
        project = client.post("/api/projects", json={"name": "Test Workspace"}).json()
        pid = project["id"]
        research = client.post(f"/api/projects/{pid}/research", json={
            "question": "What does this context say?", "context": "Sales increased."})
        assert research.status_code == 201
        rid = research.json()["id"]
        assert "OREiLO" in client.get(f"/api/projects/{pid}/research/{rid}/report.md").text
        dataset = client.post(f"/api/projects/{pid}/datasets", json={
            "filename": "sales.csv", "content": "a,b\n1,2\n3,4"})
        assert dataset.json()["profile"]["rows"] == 2
        evidence = client.post(f"/api/projects/{pid}/evidence", json={
            "title": "Note", "content": "Test text"}).json()
        assert client.get(f"/api/projects/{pid}/evidence/{evidence['id']}/verify").json()["verified"]
        assert client.get("/api/projects/invalid").status_code == 404
        assert client.get("/").status_code == 200
