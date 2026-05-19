# GENERACION.md — Desde dónde se generan los episodios

Mapa único y canónico de generación de guiones de MaquinarIA Pesada. Si
tienes que tocar la generación, empieza aquí.

> **Sin versiones**: este documento describe la única versión vigente del
> pipeline. Los scripts top-level no llevan sufijo numérico ni los guiones
> tampoco. Todo lo que termina en `_v4/_v5/_v6` está retirado (ver §8).

---

## 1. Entry points canónicos

Toda generación de episodios pasa por estos dos scripts:

| Acción | Script | Flags clave |
|---|---|---|
| Generar guion | `lanzar_produccion.py` | `--kind {M,T,S} --ep <id> [--term <slug> para S]` |
| Validar guion | `validar_episodio.py` | `--kind {M,T,S} --ep <id> --guion Guiones/<id>.txt` |

```bash
# Episodio de módulo
python lanzar_produccion.py --kind M --ep M3
python validar_episodio.py  --kind M --ep M3 --guion Guiones/M3.txt

# Episodio de tema
python lanzar_produccion.py --kind T --ep M3_T2
python validar_episodio.py  --kind T --ep M3_T2 --guion Guiones/M3_T2.txt

# Short
python lanzar_produccion.py --kind S --ep S1_RAG --term RAG
python validar_episodio.py  --kind S --ep S1_RAG --guion Guiones/S1_RAG.txt
```

`lanzar_produccion.py` delega cada `--kind` en el generador especialista
del paquete `generadores/` (ver §3). Cada llamada:

1. Lee las fuentes (PDF resumen/tema, glosario, fuentes-marco).
2. Construye el prompt con la pre-escritura inyectada.
3. Llama al LLM (Sonnet para M/T, Haiku para S).
4. Aplica post-process: `num2words` + `pronunciation_overrides` + SSML pauses.
5. Valida con el validador del formato.
6. Si hay HARD-FAIL, reintenta con feedback explícito desde
   `_RULE_ACTION_HINTS` en `generadores/base_generator.py`.
7. Registra la corrida en `costes_generacion.log`.
8. Guarda el guion final en `Guiones/<ep>.txt`.

---

## 2. Paquetes principales

```
generadores/                  # generación con LLM (M, T, S)
  base_generator.py             # pipeline común: prompt → LLM → post → validate → retry
  m_generator.py                # MODEL=claude-sonnet-4-6, prompt M con 26+ reglas
  t_generator.py                # MODEL=claude-sonnet-4-6, prompt T con 27+ reglas
  s_generator.py                # MODEL=claude-haiku-4-5,  prompt S anti-meta-texto
  shared/
    fuentes_loader.py             # glosario unificado (con campo **ES:**)
    anthropic_client.py           # cliente API + tracking de coste
    ...

validators/                   # validación técnica HARD/SOFT
  base_validator.py             # reglas comunes M/T/S
  m_validator.py                # exactas de M (concepts, leader shares, fuentes...)
  t_validator.py                # exactas de T (concepts=3, casos, limites...)
  s_validator.py                # exactas de S (no diálogo, hook, word count...)
  shared/
    blacklist.py                  # 5 listas (interjecciones, placeholder + 3 editoriales)
    glossary_expansion.py         # expansión castellana de siglas al primer uso (HARD)
    pedagogy_check.py             # expansión de términos al primer uso (SOFT)
    canonical_phrases.py          # frases canónicas literales
    audio_rules.py                # invariantes TTS (frases largas, números en cifra...)
    ...

evaluador/                    # auditor mecánico de specs (lectura de guion)
  cli.py                        # CLI: python -m evaluador --kind M --files Guiones/...
  rules/                        # reglas reutilizables (estructura, cast, pedagogy...)
  renderers/                    # markdown / json / terminal

editorial/                    # panel editorial multi-perspectiva (LLM)
  perspectives.py               # 5 voces: productor, marca, oyente, experto, SEO
  benchmark.py                  # mapa de referentes (Lex Fridman, Dot CSV, etc.)
  scoring.py                    # score ponderado + veredicto + asimetría de marca
  ...
                              # CLI: python evaluador_editorial.py --file Guiones/M3.txt
```

---

## 3. Diferencias por tipo (M / T / S)

### 3.1 M — Episodio de módulo (~20 min)

- **Spec**: [`PODCAST_M_SPEC.md`](PODCAST_M_SPEC.md)
- **Generador**: `generadores/m_generator.py` (Sonnet 4.5)
- **Fuente PDF**: `PDFs/resumenes/RESUMEN_M{n}_*.pdf` + 4 docs vivos.
- **Estructura**: HOOK → INTRO_SONIDO → SALUDO_Y_PRESENTACION →
  BLOQUE_PANORAMA → BLOQUE_DESTACADO → APLICACION_PRACTICA →
  BLOQUE_FUENTES → CIERRE_CONCEPTOS → CIERRE_FINAL → VERIFICACIONES.
