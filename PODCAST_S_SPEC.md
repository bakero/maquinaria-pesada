# Podcast S Spec — MaquinarIA Pesada

Especificación normativa para generar guiones y audio de **episodios S (Shorts)**:
píldoras de glosario de 60-90 segundos, una por término técnico seleccionado del
corpus del máster.

Los episodios M (meta-producto de módulo) tienen su spec en `PODCAST_M_SPEC.md`;
los T (temas) en `PODCAST_T_SPEC.md`.

Versión: 2026-05-14 (**v6** — formato nuevo)
Tipo: S
Duración objetivo: 60-90 segundos (objetivo 75s; audio final esperado 65-78s)

---

## 1. Filosofía del episodio S

Un episodio S es **una píldora de un único término del glosario**, pensada para
formato vertical de redes (YouTube Shorts, Reels, TikTok). Sirve a:

- Captación de audiencia nueva (los Shorts son el motor de descubrimiento).
- SEO directo: cada vídeo titulado "¿Qué es <término>?" posiciona en búsquedas.
- Tráfico hacia el podcast largo: cada S enlaza al episodio T del tema.

**Clave de diseño:** el glosario es un activo que se acumula. El S es **por
concepto**, no por episodio: un vídeo por término, reutilizable durante años,
componible en playlists ("Glosario módulo 7", "Términos para empezar con RAG").

**Lo que un S NO es:** no es un resumen de un episodio; no es un diálogo; no
lleva aviso de IA narrado; no cita papers ni URLs en el audio.

---

## 2. Principios duros

- **Una sola voz narradora.** Sin diálogo: en 75s un diálogo queda atropellado.
- Duración 60-90s hablados (objetivo 75s).
- Word count **157-198 palabras** (hard-fail fuera de rango).
- Fuente única: `PDFs/auxiliares/glosario_unificado.md`.
- Estructura interna de 4 bloques (§4).
- **Cero etiquetas TTS de tono.** El S es tan corto que cambiar de tono dentro
  suena raro; una sola entonación coherente.
- **No leer URLs ni nombres de papers** en el audio.
- Cierre canónico literal obligatorio (§5).
- Marca "MaquinarIA Pesada" mencionada **solo una vez**, en el cierre.
- El aviso de IA **no se narra**: va en la descripción del vídeo + texto en
  pantalla durante el primer segundo (decisión de diseño visual, no de guion).
- **El guion se escribe en formato neutro**, sin atribución a Yago o Maria. La
  voz es metadata del audio final (asignada por paridad del número S), no del
  guion.
- El guion debe respetar el invariante de calidad TTS sintética del §2B.
- Verificaciones reales del guion al final del archivo generado.

---

## 2B. Invariante de calidad TTS sintética (formato corto)

| Parámetro | Regla |
|---|---|
| Frases largas | Máximo 28 palabras por frase |
| Frases cortas seguidas | Máximo 2 frases <12 palabras seguidas |
| Densidad conceptual | 1 solo concepto técnico central; máx. 1 tecnicismo secundario, aterrizado |
| Muletillas | Cero |
| Pausa intra-narrador | 300ms entre bloques internos |
| Variación entonativa | Limitada → se compensa con plantilla visual + captions + música |

---

## 3. Selección y ordenación automática de Shorts

El **automatismo** decide qué términos del glosario tienen episodio S y en qué
orden se publican. **100% automático, sin intervención humana, sin override
manual.** Lo ejecuta `scripts/seleccionar_y_ordenar_shorts.py`.

### 3.1 Filtro de selección

Una entrada del glosario es candidata a S si cumple **al menos uno**:
- aparece en **≥2 módulos distintos** (transversal), o
- tiene **≥4 menciones** totales en el corpus (línea `**Fuentes:**`), o
- aparece en algún `_RESUMEN` (concepto-marco del módulo).

### 3.2 Score de ordenación

```
score = (transversalidad × 3) + min(densidad, 20) + (5 si aparece en RESUMEN)
```
- `transversalidad` = nº de módulos distintos en la línea `**Fuentes:**`.
- `densidad` = nº total de menciones (capada a 20).

### 3.3 Desempate

Cuando dos términos empatan en score: mayor transversalidad → mayor densidad →
orden alfabético del nombre canónico (estable, reproducible).

### 3.4 Numeración y escritura en el glosario

