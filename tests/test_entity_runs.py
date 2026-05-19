"""Tests del endpoint `/api/entity/{id}/runs` y de `load_entity_runs`.

El handler parsea el día-log (`logs/run/maquinaria_*.log`) con el validador
nuevo (`cockpit.core.log_validator.parse_log`) y asocia cada run a una
entidad si CUALQUIERA de sus líneas contiene tokens identificadores
(--modulo N, --ep X, RESUMEN_Mn_, S{N}_, etc.).

Verifica que el panel "Ejecuciones" del cockpit (PageModuloTema →
EpisodeRunsPanel) recibe los datos correctos para módulos M, temas T y
shorts S.
"""
from __future__ import annotations

import datetime as dt
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def fake_repo(tmp_path, monkeypatch):
    """REPO_ROOT temporal con un daylog que contiene 3 runs sintéticos:
    M3 (guion ok), M3 (audio error con retry) y S1 (short ok)."""
    (tmp_path / "logs" / "run").mkdir(parents=True)
    today = dt.date.today().isoformat()
    log_path = tmp_path / "logs" / "run" / f"maquinaria_{today}.log"

    lines = [
        f"{today}T08:00:00 [START] run=aaa111 script=generar_guion.py pid=10001 | --modulo 3 --pdf PDFs/resumenes/RESUMEN_M3_Machine_Learning_Clasico.pdf",
        f"{today}T08:00:01 [INFO ] run=aaa111 script=generar_guion.py pid=10001 | paso → load_spec step=load_spec",
        f"{today}T08:00:02 [INFO ] run=aaa111 script=generar_guion.py pid=10001 | paso → extract_concepts step=extract_concepts",
        f"{today}T08:00:05 [INFO ] run=aaa111 script=generar_guion.py pid=10001 | AI call → generate_block model=claude-sonnet-4-5 purpose=generate_block",
        f"{today}T08:00:18 [OK   ] run=aaa111 script=generar_guion.py pid=10001 | AI call ok → generate_block model=claude-sonnet-4-5 ms=13200 tokens_in=1500 tokens_out=800",
        f"{today}T08:00:19 [INFO ] run=aaa111 script=generar_guion.py pid=10001 | paso → generate step=generate",
        f"{today}T08:00:20 [INFO ] run=aaa111 script=generar_guion.py pid=10001 | paso → validate step=validate",
        f"{today}T08:00:21 [INFO ] run=aaa111 script=generar_guion.py pid=10001 | paso → save step=save",
        f"{today}T08:00:21 [END  ] run=aaa111 script=generar_guion.py pid=10001 | ejecución completada status=ok elapsed_s=21.5 out_lines=12 err_lines=0",
        f"{today}T09:30:00 [START] run=bbb222 script=generar_episodio_v2.py pid=10100 | --ep M3",
        f"{today}T09:30:01 [INFO ] run=bbb222 script=generar_episodio_v2.py pid=10100 | paso → load_script step=load_script",
        f"{today}T09:30:02 [INFO ] run=bbb222 script=generar_episodio_v2.py pid=10100 | paso → audio step=audio",
        f"{today}T09:30:15 [WARN ] run=bbb222 script=generar_episodio_v2.py pid=10100 | [generar_episodio_v2] retry attempt=2 reason=elevenlabs_502",
        f"{today}T09:30:30 [ERROR] run=bbb222 script=generar_episodio_v2.py pid=10100 | [generar_episodio_v2] AI call error → tts model=eleven_v2 status_code=502",
        f"{today}T09:30:31 [END  ] run=bbb222 script=generar_episodio_v2.py pid=10100 | ejecución abortada status=error code=1 elapsed_s=31.2 out_lines=4 err_lines=2",
        f"{today}T10:00:00 [START] run=ccc333 script=s_generator.py pid=10200 | --ep S1",
        f"{today}T10:00:01 [INFO ] run=ccc333 script=s_generator.py pid=10200 | paso → iterate step=iterate term=RAG",
        f"{today}T10:00:05 [INFO ] run=ccc333 script=s_generator.py pid=10200 | AI call → generate_short model=claude-haiku-4-5 purpose=short",
        f"{today}T10:00:09 [OK   ] run=ccc333 script=s_generator.py pid=10200 | AI call ok → generate_short model=claude-haiku-4-5 ms=4200 tokens_in=500 tokens_out=180",
        f"{today}T10:00:10 [OK   ] run=ccc333 script=s_generator.py pid=10200 | short guardado path=Guiones/S1_RAG_v6.md",
        f"{today}T10:00:11 [END  ] run=ccc333 script=s_generator.py pid=10200 | ejecución completada status=ok elapsed_s=11.4 out_lines=8 err_lines=0",
    ]
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    for mod in list(sys.modules):
        if mod.startswith("cockpit.core") or mod == "web_server":
            del sys.modules[mod]
    yield tmp_path


