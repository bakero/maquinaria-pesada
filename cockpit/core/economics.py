"""Economics: recargas de crédito por proveedor + cálculo de saldo restante.

Modelo simple:
  - Cada proveedor lleva una lista de recargas con (fecha, USD añadidos, nota).
  - El gasto se calcula desde `ai_usage.jsonl` agregando por provider.
  - Saldo = sum(recargas) - sum(gasto).

Persistencia: `logs/economics.json`. Editable desde la UI.
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import paths, usage_tracker


@dataclass
class Topup:
    timestamp: str
    provider: str  # "anthropic" | "openai" | "elevenlabs" | ...
    amount_usd: float
    note: str = ""


@dataclass
class EconomicsState:
    topups: list[Topup] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> EconomicsState:
        return cls(topups=[Topup(**t) for t in d.get("topups", [])])


def economics_path() -> Path:
    return paths.logs_dir() / "economics.json"


def load() -> EconomicsState:
    p = economics_path()
    if not p.exists():
        return EconomicsState()
    try:
        return EconomicsState.from_dict(json.loads(p.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, TypeError):
        return EconomicsState()


def save(state: EconomicsState) -> None:
    p = economics_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"topups": [asdict(t) for t in state.topups]}
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def add_topup(provider: str, amount_usd: float, note: str = "") -> EconomicsState:
    state = load()
    state.topups.append(
        Topup(
            timestamp=usage_tracker.now_iso(),
            provider=provider.lower(),
            amount_usd=round(float(amount_usd), 4),
            note=note,
        )
    )
    save(state)
    return state


def remove_topup(index: int) -> EconomicsState:
    state = load()
    if 0 <= index < len(state.topups):
        state.topups.pop(index)
        save(state)
    return state


def summary() -> dict[str, dict[str, float]]:
    """Devuelve dict provider -> {topped_up, spent, balance, calls}."""
    state = load()
    by_provider: dict[str, dict[str, float]] = defaultdict(
        lambda: {"topped_up": 0.0, "spent": 0.0, "balance": 0.0, "calls": 0}
    )
    for t in state.topups:
        by_provider[t.provider]["topped_up"] += t.amount_usd

    for ev in usage_tracker.iter_events():
        prov = (ev.get("provider") or "?").lower()
        cost = float(ev.get("cost_usd", 0) or 0)
        by_provider[prov]["spent"] += cost
        by_provider[prov]["calls"] += 1

    for data in by_provider.values():
        data["balance"] = round(data["topped_up"] - data["spent"], 4)
        data["topped_up"] = round(data["topped_up"], 4)
        data["spent"] = round(data["spent"], 4)

    return dict(by_provider)


def total_balance() -> float:
    s = summary()
    return round(sum(v["balance"] for v in s.values()), 4)