El script escribe la línea `**S:** N` en cada entrada seleccionada, donde **N es
el número de orden de publicación** (1, 2, 3...). El número es editable a mano
para controlar qué se publica primero (gancho), pero el automatismo lo asigna
por defecto según el score.

### 3.5 Propiedades obligatorias del script (con test)

- **Idempotente:** ejecutarlo dos veces sobre el mismo glosario da el mismo
  resultado.
- **Estable:** añadir términos nuevos no reordena los existentes; los nuevos se
  añaden al final del ranking.
- Genera un reporte `PDFs/auxiliares/glosario_shorts_ranking.md` con: top
  ordenado (término, score, transversalidad, densidad, en RESUMEN), excluidos
  por filtro con su motivo, y totales.

---

## 4. Estructura interna del guion S

Cuatro bloques internos. Objetivo 75s, total 157-198 palabras.

| Bloque | Duración | Palabras | Función | Regla dura |
|---|---|---|---|---|
| HOOK | 5-7s | 12-18 | Frase única que pare el scroll | Debe encajar en plantilla H1/H2/H3 |
| DEFINICIÓN | 18-22s | 45-55 | Qué es, en lenguaje plano | Máximo 3 frases, sin jerga sin explicar |
| EJEMPLO | 28-35s | 70-85 | Caso concreto que ilustra el concepto | Una analogía cotidiana O un caso técnico breve; no una lista |
| APLICACIÓN/GANCHO | 12-18s | 30-40 | Para qué sirve + cierre canónico | Termina con la frase canónica del §5 |

### 4.1 Plantillas de HOOK (lista cerrada)

El generador elige la que mejor sostiene el término. Si ninguna funciona,
regenera con parámetros distintos; no usa una por defecto.

- **H1 — Hook-contradicción.** Una afirmación que sorprende.
  *"Los modelos de lenguaje no entienden lo que dicen. Pero entender qué es un
  embedding cambia eso."*
- **H2 — Hook-número.** Una cifra impactante.
  *"El 80% de los proyectos de IA fallan por no entender bien este concepto."*
- **H3 — Hook-pregunta.** Una pregunta retórica fuerte.
  *"¿Cómo sabe ChatGPT que 'rey' y 'reina' tienen algo en común? Por esto."*

### 4.2 Cierre canónico obligatorio

La última frase debe ser **literalmente**:
> `Más sobre [tema] en el episodio T de MaquinarIA Pesada.`

Donde `[tema]` se sustituye por el módulo o tema natural derivado de la línea
`**Fuentes:**` de la entrada del glosario (p. ej. si las fuentes incluyen `M5_*`,
el cierre dice "...en el episodio T del módulo 5 de MaquinarIA Pesada").
**Hard-fail si falta o no es literal.**

---

## 5. Fuente del generador

**Fuente única: `PDFs/auxiliares/glosario_unificado.md`.**

- El generador lee la entrada del término: definición canónica + línea
  `**Fuentes:**` (para construir el `[tema]` del cierre y conocer los T
  relacionados) + número `**S:**` (para nombre de archivo y voz).
- **Modo enriquecido (opcional):** si el término aparece en `**Fuentes:**` con
  más de 15 menciones de temas distintos, el generador puede consultar **una
  sola entrada extra** (el módulo principal del término) para enriquecer el
  ejemplo. Sin saturar tokens.
- No se leen PDFs adicionales. El glosario ya es la pre-escritura.
- Hard-fail si el término no tiene entrada en el glosario.

---

## 6. Voz, nomenclatura y aviso de IA

### 6.1 Voz por paridad del número S

- **S impar → Yago. S par → Maria.**
- La voz se asigna al hacer el TTS, no en el guion (el guion es neutro).
- Si un S se regenera, conserva la voz con la que se publicó originalmente.

### 6.2 Nomenclatura de archivo

`S{N}_nombre.mp3`, donde `N` es el número de orden de publicación
(p. ej. `S1_RAG.mp3`, `S2_Embeddings.mp3`).

### 6.3 Aviso de generación por IA

**No se narra.** Se cumple con:
- una línea en la descripción del vídeo indicando contenido sintético;
- texto en pantalla durante el primer segundo del vídeo.

El spec S documenta esto pero **no genera línea hablada** para el aviso.

---

## 7. Etiquetas TTS

**Prohibidas en S.** El guion no lleva ninguna etiqueta `[tag]` de tono.
Hard-fail si aparece.

---

## 8. Reglas de producción de audio

- **Audio-Regla 1 — Números siempre en palabras** (conversión >100 vía
  `num2words`).
