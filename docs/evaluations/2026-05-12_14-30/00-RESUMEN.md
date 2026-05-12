═══════════════════════════════════════════════════════════════
  EVALUACIÓN TÉCNICA — MaquinarIA Pesada (generación contenido IA)
  Fecha: 2026-05-12_14-30    Repos analizados: 1
═══════════════════════════════════════════════════════════════

# Resumen ejecutivo

Sistema CLI Python + cockpit Streamlit para generación automática de podcasts/vídeos con IA (Anthropic Claude, OpenAI, Whisper, ElevenLabs, Kling). Arquitectura del cockpit bien diseñada (registro de connectors). Scripts de pipeline monolíticos (>500 líneas varios). **Cero tests automatizados**, **sin CI**, observabilidad basada en `print()`. Sin secrets hardcodeados ni `.env` en git. Stack no-web → áreas 04/05 no aplican.

## Panel

```
ÁREA                           ESTADO    PUNTUACIÓN   VS ANTERIOR
─────────────────────────────────────────────────────────────────
01. Calidad de código            🟡        5/10        — (1ª eval)
02. Patrones                     🟡        6/10        —
03. Tests                        🔴        0/10        —
04. Frontend (React)             ⚪        N/A         — (Streamlit)
05. Base de datos                ⚪        N/A         — (sin BD)
06. Seguridad             [×2]   🟢        7/10        —
07. CI/CD y entornos             🔴        2/10        —
08. Documentación                🟡        6/10        —
09. Dependencias                 🟡        5/10        —
10. Observabilidad               🔴        3/10        —
11. Sistemas de IA        [×2]   🟡        6/10        —
─────────────────────────────────────────────────────────────────
PUNTUACIÓN GLOBAL                🟡        4.5/10      —

BLOQUEOS CRÍTICOS: 3   MEJORABLES: 5   CORRECTOS: 1   N/A: 2

⚠️  ALERTAS LEGALES: AI Act ago-2025 (transparencia) · RGPD si hay PII en PDFs
```

## Top 3 acciones inmediatas

1. **🔴 Tests baseline (pytest + smoke de pipelines críticos)**
   → Plan Maestro: **PR 7** — "Baseline Playwright + smoke tests" (Bloque 1) — *adaptar a pytest, no Playwright*

2. **🔴 Pipeline CI mínimo (lint + ruff + smoke + verificación `.env.example`)**
   → Plan Maestro: **PR 9** — "CI GitHub Actions completo" (Bloque 1)

3. **🟡 Sustituir 428 `print()` por `logging` estructurado + correlation_id por episodio**
   → Plan Maestro: **PR 16** — "Logs centralizados (sin PII)" (Bloque 2)

## Hallazgos clave por área

### 01 · Calidad de código 🟡 (5/10)
- 18.119 LOC Python · 19 ficheros >300 líneas · top: `podcast_spec.py` 918L, `generar_episodio_v2.py` 811L, `generar_guion.py` 791L
- Sin linting (ruff/flake8/black) configurado
- Solo 3 TODO/FIXME (señal positiva)
- → PR 25, PR 29 (modularización + limpieza)

### 02 · Patrones 🟡 (6/10)
- **Cockpit bien diseñado**: `cockpit/{core,connectors,pages}` con separación clara y registro de connectors (`base.py`). Esto es la mejor parte del sistema.
- Scripts top-level monolíticos sin separación clara (validación + IO + IA + parsing en mismo fichero).
- Sin validación de inputs con pydantic.
- → PR 26 (módulos backend)

### 03 · Tests 🔴 (0/10)
- **Cero archivos de test**. Ni unitarios, ni smoke, ni integración.
- 78 commits en 4 semanas sin red de seguridad.
- → **PR 7 + PR 8** (críticos, primer Bloque)

### 06 · Seguridad ×2 🟢 (7/10)
- ✅ Sin secrets hardcodeados (verificado con grep `sk-*`, `xi-api-*`, JWT)
- ✅ `.env` en `.gitignore`, `.env.example` limpio
- ✅ Solo `.env.example` está commiteado
- ✅ API keys leídas vía `os.getenv()`
- 🟡 Sin LICENSE
- 🟡 Sin política de incidentes / data breach response (aplica si hay datos personales)
- → PR 0 ya pasado en buena parte; PR 23 pendiente (runbooks)

### 07 · CI/CD 🔴 (2/10)
- ❌ Sin `.github/workflows/`
- ❌ Sin branch protection en `master`
- ❌ Sin rama `develop`
- ❌ Sin tags de versión
- ✅ Repo activo (78 commits/4 semanas) — pero sin red
- → **PR 9 + PR 10** (críticos)

### 08 · Documentación 🟡 (6/10)
- ✅ Documentación funcional rica: `BIBLIA_SISTEMA.md` (1119L), `PODCAST_*_SPEC.md`, `APPCONTENIDOS.md`
- ✅ `README.md` (73L), `.env.example`, `WORKFLOW_PAIR_PROGRAMMING.md`
- ❌ Sin `CLAUDE.md` (con la skill `init` se puede generar)
- ❌ Sin `docs/architecture/`, sin ADRs, sin CHANGELOG, sin LICENSE
- → PR 1 (CLAUDE.md), PR 2 (auditoría funcional formal)

