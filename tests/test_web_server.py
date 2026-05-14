"""Tests del servidor web (web_server.py).

Cubre los handlers JSON y la entrega de estáticos sin red, usando un
REPO_ROOT temporal para aislar de los datos reales del repo.
"""
from __future__ import annotations

import json
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def fake_repo(tmp_path, monkeypatch):
    """Crea un REPO_ROOT mínimo con un episodio M3 fake."""
    (tmp_path / "Guiones").mkdir()
    (tmp_path / "Guiones" / "M3_Transformers.txt").write_text("hola", encoding="utf-8")
    (tmp_path / "PDFs").mkdir()
    (tmp_path / "PDFs" / "M3_T_Transformers.pdf").write_bytes(b"%PDF-1.4")
    (tmp_path / "episodios").mkdir()
    (tmp_path / "escaletas").mkdir()
    (tmp_path / "Videos").mkdir()
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "ai_usage.jsonl").write_text(
        json.dumps({
            "timestamp": "2026-05-12T10:00:00",
            "kind": "improvement",
            "provider": "anthropic",
            "model": "claude-haiku-4-5",
            "source": "test",
            "input_tokens": 100,
            "output_tokens": 50,
            "cost_usd": 0.001,
            "latency_ms": 500,
            "ok": True,
        }) + "\n",
        encoding="utf-8",
    )
    # build de Vite fake: el server sirve estáticos desde aquí
    web_dist = tmp_path / "vite_app" / "dist"
    web_dist.mkdir(parents=True)
    (web_dist / "index.html").write_text(
        "<!doctype html><html><head><title>Maquinaria Pesada · Cockpit</title>"
        "</head><body><div id=\"root\"></div></body></html>",
        encoding="utf-8",
    )
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    monkeypatch.setenv("COCKPIT_WEB_DIR", str(web_dist))
    # invalidar módulos cacheados que dependen de REPO_ROOT / WEB_DIR
    for mod in list(sys.modules):
        if mod.startswith("cockpit.core") or mod == "web_server":
            del sys.modules[mod]
    yield tmp_path


def test_bootstrap_payload_structure(fake_repo):
    import web_server
    payload = web_server.bootstrap_payload()
    assert "MODULES" in payload
    assert "EPISODES" in payload
    assert "TOKEN_DATA" in payload
    assert len(payload["MODULES"]) == 15
    # M3 debería estar marcado con algún progreso (tiene guion + pdf)
    m3 = next(m for m in payload["MODULES"] if m["id"] == "M3")
    assert m3["pct"] > 0


def test_ai_usage_aggregation(fake_repo):
    import web_server
    td = web_server.load_ai_usage()
    assert td["total_30d"] == 150
    assert td["cost_30d"] == pytest.approx(0.001, rel=1e-3) or td["cost_30d"] == 0.0
    assert any(m["model"] == "claude-haiku-4-5" for m in td["byModel"])


def test_episodes_endpoint_includes_state(fake_repo):
    import web_server
    _, eps = web_server.scan_modules_and_episodes()
    m3 = next((e for e in eps if e["id"] == "M3"), None)
    assert m3 is not None
    assert m3["state"]["guion"] == "ok"
    assert m3["state"]["pdf"] == "ok"
    assert m3["state"]["audio"] == "empty"


def test_economics_empty(fake_repo):
    import web_server
    eco = web_server.load_economics()
    assert eco["topups"] == []
    assert eco["balance_by_provider"] == {}


def test_optimization_returns_recommendations(fake_repo):
    """load_optimization analiza los eventos reales de ai_usage.jsonl."""
    import web_server
    out = web_server.load_optimization()
    assert out["ok"] is True
    assert "recommendations" in out
    assert isinstance(out["recommendations"], list)
    assert "total_savings_usd" in out
    assert out["events_analyzed"] >= 1


def test_components_map_loads(fake_repo):
    """load_components_map devuelve el grafo (default si no hay json)."""
    import web_server
    out = web_server.load_components_map()
    assert out["ok"] is True
    assert isinstance(out["nodes"], list)
    assert isinstance(out["edges"], list)


