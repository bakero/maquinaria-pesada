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
        │  validar_episodio.py + validators/*          │
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

## Sincronización generador ↔ validador

Las capas 1 y 2 están unidas por un contrato bidireccional. **Toda regla
HARD del validador (capa 2) tiene su descripción en el SYSTEM_PROMPT del
generador (capa 1).** Si la regla se modifica, las dos se cambian en el
mismo PR. El razonamiento está en `CLAUDE.md §"Sincronización generador ↔
validador"`.

### Flujo de actualización de una regla

Supongamos que quieres añadir una nueva regla `blacklist_X` que rechaza
intervenciones que empiezan con la frase "patrón_indeseado":

1. **Validator** — `validators/shared/blacklist.py`:
   - Añade la frase a la tupla `BLACKLIST_X_PHRASES`.
   - Añade la función `check_X_phrases(interventions)` que devuelve
     `ValidationResult` con `rule_name="blacklist_x"`.
   - Añade la llamada en `check_all(...)`.

2. **System prompt** — `generadores/{m,t,s}_generator.py`:
   - Añade un bullet a la sección "BLACKLISTS EDITORIALES" del
     `SYSTEM_PROMPT` mencionando textualmente la frase prohibida.
   - Si la regla solo aplica a un tipo (p.ej. solo M), añade solo en
     ese prompt.

3. **Retry hint** — `generadores/base_generator.py::_RULE_ACTION_HINTS`:
   - Añade la entrada `"blacklist_x": "ACCIÓN: elimina la frase..."`
     con instrucciones accionables para el modelo cuando el retry se
     dispare por esa regla.

4. **Test de paridad** — `tests/validators/test_generator_parity.py`:
   - Añade la tupla `("blacklist_x", "MTS", ["patrón_indeseado", ...])`
     a `RULE_PROMPT_PARITY`. El test parametrizado se generará
     automáticamente y fallará si olvidaste el paso 2.

5. **Validator caller** — si la regla nueva NO se llama desde
   `check_all(...)` (porque es específica de M o T), añade la llamada
   en `validators/m_validator.py::validate()` o
   `validators/t_validator.py::validate()`.

6. **Spec normativa** — `PODCAST_MASTER_SPEC.md §13`:
   - Documenta la regla y su severidad en la tabla correspondiente.

7. **Documento editorial** — si la regla nace de la capa editorial v6.1,
   actualiza también `EVALUADOR_EDITORIAL_GUIONES.md §11`.

### El test que mantiene el contrato

`tests/validators/test_generator_parity.py` itera sobre la lista
`RULE_PROMPT_PARITY` y, para cada par `(regla, kind)`, verifica que
alguna de las `keywords` esperadas aparece textualmente en el
`SYSTEM_PROMPT` del generador correspondiente. Falla con mensaje
accionable si:

- Has añadido una regla nueva al validador pero no al prompt.
- Has cambiado el nombre de la regla en el validator sin actualizar el
  test.
- Has reescrito el SYSTEM_PROMPT eliminando el bloque que cubría una
  regla técnica viva.

El test también ejecuta una verificación inversa (`test_all_listed_rules_
exist_in_validators`) para evitar que la lista de paridad se desfase
hacia el otro lado (cubrir reglas obsoletas que ya no existen).

## Sistema de información

| Output | Origen | Formato |
|---|---|---|
| `costes_generacion.log` | capa 1 (`anthropic_client.track_cost`) | CSV |
| `logs/episode_state/{ep}.json` | `episode_state.py` durante producción audio | JSON |
| Reporte de validación técnica | `validar_episodio.py` | stdout + exit code |
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
