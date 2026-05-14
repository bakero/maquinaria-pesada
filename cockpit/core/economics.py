"""Economics: recargas, gastos manuales y suscripciones por proveedor IA.

Tres tipos de movimientos:

  * **Topup**       — recarga pay-as-you-go (cargo en panel del proveedor).
  * **Spend**       — gasto manual fuera de `ai_usage.jsonl` (importes de
                      facturas históricas, ejecuciones pre-cockpit, etc.).
  * **Subscription** — tarifa plana mensual (Claude Max, ElevenLabs Starter…).

Saldo por proveedor:
    balance = sum(topups) − sum(spends) − sum(eventos ai_usage.jsonl)

Persistencia: `logs/economics.json`. Edición desde la UI o seed manual.
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
    provider: str
    amount_usd: float
    note: str = ""


@dataclass
class Spend:
    timestamp: str
    provider: str
    amount_usd: float
    note: str = ""


@dataclass
class Subscription:
    name: str
    provider: str
    monthly_usd: float
    started_on: str = ""
    active: bool = True
    note: str = ""


@dataclass
class EconomicsState:
    topups: list[Topup] = field(default_factory=list)
    spends: list[Spend] = field(default_factory=list)
    subscriptions: list[Subscription] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> EconomicsState:
        return cls(
            topups=[Topup(**t) for t in d.get("topups", [])],
            spends=[Spend(**s) for s in d.get("spends", [])],
            subscriptions=[Subscription(**s) for s in d.get("subscriptions", [])],
        )


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
    payload = {
        "topups": [asdict(t) for t in state.topups],
        "spends": [asdict(s) for s in state.spends],
        "subscriptions": [asdict(s) for s in state.subscriptions],
    }
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# ---- Mutators ---------------------------------------------------------


def add_topup(provider: str, amount_usd: float, note: str = "",
              timestamp: str | None = None) -> EconomicsState:
    state = load()
    state.topups.append(
        Topup(
            timestamp=timestamp or usage_tracker.now_iso(),
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


def add_spend(provider: str, amount_usd: float, note: str = "",
              timestamp: str | None = None) -> EconomicsState:
    state = load()
    state.spends.append(
        Spend(
            timestamp=timestamp or usage_tracker.now_iso(),
            provider=provider.lower(),
            amount_usd=round(float(amount_usd), 4),
            note=note,
        )
    )
    save(state)
    return state


def remove_spend(index: int) -> EconomicsState:
    state = load()
    if 0 <= index < len(state.spends):
        state.spends.pop(index)
        save(state)
    return state


def add_subscription(name: str, provider: str, monthly_usd: float,
                     started_on: str = "", note: str = "") -> EconomicsState:
    state = load()
    state.subscriptions.append(
        Subscription(
            name=name,
            provider=provider.lower(),
            monthly_usd=round(float(monthly_usd), 4),
            started_on=started_on,
            active=True,
            note=note,
        )
    )
    save(state)
    return state


def remove_subscription(index: int) -> EconomicsState:
    state = load()
    if 0 <= index < len(state.subscriptions):
        state.subscriptions.pop(index)
        save(state)
    return state


# ---- Summary ----------------------------------------------------------


def summary() -> dict[str, dict[str, float]]:
    """provider → {topped_up, spent_manual, spent_tracked, spent, balance,
                   calls, subscription_monthly, subscriptions}."""
    state = load()
    by: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "topped_up": 0.0,
            "spent_manual": 0.0,
            "spent_tracked": 0.0,
            "spent": 0.0,
            "balance": 0.0,
            "calls": 0,
            "subscription_monthly": 0.0,
            "subscriptions": 0,
        }
    )
    for t in state.topups:
        by[t.provider]["topped_up"] += t.amount_usd
    for s in state.spends:
        by[s.provider]["spent_manual"] += s.amount_usd
    for sub in state.subscriptions:
        if sub.active:
            by[sub.provider]["subscription_monthly"] += sub.monthly_usd
            by[sub.provider]["subscriptions"] += 1

    for ev in usage_tracker.iter_events():
        prov = (ev.get("provider") or "?").lower()
        cost = float(ev.get("cost_usd", 0) or 0)
        by[prov]["spent_tracked"] += cost
        by[prov]["calls"] += 1

    for data in by.values():
        data["spent"] = data["spent_manual"] + data["spent_tracked"]
        data["balance"] = round(data["topped_up"] - data["spent"], 4)
        for k in ("topped_up", "spent_manual", "spent_tracked", "spent",
                  "subscription_monthly"):
            data[k] = round(data[k], 4)

    return dict(by)


def total_balance() -> float:
    s = summary()
    return round(sum(v["balance"] for v in s.values()), 4)


def total_spent() -> float:
    s = summary()
    return round(sum(v["spent"] for v in s.values()), 4)


def total_topped_up() -> float:
    s = summary()
    return round(sum(v["topped_up"] for v in s.values()), 4)


def total_subscription_monthly() -> float:
    s = summary()
    return round(sum(v["subscription_monthly"] for v in s.values()), 4)


# ---- Snapshot real recogido el 2026-05-12 -----------------------------


SNAPSHOT_2026_05_12 = {
    "topups": [
        # Anthropic — panel billing
        ("anthropic", 24.20, "Concesión de crédito (panel Anthropic)", "2026-05-07"),
        ("anthropic", 30.25, "Concesión de crédito (panel Anthropic)", "2026-05-11"),
        # ElevenLabs — panel billing (top-ups pay-as-you-go)
        ("elevenlabs", 24.20, "Pay-as-you-go Credits Top-Up (manual)", "2026-05-06"),
        ("elevenlabs", 24.20, "Pay-as-you-go Credits Top-Up (manual)", "2026-05-12"),
        # Kling — 4 Trial Packages
        ("kling", 11.86, "Trial Package (order 881669745903280136)", "2026-05-08"),
        ("kling", 16.94, "Trial Package (order 881840112127705097)", "2026-05-08"),
        ("kling", 16.94, "Trial Package (order 881990502534086750)", "2026-05-09"),
        ("kling", 16.94, "Trial Package (order 881990681731538970)", "2026-05-09"),
    ],
    "spends": [
        # Saldo restante en Anthropic = 24.83 USD → consumido = 54.45 - 24.83 = 29.62
        ("anthropic", 29.62, "Consumo API + Claude Code + Workbench hasta 2026-05-12"),
        # ElevenLabs: 196 305 chars en producción + iteraciones → top-ups agotados aprox
        ("elevenlabs", 48.40, "Generación de 12 episodios (eleven_v3, 196k chars + iteraciones)"),
        # Kling: 14 vídeos finales descargados; gasto efectivo = total top-ups
        ("kling", 62.68, "14 vídeos generados + iteraciones (4 Trial Packages consumidos)"),
    ],
    "subscriptions": [
        ("Claude Max", "anthropic", 100.0, "2026-04", "Tarifa plana — confirmar plan exacto (100/200 USD)"),
        ("ElevenLabs Starter", "elevenlabs", 5.0, "2026-05-01", "30k créditos/mes incluidos"),
    ],
}


def seed_snapshot(snapshot: dict | None = None, replace: bool = False) -> EconomicsState:
    """Carga un snapshot de movimientos en `logs/economics.json`.

    Por defecto carga el snapshot real recogido el 2026-05-12 (Anthropic +
    ElevenLabs + Kling, datos verificados contra los paneles de cada
    proveedor).

    Args:
        snapshot: dict con claves `topups`, `spends`, `subscriptions` cada
                  una con tuplas. Si None, usa `SNAPSHOT_2026_05_12`.
        replace: si True, **reemplaza** el estado actual; si False (default),
                 se acumula encima.
    """
    snap = snapshot if snapshot is not None else SNAPSHOT_2026_05_12
    state = EconomicsState() if replace else load()

    for entry in snap.get("topups", []):
        provider, amount, note, ts = entry
        state.topups.append(
            Topup(timestamp=ts, provider=provider.lower(),
                  amount_usd=round(float(amount), 4), note=note)
        )
    for entry in snap.get("spends", []):
        provider, amount, note = entry[:3]
        ts = entry[3] if len(entry) > 3 else "2026-05-12"
        state.spends.append(
            Spend(timestamp=ts, provider=provider.lower(),
                  amount_usd=round(float(amount), 4), note=note)
        )
    for entry in snap.get("subscriptions", []):
        name, provider, monthly, started, note = entry
        state.subscriptions.append(
            Subscription(name=name, provider=provider.lower(),
                         monthly_usd=round(float(monthly), 4),
                         started_on=started, active=True, note=note)
        )
    save(state)
    return state
