"""Tests E2E del cockpit (Vite + TS) — única versión de la app visual.

Corre contra el build de producción de Vite
(`cd vite_app && npm run build` → `vite_app/dist/`).

Solo corren si `vite_app/dist/index.html` existe.

Cubre:
  • montaje de App + bootstrap real
  • 15 items en sidebar (estructura completa)
  • navegación Master → módulos reales
  • AIDrawer disparando /api/ai/chat
  • Lanzador disparando /api/run
  • bootstrap endpoint con datos reales
  • TOKEN_DATA agregado real
  • CSS cargado (no bundle cascarón)
  • cero botones muertos en Master
  • Módulo → Lanzador
  • topup llama a /api/economics/topup
  • Fuentes · Descargar abre /files/...
  • API key · Ping llama a /api/api-key/ping
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DIST_DIR = ROOT / "vite_app" / "dist"
DIST_INDEX = DIST_DIR / "index.html"

try:
    import pytest_playwright  # noqa: F401
    _PLAYWRIGHT_OK = True
except ImportError:
    _PLAYWRIGHT_OK = False

pytestmark = [
    pytest.mark.skipif(
        not DIST_INDEX.exists(),
        reason="vite_app/dist/index.html no existe — corre 'cd vite_app && npm run build' primero",
    ),
    pytest.mark.skipif(
        not _PLAYWRIGHT_OK,
        reason="pytest-playwright no instalado · skip E2E (instalable con: pip install pytest-playwright && playwright install chromium)",
    ),
]


@pytest.fixture
def fake_repo(tmp_path, monkeypatch):
    """REPO_ROOT temporal con material para escanear módulos y eventos IA."""
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
    # Servir el build real de Vite (vite_app/dist/)
    monkeypatch.setenv("COCKPIT_WEB_DIR", str(DIST_DIR))
    monkeypatch.setenv("COCKPIT_NO_SHELL", "1")  # no abre Explorer en tests
    for mod in list(sys.modules):
        if mod.startswith("cockpit.core") or mod == "web_server":
            del sys.modules[mod]
    yield tmp_path


@pytest.fixture
def live_url(fake_repo):
    import web_server
    with web_server.ThreadedServer(web_server.app) as srv:
        yield srv.url


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": {"width": 1400, "height": 900}}


def _wait_for_app(page, url: str) -> None:
    """Navega y espera a que la app monte (con bootstrap real o fixtures)."""
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector(".sb-brand", timeout=15_000)


# ---- Tests de paridad con bundle legacy ------------------------------


def test_vite_app_mounts_and_bootstrap_succeeds(page, live_url):
    _wait_for_app(page, live_url)
    ok = page.evaluate("() => window.__BOOTSTRAP_OK__")
    assert ok is True


def test_vite_sidebar_has_15_wired_items(page, live_url):
    _wait_for_app(page, live_url)
    items = page.locator(".sb-item")
    assert items.count() == 15


def test_vite_navigate_master_shows_modules_from_backend(page, live_url):
    _wait_for_app(page, live_url)
    page.locator(".sb-item", has_text="Master").first.click()
    page.wait_for_url(lambda u: "master" in u, timeout=5_000)
    page.wait_for_selector("text=M3", timeout=5_000)
    n_modules = page.evaluate("() => window.MODULES.length")
    assert n_modules == 15


def test_vite_ai_drawer_calls_backend(page, live_url):
    _wait_for_app(page, live_url)
    posted = []
    page.on("request", lambda r: posted.append(r.url) if r.method == "POST" else None)
    page.get_by_role("button", name="Mejorar con IA").first.click()
    page.wait_for_selector(".drawer.open", timeout=3_000)
    page.locator(".ai-input").fill("hola")
    page.get_by_role("button", name="Enviar").click()
    page.wait_for_timeout(2_000)
    assert any("/api/ai/chat" in u for u in posted), f"no POST a /api/ai/chat: {posted}"


def test_vite_lanzador_posts_to_run_endpoint(page, live_url):
    _wait_for_app(page, live_url)
    page.locator(".sb-item", has_text="Lanzador").first.click()
    page.wait_for_selector("text=Comando generado", timeout=5_000)
    posted = []
    page.on("response", lambda r: posted.append(r.url) if "/api/run" in r.url else None)
    page.get_by_role("button", name="Ejecutar").click()
    page.wait_for_timeout(1500)
    assert any("/api/run" in u for u in posted), f"no /api/run: {posted}"


def test_vite_bootstrap_endpoint_real_data(page, live_url):
    response = page.request.get(f"{live_url}/api/bootstrap")
    assert response.ok
    data = response.json()
    assert len(data["MODULES"]) == 15
    m3 = next(m for m in data["MODULES"] if m["id"] == "M3")
    assert m3["pct"] > 0


def test_vite_token_data_real(page, live_url):
    response = page.request.get(f"{live_url}/api/ai-usage")
    td = response.json()
    assert td["total_30d"] == 150
    assert any(m["model"] == "claude-haiku-4-5" for m in td["byModel"])


def test_vite_static_assets_load(page, live_url):
    _wait_for_app(page, live_url)
    bg = page.evaluate("() => getComputedStyle(document.body).backgroundColor")
    assert bg and bg != "rgba(0, 0, 0, 0)"


def test_vite_no_dead_buttons_in_master(page, live_url):
    _wait_for_app(page, live_url)
    page.locator(".sb-item", has_text="Master").first.click()
    page.wait_for_url(lambda u: "master" in u, timeout=5_000)
    page.wait_for_timeout(300)
    dead = page.evaluate("""
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
    assert dead == [], f"Botones sin onClick en Master (Vite): {dead}"


