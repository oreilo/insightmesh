import asyncio
import pytest
from insightmesh.intelligence import summarize, query_data
from insightmesh.workflows import execute
from insightmesh.documents import extract
from insightmesh.webresearch import validate_public_url

def test_group():
    r = summarize("a.csv", "team,score\nA,2\nA,4\nB,3\n", "team", "score")
    assert r["groups"][0]["mean"] == 3

def test_sql():
    r = query_data("a.csv", "name,value\na,2\nb,4\n", "SELECT name FROM dataset WHERE value='4'")
    assert r["rows"] == [["b"]]

def test_sql_rejects_writes():
    with pytest.raises(ValueError): query_data("a.csv", "x\na\n", "DROP TABLE dataset")

def test_workflow():
    r = asyncio.run(execute([{"action": "plan", "args": {"question": "Why?"}}]))
    assert r["status"] == "completed"

def test_documents():
    assert extract("a.txt", b"OREiLO") == "OREiLO"

def test_block_local_url():
    with pytest.raises(ValueError): validate_public_url("http://localhost:8000/")
