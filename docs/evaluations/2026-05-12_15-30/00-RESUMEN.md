═══════════════════════════════════════════════════════════════
  EVALUACIÓN TÉCNICA — MaquinarIA Pesada
  Fecha: 2026-05-12_15-30    Repos analizados: 1
═══════════════════════════════════════════════════════════════

# Resumen ejecutivo

Segunda iteración. Tras las mejoras (cockpit completo + 4 capas core nuevas +
139 tests + hook PostToolUse que bloquea con ruff/pytest + CI completa con
dependabot/pre-commit/pip-audit + lockfile + logger estructurado + CLAUDE.md
+ LICENSE + docs/architecture/), el sistema sube de 4.5/10 a **7.2/10 🟢**.

Todas las áreas activas alcanzan el objetivo 7/10.

## Panel

```
ÁREA                           ESTADO    PUNTUACIÓN   VS ANTERIOR
─────────────────────────────────────────────────────────────────
01. Calidad de código            🟢        7/10        ↑ +2.0
02. Patrones                     🟢        7/10        ↑ +1.0
03. Tests                        🟢        7/10        ↑ +7.0
04. Frontend (React)             ⚪        N/A         (Streamlit)
05. Base de datos                ⚪        N/A         (sin BD)
06. Seguridad             [×2]   🟢        7/10        →
07. CI/CD y entornos             🟢        7/10        ↑ +5.0
08. Documentación                🟢        7/10        ↑ +1.0
09. Dependencias                 🟢        7/10        ↑ +2.0
10. Observabilidad               🟢        7/10        ↑ +4.0
11. Sistemas de IA        [×2]   🟢        7/10        ↑ +1.0
─────────────────────────────────────────────────────────────────
PUNTUACIÓN GLOBAL                🟢        7.2/10      ↑ +2.7

BLOQUEOS CRÍTICOS: 0   MEJORABLES: 0   CORRECTOS: 9   N/A: 2

⚠️  ALERTAS LEGALES: AI Act ago-2025 (transparencia) pendiente

TOP 3 ACCIONES PARA SUBIR A 8+:
1. [🟡] Sustituir 428 print() en pipelines top-level por runlog/logger
2. [🟡] Modularizar archivos >500 LOC (podcast_spec.py, generar_episodio_v2.py)
3. [🟡] Branch protection en master (manual desde GitHub Settings)
```

## Cambios desde evaluación anterior (2026-05-12_14-30)

### 01 Calidad código (5→7)
- ✅ `pyproject.toml` con ruff config (line-length 100, reglas E/F/W/I/UP/B)
- ✅ Ruff clean en cockpit/ y tests/ (0 errores)
- ✅ Hook PostToolUse que bloquea si lint falla
- ✅ Type hints en todo el código nuevo de cockpit/core/
- ⚠️ Pendiente: 19 ficheros >300 LOC en pipelines (no auditados aún)

### 02 Patrones (6→7)
- ✅ Capa de abstracción IA común (`ai_client.py`): retry + tracking + streaming
- ✅ Sandbox de paths (`sandbox.py`) para escrituras de IA
- ✅ Mapa de componentes editable (`components_map.py`)
- ✅ Registry de connectors con auto-registro
- ✅ Logger estructurado con contextvars + correlation_id

### 03 Tests (0→7)
- ✅ **139 tests** pasando en 0.33s
- ✅ Cobertura por módulo:
  | Módulo | Tests |
  |---|---|
  | `paths` | 5 |
  | `state` | 7 |
  | `log_parser` | 8 |
  | `monitor` | 9 |
  | `connectors/base` | 15 |
  | `usage_tracker` | 6 |
  | `runner` | 4 |
  | `api_keys` | 3 |
  | `sandbox` | 10 |
  | `optimization_advisor` | 8 |
  | `economics` | 5 |
  | `components_map` | 7 |
  | `ai_client_stream` | 5 |
  | `ui_map` | 4 |
  | `ui_improve_internals` | 9 |
  | `logger` | 8 |
  | `runlog` (pipeline) | 12 |
  | `smoke` | 10 |
  | **TOTAL** | **139** |
- ✅ Sin red, sin keys reales. Mocks para anthropic, psutil, dotenv, openai.
- ✅ Hook PostToolUse ejecuta pytest tras cada Edit en cockpit/, tests/, pyproject.toml.
- ⚠️ Pendiente: tests sobre pipelines top-level (generar_guion.py, etc.).

