"""Tests E2E del bundle Vite + TS (web/dist/).

Solo corren si `web/dist/index.html` existe (es decir, si `cd vite_app
&& npm run build` se ha ejecutado). En CI fresca sin Node, se skipean
con un mensaje claro.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DIST_INDEX = ROOT / "web" / "dist" / "index.html"

pytestmark = pytest.mark.skipif(
    not DIST_INDEX.exists(),
    reason="web/dist/index.html no existe — corre 'cd vite_app && npm run build' primero",
)


@pytest.fixture
def fake_repo(tmp_path, monkeypatch):
    for d in ("Guiones", "PDFs", "episodios", "escaletas", "logs"):
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    (tmp_path / "Guiones" / "M3_Transformers.txt").write_text("hola", encoding="utf-8")
    (tmp_path / "PDFs" / "M3_T_Transformers.pdf").write_bytes(b"%PDF")
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
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    monkeypatch.setenv("COCKPIT_WEB_DIR", "dist")
    for mod in list(sys.modules):
        if mod.startswith("cockpit.core") or mod == "web_server":
            del sys.modules[mod]
    yield tmp_path


@pytest.fixture
def live_url(fake_repo):
    import web_server
    server = ThreadingHTTPServer(("127.0.0.1", 0), web_server.CockpitHandler)
    server.verbose = False  # type: ignore[attr-defined]
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()


def test_dist_index_served(live_url, page):
    page.goto(live_url, wait_until="networkidle")
    # El index Vite carga main.tsx y monta <App/>
    page.wait_for_selector(".kpi-grid, .loading", timeout=10_000)
    # Tras el fetch a /api/bootstrap deberían aparecer los KPIs
    page.wait_for_selector(".kpi", timeout=10_000)
    kpis = page.locator(".kpi")
    assert kpis.count() >= 3


def test_dist_uses_real_backend_data(live_url, page):
    page.goto(live_url, wait_until="networkidle")
    page.wait_for_selector(".kpi", timeout=10_000)
    # M3 debe aparecer en la lista de módulos (tiene guion+pdf en fake_repo)
    page.wait_for_selector("text=M3", timeout=5_000)


def test_dist_assets_have_hashed_names(live_url, page):
    """Verifica que el build de Vite genera nombres con hash (cache-busting)."""
    response = page.request.get(f"{live_url}/")
    html = response.text()
    assert "/assets/" in html
    # Vite usa patrón [name]-[hash].{js,css}
    import re
    assert re.search(r"/assets/index-[A-Za-z0-9_-]+\.js", html)