- **Word count**: 2700-3300 (rango duro 2400-3680).
- **Reparto**:
  - PANORAMA → Yago lidera ≥60%.
  - DESTACADO → balance 35-65%.
  - APLICACION_PRACTICA → Maria 25-45%.
- **Salida**: `Guiones/M{n}.txt` (p. ej. `Guiones/M3.txt`).

### 3.2 T — Episodio de tema (~25-28 min)

- **Spec**: [`PODCAST_T_SPEC.md`](PODCAST_T_SPEC.md)
- **Generador**: `generadores/t_generator.py` (Sonnet 4.5)
- **Fuente PDF**: `PDFs/temas/M{n}_T{k}_*.pdf`.
- **Estructura**: HOOK → INTRO_SONIDO → SALUDO → BLOQUE_PANORAMA →
  BLOQUE_COMO → BLOQUE_CASOS → BLOQUE_LIMITES → BLOQUE_FUENTES →
  CIERRE_CONCEPTOS → CIERRE_FINAL → VERIFICACIONES.
- **Word count**: 3700-4500 (rango duro 2925-4485).
- **Reparto**:
  - PANORAMA → Yago ≥60%, LIMITES → Yago ≥50%.
  - COMO → balance 35-65%.
  - CASOS → Maria ≥55% con ≥2 empresas con nombre propio.
- **Salida**: `Guiones/M{n}_T{k}.txt` (p. ej. `Guiones/M3_T2.txt`).

### 3.3 S — Short de 60-90s

- **Spec**: [`PODCAST_S_SPEC.md`](PODCAST_S_SPEC.md)
- **Generador**: `generadores/s_generator.py` (Haiku 4.5 — más rápido y
  barato para texto corto con plantilla rígida).
- **Fuente**: una entrada del glosario unificado
  (`PDFs/auxiliares/glosario_unificado.md`) seleccionada por `--term`.
- **Estructura interna** (sin cabeceras): HOOK 5-7s → DEFINICIÓN 18-22s
  → EJEMPLO 28-35s → APLICACIÓN/GANCHO 12-18s.
- **Word count**: 157-198 palabras (~75s a 1.10× TTS).
- **Voz única** (no diálogo): la paridad alterna Yago/Maria por
  `s_number`. Sin cabeceras de sección, sin tags TTS, sin URLs, sin
  citas de papers.
- **Hook**: una de las plantillas H1 (contradicción) / H2 (número) /
  H3 (pregunta) — HARD-FAIL si no encaja.
- **Cierre**: frase canónica literal:
  > *"Más sobre [tema] en el episodio T de MaquinarIA Pesada."*
- **Salida**: `Guiones/S{n}_{term}.txt` (p. ej. `Guiones/S1_RAG.txt`).

> Los tres tipos comparten arquitectura, fuentes y validador-pipeline. Lo
> que cambia es la spec y el prompt del generador. No hay un
> `GENERACION_S.md` separado por diseño: fragmentar este doc duplicaría
> la parte común y derivaría con el tiempo.

---

## 4. Modelos por defecto

| Tipo | Modelo | Motivo |
|---|---|---|
| M (generador) | `claude-sonnet-4-6` | Equilibrio coste/calidad para narrativa larga con criterio |
| T (generador) | `claude-sonnet-4-6` | Igual: T tiene más palabras pero misma complejidad cualitativa |
| S (generador) | `claude-haiku-4-5` | Texto corto + plantilla rígida → Haiku rinde igual al 5% del coste |
| Evaluador editorial | `claude-sonnet-4-6` | Panel multi-perspectiva con criterio editorial |
| Conceptos / extracción | `claude-haiku-4-5` | Tareas mecánicas reutilizables |

`CLAUDE.md §"Modelos por defecto"` es la guía vinculante. Nunca usar Opus
para tareas que Sonnet resuelve (~5× más caro).

---

## 5. Validación: dos capas obligatorias + una editorial

```
guion .txt o .md
      │
      ▼
┌────────────────────────────────────────────────────────────┐
│ CAPA 1 — Validación técnica (HARD-FAIL bloquea)            │
│ validar_episodio.py + validators/                           │
│ ~54 reglas:                                                 │
│  · estructura, secciones, word count, frases canónicas      │
│  · reparto Yago/Maria por bloque                            │
│  · blacklists (interjecciones, AI-bro, coach, cliffhanger)  │
│  · expansión castellana de siglas al primer uso             │
│  · invariantes TTS (frases >32 palabras, números en cifra)  │
└────────────────────────────────────────────────────────────┘
      │ (pasa todos los HARD)
      ▼
┌────────────────────────────────────────────────────────────┐
│ CAPA 2 — Auditor mecánico opcional                          │
│ python -m evaluador --kind M --files Guiones/M3.txt         │
│ Reportes en markdown / JSON / terminal. Mismas reglas       │
│ técnicas que la capa 1 pero formato batch + rendering.      │
└────────────────────────────────────────────────────────────┘
      │
      ▼
┌────────────────────────────────────────────────────────────┐
│ CAPA 3 — Panel editorial (no técnico)                       │
│ python evaluador_editorial.py --file Guiones/M3.txt         │
│ 5 perspectivas: productor, marca, oyente, experto, SEO.     │
│ Score 1-10 + veredicto PUBLICAR/REVISAR/BLOQUEAR.           │
│ Asimetría: 1 crítico en MARCA = BLOQUEAR.                   │
│ Ver EVALUADOR_EDITORIAL_GUIONES.md.                         │
└────────────────────────────────────────────────────────────┘
```

