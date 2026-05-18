# Auditoría de invocaciones a pipelines legacy (pre-Fase 8)

Fecha: 2026-05-17

Pipelines legacy en la raíz que la Fase 8 propone deprecar:

- `generar_guion.py` (M legacy)
- `generar_guion_t.py` (T legacy)
- `fix_guiones_v4.py`
- `normalizar_guiones.py`
- `rebalance_blocks.py`
- `validar_episodio.py` (vs. `validar_episodio_v6.py`)
- `podcast_spec.py::validate_script_text`

## Invocadores detectados

### Scripts top-level

| Script | Legacy referenciado | Estado |
|---|---|---|
| `lanzar_guiones.py` | `generar_guion.py`, `generar_guion_t.py` | **Activo legacy** — migrar a `lanzar_produccion_v6.py` (existente). |
| `producir_episodio.py` | wrapper sobre legacy | **Activo** — evaluar si todavía se usa en producción o si se elimina. |
| `produce_pending.py` | `generar_guion*` | **Activo** — migrar a v6. |
| `run_iteration.py` | `validar_episodio.py` legacy | **Activo** — migrar a `validar_episodio_v6.py` / `entrenar_v6.py`. |
| `estado_proyecto.py` | lectura de logs legacy | **Compatible** — solo lee logs, no invoca generación. Mantener. |

### Cockpit (FastAPI)

| Archivo | Referencia | Estado |
|---|---|---|
| `cockpit/connectors/pipelines/generar_guion.py` | wrapper que invoca el top-level | **Migrar** — debe llamar a `generadores.m_generator.generate`. |
| `cockpit/connectors/pipelines/generar_guion_t.py` | idem | **Migrar** — a `generadores.t_generator.generate`. |
| `cockpit/connectors/pipelines/normalizar_guiones.py` | utilidad | **Mantener** — opcional manual, no afecta pipeline v6. |
| `cockpit/connectors/pipelines/validar_episodio.py` | wrapper | **Migrar** — a `validar_episodio_v6.py`. |
| `cockpit/connectors/pipelines/validar_episodio_v6.py` | wrapper v6 | **Ya está OK** |
| `cockpit/core/{episode_sources, components_map, monitor, pizarra, gen_log, usage_tracker}.py` | strings con nombres de scripts | **Revisar** — algunos solo listan nombres conocidos; otros invocan vía `Runner`. |

### Documentación

| Doc | Mención |
|---|---|
| `GENERACION.md` | descripción funcional, **actualizar** para reflejar v6 como camino canónico. |
| `MIGRACION_V6_PLAN.md` | ya describe la transición. |
| `BIBLIA_SISTEMA.md`, `PRIMERPODCAST.md`, `VIDEOPODCAST.md`, `PODCAST.md` | mencionan filename como artefacto histórico — sin impacto técnico. |
| `CLAUDE.md` | aclarar que los legacy van a `_legacy/`. |

### Tests

`tests/test_generar_episodio.py` y otros usan los legacy. La Fase 8.3 propone validar equivalencia sobre 30 episodios antes de mover/borrar.

## Plan de migración (paso a paso)

1. **Migrar invocadores activos** (`lanzar_guiones.py`, `produce_pending.py`, `producir_episodio.py`, `run_iteration.py`) → cambiar import por el v6 correspondiente. Hacer con tests de smoke.
2. **Migrar wrappers de cockpit** en `cockpit/connectors/pipelines/`. Mantener el filename pero que invoque `generadores/*_generator.py`.
3. **Validar equivalencia** con 30 episodios reales (10 M + 10 T + 10 S). Generar con legacy y moderno, comparar pass-rate, word_count y eval humana muestra.
4. **`git mv` legacy a `_legacy/`** (preserva historia). Ver script `scripts/move_legacy.sh`.
5. Tras 2 semanas sin issues, `git rm -rf _legacy/`.

## Criterios de aceptación

- [ ] Ningún script top-level no-legacy importa `generar_guion`, `generar_guion_t`, `fix_guiones_v4`, `rebalance_blocks`, `validar_episodio` (no `_v6`).
- [ ] Cockpit ejecuta generación M / T / S vía `generadores/*_generator.py`.
- [ ] `lanzar_produccion_v6.py` es el entry point oficial documentado.
- [ ] Equivalencia validada sobre 30 episodios.
- [ ] Legacy movido a `_legacy/` (PR 1).
- [ ] Tras 2 semanas sin issues, borrado definitivo (PR 2).