def test_economics_includes_summary(fake_repo):
    import web_server
    eco = web_server.load_economics()
    assert "summary" in eco
    assert isinstance(eco["summary"], dict)


def test_connectors_returns_registry(fake_repo):
    """load_connectors itera el REGISTRY real y devuelve su .status()."""
    import web_server
    out = web_server.load_connectors()
    assert out["ok"] is True
    assert len(out["connectors"]) > 0
    cats = {c["category"] for c in out["connectors"]}
    assert cats <= {"service", "pipeline", "source"}
    for c in out["connectors"]:
        assert "status" in c and "ok" in c["status"]


def test_logs_list(fake_repo):
    """load_logs_list lista los archivos reales de logs/."""
    import web_server
    out = web_server.load_logs_list()
    assert out["ok"] is True
    paths_ = [f["path"] for f in out["files"]]
    assert "ai_usage.jsonl" in paths_


def test_ai_chat_fallback_no_key(fake_repo, monkeypatch):
    """Sin ANTHROPIC_API_KEY ni paquete real, devuelve ok:false sin crashear."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import web_server
    out = web_server.ai_chat("improve", "M3", "¿cómo mejoro el guion?")
    assert "ok" in out
    assert "text" in out


def test_launch_pipeline_nonexistent_script(fake_repo):
    import web_server
    out = web_server.launch_pipeline("scripts/no_existe.py", [])
    assert out["ok"] is False


def test_generate_episode_unknown(fake_repo):
    import web_server
    out = web_server.generate_episode_guion("M999")
    assert out["ok"] is False
    assert "fuente" in out["error"]


def test_generate_episode_resolves_but_script_missing(fake_repo):
    """El fake_repo no tiene generar_guion.py: resuelve la fuente pero no lanza."""
    import web_server
    out = web_server.generate_episode_guion("M3")
    assert out["ok"] is False
    assert "script no existe" in out["error"]


def test_read_gen_log_missing(fake_repo):
    import web_server
    out = web_server.read_gen_log("M3")
    assert out["ok"] is False
    assert out["exists"] is False


def test_read_gen_log_parses_trace(fake_repo):
    import web_server
    log_dir = fake_repo / "Guiones" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "M3_gen.log").write_text(
        "  [3/4] Generando guion (intento 1/3)...\n"
        "         Issues hard: 1 | soft: 2\n"
        "         [HARD] M3 tiene 900 palabras (minimo: 1200)\n"
        "         [WARN] bloque 4 con solo 2 frases\n"
        "         [WARN] CTA ausente\n"
        "  [3/4] Generando guion (intento 2/3)...\n"
        "         [PASS] Validacion OK\n"
        "  [4/4] Guardando guion...\n"
        "  GUION GENERADO : Guiones/M3_x.txt\n",
        encoding="utf-8",
    )
    out = web_server.read_gen_log("M3")
    assert out["ok"] is True
    assert out["exists"] is True
    assert out["attempts"] == 2
    assert out["verdict"] == "ok"
    assert out["saved"] is True
    assert len(out["hard_issues"]) == 1
    assert len(out["soft_issues"]) == 2


def test_reveal_blocks_traversal(fake_repo, monkeypatch):
    monkeypatch.setenv("COCKPIT_NO_SHELL", "1")
    import web_server
    out = web_server.reveal_path("../etc/passwd")
    assert out["ok"] is False


def test_reveal_blocks_nonexistent(fake_repo, monkeypatch):
    monkeypatch.setenv("COCKPIT_NO_SHELL", "1")
    import web_server
    out = web_server.reveal_path("no/existe.txt")
    assert out["ok"] is False


def test_reveal_allows_existing_path(fake_repo, monkeypatch):
    monkeypatch.setenv("COCKPIT_NO_SHELL", "1")
    import web_server
    out = web_server.reveal_path("Guiones")
    assert out["ok"] is True
    assert out["opened"] is False  # NO_SHELL: no se invoca al SO


def test_topup_economics_records(fake_repo):
    import web_server
    out = web_server.topup_economics("anthropic", 25.0, "test recarga")
    assert out["ok"] is True
    assert out["topups"] >= 1
    # leer de vuelta
    eco = web_server.load_economics()
    assert eco["balance_by_provider"].get("anthropic", 0) == 25.0


def test_topup_economics_rejects_invalid(fake_repo):
    import web_server
    assert web_server.topup_economics("", 10).get("ok") is False
    assert web_server.topup_economics("anthropic", 0).get("ok") is False
    assert web_server.topup_economics("anthropic", -5).get("ok") is False


def test_ping_api_key_unknown_provider(fake_repo, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import web_server
    out = web_server.ping_api_key("inventado")
    assert out["ok"] is False


def test_ping_api_key_finds_env(fake_repo, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    import web_server
    out = web_server.ping_api_key("anthropic")
    assert out["ok"] is True
    assert any(f["from"] == "env" for f in out["found"])


def test_files_endpoint_serves_repo_file(live_server, fake_repo):
    import urllib.request
    with urllib.request.urlopen(
        live_server + "/files/Guiones/M3_Transformers.txt", timeout=2,
    ) as r:
        assert r.read() == b"hola"


def test_files_endpoint_blocks_outside_allowed(live_server):
    import urllib.error
    import urllib.request
    try:
        urllib.request.urlopen(live_server + "/files/.env", timeout=2)
        raise AssertionError("debería bloquear")
    except urllib.error.HTTPError as e:
        assert e.code in (403, 404)


def test_files_endpoint_blocks_traversal(live_server):
    import urllib.error
    import urllib.request
    try:
        urllib.request.urlopen(live_server + "/files/PDFs/../../pyproject.toml", timeout=2)
        raise AssertionError("traversal no bloqueado")
    except urllib.error.HTTPError as e:
        assert e.code in (400, 403, 404)


# ---- Integration: lanzar servidor en thread y hacer requests ----------


@pytest.fixture
def live_server(fake_repo):
    """Levanta web_server.run en un thread y devuelve la URL base."""
    from http.server import ThreadingHTTPServer

    import web_server

    server = ThreadingHTTPServer(("127.0.0.1", 0), web_server.CockpitHandler)
    server.verbose = False  # type: ignore[attr-defined]
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    # warm up
    time.sleep(0.05)
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=2) as r:
        return json.loads(r.read().decode("utf-8"))


def test_live_health(live_server):
    out = _get_json(live_server + "/api/health")
    assert out["ok"] is True


def test_live_bootstrap(live_server):
    out = _get_json(live_server + "/api/bootstrap")
    assert "MODULES" in out
    assert "EPISODES" in out


def test_live_static_html(live_server):
    with urllib.request.urlopen(live_server + "/", timeout=2) as r:
        body = r.read().decode("utf-8")
    assert "<html" in body.lower()
    assert "Maquinaria Pesada" in body or "maquinaria pesada" in body.lower()


def test_live_traversal_blocked(live_server):
    """Pedir ../pyproject.toml debe devolver 403 o 404, nunca 200."""
    try:
        urllib.request.urlopen(live_server + "/../pyproject.toml", timeout=2)
        raise AssertionError("traversal no bloqueado")
    except urllib.error.HTTPError as e:
        assert e.code in (400, 403, 404)


# ---- Logging del frontend (POST /api/log) -----------------------------


def _post_json(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=2) as r:
        return json.loads(r.read().decode("utf-8"))


def test_frontend_log_records(fake_repo):
    import web_server
    out = web_server.frontend_log({"level": "error", "message": "fallo en el front",
                                   "url": "/episodios", "componente": "Modulo"})
    assert out["ok"] is True


def test_frontend_log_requires_message(fake_repo):
    import web_server
    assert web_server.frontend_log({"level": "info"}).get("ok") is False
    assert web_server.frontend_log({"message": "   "}).get("ok") is False


def test_live_api_log_endpoint(live_server):
    out = _post_json(live_server + "/api/log",
                     {"level": "warn", "message": "evento de prueba del front"})
    assert out["ok"] is True


def test_live_api_log_rejects_empty(live_server):
    out = _post_json(live_server + "/api/log", {"level": "info"})
    assert out["ok"] is False