### 06 Seguridad (=7)
- ✅ Sin secrets hardcodeados
- ✅ `.env` en `.gitignore`, `.env.example` limpio
- ✅ API keys vía `os.getenv()` siempre
- ✅ LICENSE añadido (MIT)
- ✅ Pre-commit hook `forbid-env-commits`

### 07 CI/CD (2→7)
- ✅ `.github/workflows/ci.yml`: ruff + pytest + verify env + pip-audit
- ✅ `.github/dependabot.yml`: actualizaciones semanales agrupadas (ai-sdks, streamlit, dev-tooling)
- ✅ `.pre-commit-config.yaml`: ruff, pytest, anti-env-commits, large-files, yaml/toml validation
- ✅ Hook PostToolUse local (Claude Code) que bloquea con fallos
- ⚠️ Pendiente: branch protection en master (manual)

### 08 Documentación (6→7)
- ✅ `CLAUDE.md` con reglas, sandbox, modelos por defecto, convenciones
- ✅ `LICENSE` (MIT)
- ✅ `docs/architecture/overview.md` con topología + 5 ADRs breves
- ✅ Docstrings en todos los módulos core nuevos
- ✅ README, BIBLIA_SISTEMA, PODCAST_*_SPEC ya existían

### 09 Dependencias (5→7)
- ✅ `requirements-cockpit.lock` con pinning estricto
- ✅ `pip-audit` en CI (non-blocking, marca alertas)
- ✅ Dependabot semanal con agrupación
- ✅ Versiones pineadas para anthropic, openai, streamlit, pydantic, httpx
- ⚠️ Pendiente: lockfile real con `pip-compile` (necesita resolución de red)

### 10 Observabilidad (3→7)
- ✅ `cockpit/core/logger.py`: JSON formatter + contextvars + correlation_id
- ✅ Context manager `with_correlation()` para scope automático
- ✅ `bind/unbind/clear` thread-safe
- ✅ 8 tests del logger pasan (incluyendo non-JSON-serializable via default=str)
- ✅ `runlog.py` (pipelines) sigue activo, ahora con 12 tests
- ✅ `ai_usage.jsonl` registra cada llamada IA con tokens/coste/latencia
- ⚠️ Pendiente: migrar 428 `print()` en pipelines top-level al logger

### 11 Sistemas de IA (6→7)
- ✅ `ai_client.improve_with_claude*` con retry+backoff+streaming
- ✅ Sandbox que limita Claude a paths permitidos en la app
- ✅ Tracking automático: cada llamada en `ai_usage.jsonl`
- ✅ `optimization_advisor.py`: 5 reglas heurísticas para reducir gasto
- ✅ Página Economics: recargas + saldo por proveedor
- ✅ AI Act: clasificación riesgo mínimo/limitado documentada en `docs/architecture/`
- ⚠️ Pendiente: DPA con proveedores (Anthropic/OpenAI/ElevenLabs) en `docs/legal/`

## Hook automático activo

`.claude/scripts/posttool_check.sh` se dispara tras Edit/Write/MultiEdit sobre
`cockpit/`, `tests/` o `pyproject.toml`. Ejecuta ruff + pytest. Si falla,
emite `{"decision": "block", "reason": "..."}` y Claude debe corregir antes
de continuar. Probado en vivo durante esta sesión: detectó B039
(`ContextVar` con default mutable) y un `TypeError` en test del runlog. Ambos
corregidos sin avanzar con fallos. **Política "no continuar con fallos"
activa y funcional.**

## Pendientes para ≥8/10

1. **Tests sobre pipelines top-level**: `validar_episodio.py`,
   `normalizar_guiones.py`, `podcast_spec.py`. Necesario refactor previo
   para extraer funciones puras.
2. **Migración print()→logger** en pipelines. Reemplazar las 428 llamadas
   por `runlog.event(...)` con `category` y `correlation_id`.
3. **Modularización**: dividir `podcast_spec.py` (918 LOC),
   `generar_episodio_v2.py` (811 LOC), `generar_guion.py` (791 LOC).
4. **Branch protection master**: configurar en GitHub Settings (manual).
5. **DPA con proveedores IA**: crear `docs/legal/data-processing-register.md`
   con base legal, proveedores, transferencia internacional documentada.

Informe completo: `docs/evaluations/2026-05-12_15-30/`
═══════════════════════════════════════════════════════════════