- **Audio-Regla 4 — Tecnicismos acelerados: introducción obligatoria.**
- **Audio-Regla 6 — Pausas SSML:** 300ms entre bloques internos.
- **Audio-Regla 7 — Loudness -14 LUFS** integrated, -1 dBTP.

### 8.1 Parámetros TTS específicos de S

Distintos de M/T: una sola voz sostenida 75s necesita más estabilidad y menos
velocidad para no sonar mecánica.

| Parámetro | M/T | **S** |
|---|---|---|
| stability | 0.65 / 0.68 | **0.78** |
| similarity_boost | 0.65 / 0.55 | **0.70 / 0.60** |
| speed | 1.20 | **1.10** |
| post_speed_multiplier | 1.10 | **1.00** |
| total efectivo | 1.32× | **1.10×** |
| normalization | -14 LUFS | -14 LUFS |

### 8.2 Modelo LLM

S usa `claude-haiku-4-5-20251001` (texto corto, plantilla rígida, ~12× más
barato que Sonnet). Política de retry: 1 reintento con feedback explícito.

---

## 9. Plantilla visual (documentación, no genera audio)

El vídeo S es 9:16 (1080×1920), plantilla **única** para todos:
- Fondo de color marca; logo MaquinarIA Pesada en esquina superior izquierda.
- El término en grande, animado al inicio; captions sincronizados (obligatorios:
  85% del consumo de Shorts es sin sonido).
- Numeración visible "N/total" en esquina inferior derecha.
- Música: stinger corto al inicio + base instrumental muy baja, igual en todos.
- Acento de color por módulo del término (plantilla única + variación de acento).

---

## 10. Diferencias estructurales S vs M/T (referencia rápida)

| Aspecto | M | T | **S** |
|---|---|---|---|
| Bloques de contenido | 4 | 6 | 4 internos |
| Voces | 2 (diálogo) | 2 (diálogo) | **1 (narrador)** |
| Etiquetas TTS de tono | Permitidas | Permitidas | **Prohibidas** |
| Aviso de IA | Enganche 18-25s narrado | Advertencia 12-18s narrado | **No narrado** (descripción + texto en pantalla) |
| HOOK | 30-60s | 30-60s | **5-7s** |
| CIERRE_CONCEPTOS | 3-5 conceptos | Exactamente 3 | **No tiene** |
| Cierre canónico | "Y hasta aquí..." | "Y hasta aquí..." | **"Más sobre [tema] en el episodio T..."** |
| Cobertura de fuente | ≥75% del PDF | ≥75% del PDF | No aplica (fuente = glosario) |
| Pre-escritura tabular | Sí | Sí | **No** (el glosario ya es la pre-escritura) |
| Modelo LLM | Sonnet | Sonnet | **Haiku** |
| TTS total efectivo | 1.32× | 1.32× | **1.10×** |

---

## 11. Validaciones (23 totales)

### 11.1 Hard-fail de guion (12)

| Regla | Detalle |
|---|---|
| `hard_fail_on_word_count_out_of_range` | Fuera de 157-198 palabras |
| `hard_fail_on_missing_hook_template` | HOOK no encaja en H1/H2/H3 |
| `hard_fail_on_missing_closing_phrase` | Falta el cierre canónico literal |
| `hard_fail_on_dialogue_format` | Aparece diálogo (`IAGO:` / `MARIA:`) |
| `hard_fail_on_tts_tags_present` | Aparece etiqueta `[tag]` |
| `hard_fail_on_more_than_4_blocks` | Más de 4 bloques internos |
| `hard_fail_on_url_in_speech` | URL o "http" en texto narrado |
| `hard_fail_on_paper_citation_in_speech` | Cita tipo "Lewis et al. 2020" en narración |
| `hard_fail_on_missing_glosario_source` | Término sin entrada en el glosario |
| `hard_fail_on_blacklist_interjection` | Las 8 interjecciones prohibidas |
| `hard_fail_on_voice_parity_mismatch` | Voz asignada no coincide con paridad de `S{N}` |
| `hard_fail_on_filename_format` | Nombre de archivo no cumple `S{N}_nombre.mp3` |

### 11.2 Soft-warn de guion (5)

