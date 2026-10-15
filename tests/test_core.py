import json
import pytest
from insightmesh.agents import run_research
from insightmesh.evidence import digest, verify
from insightmesh.profiling import profile
from insightmesh.reporting import markdown_report
from insightmesh.settings import Settings
from insightmesh.storage import Store


def test_profile_csv():
    result = profile("sales.csv", "name,amount\nA,10\nB,20\nC,\n")
    assert result["rows"] == 3
    amount = result["columns"][1]
    assert amount["missing"] == 1
    assert amount["statistics"]["mean"] == 15


def test_profile_jsonl():
    result = profile("events.jsonl", '{"event":"a"}\n{"event":"b"}')
    assert result["rows"] == 2


def test_profile_rejects_extension():
    with pytest.raises(ValueError):
        profile("a.exe", "x")


def test_evidence():
    assert verify("hello", digest("hello"))
    assert not verify("changed", digest("hello"))


def test_store(tmp_path):
    db = Store(str(tmp_path / "test.db"))
    project = db.create_project("Test", "")
    assert db.get_project(project["id"])["name"] == "Test"
    db.save("evidence", project["id"], {"title":"Note","content":"Hi","source":"", "sha256":digest("Hi")})
    assert len(db.list_items("evidence", project["id"])) == 1


def test_offline_workflow():
    import asyncio
    result = asyncio.run(run_research("What happened in the dataset?", "Revenue increased.", [], Settings()))
    assert not result["model_used"]
    assert result["review"]["warnings"]
    assert "OREiLO" in markdown_report(result)