### 09 · Dependencias 🟡 (5/10)
- Python only: 14 deps directas (Streamlit, anthropic, openai-whisper, pdfplumber, etc.)
- ❌ Todas con `>=` (sin pinning estricto, sin lockfile)
- ❌ Sin `pip-audit` ejecutado en CI
- ❌ Sin SBOM
- → PR 9 (audit en CI) + considerar `uv`/`poetry` para lockfile

### 10 · Observabilidad 🔴 (3/10)
- **428 llamadas `print()`** vs 1 fichero usando `logging` real
- Existe `runlog.py` y `cockpit/core/log_parser.py` (semilla buena, infrautilizada)
- ❌ Sin Sentry/Datadog
- ❌ Sin `correlation_id` por episodio (importante para depurar pipelines largos)
- ❌ Sin trazabilidad de qué modelo IA respondió qué (ver área 11)
- → **PR 16** (logs estructurados) + PR 15 (versionado de pipeline ejecutado)

### 11 · Sistemas de IA ×2 🟡 (6/10)

**FASE A — Detectado:**
| Proveedor | Modelo(s) | Uso | Ubicación |
|-----------|-----------|-----|-----------|
| Anthropic Claude | `claude-sonnet-4-5`, `claude-haiku-4-5` | Generación guiones, debate dual | `generar_guion.py`, `generar_guion_t.py`, `dual_debate_maquinaria.py` |
| OpenAI GPT | `gpt-4o`, `gpt-4o-mini` | Debate dual, generación | `dual_debate.py`, `dual_debate_maquinaria.py` |
| OpenAI Whisper | local | Transcripción audio | `maquinaria_pesada_pipeline/pipeline/transcriber.py` |
| ElevenLabs | TTS | Voz de los podcasts | `generar_episodio_v2.py`, `cockpit/connectors/services/elevenlabs.py` |
| Kling | video gen | Generación de escenas | `maquinaria_pesada_pipeline/pipeline/kling_generator.py` |

**FASE B — Arquitectura:**
- ✅ Sistema CLI local — no hay frontend público con API keys expuestas
- ✅ API keys SOLO en `os.getenv()` (correcto)
- 🟡 Prompts dispersos en cada script (no centralizados en `prompts/`)
- 🟡 Sin capa de abstracción IA común (cada script importa `anthropic.Anthropic()` directo)

**FASE D — Calidad de integración:**
- ✅ `max_tokens` configurado siempre
- ✅ Retry/backoff en `kling_generator.py` (vídeo)
- 🔴 **Sin retry/backoff en llamadas Claude/OpenAI** — un 429 rompe el pipeline
- 🔴 Sin trazabilidad: no se registra `(modelo, tokens_in, tokens_out, timestamp)` por llamada → no se puede saber qué generación costó qué
- 🟢 Existe `validar_episodio.py` (398L) → **supervisión humana presente en forma de QA automatizada** — bien

**FASE E — Legal:**
- AI Act: contenido generado (no decisiones sobre personas) → **Riesgo mínimo/limitado**
  - Obligación ago-2025: **informar al oyente que el contenido es generado por IA** (verificar en intro/outro de los podcasts)
- RGPD: PDFs procesados son materiales técnicos → riesgo bajo, pero **verificar manualmente** que ningún PDF contiene datos personales
- ❌ Sin DPA documentado con Anthropic/OpenAI/ElevenLabs (deberían figurar)
- ❌ Transferencia internacional (Anthropic/OpenAI/ElevenLabs en EE.UU.) sin documentar — añadir a `docs/legal/`

## Adaptación del Plan Maestro a este proyecto

⚠️ **El Plan Maestro está diseñado para webapp con Supabase + Vercel + beta testers.** Aplican parcialmente:

| Bloque 1 PR | Aplica | Adaptación |
|---|---|---|
| PR 0 — Auditoría secrets | ✅ Parcial | Ya OK en gran parte; falta `pip-audit` |
| PR 1 — CLAUDE.md + legales | ✅ | Sí, crear |
| PR 2 — Auditoría funcional | ✅ | Sí, formalizar lo que hay en `.md` sueltos |
| PR 5 — Inventario backend Supabase | ❌ | No aplica (sin Supabase) |
| PR 6 — Entorno PRE | 🟡 | Reformular: separación `episodios_test/` vs `episodios/` |
| PR 7 — Tests E2E | ✅ | Reformular: smoke de pipelines con pytest |
| PR 8 — Tests auth/RLS | ❌ | No aplica (sin auth) |
| PR 9 — CI completo | ✅ | Crítico |
| PR 10 — Branch protection | ✅ | Crítico |
| PR 20/21 — RLS | ❌ | No aplica |
| PR 22 — RGPD endpoints | ❌ | No aplica (sin usuarios) |

**PRs ad-hoc a añadir** (no existen en el plan):
- PR-IA-1: Capa de abstracción IA con retry/backoff común
- PR-IA-2: Centralizar prompts en `prompts/*.py` con versionado
- PR-IA-3: Trazabilidad de llamadas IA (modelo + tokens + coste por episodio)
- PR-IA-4: Política de transparencia "este podcast está generado con IA" en intro/outro

---

Informe completo: `docs/evaluations/2026-05-12_14-30/`
═══════════════════════════════════════════════════════════════