| Regla | Detalle |
|---|---|
| `soft_warn_on_brand_mention_outside_closing` | "MaquinarIA Pesada" fuera del cierre |
| `soft_warn_on_intervention_over_60_words` | Bloque interno >60 palabras |
| `soft_warn_on_digit_numbers_in_speech` | Dígitos en lugar de palabras |
| `soft_warn_on_anglicismo_without_aterrizaje` | Tecnicismo inglés sin aterrizaje en la misma frase |
| `soft_warn_on_repeated_term_in_consecutive_S` | Mismo término en `S{N}` y `S{N+1}` |

### 11.3 Validación post-TTS (3)

| Regla | Detalle |
|---|---|
| `hard_fail_on_audio_duration_out_of_range` | Audio fuera de 55-95s |
| `hard_fail_on_loudness_not_minus_14_lufs` | LUFS integrated ≠ -14 ± 0.5 |
| `soft_warn_on_silent_segments_over_2s` | Silencios >2s detectados |

### 11.4 Validación de archivo (3)

| Regla | Detalle |
|---|---|
| `hard_fail_on_missing_visual_template` | Falta plantilla visual aplicada |
| `hard_fail_on_missing_captions` | Falta archivo SRT/VTT de captions |
| `hard_fail_on_aspect_ratio_not_9_16` | Vídeo no es 9:16 (1080×1920) |

---

## 12. Configuración (JSON)

