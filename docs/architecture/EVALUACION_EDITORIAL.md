# Capa editorial — arquitectura

Documenta cómo encaja la **capa de evaluación editorial** con las dos capas
técnicas ya existentes en el repositorio.

## Tres capas de evaluación

```
                ┌──────────────────────────────┐
                │  Guion .txt generado          │
                └──────────────┬───────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │  Capa 1 — Generación con retry interno       │
        │  generadores/base_generator.run_pipeline()   │
        │  - llamada Claude + post_process_text()      │
        │  - validate_fn(...)  → list[ValidationResult]│
        │  - retry con _RULE_ACTION_HINTS              │
        └──────────────┬───────────────────────────────┘
                       │   (ya validado técnicamente, ok=True)
                       ▼
        ┌──────────────────────────────────────────────┐
        │  Capa 2 — Validación técnica externa         │
        │  validar_episodio_v6.py + validators/*       │
        │  podcast_spec.validate_script_text (legacy)  │
        │  - 54+ checks HARD/SOFT                      │
        │  - frases canónicas, secciones, balances,    │
        │    blacklists, expansión de siglas...        │
        └──────────────┬───────────────────────────────┘
                       │   (pasa los HARD, alguna soft tolerable)
                       ▼
        ┌──────────────────────────────────────────────┐
        │  Capa 3 — Evaluación editorial               │
        │  evaluador_editorial.py + editorial/*        │
        │  - panel de 5 perspectivas                   │
        │  - score 1-10, veredicto 3 niveles           │
        │  - asimetría de marca                        │
        └──────────────────────────────────────────────┘
```

## Qué evalúa cada capa

| Capa | Pregunta | Severidad | Bloquea? |
|---|---|---|---|
| 1 (retry interno) | ¿La regla técnica falla? | HARD/SOFT | Sí: HARD bloquea retry hasta corregir |
| 2 (validación externa) | ¿El guion final pasa todas las reglas técnicas? | HARD/SOFT | HARD = REJECT operativo |
| 3 (editorial) | ¿Es un BUEN podcast? | crítico/relevante/menor | crítico en MARCA = BLOQUEAR |

## Dónde ocurre la validación técnica de v6.1

Las 3 reglas editoriales que se promovieron a técnico desde el desempate
2026-05-19 viven en la capa 2:

| Regla | Archivo | Severidad |
|---|---|---|
| `glossary_term_first_use_expanded` | `validators/shared/glossary_expansion.py` | HARD (M, T) |
| `blacklist_ai_bro` | `validators/shared/blacklist.py` | HARD (M, T, S) |
| `blacklist_coach` | `validators/shared/blacklist.py` | HARD (M, T, S) |
| `blacklist_cliffhanger` | `validators/shared/blacklist.py` | HARD (M, T, S) |

Cuando el panel editorial detecta uno de estos patrones, **NO los reporta**:
ya están eliminados desde la capa técnica. El panel solo se ocupa de lo
que el validador no puede medir mecánicamente (tono, postura, frase-fuerza,
saturación de ejemplos, deriva de marca a lo largo del corpus).

## Relación con el cierre canónico

El cierre canónico (`"Y hasta aqui ha llegado nuestro episodio..."`) es
HARD-FAIL en la capa 2. El panel editorial **NO lo juzga**: el eje `cierre`
solo evalúa la **intervención previa** (CTA M / puente T) y cómo enlaza
con la frase canónica.

## Sistema de información

| Output | Origen | Formato |
|---|---|---|
| `costes_generacion.log` | capa 1 (`anthropic_client.track_cost`) | CSV |
| `logs/episode_state/{ep}.json` | `episode_state.py` durante producción audio | JSON |
| Reporte de validación técnica | `validar_episodio_v6.py` | stdout + exit code |
| Reporte editorial | `evaluador_editorial.py` (capa 3) | Markdown / JSON |

El reporte editorial JSON está pensado para consumo programático futuro
(cockpit web mostrando semáforo por guion). Su esquema está versionado en
`editorial/report.py::render_json`.

## Decisiones de integración (registro)

Las 8 decisiones del desempate 2026-05-19 están registradas en:

- `EVALUADOR_EDITORIAL_GUIONES.md §11`
- `PODCAST_MASTER_SPEC.md §13`

Cualquier ajuste futuro de la integración (relajar HARD a SOFT, ampliar
listas negras, traducir más entradas del glosario, etc.) debe actualizar
ambos documentos.
