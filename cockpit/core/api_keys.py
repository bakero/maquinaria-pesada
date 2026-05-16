"""Verificación de API keys de los proveedores usados por el sistema.

Hace una llamada barata (list models / cuenta) a cada proveedor y devuelve
estado + latencia. Cachea resultado en `logs/api_status.json` para no
pegar a los proveedores en cada refresh.

No persiste las keys. Las lee de `.env` + entorno.
"""
from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from . import paths, usage_tracker

CACHE_FILE = Path("logs") / "api_status.json"
CACHE_TTL_SECONDS = 300  # 5 min


@dataclass
class KeyStatus:
    provider: str
    env_var: str
    present: bool
    ok: bool
    detail: str = ""
    latency_ms: int = 0
    checked_at: str = ""


def _merged_env() -> dict[str, str]:
    """Combina .env del repo + os.environ. os.environ gana."""
    env: dict[str, str] = {}
    env_path = paths.env_file()
    if env_path.exists():
        try:
            from dotenv import dotenv_values

            env.update({k: v for k, v in dotenv_values(env_path).items() if v})
        except ImportError:
            pass
    env.update({k: v for k, v in os.environ.items() if v})
    return env


def _check_anthropic(api_key: str) -> tuple[bool, str]:
    try:
        import anthropic
    except ImportError:
        return False, "paquete 'anthropic' no instalado"
    try:
        client = anthropic.Anthropic(api_key=api_key)
        # Llamada mínima: 1 token de output sobre prompt trivial.
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1,
            messages=[{"role": "user", "content": "ok"}],
        )
        return True, f"modelo {resp.model}"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:120]}"


def _check_openai(api_key: str) -> tuple[bool, str]:
    try:
        from openai import OpenAI
    except ImportError:
        return False, "paquete 'openai' no instalado"
    try:
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        return True, f"{len(list(models.data))} modelos disponibles"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:120]}"


def _check_elevenlabs(api_key: str) -> tuple[bool, str]:
    try:
        import urllib.request
    except ImportError:
        return False, "urllib no disponible"
    try:
        req = urllib.request.Request(
            "https://api.elevenlabs.io/v1/user/subscription",
            headers={"xi-api-key": api_key},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
        tier = data.get("tier", "?")
        chars = data.get("character_count", 0)
        limit = data.get("character_limit", 0)
        return True, f"tier {tier} · {chars}/{limit} chars"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:120]}"


PROVIDERS: list[tuple[str, str, Callable[[str], tuple[bool, str]]]] = [
    ("Anthropic", "ANTHROPIC_API_KEY", _check_anthropic),
    ("OpenAI", "OPENAI_API_KEY", _check_openai),
    ("ElevenLabs", "ELEVENLABS_API_KEY", _check_elevenlabs),
]


def check_all(force: bool = False) -> list[KeyStatus]:
    """Comprueba todas las keys. Usa caché si vigente y `force=False`."""
    if not force:
        cached = _read_cache()
        if cached is not None:
            return cached

    env = _merged_env()
    out: list[KeyStatus] = []
    for provider, var, checker in PROVIDERS:
        key = env.get(var, "").strip()
        if not key:
            st = KeyStatus(
                provider=provider,
                env_var=var,
                present=False,
                ok=False,
                detail=f"{var} no definido",
                checked_at=usage_tracker.now_iso(),
            )
        else:
            t0 = time.monotonic()
            ok, detail = checker(key)
            st = KeyStatus(
                provider=provider,
                env_var=var,
                present=True,
                ok=ok,
                detail=detail,
                latency_ms=int((time.monotonic() - t0) * 1000),
                checked_at=usage_tracker.now_iso(),
            )
            usage_tracker.record(
                usage_tracker.UsageEvent(
                    timestamp=st.checked_at,
                    kind="api_check",
                    provider=provider.lower(),
                    model="probe",
                    source="api_keys_page",
                    latency_ms=st.latency_ms,
                    ok=ok,
                    error="" if ok else detail,
                )
            )
        out.append(st)

    _write_cache(out)
    return out


def _read_cache() -> list[KeyStatus] | None:
    if not CACHE_FILE.exists():
        return None
    try:
        with CACHE_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
        ts = data.get("ts", 0)
        if time.time() - ts > CACHE_TTL_SECONDS:
            return None
        return [KeyStatus(**item) for item in data.get("items", [])]
    except (json.JSONDecodeError, TypeError):
        return None


def _write_cache(items: list[KeyStatus]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {"ts": time.time(), "items": [asdict(i) for i in items]}
    CACHE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