def test_load_entity_runs_M3_captures_modulo_and_pdf_tokens(fake_repo):
    """Un run con `--modulo 3` o path `RESUMEN_M3_…` debe asociarse a M3."""
    import web_server
    payload = web_server.load_entity_runs("M3", days=2, limit=10)
    assert payload["ok"] is True
    run_ids = {r["run_id"] for r in payload["runs"]}
    # aaa111 tiene --modulo 3 + RESUMEN_M3_; bbb222 tiene --ep M3.
    assert "aaa111" in run_ids
    assert "bbb222" in run_ids
    # ccc333 es de S1, no debe aparecer en M3
    assert "ccc333" not in run_ids


def test_load_entity_runs_returns_structured_summary(fake_repo):
    """El payload por run debe traer status, elapsed, pasos, AI calls."""
    import web_server
    runs = web_server.load_entity_runs("M3", days=2)["runs"]
    by_id = {r["run_id"]: r for r in runs}

    ok_run = by_id["aaa111"]
    assert ok_run["status"] == "ok"
    assert ok_run["elapsed_s"] == 21.5
    assert ok_run["script"] == "generar_guion.py"
    # 5 pasos en EXPECTED_STEPS de generar_guion.py
    for expected in ("load_spec", "extract_concepts", "generate", "validate", "save"):
        assert expected in ok_run["steps"]
    assert ok_run["ai_calls"]["ok"] == 1
    assert ok_run["ai_calls"]["error"] == 0
    assert ok_run["last_error"] is None

    err_run = by_id["bbb222"]
    assert err_run["status"] == "error"
    assert err_run["retries"] == 1
    assert err_run["ai_calls"]["error"] == 1
    assert err_run["last_error"] is not None
    assert "tts" in err_run["last_error"]


def test_load_entity_runs_S1_captures_short_tokens(fake_repo):
    """Para un Short, el filtro debe matchear `--ep S1` y paths `S1_…`."""
    import web_server
    payload = web_server.load_entity_runs("S1", days=2)
    run_ids = {r["run_id"] for r in payload["runs"]}
    assert "ccc333" in run_ids
    # No mezcla con M3
    assert "aaa111" not in run_ids
    assert "bbb222" not in run_ids


def test_load_entity_runs_sorted_desc_by_started_at(fake_repo):
    """Los runs vuelven ordenados por started_at descendiente (más reciente
    primero) para que el timeline ponga lo último arriba."""
    import web_server
    runs = web_server.load_entity_runs("M3", days=2)["runs"]
    starts = [r["started_at"] for r in runs]
    assert starts == sorted(starts, reverse=True)


def test_load_entity_runs_no_log_dir(tmp_path, monkeypatch):
    """Sin carpeta logs/run/ devuelve `ok=True, runs=[]` sin romper."""
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    for mod in list(sys.modules):
        if mod.startswith("cockpit.core") or mod == "web_server":
            del sys.modules[mod]
    import web_server
    payload = web_server.load_entity_runs("M3", days=2)
    assert payload["ok"] is True
    assert payload["runs"] == []
    assert payload["days_scanned"] == 0


def test_api_endpoint_entity_runs_serves_json(fake_repo, monkeypatch):
    """El endpoint HTTP `/api/entity/{id}/runs` responde 200 con shape
    correcto. Usa el TestClient de FastAPI (sin red real)."""
    monkeypatch.setenv("COCKPIT_NO_SHELL", "1")
    from fastapi.testclient import TestClient

    import web_server
    importlib.reload(web_server)
    client = TestClient(web_server.app)
    r = client.get("/api/entity/M3/runs?days=2")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["entity_id"] == "M3"
    assert any(run["run_id"] == "aaa111" for run in body["runs"])
