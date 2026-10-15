"""Request and response contracts."""
from typing import Any
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)


class ResearchRequest(BaseModel):
    question: str = Field(min_length=5, max_length=5000)
    context: str = Field(default="", max_length=15000)
    sources: list[str] = Field(default_factory=list, max_length=30)


class EvidenceCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=100000)
    source: str = Field(default="", max_length=1000)


class DatasetRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=2_000_000)


class AgentStep(BaseModel):
    agent: str
    output: dict[str, Any]