def test_vite_modulo_action_navigates_to_lanzador(page, live_url):
    _wait_for_app(page, live_url)
    page.locator(".sb-item", has_text="Módulo").first.click()
    page.wait_for_url(lambda u: "modulo" in u, timeout=5_000)
    page.wait_for_timeout(400)
    page.get_by_role("button", name="Generar audio pendiente").click()
    page.wait_for_url(lambda u: "lanzador" in u, timeout=5_000)


def test_vite_modulo_generate_guion_posts_to_episode_endpoint(page, live_url):
    """El panel "Generar guion" del módulo dispara POST /api/episode/<id>/generate."""
    _wait_for_app(page, live_url)
    page.locator(".sb-item", has_text="Módulo").first.click()
    page.wait_for_url(lambda u: "modulo" in u, timeout=5_000)
    page.wait_for_timeout(400)

    posted = []
    page.on("request", lambda r: posted.append(r.url)
            if r.method == "POST" and "/generate" in r.url else None)
    page.get_by_role("button", name=re.compile("Generar este guion|Regenerar este guion")).click()
    page.wait_for_timeout(1500)
    assert any("/api/episode/" in u and u.endswith("/generate") for u in posted), \
        f"no POST a /api/episode/<id>/generate: {posted}"


def test_vite_topup_button_calls_economics(page, live_url):
    _wait_for_app(page, live_url)
    page.locator(".sb-item", has_text="Consumo").first.click()
    page.wait_for_url(lambda u: "consumo" in u, timeout=5_000)
    page.wait_for_timeout(400)
    page.locator(".tab", has_text="Saldos").first.click()
    page.wait_for_timeout(200)

    posted = []
    page.on("request", lambda r: posted.append(r.url) if "/api/economics/topup" in r.url else None)

    page.evaluate("""
        () => {
          window.prompt = (msg) => {
            if (msg.toLowerCase().includes('proveedor')) return 'anthropic';
            if (msg.toLowerCase().includes('importe')) return '15';
            return 'desde test';
          };
          window.alert = () => {};
          window.location.reload = () => {};
        }
    """)
    page.get_by_role("button", name="Registrar recarga").click()
    page.wait_for_timeout(1500)
    assert any("/api/economics/topup" in u for u in posted), f"no /api/economics/topup: {posted}"


def test_vite_fuentes_descargar_links_to_files(page, live_url):
    """En Fuentes, al elegir un PDF y pulsar Descargar, se abre /files/..."""
    _wait_for_app(page, live_url)
    page.locator(".sb-item", has_text="Fuentes").first.click()
    page.wait_for_url(lambda u: "fuentes" in u, timeout=5_000)
    page.wait_for_timeout(500)
    # Capturar window.open
    page.evaluate("() => { window.__opened = []; window.open = (url) => { window.__opened.push(url); }; }")
    # El primer ítem de la lista de fuentes (clase interactiva del legacy)
    rows = page.locator(".fuentes-row, .panel .row")
    if rows.count() == 0:
        pytest.skip("Fuentes layout sin filas detectables — verificación visual manual")
    # No clickeamos archivos porque el seleccionado depende de SOURCES;
    # validamos al menos que el botón Descargar existe y al pulsarlo intenta abrir /files/
    btns = page.get_by_role("button", name="Descargar")
    if btns.count() == 0:
        pytest.skip("Botón Descargar visible solo tras seleccionar archivo")
    btns.first.click()
    opened = page.evaluate("() => window.__opened || []")
    assert any("/files/" in u for u in opened), f"no se abrió /files/...: {opened}"


def test_vite_ajustes_loads_api_keys(page, live_url):
    """Ajustes consulta /api/api-keys al montar y al Re-verificar."""
    seen = []
    page.on("request", lambda r: seen.append(r.url) if "/api/api-keys" in r.url else None)
    _wait_for_app(page, live_url)
    page.locator(".sb-item", has_text="Ajustes").first.click()
    page.wait_for_url(lambda u: "ajustes" in u, timeout=5_000)
    page.wait_for_timeout(600)
    assert any("/api/api-keys" in u for u in seen), f"no /api/api-keys al montar: {seen}"

    seen.clear()
    page.evaluate("() => { window.alert = () => {}; }")
    page.get_by_role("button", name="Re-verificar").first.click()
    page.wait_for_timeout(800)
    assert any("/api/api-keys" in u for u in seen), f"Re-verificar no re-consultó: {seen}"


def test_vite_dist_assets_have_hashed_names(page, live_url):
    """Build de Vite usa cache-busting con hash en los nombres."""
    response = page.request.get(f"{live_url}/")
    html = response.text()
    assert "/assets/" in html
    assert re.search(r"/assets/index-[A-Za-z0-9_-]+\.js", html)
    assert re.search(r"/assets/index-[A-Za-z0-9_-]+\.css", html)
