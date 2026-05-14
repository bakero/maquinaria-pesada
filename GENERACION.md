# GENERACION.md — Desde dónde se generan los episodios

Mapa único y canónico del pipeline de generación de **guiones** de MaquinarIA
Pesada. Si tienes que tocar la generación, empieza aquí.

## Entry points (los únicos que generan episodios)

| Tipo | Script | Spec | Salida |
|---|---|---|---|
| **T** — Tema individual | `generar_guion_t.py` | `PODCAST_T_SPEC.md` | `Guiones/M{n}_T{k}_{slug}.txt` (mismo stem que el PDF) |
| **M** — Resumen de módulo | `generar_guion.py` | `PODCAST_M_SPEC.md` | `Guiones/M{n}_{Nombre}.txt` |

Ambos usan la **API de Anthropic Claude** (Sonnet 4.5 para generación, Haiku
para extracción de conceptos). No usan OpenAI. Codex/Claude Code se usan como
*ejecutores* que lanzan estos scripts; no escriben el guion a mano.

```bash
python generar_guion_t.py --pdf PDFs/temas/M7_T1_que_es_rag.pdf
python generar_guion.py --modulo 6 --pdf PDFs/resumenes/RESUMEN_M6_Ingenieria_Prompts.pdf
```

## Arquitectura

```
generar_guion.py (M) ─┐
                      ├─→ guion_common.py  ← núcleo compartido
generar_guion_t.py(T)─┘        │
                               ├─ cliente Anthropic, lectura de PDF
                               ├─ normalize_generated_script, enforce_fixed_phrases
                               └─ post-proceso: anti-pingpong, rebalanceo,
                                  split de bloques largos, números→palabras
                               │
                      podcast_spec.py  ← parsing + validación (validate_script_text)
                               │
                      PODCAST_T_SPEC.md / PODCAST_M_SPEC.md  ← las reglas (JSON)
```

Cada generador conserva solo lo que es **específico de su tipo**:
`build_generation_prompt` (el prompt con las reglas operativas) y
`build_verification_section`.

## Fuente única de verdad

| Qué | Dónde |
|---|---|
| Reglas (estructura, word count, blacklist, frases fijas, marcadores temporales) | `PODCAST_T_SPEC.md` / `PODCAST_M_SPEC.md` (bloque JSON) |
| Parsing de bloques + validación (`validate_script_text`) | `podcast_spec.py` |
| Post-proceso mecánico del guion | `guion_common.py` |
| Prompt de generación (instrucciones al modelo) | `build_generation_prompt` en cada generador |

No dupliques estas listas en otros ficheros: cárgalas vía `load_spec()`.

## Utilidades LEGACY (NO generan episodios)

Scripts standalone que se ejecutan a mano sobre guiones `.txt` ya escritos.
No forman parte del pipeline y nada los importa:

- `fix_guiones_v4.py` — corrige hard-fails mecánicos en guiones existentes.
- `rebalance_blocks.py` — rebalanceo manual de palabras por bloque/speaker.
- `normalizar_guiones.py` — conversor de formato B (codex antiguo) → A.
  ⚠️ Genera estructura **pre-v5** (`BLOQUE_1..4`, `INSERCION`) incompatible con
  el validador actual. No usar sobre guiones v5.

## Validación del producto final

- `validar_episodio.py` — valida el **MP3 + log** (duración, tamaño, bloques).
- `cockpit/core/verifications.py` — checks ligeros desde la cockpit.
