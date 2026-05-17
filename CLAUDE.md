# CLAUDE.md — Guía para Claude Code

Reglas y contexto para trabajar en MaquinarIA Pesada.

## Qué es este proyecto

Sistema de generación automática de podcasts y vídeos con IA en Python.

- **Pipelines top-level (CLI)**: `generar_guion.py`, `generar_episodio_v2.py`,
  `validar_episodio.py`, `normalizar_guiones.py`, `podcast_spec.py`, etc.
  Producen contenido a partir de PDFs fuente.
- **Generación de guiones**: ver `GENERACION.md` — los episodios se generan
  SOLO con `generar_guion.py` (M) y `generar_guion_t.py` (T), que comparten
  `guion_common.py` y validan con `podcast_spec.py`. `fix_guiones_v4.py`,
  `rebalance_blocks.py` y `normalizar_guiones.py` son utilidades legacy
  manuales: NO generan episodios.
- **Cockpit web** (React + Vite + FastAPI): la app de control para ejecutar
  pipelines, inspeccionar logs, gestionar API keys, controlar gasto IA, ver
  mapa de componentes y conversar con Claude para mejorar contenido. El
  frontend vive en `vite_app/` y se sirve desde `web_server.py`, que expone
  la API JSON sobre `cockpit.core` + `cockpit.connectors`. **La cabina
  Streamlit fue retirada**: ya no existen `cockpit/app.py`, `cockpit/pages/*`,
  `cockpit/ui*.py` ni la dependencia `streamlit`.
- **Proveedores IA**: Anthropic Claude (guiones), OpenAI GPT (debate dual),
  Whisper local (transcripción), ElevenLabs (TTS), Kling (vídeo).

Lee `GENERACION.md`, `BIBLIA_SISTEMA.md` y `PODCAST_M_SPEC.md` para detalles
funcionales.

## Sandbox de Claude DENTRO de la app

`cockpit/core/sandbox.py` define qué paths puede escribir Claude **cuando
opera a través de la cockpit** (botones "Mejorar con IA", chat del mapa,
acciones del módulo/tema):

- Permitido: `Guiones/`, `episodios/`, `escaletas/`, `RRSS/`, `output/`,
  `PDFs/{auxiliares,resumenes,temas}/`, `prompts/`,
  `Videos/escenas_biblioteca/`, `cockpit/components_map.json`,
  `logs/ai_usage.jsonl`, `logs/economics.json`.
- Prohibido: todo `cockpit/`, pipelines top-level `.py`, `.github/`,
  `pyproject.toml`, `requirements*.txt`, `.env`, `_archivo/`, `tests/`,
  `vite_app/` (especialmente `vite_app/src/`).

Esto **no** restringe a Claude Code (esta sesión). Restringe al modo
conversación dentro del cockpit web. Aún así, respeta el espíritu: la app
no debería auto-modificarse vía su propio chat.

## Antes de cada cambio en código

1. **Tests obligatorios**: tras Edit/Write/MultiEdit sobre `cockpit/`,
   `tests/`, `web_server.py`, `pyproject.toml` o `vite_app/src/`, el hook
   `.claude/scripts/posttool_check.sh` ejecuta `ruff check` + `pytest`
   (sin la suite e2e). Si fallan, bloquean. No se continúa con fallos.
2. **Suite e2e Playwright** (`tests/test_e2e_vite.py`, 19 tests, ~90 s):
   no se ejecuta automáticamente. Si quieres que el hook también la
   corra al editar UI o `web_server.py`/`episodes.py`, exporta
   `MP_RUN_E2E=1` antes de la sesión. Manualmente:
   `python3 -m pytest tests/test_e2e_vite.py -v`. CI la corre siempre en
   el job `e2e-cockpit-v3`.
3. **No se commitea sin OK explícito del usuario**.
4. **No tocar pipelines top-level salvo petición explícita**: son scripts
   CLI estables con generación real y costosa.
5. **Cambios en `vite_app/src/`** requieren `cd vite_app && npm run build`
   para que `web_server.py` sirva el frontend actualizado desde
   `vite_app/dist/`.

## Convenciones de código

- Python 3.10+, type hints en código nuevo.
- Ruff configurado en `pyproject.toml` (line-length 100, reglas E/F/W/I/UP/B).
- Tests con pytest, archivos `tests/test_*.py`, sin red ni keys reales.
- Mocks para `anthropic`, `openai`, `psutil`, `dotenv` cuando aplique.
- Streaming de IA preferido sobre llamadas bloqueantes (verbose en UI).
- Cada llamada IA debe pasar por `cockpit/core/ai_client.improve_with_claude*`
  para tener retry + tracking automático en `logs/ai_usage.jsonl`.
- Frontend: TypeScript estricto (`tsc --noEmit` en el build), Inter +
  JetBrains Mono, sin emojis decorativos en JSX.

## Modelos por defecto

- Sonnet 4.6 para generación equilibrada.
- Haiku 4.5 para iteración rápida y checks.
- Opus 4.7 solo cuando Sonnet falla en tarea técnica compleja.

Nunca uses Opus para tareas que Sonnet resuelve. Cuesta ~5× más.

## Estructura

```
cockpit/                   # lógica reutilizable (sin UI)
  core/                    # paths, log_parser, monitor, state, prompt_builder,
                           # runner, ai_client, api_keys, usage_tracker,
                           # sandbox, economics, optimization_advisor,
                           # components_map, episodes, verifications, gen_log
  connectors/              # services/, pipelines/, sources/ + analytics/
                           # (Spotify · iVoox · LinkedIn) con registry
web_server.py              # FastAPI · sirve vite_app/dist + API JSON
vite_app/                  # cockpit React (Vite + TS)
  src/pages/               # PageProduccion, PageModuloTema, PageDatos,
                           # PageSistema y subpáginas legacy reutilizadas
  src/shell/               # TopNav, AIDrawer, CommandPalette, OnboardingTour
  src/lib/                 # nav, useEntity (hooks + SSE), useHotkeys
  src/styles.css           # tokens v3 industrial + componentes
tests/                     # 600+ tests, todos sin red
.github/workflows/         # CI (lint + pytest)
.claude/                   # settings.json, scripts/posttool_check.sh, skills/
docs/                      # arquitectura, evaluaciones, integraciones
logs/                      # ai_usage.jsonl, economics.json (no commiteados)
```

## Comandos frecuentes

```bash
# Lanzar cockpit web (build + serve)
cd vite_app && npm install && npm run build && cd ..
python web_server.py

# Solo recargar el frontend tras tocar vite_app/src
cd vite_app && npm run build

# Verificar antes de cualquier cambio Python
ruff check cockpit/ tests/ web_server.py
pytest tests/ -q

# Generar guion (ejemplo)
python generar_guion.py --pdf PDFs/M3_T_ML.pdf --ep M3_T_ML --duracion-min 15

# Validar episodio
python validar_episodio.py --ep M3_T_ML --guion Guiones/M3_T_ML.txt
```

## Reglas duras

- No commitear `.env`, claves o cualquier secret.
- No skip de tests (`--no-verify`, `pytest.skip` masivo, etc.).
- No reemplazar `print()` masivamente en pipelines top-level sin tests previos.
- Mantener la batería de tests verde tras cada cambio (lo aplica el hook).
- Documentar cambios de arquitectura en `docs/architecture/`.
- Cualquier nueva llamada a IA pasa por `ai_client.improve_with_claude*`.
- No reintroducir Streamlit. Si necesitas UI nueva, va en `vite_app/src/`.
