# CLAUDE.md — Guía para Claude Code

Reglas y contexto para trabajar en MaquinarIA Pesada.

## Qué es este proyecto

Sistema de generación automática de podcasts y vídeos con IA en Python.

- **Pipelines top-level (CLI)**: `generar_guion.py`, `generar_episodio_v2.py`,
  `validar_episodio.py`, `normalizar_guiones.py`, `podcast_spec.py`, etc.
  Producen contenido a partir de PDFs fuente.
- **Cockpit Streamlit** (`cockpit/`): centro de control para ejecutar pipelines,
  inspeccionar logs, gestionar API keys, controlar gasto IA, ver mapa de
  componentes, conversar con Claude para mejorar contenido.
- **Proveedores IA**: Anthropic Claude (guiones), OpenAI GPT (debate dual),
  Whisper local (transcripción), ElevenLabs (TTS), Kling (vídeo).

Lee `BIBLIA_SISTEMA.md` y `PODCAST_M_SPEC.md` para detalles funcionales.

## Sandbox de Claude DENTRO de la app

`cockpit/core/sandbox.py` define qué paths puede escribir Claude **cuando
opera a través de la cockpit** (botones "✨ Mejorar con IA", chat del mapa):

- ✅ Permitido: `Guiones/`, `episodios/`, `escaletas/`, `RRSS/`, `output/`,
  `PDFs/{auxiliares,resumenes,temas}/`, `prompts/`, `Videos/escenas_biblioteca/`,
  `cockpit/components_map.json`, `logs/ai_usage.jsonl`, `logs/economics.json`.
- ❌ Prohibido: todo `cockpit/`, pipelines top-level `.py`, `.github/`,
  `pyproject.toml`, `requirements*.txt`, `.env`, `_archivo/`, `tests/`.

Esto **no** restringe a Claude Code (esta sesión). Restringe al modo conversación
dentro de la app Streamlit. Aún así, respeta el espíritu: la app no debería
auto-modificarse vía su propio chat.

## Antes de cada cambio en código

1. **Tests obligatorios**: tras Edit/Write/MultiEdit sobre `cockpit/`, `tests/`
   o `pyproject.toml`, el hook `.claude/scripts/posttool_check.sh` ejecuta
   `ruff check` + `pytest`. Si fallan, bloquean. No se continúa con fallos.
2. **No se commitea sin OK explícito del usuario**.
3. **No tocar pipelines top-level salvo petición explícita**: son scripts CLI
   estables con generación real y costosa.

## Convenciones de código

- Python 3.10+, type hints en código nuevo.
- Ruff configurado en `pyproject.toml` (line-length 100, reglas E/F/W/I/UP/B).
- Tests con pytest, archivos `tests/test_*.py`, sin red ni keys reales.
- Mocks para `anthropic`, `openai`, `psutil`, `dotenv` cuando aplique.
- Streaming de IA preferido sobre llamadas bloqueantes (verbose en UI).
- Cada llamada IA debe pasar por `cockpit/core/ai_client.improve_with_claude*`
  para tener retry + tracking automático en `logs/ai_usage.jsonl`.

## Modelos por defecto

- Sonnet 4.6 para generación equilibrada.
- Haiku 4.5 para iteración rápida y checks.
- Opus 4.7 solo cuando Sonnet falla en tarea técnica compleja.

Nunca uses Opus para tareas que Sonnet resuelve. Cuesta ~5× más.

## Estructura

```
cockpit/
  core/             # paths, log_parser, monitor, state, prompt_builder,
                    # runner, ai_client, api_keys, usage_tracker, sandbox,
                    # economics, optimization_advisor, components_map
  connectors/       # services/, pipelines/, sources/ con registry
  pages/            # 12 páginas Streamlit
  app.py            # entry point
  ui.py, ui_improve.py, ui_map.py, theme.py
tests/              # 119 tests, todos sin red
.github/workflows/  # CI (lint + pytest)
.claude/            # settings.json, scripts/posttool_check.sh, skills/
docs/evaluations/   # informes de auditoría con semáforo
logs/               # ai_usage.jsonl, economics.json (no commiteados)
```

## Comandos frecuentes

```bash
# Lanzar cockpit
streamlit run cockpit/app.py

# Verificar antes de cualquier cambio
ruff check cockpit/ tests/
pytest tests/ -q

# Generar guion (ejemplo)
python generar_guion.py --pdf PDFs/M3_T_ML.pdf --ep M3_T_ML --duracion-min 15

# Validar episodio
python validar_episodio.py --ep M3_T_ML --guion Guiones/M3_T_ML.txt
```

## Reglas duras

- ❌ No commitear `.env`, claves o cualquier secret.
- ❌ No skip de tests (`--no-verify`, `pytest.skip` masivo, etc.).
- ❌ No reemplazar `print()` masivamente en pipelines top-level sin tests previos.
- ✅ Mantener la batería de tests verde tras cada cambio (lo aplica el hook).
- ✅ Documentar cambios de arquitectura en `docs/architecture/`.
- ✅ Cualquier nueva llamada a IA pasa por `ai_client.improve_with_claude*`.
