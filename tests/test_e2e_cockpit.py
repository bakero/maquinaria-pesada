"""Tests E2E del cockpit web con Playwright.

Levanta `web_server.CockpitHandler` en un thread con REPO_ROOT temporal y
abre Chromium headless para validar la navegación, el bootstrap real
desde /api/bootstrap, el AIDrawer, y el Lanzador.

Para correr solo estos:
    pytest tests/test_e2e_cockpit.py -v

Requisitos:
    pip install pytest-playwright playwright
    playwright install chromium
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


# ---- Fake repo & live server ------------------------------------------


@pytest.fixture
def fake_repo(tmp_path, monkeypatch):
    """REPO_ROOT temporal con un episodio M3 fake y un evento de uso IA."""
    for d in ("Guiones", "PDFs", "PDFs/temas", "episodios", "escaletas",
              "Videos", "logs"):
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    (tmp_path / "Guiones" / "M3_Transformers.txt").write_text("hola", encoding="utf-8")
    (tmp_path / "Guiones" / "M0_Cimientos.txt").write_text("hola", encoding="utf-8")
    (tmp_path / "PDFs" / "M3_T_Transformers.pdf").write_bytes(b"%PDF-1.4")
    (tmp_path / "episodios" / "M0.mp3").write_bytes(b"\x00" * 16)
    (tmp_path / "escaletas" / "M0_intro.md").write_text("# M0", encoding="utf-8")
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
    monkeypatch.setenv("COCKPIT_WEB_DIR", "legacy")
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


# ---- Playwright config ------------------------------------------------


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    # Babel-standalone tarda en compilar JSX inline; necesitamos timeouts altos
    return {**browser_context_args, "viewport": {"width": 1400, "height": 900}}


def _wait_for_app(page, url: str) -> None:
    """Navega y espera a que la app monte (con bootstrap real o fixtures)."""
    page.goto(url, wait_until="domcontentloaded")
    # La sidebar aparece tras montaje de App + babel transform
    page.wait_for_selector(".sb-brand", timeout=20_000)


# ---- Tests ------------------------------------------------------------


def test_app_mounts_and_bootstrap_succeeds(page, live_url):
    _wait_for_app(page, live_url)
    # bootstrap real debe haber poblado window.__BOOTSTRAP_OK__
    ok = page.evaluate("() => window.__BOOTSTRAP_OK__")
    assert ok is True


def test_sidebar_has_15_wired_items(page, live_url):
    _wait_for_app(page, live_url)
    items = page.locator(".sb-item")
    assert items.count() == 15


def test_navigate_master_shows_modules_from_backend(page, live_url):
    _wait_for_app(page, live_url)
    # En el sidebar, "Master" es el item #01
    page.locator(".sb-item", has_text="Master").first.click()
    page.wait_for_url(lambda u: "master" in u, timeout=5_000)
    # Debe haber un módulo M3 visible en la página
    page.wait_for_selector("text=M3", timeout=5_000)
    # MODULES en window debe venir del backend (15 módulos)
    n_modules = page.evaluate("() => window.MODULES.length")
    assert n_modules == 15


def test_topbar_opens_ai_drawer_and_calls_backend(page, live_url):
    _wait_for_app(page, live_url)
    # Captura el POST al backend
    posted = []
    page.on("request", lambda r: posted.append(r.url) if r.method == "POST" else None)

    page.get_by_role("button", name="Mejorar con IA").first.click()
    page.wait_for_selector(".drawer.open", timeout=3_000)
    page.locator(".ai-input").fill("¿qué tal va?")
    page.get_by_role("button", name="Enviar").click()
    # Esperar a que el send termine (1.5s de margen para el typewriter+request)
    page.wait_for_timeout(2_000)
    assert any("/api/ai/chat" in u for u in posted), f"no POST a /api/ai/chat: {posted}"


def test_lanzador_posts_to_run_endpoint(page, live_url):
    _wait_for_app(page, live_url)
    page.locator(".sb-item", has_text="Lanzador").first.click()
    page.wait_for_selector("text=Comando generado", timeout=5_000)

    posted = []
    page.on("response", lambda r: posted.append(r.url) if "/api/run" in r.url else None)

    page.get_by_role("button", name="Ejecutar").click()
    page.wait_for_timeout(1500)
    assert any("/api/run" in u for u in posted), f"no se llamó /api/run: {posted}"


def test_bootstrap_endpoint_returns_real_modules(page, live_url):
    response = page.request.get(f"{live_url}/api/bootstrap")
    assert response.ok
    data = response.json()
    assert len(data["MODULES"]) == 15
    m3 = next(m for m in data["MODULES"] if m["id"] == "M3")
    assert m3["pct"] > 0  # tiene guion + pdf, debe progresar


def test_token_data_reflects_real_log(page, live_url):
    response = page.request.get(f"{live_url}/api/ai-usage")
    assert response.ok
    td = response.json()
    assert td["total_30d"] == 150  # 100 input + 50 output
    assert any(m["model"] == "claude-haiku-4-5" for m in td["byModel"])


def test_static_assets_load(page, live_url):
    _wait_for_app(page, live_url)
    # Comprobar que styles.css cargó (color de fondo del body)
    bg = page.evaluate("() => getComputedStyle(document.body).backgroundColor")
    assert bg and bg != "rgba(0, 0, 0, 0)"


def test_no_dead_buttons_in_master(page, live_url):
    """Master no debe tener ningún botón visible sin handler de click.

    Comprobación dinámica: para cada <button> visible en la página,
    verifica que tenga al menos un listener (React añade el handler en el
    nodo, así que comprobamos `onclick` o cualquier propiedad React)."""
    _wait_for_app(page, live_url)
    page.locator(".sb-item", has_text="Master").first.click()
    page.wait_for_url(lambda u: "master" in u, timeout=5_000)
    page.wait_for_timeout(300)
    n_dead = page.evaluate("""
        () => {
          const buttons = Array.from(document.querySelectorAll('button.btn'));
          return buttons.filter(b => {
            if (b.disabled) return false;
            const key = Object.keys(b).find(k => k.startsWith('__reactProps'));
            if (!key) return false;
            return !b[key].onClick;
          }).map(b => b.textContent.trim()).filter(Boolean);
        }
    """)
    assert n_dead == [], f"Botones sin onClick en Master: {n_dead}"


def test_modulo_action_buttons_navigate_or_open_ai(page, live_url):
    """En la página Módulo, los botones de acciones deben navegar o
    disparar el AI drawer, nunca quedarse mudos."""
    _wait_for_app(page, live_url)
    # Navegar a Módulo vía sidebar (cambiar hash no re-renderea sin handler)
    page.locator(".sb-item", has_text="Módulo").first.click()
    page.wait_for_url(lambda u: "modulo" in u, timeout=5_000)
    page.wait_for_timeout(400)
    # "Regenerar guion (todos)" debe navegar a lanzador
    btn = page.get_by_role("button", name="Regenerar guion (todos)")
    btn.click()
    page.wait_for_url(lambda u: "lanzador" in u, timeout=5_000)


def test_topup_button_calls_economics_endpoint(page, live_url):
    """Registrar recarga llama a /api/economics/topup tras los prompts."""
    _wait_for_app(page, live_url)
    page.locator(".sb-item", has_text="Consumo").first.click()
    page.wait_for_url(lambda u: "consumo" in u, timeout=5_000)
    page.wait_for_timeout(400)
    # Cambia a la tab "saldo" donde está el botón
    page.locator(".tab", has_text="Saldos").first.click()
    page.wait_for_timeout(200)

    posted = []
    page.on("request", lambda r: posted.append(r.url) if "/api/economics/topup" in r.url else None)

    # Stub de window.prompt para no bloquear el test
    page.evaluate("""
        () => {
          window.prompt = (msg) => {
            if (msg.toLowerCase().includes('proveedor')) return 'anthropic';
            if (msg.toLowerCase().includes('importe')) return '10';
            return 'test';
          };
          window.alert = () => {};
          // Evita el reload que ejecuta el handler tras OK
          const origReload = window.location.reload;
          window.location.reload = () => {};
        }
    """)
    page.get_by_role("button", name="Registrar recarga").click()
    page.wait_for_timeout(1500)
    assert any("/api/economics/topup" in u for u in posted), f"no POST a topup: {posted}"
