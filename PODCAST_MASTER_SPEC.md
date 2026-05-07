# Podcast Master Spec

Fuente unica de verdad para generar guiones y audio del podcast MaquinarIA Pesada.
Este archivo actua como especificacion normativa y como instruccion operativa para Codex.

Principios:
- Priorizar claridad antes que estilo.
- No huir de la explicacion tecnica, pero aterrizar siempre con ejemplos.
- Mantener un tono divulgativo tecnico, con rigor y accesibilidad.
- Hacer episodios de 14 a 17 minutos, con objetivo practico de 15 minutos.
- Empezar siempre con hook.
- Alternar el hook por paridad: impares Iago, pares Maria.
- Usar "Yago" dentro del texto hablado, nunca "Iago".
- Incluir la advertencia de contenido generado por IA en el saludo despues de la sintonia.
- Exigir verificaciones reales del guion al final del archivo generado.
- Exigir validacion real del audio y reportar creditos en el log.

Estructura obligatoria del guion:
1. `# HOOK`
2. `# INTRO_SONIDO`
3. `# SALUDO_Y_PRESENTACION`
4. `# BLOQUE_1`
5. `# BLOQUE_2`
6. `# INSERCION_1`
7. `# BLOQUE_3`
8. `# BLOQUE_4`
9. `# CIERRE_CONCEPTOS`
10. `# CIERRE_FINAL`
11. `# VERIFICACIONES`

Bloques opcionales:
- `# BLOQUE_5`
- `# BLOQUE_6`
- `# INSERCION_2`
- `# INSERCION_3`

Hook:
- Debe usar la variante mas agresiva del conflicto del episodio.
- Debe cerrar exactamente con:
  `Esto es MaquinarIA Pesada. Arrancamos.`

Intro de sonido:
- Debe incluir el comentario:
  `# [INTRO - SONIDO DE MAQUINAS ARRANCANDO - 8-10 segundos]`

Cierre:
- `# CIERRE_CONCEPTOS` debe abrir con:
  `No te puedes ir de este capitulo sin haber entendido estos conceptos`
- Debe listar un maximo de cinco conceptos.
- `# CIERRE_FINAL` debe incluir:
  `Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada. Siguenos para nuevos capitulos donde la I.A. crea contenido sobre I.A.`

Reglas de dialogo:
- Intervenciones de desarrollo: 2 a 6 frases por intervencion.
- Intervenciones de desarrollo: maximo 32 palabras por intervencion como objetivo, pero permitiendo expansion cuando un concepto lo requiera.
- Intervenciones de reaccion o pregunta: maximo 12 palabras.
- Minimo dos frases por intervencion como norma general.
- Insertar intercambios mas cortos cada 4 o 5 intervenciones largas.
- Mantener alternancia ligada: no cambios constantes de voz sin desarrollo.

Reglas de tecnicismos:
- Traducir y aterrizar al castellano cualquier termino tecnico o ingles relevante en la misma intervencion.
- No acumular mas de dos tecnicismos seguidos sin frase de aterrizaje.

Reglas de contenido:
- Cubrir al menos el 75 por ciento de los conceptos clave del PDF del tema.
- Explicar los conceptos complejos con ejemplos cotidianos y traslacion corporativa.
- Insertar una noticia, patron documentado o caso de uso cada dos bloques.
- Si un concepto del PDF es muy visual para audio, justificar su ausencia.

Etiquetas TTS:
- Una sola etiqueta por intervencion.
- La etiqueta va al inicio del texto.
- Las etiquetas son instrucciones de tono, no separadores de microfrases.
- Deben usarse con criterio para reforzar ideas, no para fragmentar la voz.

