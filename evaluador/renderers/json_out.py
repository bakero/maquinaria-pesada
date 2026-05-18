"""Renderer JSON."""

from __future__ import annotations

import json
from datetime import datetime


def render_json(results: list[dict], directory: str, mode: str, strict: bool) -> str:
    totals = {
        "files": len(results),
        "pass": sum(
            1
            for r in results
            if not any(f["severity"] == "hard" for f in r.get("findings", []))
        ),
        "hard_fails": sum(
            sum(1 for f in r.get("findings", []) if f["severity"] == "hard")
            for r in results
        ),
        "soft_warns": sum(
            sum(1 for f in r.get("findings", []) if f["severity"] == "soft")
            for r in results
        ),
    }
    payload = {
        "version": "v1",
        "timestamp": datetime.now().isoformat(),
        "directory": directory,
        "config": {"mode": mode, "strict": strict},
        "totals": totals,
        "results": results,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
