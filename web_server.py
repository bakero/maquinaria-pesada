"""Servidor HTTP para el cockpit en React (vite_app/).

Sirve el build de Vite (`vite_app/dist/`) y expone una API JSON en `/api/*`
que conecta con los módulos reales de `cockpit/core` (episodios,
ai_usage, economics, runner, ai_client).

Build del frontend:  cd vite_app && npm run build  → vite_app/dist/

Uso:
    python web_server.py [--port 8765] [--host 127.0.0.1]

Endpoints (todos JSON salvo donde se indique):

    GET  /                       → vite_app/dist/index.html
    GET  /<archivo estático>     → vite_app/dist/<archivo>

    GET  /api/health             → {"ok": true}
    GET  /api/bootstrap          → datos iniciales para data.jsx
                                   (MODULES, EPISODES, TOKEN_DATA, …)
    GET  /api/episodes           → lista de episodios escaneados del repo
    GET  /api/episode/<id>       → metadatos del episodio + rutas reales de
                                   pdf/guion/escaleta/audio/video/logs
    GET  /api/episode/<id>/checks → verificaciones reales (verifications.run_all)
    GET  /api/episode/<id>/gen-log → traza de generación/validación del guion
                                   (intentos, issues hard/soft, veredicto)
    GET  /api/ai-usage           → eventos de logs/ai_usage.jsonl agregados
    GET  /api/economics          → estado de logs/economics.json + summary
    GET  /api/optimization       → recomendaciones de ahorro (heurísticas
                                   reales sobre ai_usage.jsonl)
    GET  /api/components-map     → grafo de cockpit/components_map.json
    GET  /api/connectors         → estado real de los conectores registrados
    GET  /api/pizarra            → lienzo guardado de la Pizarra (o null)
    GET  /api/metrics            → métricas de difusión reales (Spotify /
                                   iVoox / LinkedIn vía connectors/analytics)
    GET  /api/logs               → archivos de logs/ (path, size, mtime)
    GET  /api/live               → procesos en producción (psutil best-effort)
    GET  /api/recent-files       → últimos artefactos modificados

    POST /api/ai/chat            → Body: {mode, target, message}
                                   Llama a improve_with_claude (no streaming
                                   en stdlib por simplicidad: devuelve texto
                                   completo). Si falta la key, devuelve un
                                   mensaje placeholder con ok:false.
    POST /api/run                → Body: {script, flags}
                                   Lanza un pipeline en background con runner
                                   y devuelve {pid, cmd}.
    POST /api/episode/<id>/generate → Genera el guion de UN episodio concreto.
                                   Resuelve PDF + script vía episode_sources y
                                   redirige la traza a Guiones/logs/<id>_gen.log.
    POST /api/pizarra            → Persiste el lienzo de la Pizarra (nodes/edges).
    POST /api/pizarra/generate-component → Genera código de un componente con
                                   Claude (ai_client). Body: {name, description, kind}.
    POST /api/reveal             → Body: {path} (relativo a REPO_ROOT)
                                   Abre la carpeta/archivo en el explorador.
    POST /api/economics/topup    → Body: {provider, amount, note}
                                   Registra una recarga en economics.json.
    POST /api/api-key/ping       → Body: {provider}
                                   Comprueba si la API key del proveedor está
                                   presente en .env o env vars.
    POST /api/log                → Body: {level, message, ...contexto}
                                   Registra en la bitácora central un evento
                                   o error enviado por el frontend JS.

    GET  /files/<ruta>           → Sirve archivos del repo (PDFs, Guiones,
                                   episodios, escaletas, logs). Solo lectura
                                   y solo dentro de REPO_ROOT.

El servidor es deliberadamente sin dependencias externas: usa solo
http.server de la stdlib. Diseñado para localhost; no expone CORS amplio.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
WEB_DIST = ROOT / "vite_app" / "dist"


def _resolve_web_dir() -> Path:
    """Devuelve el directorio del build Vite (`vite_app/dist/`).

    Permite forzar otra ruta via env var COCKPIT_WEB_DIR (ruta absoluta),
    útil para tests."""
    override = os.environ.get("COCKPIT_WEB_DIR", "").strip()
    if override:
        return Path(override)
    return WEB_DIST


WEB_DIR = _resolve_web_dir()

# Permitir importar cockpit/core sin Streamlit
sys.path.insert(0, str(ROOT))

# Sistema único de logs: todo evento del backend va a la bitácora diaria
# (logs/run/), correlacionado con el RunLog del servidor (campo run=).
from daylog import get_logger  # noqa: E402

_log = get_logger("web_server")
_frontend_log = get_logger("web_frontend")


# ---- API helpers ------------------------------------------------------


def _state_for_episode(ep) -> dict:
    """Convierte un Episode en el dict que data.jsx espera (ok/warn/alert/empty)."""
    def s(content: str) -> str:
        return "ok" if ep.has(content) else "empty"
    logs_state = "ok" if ep.logs else "empty"
    video_state = "ok" if ep.has("video") else "empty"
    return {
        "pdf":      s("pdf"),
        "guion":    s("guion"),
        "escaleta": s("escaleta"),
        "audio":    s("audio"),
        "video":    video_state,
        "logs":     logs_state,
    }


def _modulo_status_from_eps(eps: list, ratio: float) -> str:
    """Mapea ratio (0..1) a status UI: ok/warn/alert/empty."""
    if ratio >= 1.0:
        return "ok"
    if ratio >= 0.5:
        return "warn"
    if ratio > 0.0:
        return "alert"
    return "empty"


def scan_modules_and_episodes() -> tuple[list[dict], list[dict]]:
    try:
        from cockpit.core import episodes
    except Exception:
        return [], []

    try:
        all_eps = episodes.scan_all()
    except Exception:
        all_eps = []

    by_module: dict[str, list] = {}
    for ep in all_eps:
        by_module.setdefault(ep.module, []).append(ep)

    modules_out: list[dict] = []
    for m in episodes.modules_meta():
        eps_m = by_module.get(m["id"], [])
        if eps_m:
            _, ratio = episodes.module_status(eps_m)
        else:
            ratio = 0.0
        modules_out.append({
            **m,
            "pct": int(round(ratio * 100)),
            "status": _modulo_status_from_eps(eps_m, ratio),
        })

    episodes_out: list[dict] = []
    for ep in all_eps:
        episodes_out.append({
            "id": ep.id,
            "mod": ep.module,
            "kind": ep.kind,
            "title": ep.label or f"Episodio {ep.id}",
            "dur": "—",
            "state": _state_for_episode(ep),
        })
    return modules_out, episodes_out


def load_ai_usage() -> dict:
    """Agrega ai_usage.jsonl en el formato que espera TOKEN_DATA."""
    try:
        from cockpit.core import usage_tracker
    except Exception:
        return _fallback_token_data()

    events = list(usage_tracker.iter_events())
    if not events:
        return _fallback_token_data()

    agg = usage_tracker.aggregate(events)
    total_tok = agg["total_input_tokens"] + agg["total_output_tokens"]
    total_cost = agg["total_cost_usd"]

    by_model_out = []
    for model, stats in sorted(
        agg["by_model"].items(), key=lambda kv: -kv[1]["cost"]
    ):
        toks = stats["in"] + stats["out"]
        share = round((toks / total_tok) * 100, 1) if total_tok else 0
        by_model_out.append({
            "model": model,
            "tokens": int(toks),
            "cost": round(stats["cost"], 2),
            "share": share,
        })

    by_kind_out = []
    for kind, stats in agg["by_kind"].items():
        share = round((stats["cost"] / total_cost) * 100, 1) if total_cost else 0
        by_kind_out.append({"kind": kind, "pct": share})

    last5 = []
    for ev in events[-5:][::-1]:
        last5.append({
            "t": ev.get("timestamp", ""),
            "model": ev.get("model", "?"),
            "kind": ev.get("kind", "?"),
            "tok": int(ev.get("input_tokens", 0)) + int(ev.get("output_tokens", 0)),
            "cost": round(float(ev.get("cost_usd", 0.0)), 4),
        })

    return {
        "total_30d": total_tok,
        "cost_30d": round(total_cost, 2),
        "budget": 250,
        "byModel": by_model_out,
        "byKind": by_kind_out,
        "log": last5,
    }


def _fallback_token_data() -> dict:
    return {
        "total_30d": 0,
        "cost_30d": 0.0,
        "budget": 250,
        "byModel": [],
        "byKind": [],
        "log": [],
    }


def load_economics() -> dict:
    try:
        from cockpit.core import economics
    except Exception:
        return {"topups": [], "spends": [], "subscriptions": [],
                "balance_by_provider": {}, "summary": {}}

    state = economics.load()
    balance: dict[str, float] = {}
    for t in state.topups:
        balance[t.provider] = balance.get(t.provider, 0.0) + t.amount_usd
    for s in state.spends:
        balance[s.provider] = balance.get(s.provider, 0.0) - s.amount_usd
    try:
        summary = economics.summary()
    except Exception:
        summary = {}
    return {
        "topups": [t.__dict__ for t in state.topups],
        "spends": [s.__dict__ for s in state.spends],
        "subscriptions": [s.__dict__ for s in state.subscriptions],
        "balance_by_provider": {k: round(v, 2) for k, v in balance.items()},
        # summary: provider → {topped_up, spent, spent_tracked, balance, calls, …}
        "summary": summary,
    }


def load_optimization() -> dict:
    """Recomendaciones de ahorro: heurísticas reales sobre ai_usage.jsonl."""
    try:
        from cockpit.core import optimization_advisor, usage_tracker
    except Exception as exc:
        return {"ok": False, "error": str(exc), "recommendations": []}

    try:
        events = list(usage_tracker.iter_events())
        recs = optimization_advisor.analyze(events)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "recommendations": []}

    total_savings = round(sum(r.savings_estimate_usd for r in recs), 2)
    return {
        "ok": True,
        "events_analyzed": len(events),
        "total_savings_usd": total_savings,
        "recommendations": [
            {
                "rule_id": r.rule_id,
                "severity": r.severity,
                "title": r.title,
                "evidence": r.evidence,
                "action": r.action,
                "savings": round(r.savings_estimate_usd, 2),
            }
            for r in recs
        ],
    }


def load_components_map() -> dict:
    """Grafo de componentes del cockpit desde cockpit/components_map.json."""
    try:
        from cockpit.core import components_map
    except Exception as exc:
        return {"ok": False, "error": str(exc), "nodes": [], "edges": []}
    try:
        return {"ok": True, **components_map.load().to_dict()}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "nodes": [], "edges": []}


def load_connectors() -> dict:
    """Estado real de los conectores registrados (services/pipelines/sources).

    Cada conector expone .status() — para servicios comprueba credenciales
    en .env, para pipelines que el script exista, etc."""
    try:
        from cockpit import connectors
    except Exception as exc:
        return {"ok": False, "error": str(exc), "connectors": []}
    out = []
    for cid, c in connectors.REGISTRY.items():
        try:
            s = c.status()
            st = {"ok": bool(s.ok), "detail": s.detail or ""}
        except Exception as exc:  # noqa: BLE001
            st = {"ok": False, "detail": f"error: {exc}"}
        out.append({
            "id": cid,
            "category": c.category,
            "label": c.label or cid,
            "icon": c.icon or "",
            "description": c.description or "",
            "script": getattr(c, "script", "") or "",
            "status": st,
        })
    out.sort(key=lambda c: (c["category"], c["id"]))
    return {"ok": True, "connectors": out}


def load_episode_detail(ep_id: str) -> dict | None:
    """Metadatos + rutas reales (relativas al repo) de un episodio."""
    try:
        from cockpit.core import episodes, paths
    except Exception:
        return None
    ep = episodes.get_episode(ep_id)
    if ep is None:
        return None
    root = paths.repo_root().resolve()

    def rel(p) -> str | None:
        if not p:
            return None
        try:
            return Path(p).resolve().relative_to(root).as_posix()
        except (ValueError, OSError):
            return None

    return {
        "id": ep.id,
        "mod": ep.module,
        "kind": ep.kind,
        "number": ep.number,
        "slug": ep.slug,
        "title": ep.label or f"Episodio {ep.id}",
        "dur": "—",
        "state": _state_for_episode(ep),
        "paths": {
            "pdf": rel(ep.pdf),
            "guion": rel(ep.guion),
            "escaleta": rel(ep.escaleta),
            "audio": rel(ep.audio),
            "video": rel(ep.video),
            "logs": [r for r in (rel(p) for p in ep.logs) if r],
        },
    }


def load_episode_checks(ep_id: str) -> dict:
    """Verificaciones reales de un episodio (cockpit.core.verifications)."""
    try:
        from cockpit.core import episodes, verifications
    except Exception as exc:
        return {"ok": False, "error": str(exc), "groups": {}}
    ep = episodes.get_episode(ep_id)
    if ep is None:
        return {"ok": False, "error": f"episodio no encontrado: {ep_id}", "groups": {}}
    try:
        results = verifications.run_all(ep)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "groups": {}}
    return {
        "ok": True,
        "groups": {
            k: [
                {"id": c.id, "label": c.label, "status": c.status, "detail": c.detail}
                for c in v
            ]
            for k, v in results.items()
        },
    }


def load_pizarra() -> dict:
    """Lienzo guardado de la Pizarra (cockpit/pizarra_board.json) o None."""
    try:
        from cockpit.core import pizarra
    except Exception as exc:
        return {"ok": False, "error": str(exc), "board": None}
    try:
        return {"ok": True, "board": pizarra.load_board()}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "board": None}


def save_pizarra(data: dict) -> dict:
    """Persiste el lienzo de la Pizarra."""
    try:
        from cockpit.core import pizarra
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    try:
        pizarra.save_board(data or {})
        return {"ok": True}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def pizarra_generate_component(name: str, description: str, kind: str) -> dict:
    """Genera código real de un componente con Claude (vía ai_client).

    Sin API key, ai_client devuelve usage.ok=False y un texto de fallback —
    el front lo trata como error mostrando el mensaje."""
    if not (name or "").strip() or not (description or "").strip():
        return {"ok": False, "error": "name y description requeridos", "code": ""}
    try:
        from cockpit.core import ai_client
    except Exception as exc:
        return {"ok": False, "error": f"ai_client no disponible: {exc}", "code": ""}

    system = (
        "Eres un ingeniero senior del pipeline 'MaquinarIA Pesada' (Python 3.10+). "
        "Genera UN script Python autocontenido para el componente que se describe. "
        "Convenciones: type hints, función run() como entry-point, docstring inicial, "
        "sin dependencias exóticas. Devuelve SOLO el código, sin explicaciones ni "
        "bloques markdown."
    )
    user = (
        f"Nombre del componente: {name}\n"
        f"Tipo: {kind}\n"
        f"Qué debe hacer:\n{description}"
    )
    try:
        text, usage = ai_client.improve_with_claude(
            system=system,
            user=user,
            source="web_pizarra:generate",
            kind="generation",
            model="claude-sonnet-4-6",
            max_tokens=2000,
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "code": ""}
    return {
        "ok": bool(usage.ok),
        "code": text,
        "error": "" if usage.ok else "Claude no disponible (¿falta ANTHROPIC_API_KEY?)",
        "usage": {
            "model": usage.model,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cost_usd": usage.cost_usd,
        },
    }


def load_metrics() -> dict:
    """Métricas de difusión reales (Spotify / iVoox / LinkedIn).

    Cada conector hace HTTP real y cachea en logs/analytics/. Sin credenciales
    en .env el conector reporta configured=False y la página lo muestra como
    "no configurado" — degradación honesta, sin datos sintéticos."""
    import importlib
    from dataclasses import asdict, is_dataclass

    try:
        from cockpit.connectors.analytics.base import AnalyticsConnector, Unavailable
    except Exception as exc:
        return {"ok": False, "error": str(exc), "platforms": {}}

    def ser(o):
        return asdict(o) if is_dataclass(o) else o

    platforms: dict[str, dict] = {}
    for src in ("spotify", "ivoox", "linkedin"):
        entry: dict = {
            "source": src, "label": src, "configured": False, "detail": "",
            "show": None, "episodes": [], "posts": [],
        }
        try:
            mod = importlib.import_module(f"cockpit.connectors.analytics.{src}")
            cls = next(
                (o for o in vars(mod).values()
                 if isinstance(o, type) and issubclass(o, AnalyticsConnector)
                 and o is not AnalyticsConnector),
                None,
            )
            if cls is None:
                entry["error"] = "conector no encontrado"
                platforms[src] = entry
                continue
            conn = cls()
            entry["label"] = getattr(conn, "label", src)
            entry["icon"] = getattr(conn, "icon", "")
            entry["configured"] = conn.is_configured()
            entry["detail"] = conn.status_detail()
            entry["missing"] = conn.missing_config()
            if conn.is_configured():
                try:
                    show = conn.fetch_show()
                    entry["show"] = ser(show) if show else None
                    entry["episodes"] = [ser(e) for e in conn.fetch_episodes()]
                    entry["posts"] = [ser(p) for p in conn.fetch_posts()]
                except Unavailable as exc:
                    entry["detail"] = str(exc)
                except Exception as exc:  # noqa: BLE001
                    entry["error"] = str(exc)
        except Exception as exc:  # noqa: BLE001
            entry["error"] = str(exc)
        platforms[src] = entry
    return {"ok": True, "platforms": platforms}


def load_logs_list() -> dict:
    """Lista los archivos de logs/ (jsonl/log/json) ordenados por mtime."""
    try:
        from cockpit.core import paths
    except Exception as exc:
        return {"ok": False, "error": str(exc), "files": []}
    logs_dir = paths.repo_root() / "logs"
    if not logs_dir.exists():
        return {"ok": True, "files": []}
    rows: list[tuple[float, dict]] = []
    for p in logs_dir.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in (".jsonl", ".log", ".json"):
            continue
        try:
            stt = p.stat()
        except OSError:
            continue
        rel = p.relative_to(logs_dir).as_posix()
        rows.append((stt.st_mtime, {
            "path": rel,
            "size": stt.st_size,
            "mtime": stt.st_mtime,
            "t": _human_ago(stt.st_mtime),
        }))
    rows.sort(key=lambda r: -r[0])
    return {"ok": True, "files": [r[1] for r in rows]}


def load_recent_files() -> list[dict]:
    """Lista los archivos modificados más recientemente en las carpetas clave."""
    try:
        from cockpit.core import paths
    except Exception:
        return []

    targets = [
        ("Guiones", "Claude"),
        ("episodios", "runner"),
        ("escaletas", "Claude"),
        ("logs", "runner"),
    ]
    rows: list[tuple[float, dict]] = []
    for folder, default_by in targets:
        d = paths.repo_root() / folder
        if not d.exists():
            continue
        for p in d.rglob("*"):
            if not p.is_file():
                continue
            try:
                mtime = p.stat().st_mtime
            except OSError:
                continue
            rel = p.relative_to(paths.repo_root()).as_posix()
            rows.append((mtime, {
                "path": rel,
                "t": _human_ago(mtime),
                "by": default_by,
                "mtime": mtime,
            }))
    rows.sort(key=lambda r: -r[0])
    return [r[1] for r in rows[:8]]


def _human_ago(mtime: float) -> str:
    diff = time.time() - mtime
    if diff < 60:
        return f"hace {int(diff)} s"
    if diff < 3600:
        return f"hace {int(diff // 60)} min"
    if diff < 86400:
        return f"hace {int(diff // 3600)} h"
    return f"hace {int(diff // 86400)} d"


def load_live_procs() -> list[dict]:
    """Mejor esfuerzo: lista de procesos python relacionados con el repo."""
    try:
        import psutil
    except ImportError:
        return []

    try:
        from cockpit.core import paths
    except Exception:
        return []

    root_str = str(paths.repo_root()).lower()
    out = []
    for p in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
        try:
            cmdline = p.info.get("cmdline") or []
            if not cmdline:
                continue
            joined = " ".join(cmdline).lower()
            if "python" not in (p.info.get("name") or "").lower():
                continue
            if root_str not in joined and "generar_" not in joined and "validar_" not in joined:
                continue
            elapsed = int(time.time() - p.info["create_time"])
            h, rem = divmod(elapsed, 3600)
            m, s = divmod(rem, 60)
            short_cmd = " ".join(Path(c).name if "/" in c or "\\" in c else c for c in cmdline)
            out.append({
                "id": f"p{p.info['pid']}",
                "cmd": short_cmd[:80],
                "pid": p.info["pid"],
                "t": f"{h:02d}:{m:02d}:{s:02d}",
                "cost": "—",
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return out[:5]


def bootstrap_payload() -> dict:
    modules, episodes_ = scan_modules_and_episodes()
    return {
        "MODULES": modules,
        "EPISODES": episodes_,
        "LIVE_PROC": load_live_procs(),
        "RECENT_FILES": load_recent_files(),
        "TOKEN_DATA": load_ai_usage(),
        "ECONOMICS": load_economics(),
    }


# ---- AI chat ----------------------------------------------------------


def ai_chat(mode: str, target: str | None, message: str) -> dict:
    """Llama a improve_with_claude. Si falla (no key, no SDK), devuelve placeholder."""
    try:
        from cockpit.core import ai_client
    except Exception as exc:
        return {"ok": False, "text": f"AI client no disponible: {exc}", "usage": None}

    system_prompts = {
        "improve": (
            "Eres un asistente experto en producción de podcast educativo. "
            "Analiza el recurso indicado y propone mejoras concretas y aplicables. "
            "Responde en español, breve y accionable."
        ),
        "fix": (
            "Eres un ingeniero senior del pipeline de Maquinaria Pesada. "
            "Tienes el contexto de un fallo en producción. Diagnostica la causa "
            "más probable y propone los pasos concretos para arreglarlo, sin "
            "tocar el guion ni la escaleta a menos que sea necesario."
        ),
    }
    system = system_prompts.get(mode, system_prompts["improve"])
    target_line = f"Recurso: {target}\n\n" if target else ""
    user = f"{target_line}Petición del usuario:\n{message}"

    try:
        text, usage = ai_client.improve_with_claude(
            system=system,
            user=user,
            source=f"web_cockpit:{mode}",
            kind="improvement" if mode == "improve" else "fix",
            model="claude-haiku-4-5",
            max_tokens=600,
        )
        return {
            "ok": usage.ok,
            "text": text,
            "usage": {
                "model": usage.model,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cost_usd": usage.cost_usd,
                "latency_ms": usage.latency_ms,
            },
        }
    except Exception as exc:
        return {"ok": False, "text": f"[fallback] No se pudo contactar a Claude: {exc}", "usage": None}


# ---- Run pipeline -----------------------------------------------------


def reveal_path(rel: str) -> dict:
    """Abre `rel` (relativo a REPO_ROOT) en el explorador del SO.

    Validación estricta: solo paths dentro de REPO_ROOT, sin traversal.
    En tests devolvemos {ok: True, opened: false} sin invocar el SO."""
    try:
        from cockpit.core import paths
    except Exception as exc:
        return {"ok": False, "error": f"paths no disponible: {exc}"}

    root = paths.repo_root().resolve()
    target = (root / rel).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return {"ok": False, "error": "path fuera de REPO_ROOT"}
    if not target.exists():
        return {"ok": False, "error": f"no existe: {rel}"}

    if os.environ.get("COCKPIT_NO_SHELL"):
        return {"ok": True, "opened": False, "path": str(target)}

    try:
        if sys.platform == "win32":
            os.startfile(str(target))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            import subprocess
            subprocess.Popen(["open", str(target)])
        else:
            import subprocess
            subprocess.Popen(["xdg-open", str(target)])
        return {"ok": True, "opened": True, "path": str(target)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def topup_economics(provider: str, amount: float, note: str = "") -> dict:
    """Registra una recarga en logs/economics.json."""
    try:
        from cockpit.core import economics
    except Exception as exc:
        return {"ok": False, "error": f"economics no disponible: {exc}"}
    if not provider or amount <= 0:
        return {"ok": False, "error": "provider y amount>0 requeridos"}
    try:
        state = economics.add_topup(provider=provider, amount_usd=float(amount),
                                     note=note or "")
        return {
            "ok": True,
            "topups": len(state.topups),
            "last": {
                "provider": state.topups[-1].provider,
                "amount_usd": state.topups[-1].amount_usd,
                "timestamp": state.topups[-1].timestamp,
            },
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def ping_api_key(provider: str) -> dict:
    """Comprueba si la API key del proveedor está presente. No la valida
    contra la API remota (eso requeriría red y créditos)."""
    try:
        from cockpit.core import paths
    except Exception as exc:
        return {"ok": False, "error": f"paths no disponible: {exc}"}

    keys_by_provider = {
        "anthropic": ["ANTHROPIC_API_KEY"],
        "openai":    ["OPENAI_API_KEY"],
        "elevenlabs":["ELEVENLABS_API_KEY", "ELEVEN_API_KEY"],
        "kling":     ["KLING_API_KEY"],
        "spotify":   ["SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET"],
    }
    names = keys_by_provider.get(provider.lower())
    if not names:
        return {"ok": False, "error": f"proveedor desconocido: {provider}"}

    found = []
    for n in names:
        if os.environ.get(n):
            found.append({"name": n, "from": "env"})
    if len(found) < len(names):
        env_path = paths.env_file()
        if env_path.exists():
            try:
                from dotenv import dotenv_values
                values = dotenv_values(env_path)
                for n in names:
                    if values.get(n) and not any(f["name"] == n for f in found):
                        found.append({"name": n, "from": ".env"})
            except ImportError:
                pass
    return {
        "ok": len(found) == len(names),
        "provider": provider,
        "expected": names,
        "found": found,
    }


def launch_pipeline(script: str, flags: list) -> dict:
    """Lanza un script python en background sin bloquear el server."""
    try:
        from cockpit.core import paths, runner
    except Exception as exc:
        _log.error(f"launch_pipeline: runner no disponible: {exc!r}")
        return {"ok": False, "error": f"runner no disponible: {exc}"}

    script_path = paths.repo_root() / script
    if not script_path.exists():
        _log.warning(f"launch_pipeline: script no existe: {script}")
        return {"ok": False, "error": f"script no existe: {script}"}

    argv = runner.build_argv(str(script_path), list(flags or []))
    log_dir = paths.logs_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"web_run_{int(time.time())}.log"

    import subprocess
    f = log_path.open("w", encoding="utf-8")
    proc = subprocess.Popen(
        argv,
        cwd=str(paths.repo_root()),
        stdout=f,
        stderr=subprocess.STDOUT,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    _log.info(f"pipeline lanzado: {script} flags={list(flags or [])} "
              f"pid={proc.pid} log={log_path.name}")
    return {"ok": True, "pid": proc.pid, "cmd": argv, "log": log_path.name}


# ---- Generación de guion por episodio ---------------------------------
# El parseo de la traza vive en cockpit.core.gen_log; aquí solo el glue HTTP
# (resolver fuente + lanzar el proceso en background).


def generate_episode_guion(ep_id: str) -> dict:
    """Lanza la generación del guion de UN episodio concreto.

    Resuelve el PDF + script vía cockpit.core.episode_sources y redirige la
    salida (que incluye la traza de validación y regeneración) a la ruta
    determinista Guiones/logs/{ep_id}_gen.log."""
    try:
        from cockpit.core import episode_sources, gen_log, paths, runner
    except Exception as exc:
        return {"ok": False, "error": f"módulos no disponibles: {exc}"}

    src = episode_sources.source_for(ep_id)
    if src is None:
        return {"ok": False, "error": f"episodio sin fuente configurada: {ep_id}"}

    script_path = paths.repo_root() / src.script
    if not script_path.exists():
        return {"ok": False, "error": f"script no existe: {src.script}"}

    argv = runner.build_argv(str(script_path), list(src.flags))
    log_path = gen_log.gen_log_path(src.ep_id)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    import subprocess
    f = log_path.open("w", encoding="utf-8")
    proc = subprocess.Popen(
        argv,
        cwd=str(paths.repo_root()),
        stdout=f,
        stderr=subprocess.STDOUT,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    return {
        "ok": True,
        "ep_id": src.ep_id,
        "kind": src.kind,
        "pdf": src.pdf,
        "pid": proc.pid,
        "cmd": argv,
        "log": log_path.name,
    }


def read_gen_log(ep_id: str) -> dict:
    """Lee y parsea la traza de generación/validación de un episodio.

    Adaptador fino sobre cockpit.core.gen_log.read para el endpoint HTTP."""
    try:
        from cockpit.core import gen_log
    except Exception as exc:
        return {"ok": False, "ep_id": ep_id, "exists": False,
                "error": f"gen_log no disponible: {exc}"}
    return gen_log.read(ep_id)


def frontend_log(body: dict) -> dict:
    """Registra en la bitácora central un evento/error enviado por el front JS.

    Body: {level, message, ...contexto}. `level` ∈ {debug,info,warn,error}
    (por defecto info). Cualquier clave extra (url, componente, stack…) se
    anexa al mensaje como contexto.
    """
    level = str(body.get("level", "info")).strip().lower()
    message = str(body.get("message", "")).strip()
    if not message:
        return {"ok": False, "error": "message requerido"}
    ctx = {k: v for k, v in body.items() if k not in ("level", "message")}
    if ctx:
        message = f"{message} | {ctx}"
    emit = {
        "error": _frontend_log.error,
        "warn": _frontend_log.warning,
        "warning": _frontend_log.warning,
        "debug": _frontend_log.debug,
    }.get(level, _frontend_log.info)
    emit(message[:1500])
    return {"ok": True}


# ---- HTTP handler -----------------------------------------------------


class CockpitHandler(BaseHTTPRequestHandler):
    server_version = "MaquinariaCockpit/0.1"

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # Silencioso por defecto; activa con --verbose
        if getattr(self.server, "verbose", False):
            super().log_message(format, *args)

    # ---- JSON helpers ----
    def _send_json(self, status: int, payload) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, rel: str) -> None:
        # Normalizar y prevenir traversal
        if rel.startswith("/"):
            rel = rel[1:]
        if rel == "":
            rel = "index.html"
        candidate = (WEB_DIR / rel).resolve()
        try:
            candidate.relative_to(WEB_DIR.resolve())
        except ValueError:
            self.send_error(403, "forbidden")
            return
        if not candidate.exists() or not candidate.is_file():
            self.send_error(404, f"not found: {rel}")
            return
        ctype, _ = mimetypes.guess_type(candidate.name)
        if ctype is None:
            ctype = "application/octet-stream"
        data = candidate.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _safe_500(self, exc: Exception) -> None:
        """Devuelve un 500 JSON sin reventar si la conexión ya se cerró."""
        try:
            self._send_json(500, {"ok": False, "error": "internal",
                                  "detail": str(exc)})
        except Exception:  # noqa: BLE001
            pass

    # ---- Routes ----
    def do_GET(self) -> None:  # noqa: N802
        try:
            self._handle_get()
        except Exception as exc:  # noqa: BLE001 - todo error de request va al log
            _log.error(f"GET {urlparse(self.path).path} → "
                       f"{type(exc).__name__}: {exc}")
            self._safe_500(exc)

    def _handle_get(self) -> None:
        path = urlparse(self.path).path

        if path == "/api/health":
            return self._send_json(200, {"ok": True, "ts": time.time()})
        if path == "/api/bootstrap":
            return self._send_json(200, bootstrap_payload())
        if path == "/api/episodes":
            _, eps = scan_modules_and_episodes()
            return self._send_json(200, eps)
        if path.startswith("/api/episode/") and path.endswith("/gen-log"):
            ep_id = path[len("/api/episode/"):-len("/gen-log")]
            return self._send_json(200, read_gen_log(ep_id))
        if path.startswith("/api/episode/") and path.endswith("/checks"):
            ep_id = path[len("/api/episode/"):-len("/checks")]
            return self._send_json(200, load_episode_checks(ep_id))
        if path.startswith("/api/episode/"):
            ep_id = path[len("/api/episode/"):]
            detail = load_episode_detail(ep_id)
            if detail is None:
                return self._send_json(404, {"error": "not found"})
            return self._send_json(200, detail)
        if path == "/api/ai-usage":
            return self._send_json(200, load_ai_usage())
        if path == "/api/economics":
            return self._send_json(200, load_economics())
        if path == "/api/optimization":
            return self._send_json(200, load_optimization())
        if path == "/api/components-map":
            return self._send_json(200, load_components_map())
        if path == "/api/connectors":
            return self._send_json(200, load_connectors())
        if path == "/api/pizarra":
            return self._send_json(200, load_pizarra())
        if path == "/api/metrics":
            return self._send_json(200, load_metrics())
        if path == "/api/logs":
            return self._send_json(200, load_logs_list())
        if path == "/api/live":
            return self._send_json(200, load_live_procs())
        if path == "/api/recent-files":
            return self._send_json(200, load_recent_files())

        # Archivos del repo (PDFs, Guiones, audio, logs)
        if path.startswith("/files/"):
            return self._send_repo_file(path[len("/files/"):])

        # Static (web/dist o web/legacy)
        return self._send_static(path)

    def do_POST(self) -> None:  # noqa: N802
        try:
            self._handle_post()
        except Exception as exc:  # noqa: BLE001 - todo error de request va al log
            _log.error(f"POST {urlparse(self.path).path} → "
                       f"{type(exc).__name__}: {exc}")
            self._safe_500(exc)

    def _handle_post(self) -> None:
        path = urlparse(self.path).path
        body = self._read_json()

        if path == "/api/ai/chat":
            mode = body.get("mode", "improve")
            target = body.get("target")
            message = body.get("message", "")
            return self._send_json(200, ai_chat(mode, target, message))

        if path == "/api/run":
            script = body.get("script", "")
            flags = body.get("flags", [])
            return self._send_json(200, launch_pipeline(script, flags))

        if path.startswith("/api/episode/") and path.endswith("/generate"):
            ep_id = path[len("/api/episode/"):-len("/generate")]
            return self._send_json(200, generate_episode_guion(ep_id))

        if path == "/api/pizarra":
            return self._send_json(200, save_pizarra(body))

        if path == "/api/pizarra/generate-component":
            return self._send_json(200, pizarra_generate_component(
                body.get("name", ""), body.get("description", ""),
                body.get("kind", "ai"),
            ))

        if path == "/api/reveal":
            return self._send_json(200, reveal_path(body.get("path", "")))

        if path == "/api/economics/topup":
            return self._send_json(200, topup_economics(
                provider=body.get("provider", ""),
                amount=float(body.get("amount", 0) or 0),
                note=body.get("note", ""),
            ))

        if path == "/api/api-key/ping":
            return self._send_json(200, ping_api_key(body.get("provider", "")))

        if path == "/api/log":
            return self._send_json(200, frontend_log(body))

        return self._send_json(404, {"error": "route not found"})

    # ---- repo files ----
    def _send_repo_file(self, rel: str) -> None:
        """Sirve archivos dentro de REPO_ROOT como solo lectura."""
        try:
            from cockpit.core import paths
        except Exception:
            self.send_error(500, "paths no disponible")
            return
        root = paths.repo_root().resolve()
        # Permitir lectura solo de carpetas conocidas
        allowed_prefixes = ("PDFs", "Guiones", "escaletas", "episodios",
                            "videopodcast", "Videos", "logs", "output", "RRSS")
        if not rel or not any(rel.startswith(p + "/") or rel == p for p in allowed_prefixes):
            self.send_error(403, "carpeta no permitida")
            return
        candidate = (root / rel).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            self.send_error(403, "fuera de REPO_ROOT")
            return
        if not candidate.exists() or not candidate.is_file():
            self.send_error(404, "no encontrado")
            return
        ctype, _ = mimetypes.guess_type(candidate.name)
        if ctype is None:
            ctype = "application/octet-stream"
        data = candidate.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)


def run(host: str = "127.0.0.1", port: int = 8765, verbose: bool = False) -> None:
    if not WEB_DIR.exists():
        raise SystemExit(
            f"build del frontend no existe: {WEB_DIR}\n"
            "  Ejecuta:  cd vite_app && npm install && npm run build"
        )
    server = ThreadingHTTPServer((host, port), CockpitHandler)
    server.verbose = verbose  # type: ignore[attr-defined]
    print(f"Cockpit web en http://{host}:{port}/")
    print(f"  static : {WEB_DIR}")
    print("  API    : /api/bootstrap, /api/ai/chat, /api/run …")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrando…")
        server.server_close()


def main() -> None:
    ap = argparse.ArgumentParser(description="Cockpit web (React + API JSON)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    run(host=args.host, port=args.port, verbose=args.verbose)


if __name__ == "__main__":
    # Bitácora diaria centralizada (logs/run/). Si daylog fallara, el servidor
    # sigue igual gracias al nullcontext de respaldo.
    import sys as _sys
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="web_server.py", params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        main()
