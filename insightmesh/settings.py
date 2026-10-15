"""Environment-backed application settings."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database: str = os.getenv("INSIGHTMESH_DB", "./insightmesh.db")
    llm_url: str = os.getenv("INSIGHTMESH_LLM_URL", "")
    llm_model: str = os.getenv("INSIGHTMESH_LLM_MODEL", "")
    llm_key: str = os.getenv("INSIGHTMESH_LLM_KEY", "")


def get_settings() -> Settings:
    return Settings(
        database=os.getenv("INSIGHTMESH_DB", "./insightmesh.db"),
        llm_url=os.getenv("INSIGHTMESH_LLM_URL", ""),
        llm_model=os.getenv("INSIGHTMESH_LLM_MODEL", ""),
        llm_key=os.getenv("INSIGHTMESH_LLM_KEY", ""),
    )
