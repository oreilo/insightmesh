"""Markdown report formatting."""
from datetime import datetime, timezone

def markdown_report(result: dict) -> str:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(result["plan"]["steps"], 1))
    warnings = "\n".join(f"- {w}" for w in result["review"]["warnings"])
    sources = "\n".join(f"- {s}" for s in result["analysis"]["sources_supplied"])
    return (f"# OREiLO InsightMesh Research Brief\n\nGenerated: {date}\n\n"
            f"## Question\n{result['question']}\n\n## Research plan\n{steps}\n\n"
            f"## Draft\n{result['report']}\n\n## Supplied references\n"
            f"{sources or 'None provided'}\n\n## Verification notes\n{warnings}\n")
