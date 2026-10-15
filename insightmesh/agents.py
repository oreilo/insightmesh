"""Independent research workflow: planner, analyst, critic and reporter.

Offline mode does not invent sources or pretend research was performed.
An optional OpenAI-compatible endpoint can generate a draft from user-provided context.
"""
import re
from typing import Any

import httpx
from .settings import Settings


def plan(question: str) -> dict:
    return {"objective": question, "steps": [
        "Define the research question and its scope",
        "Collect and register source material",
        "Extract supported claims and note uncertainty",
        "Review counterarguments and missing evidence",
        "Prepare a traceable research brief",
    ]}


def analyze(question: str, context: str, sources: list[str]) -> dict:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", context) if s.strip()]
    return {"question": question, "context_excerpt": context[:1200],
            "candidate_claims": sentences[:8], "sources_supplied": sources,
            "mode": "context-only"}


def critique(analysis: dict) -> dict:
    warnings = []
    if not analysis["sources_supplied"]:
        warnings.append("No sources were supplied; claims are not independently verified.")
    if not analysis["candidate_claims"]:
        warnings.append("No supporting context was supplied; further evidence is required.")
    warnings.append("Source URLs are user-supplied references, not automatically retrieved or validated.")
    return {"warnings": warnings, "verification": "not independently verified"}


async def _model_draft(question: str, context: str, settings: Settings) -> str | None:
    if not settings.llm_url or not settings.llm_model:
        return None
    if not settings.llm_url.startswith(("https://", "http://localhost", "http://127.0.0.1")):
        raise ValueError("LLM endpoint must use HTTPS or local HTTP")
    headers = {"Content-Type": "application/json"}
    if settings.llm_key:
        headers["Authorization"] = f"Bearer {settings.llm_key}"
    body = {"model": settings.llm_model, "temperature": 0.2,
            "messages": [
                {"role": "system", "content": "Write a concise research draft using ONLY the supplied context. Do not invent sources, citations, or facts. Clearly state uncertainty."},
                {"role": "user", "content": f"Question: {question}\n\nSupplied context:\n{context}"},
            ]}
    async with httpx.AsyncClient(timeout=35.0) as client:
        response = await client.post(settings.llm_url, headers=headers, json=body)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


async def run_research(question: str, context: str, sources: list[str],
                       settings: Settings) -> dict[str, Any]:
    planning = plan(question)
    analysis = analyze(question, context, sources)
    review = critique(analysis)
    draft = await _model_draft(question, context, settings)
    if draft is None:
        draft = ("Research question: " + question + "\n\n" +
                 ("Provided context:\n" + context[:3000] if context else
                  "No source material provided. Add context and sources to develop this brief.") +
                 "\n\nLimitations: This offline brief does not perform web research or validate claims.")
    return {"question": question, "plan": planning, "analysis": analysis,
            "review": review, "report": draft, "model_used": bool(settings.llm_url)}
