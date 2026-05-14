# Arquitectura — MaquinarIA Pesada

## Resumen

Sistema CLI Python + Streamlit que orquesta múltiples motores IA (Anthropic,
OpenAI, Whisper, ElevenLabs, Kling) para producir podcasts y vídeos a partir
de PDFs fuente.

## Topología

```
PDFs/              ──┐
                     │  generar_guion.py (Anthropic + OpenAI)
                     ▼
Guiones/*.txt      ──┐
                     │  generar_episodio_v2.py (ElevenLabs)
                     ▼
episodios/*.mp3    ──┐
                     │  validar_episodio.py (QA)
                     ▼
                  validación
                     │
escaletas/*.json ◀── escaleta_generator.py
                     │
                     │  video_compositor.py (Kling + ffmpeg)
                     ▼
Videos/*.mp4
```

El **cockpit** (`cockpit/`) es el centro de control: orquesta, monitoriza y
permite mejorar cada pieza vía Claude. **No reemplaza** los pipelines: los
ejecuta vía `cockpit/core/runner.py` con streaming de stdout.

## Capas

### 1. Pipelines top-level (estables, costosos)

Cada `.py` raíz es un script CLI con `argparse`. Llaman directamente a las
APIs IA con `os.getenv()` para credenciales. Producen artefactos en
`Guiones/`, `episodios/`, `Videos/`, `escaletas/`. No están testeados al 100 %
todavía — la batería de tests se centra en helpers puros.

### 2. Cockpit (UI y orquestación)

#### Core (`cockpit/core/`)
| Módulo | Responsabilidad |
|---|---|
| `paths` | Resolución central de rutas vía `REPO_ROOT`. |
| `state` | Inventario M0..M14 (PDF/guion/audio/vídeo/log). |
| `log_parser` | Parseo JSONL preferido + fallback texto. |
| `monitor` | Detección de procesos Python en ejecución (psutil). |
| `runner` | Subprocess streaming para ejecutar pipelines desde la UI. |
| `prompt_builder` | Construcción de comandos CLI para «copia-pega a Codex». |
| `ai_client` | Cliente Anthropic común: retry+backoff+streaming+tracking. |
| `usage_tracker` | Persistencia de `logs/ai_usage.jsonl` + agregados. |
| `api_keys` | Verificación de keys (Anthropic, OpenAI, ElevenLabs). |
| `economics` | Recargas manuales y cálculo de saldo por proveedor. |
| `optimization_advisor` | Heurísticas sobre el log para detectar gasto subóptimo. |
| `sandbox` | Whitelist de paths que Claude puede escribir desde la app. |
| `components_map` | Modelo del grafo de componentes + persistencia JSON. |
| `logger` | Logging estructurado JSON con `correlation_id`. |

#### Connectors (`cockpit/connectors/`)
Registry de **services** (Anthropic, OpenAI, ElevenLabs, ffmpeg, codex),
**pipelines** (mapean scripts CLI a formularios) y **sources** (PDF, guión,
audio, vídeo, log). Cada categoría hereda de `base.py` y se auto-registra.

#### Pages (`cockpit/pages/`)
12 páginas Streamlit, cada una con su bloque «✨ Mejorar con IA»:
1. Estado (M0..M14)
2. Conectores (servicios/pipelines/fuentes)
3. Generar Prompt (formulario + ejecutor)
4. Fuentes (explorador)
5. Logs (visor con diagnóstico IA)
6. API Keys (verificación)
7. Tokens (consumo agregado)
8. Previsualizar (audio/vídeo)
9. Asistente (chat libre)
10. Optimizar (recomendaciones advisor)
11. Economics (recargas/saldos)
12. Mapa (grafo editable con chat scope-limitado)

### 3. Calidad y operación

- `tests/` — 119 tests sin red, sin keys reales. Mocks para `anthropic`,
  `psutil`, `dotenv`, `openai`.
- `.github/workflows/ci.yml` — ruff + pytest + verificación de `.env.example`.
- `.claude/scripts/posttool_check.sh` — hook PostToolUse que ejecuta ruff y
  pytest tras cada Edit/Write/MultiEdit sobre código.
- `docs/evaluations/` — informes de auditoría con semáforo por área.

## Decisiones clave (ADR-style breves)

### ADR-001 · Cockpit no toca código del pipeline
Las mejoras propuestas por la IA en la cockpit **solo** modifican contenido
generado y configuración (`components_map.json`), nunca código de la app o
pipelines. Implementado en `cockpit/core/sandbox.py`.

### ADR-002 · Streaming visible por defecto
Cualquier llamada IA usa `improve_with_claude_stream` con UI que muestra
texto incremental, contador en vivo y aviso a 2 minutos. El usuario nunca
ve "spinner sin información".

### ADR-003 · Tracking JSONL para todo
Cada llamada a IA (improvement, update, api_check) deja una línea en
`logs/ai_usage.jsonl` con tokens, coste, latencia y `source`. Esto alimenta
las páginas Tokens, Economics y Optimizar.

### ADR-004 · Retry solo en errores retryables
`ai_client._is_retryable` filtra a `RateLimitError`, `APIConnectionError`,
`APITimeoutError` y `5xx`. Backoff exponencial 1s, 2s, 4s, 8s, máximo 3
reintentos por defecto.

### ADR-005 · Streamlit-flow opcional para drag&drop
La página Mapa funciona con graphviz por defecto. Drag&drop visual requiere
`pip install streamlit-flow-component`. La dep está comentada en
`requirements-cockpit.txt` para no romper CI.

## Flujos de datos personales y compliance

Hoy el sistema procesa **PDFs técnicos** (cursos de IA) sin datos personales
identificables. **AI Act**: clasificación de riesgo mínimo/limitado
(generación de contenido, no decisión sobre personas). Obligación pendiente
(ago-2025): informar en intro/outro que el podcast está generado con IA.

**Transferencia internacional**: Anthropic, OpenAI y ElevenLabs en EE.UU.
Sin DPA documentado todavía. Pendiente añadir `docs/legal/data-processing-register.md`.
