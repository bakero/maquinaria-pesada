"""Tests E2E del cockpit v3 industrial (Vite + TS).

Corre contra el build de producción de Vite (`cd vite_app && npm run build`
→ `vite_app/dist/`). Levanta un `web_server.ThreadedServer` real apuntado a
un `fake_repo` aislado con material mínimo para que el escaneo de episodios
encuentre cosas predecibles y los assertions sean estables.

Cubre el shell + las 3 páginas v3:

  · TopNav         · 3 secciones, pill live, ⌘K, IA
  · CommandPalette · abre con ⌘K
  · AIDrawer       · POST /api/ai/chat
  · PageProduccion · KPIs reales del bootstrap, click en módulo navega
  · PageModuloTema · header limpio, sibling rail sticky con contador,
                     slots PDF/Guion/Audio, botón Regenerar guion en
                     amarillo (primary), SlotLogFull oculto cuando no
                     hay log, EntityLogViewer consumiendo el endpoint
                     /api/entity/{id}/log-lines (no /files/log entero),
                     POST /api/episode/{id}/generate
  · PageDatos      · 4 sub-tabs (consumo/métricas/optimizar/logs)
  · PageSistema    · 5 sub-tabs (conectores/lanzador/fuentes/mapa/ajustes)
                     · Lanzador → POST /api/run
                     · Ajustes → /api/api-keys
  · /files/<path>  · sirve PDFs reales con HTTP 200

Para correrlos: ``python3 -m pytest tests/test_e2e_vite.py -v``.
Requiere ``pytest-playwright`` y un chromium compatible.
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
        reason="pytest-playwright no instalado · skip E2E "
               "(instalable con: pip install pytest-playwright && playwright install chromium)",
    ),
]


# ──────────────────────────── fixtures ────────────────────────────


@pytest.fixture
def fake_repo(tmp_path, monkeypatch):
    """REPO_ROOT temporal con material predecible:

      · M0 completo (PDF, guion, escaleta, audio)
      · M3 con guion + PDF de tema M3_T1 (valida regex de temas)
      · evento ai_usage.jsonl para que la página Consumo tenga datos
    """
    for d in ("Guiones", "PDFs", "PDFs/temas", "episodios", "escaletas",
              "Videos", "logs", "logs/run"):
        (tmp_path / d).mkdir(parents=True, exist_ok=True)

    (tmp_path / "PDFs" / "M0_T_Introduccion.pdf").write_bytes(b"%PDF-1.4 fake")
    (tmp_path / "Guiones" / "M0_Introduccion.txt").write_text("# M0", encoding="utf-8")
    (tmp_path / "escaletas" / "M0_intro.md").write_text("# M0", encoding="utf-8")
    (tmp_path / "episodios" / "M0.mp3").write_bytes(b"\x00" * 16)

    (tmp_path / "PDFs" / "M3_T_Machine_Learning_Clasico.pdf").write_bytes(b"%PDF-1.4 fake")
    (tmp_path / "Guiones" / "M3_Machine_Learning_Clasico.txt").write_text("# M3", encoding="utf-8")
    (tmp_path / "PDFs" / "temas" / "M3_T1_tipos_aprendizaje.pdf").write_bytes(b"%PDF-1.4 fake")

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
    monkeypatch.setenv("COCKPIT_WEB_DIR", str(DIST_DIR))
    monkeypatch.setenv("COCKPIT_NO_SHELL", "1")
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
    """Navega y espera al shell v3 (TopNav brand) montado.

    Marca el OnboardingTour como visto en localStorage ANTES del primer
    goto: en su primera visita el tour superpone un .onb-backdrop que
    intercepta todos los clicks y rompe el resto de la suite. La clave
    está definida en vite_app/src/shell/OnboardingTour.tsx.
    """
    page.add_init_script("localStorage.setItem('mp:onboarding:v3:done', '1');")
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector(".topnav3-brand", timeout=15_000)
    # Sanity: si algún reseteo dejó el backdrop, ciérralo
    if page.locator(".onb-backdrop").count():
        page.locator(".onb-backdrop").click()
        page.wait_for_selector(".onb-backdrop", state="detached", timeout=3000)


def _open_module_via_palette(page, mod_id: str = "M3") -> None:
    """Atajo: abre la CommandPalette y navega al MÓDULO `mod_id`.

    Filtra por "Módulo M3" en lugar de "M3" a secas porque la palette
    contiene también entries de temas (Tema M3_T1 …) que matchearían
    primero y nos llevarían a una entidad sin guion.
    """
    page.keyboard.press("Control+K")
    page.wait_for_selector(".cmdp", timeout=3000)
    page.fill(".cmdp-input input", f"Módulo {mod_id}")
    page.wait_for_timeout(250)
    page.locator(".cmdp-list").get_by_text(
        re.compile(rf"Módulo {mod_id}\b")
    ).first.click()
    page.wait_for_selector(".v3-mt-hd", timeout=5000)


# ────────────────────────── SHELL · TopNav ──────────────────────────


def test_app_mounts_and_shell_renders(page, live_url):
    """La app monta el shell v3 (top-nav visible, wordmark correcto)."""
    _wait_for_app(page, live_url)
    assert page.locator(".topnav3").count() == 1
    assert "MAQUINARIA" in page.locator(".topnav3-wordmark").inner_text()


def test_topnav_has_three_sections(page, live_url):
    """v3 industrial: Producción, Datos, Sistema."""
    _wait_for_app(page, live_url)
    items = page.locator(".topnav3-item").all_inner_texts()
    assert len(items) == 3, f"esperaba 3 items, encontré {len(items)}: {items}"
    joined = " ".join(items).lower()
    for expected in ("producción", "datos", "sistema"):
        assert expected in joined, f"falta sección {expected!r} en {items}"


def test_topnav_has_search_and_ai_buttons(page, live_url):
    """Botones de búsqueda (⌘K) e IA siempre visibles en el top-nav."""
    _wait_for_app(page, live_url)
    assert page.locator(".topnav3-search").count() == 1
    assert page.locator(".topnav3-ai").count() == 1


def test_command_palette_opens_with_cmd_k(page, live_url):
    """⌘K / Ctrl+K abre el CommandPalette y Esc lo cierra."""
    _wait_for_app(page, live_url)
    assert page.locator(".cmdp").count() == 0
    page.keyboard.press("Control+K")
    page.wait_for_selector(".cmdp", timeout=3000)
    assert page.locator(".cmdp-input").count() == 1
    assert page.locator(".cmdp-list").count() == 1
    page.keyboard.press("Escape")
    page.wait_for_selector(".cmdp", state="detached", timeout=3000)


def test_ai_drawer_posts_to_api_chat(page, live_url):
    """Click en botón IA abre drawer; enviar mensaje → POST /api/ai/chat."""
    _wait_for_app(page, live_url)
    page.click(".topnav3-ai")
    page.wait_for_selector(".drawer.open", timeout=3000)
    page.fill(".ai-input", "hola test")
    with page.expect_request(
        lambda r: r.url.endswith("/api/ai/chat") and r.method == "POST",
        timeout=5000,
    ) as ev:
        page.locator(".drawer-foot").get_by_role(
            "button", name=re.compile(r"enviar", re.I)
        ).first.click()
    body = ev.value.post_data or ""
    assert "hola test" in body or '"message"' in body


# ──────────────────────── PageProduccion ────────────────────────


def test_produccion_renders_kpis_from_bootstrap(page, live_url):
    """KPIs del master vienen del backend (no de FIXTURE_* hardcoded)."""
    _wait_for_app(page, live_url)
    page.wait_for_selector(".v3-stats", timeout=5000)
    stats = page.locator(".v3-stat-value").all_inner_texts()
    assert len(stats) >= 3
    pct = page.locator(".v3-stat-value").first.inner_text()
    assert "%" in pct


def test_produccion_lists_modules_from_backend(page, live_url):
    """La página master lista los 15 módulos del currículum (M0..M14)."""
    _wait_for_app(page, live_url)
    page.wait_for_selector(".v3-stats", timeout=5000)
    body = page.locator(".v3-page").inner_text()
    for mod in ("M0", "M3", "M14"):
        assert mod in body, f"módulo {mod} ausente en PageProduccion"


# ──────────────────────── PageModuloTema ────────────────────────


def test_modulo_header_shows_clean_title_and_id(page, live_url):
    """Header de PageModuloTema: id 'M3' + título limpio sin prefijos."""
    _wait_for_app(page, live_url)
    _open_module_via_palette(page, "M3")
    id_text = page.locator(".v3-mt-id").inner_text()
    assert "M3" in id_text
    name_text = page.locator(".v3-mt-name").inner_text()
    assert "Episodio M" not in name_text
    assert not re.match(r"^T\d+ — ", name_text)


def test_modulo_sibling_rail_is_sticky_with_counter(page, live_url):
    """Sibling rail tiene wrapper sticky con contador 'completos/con algo/total'."""
    _wait_for_app(page, live_url)
    _open_module_via_palette(page, "M3")
    page.wait_for_selector(".v3-mt-rail-wrap", timeout=5000)
    pos = page.locator(".v3-mt-rail-wrap").evaluate(
        "(el) => getComputedStyle(el).position"
    )
    assert pos == "sticky"
    assert page.locator(".v3-mt-rail-meta-count strong").count() == 3
    text = page.locator(".v3-mt-rail-meta-count").inner_text().lower()
    assert "completo" in text and "con algo" in text and "total" in text


def test_modulo_slot_guion_button_is_primary_yellow(page, live_url):
    """Botón 'Regenerar' del slot Guion lleva la clase 'primary' (amarillo)."""
    _wait_for_app(page, live_url)
    _open_module_via_palette(page, "M3")
    page.wait_for_selector(".v3-slot-row", timeout=5000)
    guion_row = page.locator(".v3-slot-row").filter(
        has_text=re.compile(r"Guion|Guión", re.I)
    ).first
    assert guion_row.count() >= 1
    btn = guion_row.get_by_role("button", name=re.compile(r"regenerar", re.I)).first
    cls = btn.get_attribute("class") or ""
    assert "primary" in cls, f"esperaba clase 'primary' en botón Regenerar guion, vi: {cls!r}"


def test_modulo_slot_log_block_hidden_when_no_log(page, live_url):
    """SlotLogFull NO renderiza '(sin log de X)' fantasma en slots vacíos."""
    _wait_for_app(page, live_url)
    _open_module_via_palette(page, "M3")
    page.wait_for_selector(".v3-slot-row", timeout=5000)
    video_row = page.locator(".v3-slot-row").filter(
        has_text=re.compile(r"V[ií]deo", re.I)
    ).first
    video_row.click()
    page.wait_for_timeout(400)
    body_text = (
        page.locator(".v3-slot-body").first.inner_text()
        if page.locator(".v3-slot-body").count() else ""
    )
    assert "(sin log de" not in body_text


def test_entity_log_lines_endpoint_responds(live_url):
    """/api/entity/{id}/log-lines responde con el contrato esperado.

    Este es el endpoint que EntityLogViewer consume (en vez de bajar el
    log entero del slot vía /files/...).
    """
    import urllib.request
    with urllib.request.urlopen(
        f"{live_url}/api/entity/M3/log-lines?days=7&limit=10"
    ) as r:
        data = json.loads(r.read())
    assert data["ok"] is True
    assert isinstance(data.get("entries"), list)
    assert "days_scanned" in data


def test_modulo_regenerate_guion_posts_to_episode_generate(page, live_url):
    """Click 'Regenerar' del slot Guion → POST /api/episode/M3/generate."""
    _wait_for_app(page, live_url)
    _open_module_via_palette(page, "M3")
    page.wait_for_selector(".v3-slot-row", timeout=5000)
    guion_row = page.locator(".v3-slot-row").filter(
        has_text=re.compile(r"Guion|Guión", re.I)
    ).first
    btn = guion_row.get_by_role("button", name=re.compile(r"regenerar", re.I)).first
    with page.expect_request(
        lambda r: "/api/episode/M3/generate" in r.url and r.method == "POST",
        timeout=5000,
    ) as ev:
        btn.click()
    assert ev.value is not None


# ──────────────────────── PageDatos · sub-tabs ────────────────────────


def test_datos_has_four_subtabs(page, live_url):
    """PageDatos tiene 4 sub-tabs (labels reales: Coste IA / Difusión / Optimización / Logs)."""
    _wait_for_app(page, live_url)
    page.locator(".topnav3-item").filter(has_text=re.compile(r"datos", re.I)).first.click()
    page.wait_for_selector(".v3-hd-eyebrow", timeout=5000)
    assert "datos" in page.locator(".v3-hd-eyebrow").first.inner_text().lower()
    subtabs = page.locator(".v3-hd-right .v3-btn").all_inner_texts()
    joined = " ".join(subtabs).lower()
    for expected in ("coste", "difusión", "optimización", "logs"):
        assert expected in joined, f"sub-tab {expected!r} ausente en {subtabs}"


# ──────────────────────── PageSistema · sub-tabs ──────────────────────


def test_sistema_has_five_subtabs(page, live_url):
    """PageSistema tiene 5 sub-tabs (labels reales incluyen 'Lanzar pipeline')."""
    _wait_for_app(page, live_url)
    page.locator(".topnav3-item").filter(has_text=re.compile(r"sistema", re.I)).first.click()
    page.wait_for_selector(".v3-hd-eyebrow", timeout=5000)
    assert "sistema" in page.locator(".v3-hd-eyebrow").first.inner_text().lower()
    subtabs = page.locator(".v3-hd-right .v3-btn").all_inner_texts()
    joined = " ".join(subtabs).lower()
    for expected in ("conectores", "lanzar pipeline", "fuentes", "mapa", "ajustes"):
        assert expected in joined, f"sub-tab {expected!r} ausente en {subtabs}"


def test_lanzador_posts_to_run_endpoint(page, live_url):
    """Sistema → Lanzador → seleccionar pipeline → Ejecutar → POST /api/run."""
    _wait_for_app(page, live_url)
    page.locator(".topnav3-item").filter(has_text=re.compile(r"sistema", re.I)).first.click()
    page.wait_for_selector(".v3-hd-eyebrow", timeout=5000)
    page.locator(".v3-hd-right .v3-btn").filter(
        has_text=re.compile(r"lanzar pipeline", re.I)
    ).first.click()
    # Esperar a que cargue la lista de pipelines (sale del estado "Cargando pipelines…")
    page.wait_for_selector("text=Pipeline", timeout=5000)
    page.wait_for_timeout(500)
    # Botón Ejecutar (puede aparecer deshabilitado hasta seleccionar uno).
    # Click en la primera tarjeta de pipeline para seleccionarla.
    cards = page.locator(".display").filter(
        has_text=re.compile(r"^[A-Z]")
    )
    if cards.count() > 0:
        cards.first.click()
    page.wait_for_timeout(300)
    btn = page.get_by_role("button", name=re.compile(r"^ejecutar", re.I)).first
    with page.expect_request(
        lambda r: r.url.endswith("/api/run") and r.method == "POST",
        timeout=6000,
    ) as ev:
        btn.click()
    body = ev.value.post_data or ""
    assert '"script"' in body


def test_ajustes_loads_api_keys(page, live_url):
    """Sistema → Ajustes → GET /api/api-keys (200)."""
    _wait_for_app(page, live_url)
    page.locator(".topnav3-item").filter(has_text=re.compile(r"sistema", re.I)).first.click()
    page.wait_for_selector(".v3-hd-eyebrow", timeout=5000)
    with page.expect_response(
        lambda r: r.url.endswith("/api/api-keys") and r.status == 200,
        timeout=5000,
    ):
        page.locator(".v3-hd-right .v3-btn").filter(
            has_text=re.compile(r"^ajustes$", re.I)
        ).first.click()


# ──────────────────────── /files/<path> + build ────────────────────────


def test_files_endpoint_serves_real_pdf(live_url):
    """El endpoint /files/<path> sirve los PDFs del fake_repo."""
    import urllib.request
    with urllib.request.urlopen(
        f"{live_url}/files/PDFs/temas/M3_T1_tipos_aprendizaje.pdf"
    ) as r:
        assert r.status == 200
        head = r.read(8)
        assert head.startswith(b"%PDF")


def test_dist_assets_have_hashed_names():
    """vite_app/dist/assets/* tiene nombres con hash (cache-busting)."""
    assets = list((DIST_DIR / "assets").glob("index-*.js"))
    assert assets, "no se encontró ningún bundle JS en dist/assets/"
    assert any(re.search(r"index-[A-Za-z0-9_-]{6,}\.js$", str(a)) for a in assets)