---

## 6. Contrato bidireccional generador ↔ validador

**Toda regla HARD del validador tiene que estar en el SYSTEM_PROMPT del
generador correspondiente.** Y al revés. Es un contrato del PR, no algo
"a posteriori".

Cuando añadas, renombres o quites una regla:

1. Edita el validator (función, lista negra, severidad).
2. Edita el SYSTEM_PROMPT del generador con descripción humana.
3. Añade el `_RULE_ACTION_HINTS` en `generadores/base_generator.py` para
   que el retry sepa pedir la corrección concreta.
4. Añade/actualiza `RULE_PROMPT_PARITY` en
   `tests/validators/test_generator_parity.py`.
5. Documenta en `PODCAST_MASTER_SPEC.md §13` (spec normativa).

El test de paridad bloquea el PR si te olvidas de algún paso. Detalle
completo en `docs/architecture/EVALUACION_EDITORIAL.md §Sincronización`
y `CLAUDE.md §"Sincronización generador ↔ validador"`.

---

## 7. Glosario unificado (fuente de verdad)

`PDFs/auxiliares/glosario_unificado.md` es la fuente canónica de
definiciones técnicas. Cada entrada admite estas líneas estructuradas:

| Campo | Obligatorio | Función |
|---|---|---|
| `**Fuentes:**` | sí | PDFs donde aparece el concepto (M3_T1, M5_RESUMEN...) |
| `**S:**` | no | Número de orden del Short asociado al término |
| `**ES:**` | no (gradual) | Expansión castellana exigida en aposición con comas al primer uso |

Mientras el campo `**ES:**` no esté en una entrada, su sigla NO se valida
contra la regla `glossary_term_first_use_expanded`. Rollout permisivo
intencional. Ver `PODCAST_MASTER_SPEC.md §13.1`.

---

## 8. Scripts legacy retirados

Los siguientes scripts top-level **fueron borrados** del repo (eran v5
con sufijo o utilidades manuales sobre guiones pre-v5). No los uses,
no existen:

| Script borrado | Reemplazo canónico |
|---|---|
| `generar_guion.py` | `python lanzar_produccion.py --kind M --ep M<N>` |
| `generar_guion_t.py` | `python lanzar_produccion.py --kind T --ep M<N>_T<K>` |
| `lanzar_produccion.py` (versión v5) | `python lanzar_produccion.py --kind {M,T,S} --ep <id>` |
| `validar_episodio.py` (versión v5) | `python validar_episodio.py --kind ... --ep ... --guion ...` |
| `fix_guiones_v4.py` | utilidad manual, sin reemplazo (no se necesita con el nuevo pipeline) |
| `rebalance_blocks.py` | utilidad manual, sin reemplazo |
| `normalizar_guiones.py` | utilidad manual, sin reemplazo |
| `producir_episodio.py` | `lanzar_produccion.py` + `generar_episodio_v2.py` |
| `run_iteration.py` | `lanzar_guiones.py` |

Los nombres de los pipelines vigentes (`lanzar_produccion.py`,
`validar_episodio.py`) son los **únicos** y **no llevan sufijo de versión**.
Si alguien menciona `lanzar_produccion_v6.py` o `validar_episodio_v6.py`,
está mirando docs anteriores: el rename mecánico ya se hizo.

---

## 9. Documentación relacionada

- `PODCAST_MASTER_SPEC.md` — spec normativa común (incluye §13 reglas
  editoriales v6.1).
- `PODCAST_M_SPEC.md`, `PODCAST_T_SPEC.md`, `PODCAST_S_SPEC.md` — specs
  por formato.
- `EVALUADOR_EDITORIAL_GUIONES.md` — documento normativo del panel
  editorial (5 perspectivas, pesos, veredicto).
- `docs/architecture/EVALUACION_EDITORIAL.md` — arquitectura de las 3
  capas de evaluación y contrato bidireccional generador ↔ validador.
- `BIBLIA_SISTEMA.md` — biografía y posicionamiento de marca.
- `CLAUDE.md` — reglas para trabajar en el repo (tests obligatorios,
  sincronización, no commit sin OK, etc.).