<!-- PODCAST_S_SPEC_JSON_START -->
```json
{
  "version": "2026-05-14-v6",
  "spec_type": "S",
  "project_name": "MaquinarIA Pesada",
  "language": "es",
  "directories": {
    "pdfs_auxiliares_dir": "PDFs/auxiliares",
    "glosario_path": "PDFs/auxiliares/glosario_unificado.md",
    "shorts_ranking_path": "PDFs/auxiliares/glosario_shorts_ranking.md",
    "scripts_dir": "Guiones",
    "output_dir": "episodios",
    "temp_dir": "episodios/temp",
    "videos_dir": "Videos",
    "music_dir": "Música",
    "logos_dir": "Logos"
  },
  "anthropic": {
    "default_generation_model": "claude-haiku-4-5-20251001",
    "temperature": 0.7,
    "max_output_tokens": 1000,
    "stream": true,
    "retry_on_hard_fail": {
      "max_retries": 1,
      "strategy": "explicit_feedback_to_llm"
    }
  },
  "episode_defaults": {
    "duration_seconds": 75,
    "duration_range_seconds": [60, 90],
    "audio_duration_expected_seconds": [65, 78],
    "target_audience": "Audiencia amplia de redes sociales que descubre conceptos de IA en formato corto vertical.",
    "tone": "tecnico pero accesible, directo, una sola voz narradora"
  },
  "tts_invariants": {
    "max_words_per_sentence": 28,
    "max_consecutive_short_sentences": 2,
    "single_central_concept": true,
    "max_secondary_technicisms": 1,
    "no_unscripted_fillers": true,
    "ssml_pauses_ms": {"between_internal_blocks": 300}
  },
  "selection": {
    "filter": "min_2_modules_OR_min_4_mentions_OR_in_RESUMEN",
    "module_threshold": 2,
    "mention_threshold": 4,
    "resumen_inclusion": true,
    "override_manual": false
  },
  "ordering": {
    "score_formula": "transversalidad*3 + min(densidad,20) + (5 si en RESUMEN)",
    "transversalidad_weight": 3,
    "densidad_cap": 20,
    "resumen_bonus": 5,
    "tiebreak": ["transversalidad", "densidad", "alfabetico"],
    "idempotent": true,
    "stable_on_new_terms": true,
    "writes_field": "**S:** N",
    "report_path": "PDFs/auxiliares/glosario_shorts_ranking.md"
  },
  "enrichment": {
    "enabled": true,
    "trigger_min_distinct_topics": 15,
    "max_extra_entries": 1
  },
  "parity_rules": {
    "applies_to": "S_number",
    "rule": "S_impar_yago__S_par_maria",
    "voice_assigned_at_tts_not_in_script": true,
    "voice_frozen_on_regeneration": true
  },
  "naming": {
    "filename_pattern": "S{N}_nombre.mp3",
    "numbering_visible_in_video": true
  },
  "script_rules": {
    "minimum_word_count": 157,
    "maximum_word_count": 198,
    "internal_blocks": ["HOOK", "DEFINICION", "EJEMPLO", "APLICACION_GANCHO"],
    "internal_block_count_exact": 4,
    "block_word_targets": {
      "HOOK": {"min": 12, "max": 18},
      "DEFINICION": {"min": 45, "max": 55},
      "EJEMPLO": {"min": 70, "max": 85},
      "APLICACION_GANCHO": {"min": 30, "max": 40}
    },
    "hook_templates": ["H1_contradiccion", "H2_numero", "H3_pregunta"],
    "single_voice_narrator": true,
    "dialogue_forbidden": true,
    "tts_tags_forbidden": true,
    "urls_in_speech_forbidden": true,
    "paper_citations_in_speech_forbidden": true,
    "closing_phrase_template": "Más sobre [tema] en el episodio T de MaquinarIA Pesada.",
    "closing_phrase_required_literal": true,
    "brand_mention_only_in_closing": true,
    "ia_warning_narrated": false,
    "ia_warning_in_description_and_overlay": true,
    "script_neutral_no_speaker_attribution": true,
    "blacklist_validation_interjections": ["exactamente", "claro que sí", "muy bien dicho", "tienes toda la razón", "exacto", "por supuesto", "eso es", "totalmente"],
    "sources": {
      "primary": {
        "path": "PDFs/auxiliares/glosario_unificado.md",
        "required": true,
        "rule": "single_source_per_term"
      }
    }
  },
  "audio_rules": {
    "model": "eleven_v3",
    "output_format": "mp3_44100_128",
    "export_bitrate": "192k",
    "post_speed_multiplier": 1.00,
    "normalization_target_lufs": -14,
    "true_peak_target_dbtp": -1.0,
    "intra_speaker_pause_ms": 300,
    "block_separator_pause_ms": 500,
    "ssml_pauses_enabled": true,
    "voices": {
      "IAGO": {"voice_id": "CdAqYBLnsNjmTqYgD5Ha", "stability": 0.78, "similarity_boost": 0.70, "style": 0.0, "use_speaker_boost": false, "speed": 1.10},
      "MARIA": {"voice_id": "gD1IexrzCvsXPHUuT0s3", "stability": 0.78, "similarity_boost": 0.60, "style": 0.0, "use_speaker_boost": false, "speed": 1.10}
    }
  },
  "video_template": {
    "aspect_ratio": "9:16",
    "resolution": [1080, 1920],
    "captions_required": true,
    "captions_format": ["srt", "vtt"],
    "single_template_for_all": true,
    "module_accent_color": true,
    "numbering_visible": true,
    "ia_disclosure_overlay_first_second": true
  },
  "qa_rules": {
    "hard_fail_on_word_count_out_of_range": true,
    "hard_fail_on_missing_hook_template": true,
    "hard_fail_on_missing_closing_phrase": true,
    "hard_fail_on_dialogue_format": true,
    "hard_fail_on_tts_tags_present": true,
    "hard_fail_on_more_than_4_blocks": true,
    "hard_fail_on_url_in_speech": true,
    "hard_fail_on_paper_citation_in_speech": true,
    "hard_fail_on_missing_glosario_source": true,
    "hard_fail_on_blacklist_interjection": true,
    "hard_fail_on_voice_parity_mismatch": true,
    "hard_fail_on_filename_format": true,
    "soft_warn_on_brand_mention_outside_closing": true,
    "soft_warn_on_intervention_over_60_words": true,
    "soft_warn_on_digit_numbers_in_speech": true,
    "soft_warn_on_anglicismo_without_aterrizaje": true,
    "soft_warn_on_repeated_term_in_consecutive_S": true,
    "hard_fail_on_audio_duration_out_of_range": true,
    "audio_duration_range_seconds": [55, 95],
    "hard_fail_on_loudness_not_minus_14_lufs": true,
    "loudness_tolerance_lufs": 0.5,
    "soft_warn_on_silent_segments_over_2s": true,
    "hard_fail_on_missing_visual_template": true,
    "hard_fail_on_missing_captions": true,
    "hard_fail_on_aspect_ratio_not_9_16": true
  },
  "presenter_names": {
    "allow_only": ["Maria", "Yago"],
    "forbid_surnames": true,
    "forbidden_surname_regex": "\\b(Maria|Yago)\\s+[A-ZÁÉÍÓÚÑ][a-zñáéíóú]+"
  },
  "reporting": {
    "require_script_validation": true,
    "require_audio_validation": true,
    "print_anthropic_tokens": true,
    "print_elevenlabs_credits": true,
    "cost_tracking_log": "costes_generacion.log"
  }
}
```
<!-- PODCAST_S_SPEC_JSON_END -->
