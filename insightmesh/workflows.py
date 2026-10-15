"""Declarative, bounded local workflow executor."""
import asyncio
from .agents import plan, analyze, critique
from .profiling import profile

ALLOWED = {"plan", "analyze", "review", "profile"}

async def execute(steps: list[dict]) -> dict:
    if not 1 <= len(steps) <= 20: raise ValueError("Workflow must contain 1-20 steps")
    outputs = []
    for index, step in enumerate(steps):
        action = step.get("action")
        if action not in ALLOWED: raise ValueError(f"Unsupported action: {action}")
        args = step.get("args", {})
        if action == "plan": value = plan(args.get("question", ""))
        elif action == "analyze": value = analyze(args.get("question", ""), args.get("context", ""), args.get("sources", []))
        elif action == "review": value = critique(args.get("analysis", {"sources_supplied": [], "candidate_claims": []}))
        else: value = profile(args.get("filename", ""), args.get("content", ""))
        outputs.append({"index": index, "action": action, "output": value})
        await asyncio.sleep(0)
    return {"status": "completed", "steps": outputs}