<!-- PODCAST_SPEC_JSON_START -->
```json
{
  "version": "2026-05-05",
  "project_name": "MaquinarIA Pesada",
  "language": "es",
  "directories": {
    "pdfs_dir": "PDFs",
    "scripts_dir": "Guiones",
    "output_dir": "episodios",
    "temp_dir": "episodios/temp",
    "videos_dir": "Videos",
    "music_dir": "Música",
    "intro_dir": "intro",
    "logos_dir": "Logos",
    "default_logo": "Logos/logo sin fondo.png"
  },
  "openai": {
    "default_generation_model": "gpt-4.1",
    "default_review_model": "gpt-4.1-mini",
    "default_concept_model": "gpt-4.1-mini",
    "temperature": 0.7,
    "max_output_tokens": 7000,
    "max_review_tokens": 2200,
    "max_concept_tokens": 900
  },
  "episode_defaults": {
    "duration_minutes": 15,
    "duration_range_minutes": [14, 17],
    "target_audience": "Profesionales cercanos a tecnologia que lideran o participan en proyectos de IA en empresa",
    "structure_margin": "fija_con_margen_controlado",
    "tone": "divulgativo tecnico, riguroso pero accesible",
    "hook_style": "agresivo y conflictivo",
    "minimum_audio_minutes": 12.5,
    "maximum_audio_minutes": 18.5
  },
  "speakers": {
    "IAGO": {
      "display_name": "Iago",
      "spoken_name": "Yago",
      "opens_odd_episodes": true,
      "opens_even_episodes": false,
      "traits": ["grave", "contundente", "tecnico"],
      "allowed_tags": [
        "didactico",
        "explicativo",
        "directo",
        "serio",
        "firme",
        "contundente",
        "grave",
        "tenso",
        "conversacional",
        "reflexivo",
        "reflexiva",
        "curioso",
        "ironico",
        "esceptico",
        "natural",
        "pausado",
        "calido",
        "claro",
        "clara",
        "analitica",
        "calida"
      ]
    },
    "MARIA": {
      "display_name": "Maria",
      "spoken_name": "Maria",
      "opens_odd_episodes": false,
      "opens_even_episodes": true,
      "traits": ["clara", "analitica", "directa"],
      "allowed_tags": [
        "didactico",
        "explicativo",
        "directo",
        "serio",
        "firme",
        "contundente",
        "grave",
        "tenso",
        "conversacional",
        "reflexivo",
        "reflexiva",
        "curioso",
        "ironico",
        "esceptico",
        "natural",
        "pausado",
        "calido",
        "claro",
        "clara",
        "analitica",
        "calida"
      ]
    }
  },
  "script_rules": {
    "required_sections": [
      "HOOK",
      "INTRO_SONIDO",
      "SALUDO_Y_PRESENTACION",
      "BLOQUE_1",
      "BLOQUE_2",
      "INSERCION_1",
      "BLOQUE_3",
      "BLOQUE_4",
      "CIERRE_CONCEPTOS",
      "CIERRE_FINAL",
      "VERIFICACIONES"
    ],
    "optional_section_prefixes": [
      "BLOQUE_5",
      "BLOQUE_6",
      "INSERCION_2",
      "INSERCION_3"
    ],
    "content_block_prefix": "BLOQUE_",
    "insertion_prefix": "INSERCION_",
    "minimum_content_blocks": 4,
    "maximum_content_blocks": 6,
    "max_consecutive_blocks_same_speaker": 3,
    "five_key_ideas_block_count": 5,
    "minimum_word_count": 1800,
    "minimum_sentences_per_intervention": 2,
    "maximum_sentences_per_intervention": 6,
    "reaction_word_limit": 12,
    "target_avg_words_per_intervention_min": 45,
    "target_avg_words_per_intervention_max": 80,
    "maximum_long_intervention_percentage": 60,
    "minimum_short_intervention_percentage": 5,
    "long_intervention_threshold": 85,
    "short_intervention_threshold": 10,
    "minimum_concept_mentions": 2,
    "minimum_pdf_coverage_percent": 75,
    "hook_closing_phrase": "Esto es MaquinarIA Pesada. Arrancamos.",
    "intro_comment": "[INTRO - SONIDO DE MAQUINAS ARRANCANDO - 8-10 segundos]",
    "warning_phrase_keywords": [
      "sistema automatico",
      "puede contener errores"
    ],
    "concepts_closing_phrase": "No te puedes ir de este capitulo sin haber entendido estos conceptos",
    "final_closing_phrase": "Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada. Siguenos para nuevos capitulos donde la I.A. crea contenido sobre I.A.",
    "speaker_aliases": {
      "MARIA": ["MARIA", "MARÍA"],
      "IAGO": ["IAGO"]
    }
  },
  "audio_rules": {
    "model": "eleven_v3",
    "output_format": "mp3_44100_128",
    "export_bitrate": "192k",
    "initial_silence_ms": 2000,
    "same_speaker_pause_ms": 250,
    "different_speaker_pause_ms": 500,
    "background_music_db": -20,
    "background_bed_path": "Música/base podcast.mp3",
    "intro_theme_path": "Música/Sintonia Maquinaria pesada.mp3",
    "pre_hook_bed_ms": 2000,
    "post_hook_bed_ms": 2000,
    "post_hook_bed_fade_out_ms": 2000,
    "post_intro_bed_ms": 2000,
    "final_bed_tail_ms": 3000,
    "final_bed_tail_fade_out_ms": 3000,
    "music_fade_in_ms": 3000,
    "music_fade_out_ms": 5000,
    "normalization_target_dbfs": -16,
    "true_peak_target_dbtp": -1.5,
    "post_speed_multiplier": 1.10,
    "voices": {
      "IAGO": {
        "voice_id": "CdAqYBLnsNjmTqYgD5Ha",
        "stability": 0.65,
        "similarity_boost": 0.65,
        "style": 0.0,
        "use_speaker_boost": false,
        "speed": 1.20
      },
      "MARIA": {
        "voice_id": "gD1IexrzCvsXPHUuT0s3",
        "stability": 0.68,
        "similarity_boost": 0.55,
        "style": 0.0,
        "use_speaker_boost": false,
        "speed": 1.20
      }
    },
    "music_prompt": "Industrial startup sound with machine ignition textures evolving into subtle lo-fi technology podcast bed, no vocals, unobtrusive and loopable",
    "music_duration_seconds": 30,
    "music_prompt_influence": 0.3
  },
  "reporting": {
    "require_script_validation": true,
    "require_audio_validation": true,
    "print_openai_tokens": true,
    "print_elevenlabs_credits": true,
    "remaining_tokens_mode": "budget_or_unknown",
    "remaining_credits_mode": "api_if_available"
  }
}
```
<!-- PODCAST_SPEC_JSON_END -->
