# BIBLIA DEL SISTEMA · MaquinarIA Pesada

> Documento maestro: explica de extremo a extremo el sistema automático de
> producción del videopodcast **MaquinarIA Pesada**. Cubre arquitectura,
> tecnologías, scripts, técnicas de IA, layout visual, infraestructura,
> cuentas y operativa.
>
> **Última actualización:** 8 mayo 2026
> **Repositorio:** https://github.com/bakero/maquinaria-pesada (público)
> **Rama activa:** `videopodcast` (consolidaciones a `master` cuando algo funciona)
> **Mantenedor:** bkasero@gmail.com

---

## ÍNDICE

1. [¿Qué es MaquinarIA Pesada?](#1-qué-es-maquinaria-pesada)
2. [Arquitectura general](#2-arquitectura-general-del-sistema)
3. [Tecnologías usadas](#3-tecnologías-usadas)
4. [Cuentas, claves y secretos](#4-cuentas-claves-y-secretos)
5. [Estructura de carpetas](#5-estructura-de-carpetas)
6. [Pipeline guion + audio](#6-pipeline-de-generación-de-guion--audio-raíz-del-repo)
7. [Pipeline de video](#7-pipeline-de-video-maquinaria_pesada_pipeline)
8. [Layout visual del videopodcast](#8-layout-visual-del-videopodcast)
9. [Operativa: cómo producir un episodio](#9-operativa-cómo-producir-un-episodio)
10. [Cockpit (consola web de control)](#10-cockpit-consola-web-de-control)
11. [Técnicas de IA aplicadas (deep dive)](#11-técnicas-de-ia-aplicadas-deep-dive)
12. [Bugs conocidos y resueltos](#12-bugs-conocidos-y-resueltos-cronología)
13. [Pendientes vivos](#13-pendientes-vivos)
14. [Reglas de oro del sistema](#14-reglas-de-oro-del-sistema)
15. [Anexo: comandos útiles](#15-anexo-comandos-útiles)
16. [Glosario](#16-glosario)

---

## 1. ¿Qué es MaquinarIA Pesada?

Podcast/videopodcast educativo sobre Inteligencia Artificial: 14 módulos
del máster (M0 hasta M14) producidos íntegramente con IA generativa, sin
intervención humana en grabación. El producto final es:

- **MP4 1080p** subido a YouTube
- **MP3** subido a Spotify
- **Cápsulas** y posts derivados para RRSS

Cada episodio dura 14-17 min. Tono divulgativo técnico. Dos presentadores
ficticios: **María** (voz femenina, color marca amarillo CAT `#F5C400`) y
**Yago** (voz masculina, azul `#4DB8FF`). En el guion va escrito como
"Yago"; algunos campos legacy lo guardan como "IAGO".

El sistema completo cubre: generación de **guion → audio → video** con
escaleta de producción profesional, lip-sync futuro, subtítulos y assets
visuales (estudio + pizarra dinámica).

---

## 2. Arquitectura general del sistema

```
                                        ┌──────────────────────┐
                                        │ PDFs del Máster      │
                                        │ (input humano)       │
                                        └──────────┬───────────┘
                                                   │
                                          ┌────────▼────────┐
                                          │ podcast_spec.py │ ← Reglas
                                          │ + spec markdown │   normativas
                                          └────────┬────────┘
                                                   │
                                          ┌────────▼─────────┐
                                          │ generar_guion.py │ Anthropic
                                          │  (Claude Sonnet) │ Sonnet 4.5
                                          └────────┬─────────┘
                                                   │
                                                   ▼ guion .txt
                                       ┌────────────────────────┐
                                       │ generar_episodio_v2.py │ ElevenLabs
                                       │  (TTS dual MARIA/YAGO) │ eleven_v3
                                       └───────────┬────────────┘
                                                   ▼ audio .mp3
   ┌────────────────────────────────────────────────────────────────────┐
   │                  PIPELINE de VIDEO                                 │
   │                                                                    │
   │  1. transcriber.py        Whisper large-v3 word-level              │
   │  2. content_extractor.py  Parser guion + PDF                       │
   │  3. audio_analyzer.py     Silencedetect + sintonia_detector        │
   │      (cross-correlation con scipy.signal.correlate)                │
   │  4. concept_extractor.py  Claude Haiku → 1614 conceptos PDFs       │
   │  5. media_finder.py       Wikipedia + Tenor (gifs)                 │
   │  6. escaleta_generator.py Claude Sonnet 4.5 → escaleta markdown    │
   │  7. escaleta_parser.py    markdown → estructura canónica           │
   │  8. escaleta_to_pipeline  scene_track + scene_timeline             │
   │  9. overlay_renderer.py   PIL → frames PNG por escena              │
   │  10. subtitle_generator   .srt blanco desde Whisper word-level     │
   │  11. video_compositor.py  ffmpeg compose Layout C (PIP)            │
   │                                                                    │
   │  Generadores de assets (offline):                                  │
   │    luma_generator.py    Luma Dream Machine (legacy, deprecado)     │
   │    kling_generator.py   Kling 1.6 Pro vía API oficial Kuaishou     │
   │      (image-to-video + extend chain para clips de 20s)             │
   │    sintonia_detector    scipy correlate → posición exacta sintonía │
   │                                                                    │
   └────────────────────────────────────────────────────────────────────┘
                                                   ▼
                                          ┌──────────────┐
                                          │  MP4 final   │
                                          └──────────────┘
```

El pipeline está dividido en **dos sub-sistemas**:

1. **Generación de guion + audio** (raíz del repo, scripts CLI Python).
2. **Generación de video** (`maquinaria_pesada_pipeline/`).

Encima vive una **consola web de control** (`cockpit/`, Streamlit) para
observabilidad y orquestación.

---

## 3. Tecnologías usadas

### 3.1 Lenguajes y stack

| Componente | Tecnología |
|---|---|
| Lenguaje principal | Python 3.12 |
| Sistema operativo | Windows 11 (paths absolutos `C:\Users\Asus\...`) |
| Shell | Git Bash + PowerShell 5.1 |
| Repo | Git, GitHub público `bakero/maquinaria-pesada` |
| Branch activo | `videopodcast` |
| Web UI | Streamlit (cockpit) |
| Media engine | ffmpeg + ffprobe (debe estar en PATH) |
| Procesamiento imagen | Pillow (PIL) |
| Procesamiento audio DSP | scipy.signal (cross-correlation) |
| HTTP / SDKs | requests, anthropic, elevenlabs, PyJWT |

### 3.2 Modelos de IA usados

| Tarea | Modelo | Coste aprox./episodio |
|---|---|---|
| Generación guion | Claude Sonnet 4.6 (`claude-sonnet-4-6`) | ~$0.30 |
| Generación escaleta | Claude Sonnet 4.5 (max 32k tokens, streaming) | ~$0.30 |
| Extracción conceptos PDF | Claude Haiku 4.5 | ~$0.05 (todos los PDFs juntos) |
| TTS dual | ElevenLabs `eleven_v3` (multi-speaker) | ~$0.50 (8-10 min audio) |
| Transcripción ASR | OpenAI Whisper `large-v3` o `medium` (local) | $0 |
| Generación clips estudio | Kling 1.6 Pro (Kuaishou) image-to-video | ~$1.40/clip 20s · ~$24 catálogo 18 clips |
| Imagen referencia | DALL-E 3 / Gemini Imagen 3 | manual |

### 3.3 Servicios externos

| Servicio | Uso | Endpoint |
|---|---|---|
| Anthropic API | Claude Sonnet 4.5 + Haiku 4.5 | `api.anthropic.com` |
| ElevenLabs API | TTS dual con `eleven_v3` | `api.elevenlabs.io` |
| Kling AI (Kuaishou) | Image-to-video con JWT auth | `api.klingai.com` |
| GitHub (público) | Hosting de imágenes ref para Kling | `raw.githubusercontent.com` |
| OpenAI Whisper (local) | ASR | sin red |
| Wikipedia ES/EN | Imágenes conceptos | `wikipedia.org` |
| Wikimedia Commons | Imágenes libres | `commons.wikimedia.org` |
| Tenor | GIFs/memes | `tenor.googleapis.com` |
| Fal.ai | (Descartado, usábamos antes para Kling) | — |
| Sync.so / Hedra | Lip-sync (PENDIENTE de SYNC_API_KEY) | `api.sync.so` |

---

## 4. Cuentas, claves y secretos

### 4.1 Archivo `.env` (raíz del repo, en `.gitignore`)

```bash
# Generación de texto e imágenes
ANTHROPIC_API_KEY=sk-ant-api03-...

# TTS
ELEVENLABS_API_KEY=...

# Generación de video estudio (Kling oficial Kuaishou)
KLING_ACCESS_KEY=AK...                 # 32 chars
KLING_SECRET_KEY=SK...                 # 32 chars

# Lip-sync (cuando esté contratado)
SYNC_API_KEY=...                       # Sync.so

# Tenor para gifs/memes (opcional)
TENOR_API_KEY=...
```

**Nota crítica**: el repo usa `load_dotenv(path, override=True)` con la
ruta absoluta `C:\Users\Asus\maquinaria_pesada\.env` para evitar que
variables de entorno de Windows ya cargadas tengan precedencia sobre el
archivo.

### 4.2 GitHub público

- Repo: https://github.com/bakero/maquinaria-pesada
- Visibilidad: **público** (necesario para que Kling pueda descargar las
  imágenes de referencia desde `raw.githubusercontent.com`)
- Branch principal: `master`
- Branch desarrollo: `videopodcast`

### 4.3 Cuentas externas activas

- **Anthropic Console**: https://console.anthropic.com — saldo activo.
- **ElevenLabs**: usuario con voces clonadas/calibradas para María y Yago.
- **Kling AI / Kuaishou Cloud**: https://app.klingai.com/global/dev/account
  — credenciales JWT (Access + Secret).
- **GitHub**: usuario `bakero`.

---

## 5. Estructura de carpetas

```
C:\Users\Asus\maquinaria_pesada\
│
├── .env                          ← claves API (gitignored)
├── .env.example                  ← plantilla pública
├── .gitignore
├── README.md
├── BIBLIA_SISTEMA.md             ← este documento
├── PODCAST_MASTER_SPEC.md        ← reglas de guion (normativa)
├── VOICE_CONFIG_REFERENCE.md     ← config voces ElevenLabs validada
├── INSTRUCCIONES.txt             ← manual usuario (legacy)
├── SESION_genepisodios.md        ← memoria sesión (legacy)
│
├── PDFs/                         ← INPUT humano: PDFs del máster M0..M14
├── Guiones/                      ← INPUT humano + OUTPUT generador guion
│   └── M0_T_Introduccion_Estrategica.txt
├── Logos/                        ← Logo MAQUINARIA PESADA + watermark
├── Música/                       ← Sintonía + base musical
│   ├── Sintonia Maquinaria pesada.mp3
│   └── base podcast.mp3
├── intro/                        ← intro_video.mp4 (sintonía visual)
│
├── episodios/                    ← Audio MP3 generado por episodio
│   └── M0_E_Introduccion_Estrategica.mp3
├── escaletas/                    ← Markdown escaleta producción
│   ├── EP-MOD000_escaleta.md
│   └── EP-MOD000_escaleta_v1.md.bak
├── Videos/                       ← OUTPUT final + biblioteca clips
│   ├── M0_V_Introduccion_Estrategica.mp4
│   ├── M0_V_Introduccion_Estrategica.srt
│   └── escenas_biblioteca/
│       ├── _scenes_index.json    ← Catálogo clips
│       ├── _concepts_index.json  ← 1614 conceptos extraídos PDFs
│       ├── refs/                 ← Imágenes referencia Kling
│       │   ├── Maria.png         ← URL pública GitHub raw
│       │   ├── Yago.png
│       │   ├── establishing.png  ← Plano amplio dos presentadores
│       │   └── studio.png        ← Estudio vacío
│       ├── estudio/              ← Clips Kling 20s
│       │   ├── studio_maria_solo_v1.mp4
│       │   └── ...               ← v2, v3, v4 + two_shots
│       └── conceptos/            ← Clips Luma legacy (deprecado)
│
├── RRSS/                         ← Posts redes sociales (futuro)
│
├── maquinaria_pesada_pipeline/   ← PIPELINE de video
│   ├── run_pipeline.py           ← Orquestador completo legacy (8 pasos)
│   ├── setup_project.py          ← Wizard inicial → project_config.json
│   ├── project_config.json       ← Paths del episodio actual
│   ├── requirements.txt
│   ├── outputs/                  ← Cache intermedio + logs
│   │   ├── transcription_raw.json
│   │   ├── content_data.json
│   │   ├── audio_structure.json
│   │   ├── aligned_interventions.json
│   │   ├── scene_timeline.json
│   │   ├── scene_track.json
│   │   ├── frames_index.json
│   │   ├── frames_cache/         ← PNGs renderizados con PIL
│   │   ├── _compose_tmp/         ← MP4 segmentos intermedios
│   │   └── logs/EP-MOD000_pipeline.log
│   │
│   ├── pipeline/                 ← Módulos del pipeline (ver §7)
│   │   ├── logger.py
│   │   ├── brand.py              ← Colores marca, resoluciones
│   │   ├── asset_validator.py
│   │   ├── transcriber.py
│   │   ├── content_extractor.py
│   │   ├── audio_analyzer.py
│   │   ├── sintonia_detector.py
│   │   ├── concept_extractor.py
│   │   ├── media_finder.py
│   │   ├── escaleta_generator.py
│   │   ├── escaleta_parser.py
│   │   ├── escaleta_to_pipeline.py
│   │   ├── scene_builder.py      ← (legacy, sólo si NO hay escaleta)
│   │   ├── scene_track_builder.py ← (legacy)
│   │   ├── scene_library.py
│   │   ├── overlay_renderer.py
│   │   ├── subtitle_generator.py
│   │   ├── video_compositor.py
│   │   ├── metadata_generator.py
│   │   ├── kling_generator.py
│   │   ├── luma_generator.py     ← (legacy, no usar)
│   │   └── production_log_parser.py
│   │
│   ├── tools/                    ← CLIs de soporte
│   │   ├── render_from_escaleta.py        ← MAIN: render desde escaleta
│   │   ├── generate_escaleta.py           ← Genera escaleta con LLM
│   │   ├── generate_studio_clips_kling.py ← Genera 18 clips estudio
│   │   ├── generate_studio_clips.py       ← (legacy Luma)
│   │   ├── kling_recover.py               ← Rescatar tasks huérfanas
│   │   ├── reverse_clips.py               ← Duplica catálogo gratis
│   │   ├── rescan_library.py              ← Re-registra mp4s en index
│   │   ├── analyze_concepts.py            ← Dashboard conceptos
│   │   └── find_media_for_concepts.py     ← Wikipedia + Tenor
│   │
│   └── templates/
│       ├── overlay_types.py      ← 11 tipos PIL: stat_card, hierarchy,…
│       ├── background_generators.py
│       ├── sticker_manager.py
│       └── system_prompt_timeline.txt
│
├── cockpit/                      ← Consola web Streamlit (ver §10)
│   ├── app.py
│   ├── ui.py
│   ├── core/
│   ├── connectors/
│   ├── pages/
│   ├── PLAN.md
│   └── SESSION_CONTEXT.md
│
├── (scripts CLI legacy en raíz)
├── generar_guion.py              ← Genera guion .txt con Claude
├── generar_episodio_v2.py        ← Genera audio .mp3 con ElevenLabs
├── producir_episodio.py          ← Wrapper guion+audio
├── lanzar_produccion.py          ← Lanzador masivo M0..M14
├── validar_episodio.py           ← Verifica calidad audio
├── normalizar_guiones.py         ← Limpia guiones manuales
├── estado_proyecto.py            ← Snapshot inventario
├── podcast_spec.py               ← Reglas episodio en Python
└── dual_debate.py                ← Modo debate experimental
```

---

## 6. Pipeline de generación de guion + audio (raíz del repo)

### 6.1 `generar_guion.py`

Convierte un PDF del módulo en un guion `.txt` siguiendo estrictamente
`PODCAST_MASTER_SPEC.md`:

- **Input**: `PDFs/RESUMEN_M0_*.pdf`
- **Output**: `Guiones/M0_T_*.txt`
- **Modelo**: Claude Sonnet 4.5 con system prompt de 5KB
- **Estructura forzada**: HOOK → INTRO_SONIDO → SALUDO → BLOQUE_1..BLOQUE_4
  → INSERCION_1 → CIERRE_CONCEPTOS → CIERRE_FINAL → VERIFICACIONES
- **Reglas duras**:
  - hook agresivo cierra con _"Esto es MaquinarIA Pesada. Arrancamos."_
  - cierre cita _"...la I.A. crea contenido sobre I.A."_
  - intervenciones de desarrollo 2-6 frases, máx 32 palabras
  - tecnicismos con aterrizaje en castellano
  - etiquetas TTS al inicio (una por intervención)

### 6.2 `generar_episodio_v2.py`

Convierte el guion `.txt` en MP3 dual:

- **Input**: `Guiones/M0_T_*.txt`
- **Output**: `episodios/M0_E_*.mp3`
- **TTS engine**: ElevenLabs `eleven_v3` (modelo de máxima calidad
  multi-speaker)
- **Voces**: IDs validados en `VOICE_CONFIG_REFERENCE.md` con
  `VoiceSettings` calibrados (stability, similarity_boost, style,
  use_speaker_boost)
- **Etiquetas**: `[ironico]`, `[serio]`, `[tecnico]`, `[curioso]`,
  `[firme]`, `[risas]` etc. — una por intervención al inicio
- **Silencios**: pausas controladas con `<silence duration="2s"/>`
- **Patrón temporal del audio**:
  ```
  [silencio 2s] [HOOK] [silencio 2s] [SINTONIA 10s] [silencio]
   [CONTENIDO ~13min] [silencio 3s final]
  ```

### 6.3 `producir_episodio.py` y `lanzar_produccion.py`

Wrappers para producir uno o varios episodios en cadena.

### 6.4 `validar_episodio.py`

Comprobaciones post-producción: duración 14-17 min, ausencia de errores
TTS, presencia de hooks/cierres canónicos, créditos consumidos.

---

## 7. Pipeline de video (`maquinaria_pesada_pipeline/`)

El pipeline tiene **dos modos de entrada**:

- **Modo legacy**: `run_pipeline.py` con scene_builder LLM (genera todo
  con Claude on-the-fly). _No recomendado._
- **Modo escaleta** (canónico actual): `tools/render_from_escaleta.py`
  parte de un `escaletas/<EP>_escaleta.md` ya redactado, que actúa como
  **guion de producción canónico**. Predecible y editable.

### 7.1 Diagrama de pasos (modo escaleta)

```
[EP audio.mp3]                     [escaleta.md]                    [PDFs]
     │                                  │                              │
     ▼                                  ▼                              ▼
  transcriber                    escaleta_parser              concept_extractor
  (Whisper)                      ( markdown → dict )          (Claude Haiku)
     │                                  │                              │
     ▼                                  │                              ▼
  audio_analyzer ───sintonia_detector   │                       _concepts_index.json
  (silencedetect + cross-correlate)     │                              ↑
     │                                  ▼                              │
     ▼                          escaleta_to_pipeline ──────────────────┘
  audio_structure.json          (split sub-segs, rotate pool,
     │                            no-repeat, fix overlaps)
     │                                  │
     │                                  ├── scene_timeline.json (overlays PIL)
     │                                  └── scene_track.json    (estudio/pizarra/blank)
     │                                              │
     │                                              ▼
     │                                      overlay_renderer
     │                                      (PIL → PNG frames)
     │                                              │
     │                                              ▼
     │                                      frames_index.json
     │                                              │
     ▼                                              ▼
  subtitle_generator                       video_compositor (ffmpeg)
  (whisper words →                          ├── body_video (concat segmentos)
   chunks ~7w / 3s)                         ├── intro_overlay sobre sintonía
     │                                      └── subs blancos quemados
     ▼                                              │
  M0_V_*.srt                                        ▼
                                            M0_V_*.mp4 (1080p)
```

### 7.2 Detalle por módulo

#### `transcriber.py`
- Whisper local (`pip install openai-whisper`).
- Modelo configurable: `tiny`, `base`, `small`, `medium`, `large-v3`.
- Devuelve `transcription = {text, segments, words}` con `word.start` /
  `word.end` por palabra (precisión ~50ms con `medium`).
- Cache en `outputs/transcription_raw.json`.

#### `content_extractor.py`
- Lee guion + PDF.
- Parsea estructura (HOOK, BLOQUE_X, intervenciones por speaker).
- Extrae keywords, citas, datos.
- Cache en `outputs/content_data.json`.

#### `audio_analyzer.py`
- Detecta hitos del audio: lead silence (2s), HOOK, sintonía, contenido,
  silencio final.
- Usa `ffmpeg -af silencedetect` con threshold `-20dB / 1.5s` (calibrado
  para audio con música de fondo).
- Cache en `outputs/audio_structure.json`.

#### `sintonia_detector.py`
- **Cross-correlación con scipy.signal.correlate** entre el audio del
  episodio y `Sintonia Maquinaria pesada.mp3`.
- Devuelve el offset exacto (start, end) con confianza.
- Imprescindible: silencedetect daba 8.54s para una sintonía de 10s
  (cortaba). La correlación da 35.21-45.20 = 10.000s exactos.
- Si confianza ≥ 0.3 anula el resultado de silencedetect.

#### `concept_extractor.py`
- Procesa todos los PDFs del máster con **Claude Haiku 4.5**.
- Por cada PDF extrae conceptos: nombre, slug, definición, sinónimos,
  visual_idea, importance, tema.
- Salida: `Videos/escenas_biblioteca/_concepts_index.json`
- Stats actuales: **1614 conceptos / 1355 únicos** (M0..M14 cubierto).

#### `media_finder.py`
- Busca imágenes/gifs para los conceptos.
- Fuentes: Wikipedia ES → Wikipedia EN → Wikimedia Commons → Tenor
  (con `TENOR_API_KEY` opcional).
- Filtro `_title_matches_term` para descartar resultados irrelevantes.

#### `escaleta_generator.py`
- **Crea la escaleta de producción** con Claude Sonnet 4.5.
- System prompt: "Guionista senior de programas de TV con 15 años en
  cadenas españolas".
- Reglas v2 actuales:
  - Layout C (pizarra fullscreen + PIP presentador 25% bottom-right)
  - Por cada intervención: campo `**PIZARRA:** SI/NO`
  - Si SI → mínimo 15s, elementos cada 4s, vincular al párrafo dicho
  - **Nunca poner texto del guion en la pizarra** (sólo datos, gráficos,
    imágenes, memes — NO citas literales)
  - ≥1 pizarra cada 3 minutos como mínimo
- Streaming con `client.messages.stream` (max_tokens 32000).
- Output: `escaletas/<EP>_escaleta.md` con frontmatter YAML.

#### `escaleta_parser.py`
- Parser markdown → dict canónico.
- Reconoce: bloques `## NOMBRE TC IN: ... TC OUT: ...`, intervenciones
  `### N.M — Speaker`, campos TC / TONO / TEXTO / PLANO / PIZARRA / 
  ON-SCREEN tabla / TRANSICION.
- Detecta separador em-dash U+2014 entre número y speaker.
- Cualquier inconsistencia se loguea pero no rompe.

#### `escaleta_to_pipeline.py`
- Convierte la escaleta parseada en `scene_timeline.json` + `scene_track.json`.
- **Rotación no-repeat**: por cada intervención, escoge clips del pool
  del speaker (`SPEAKER_POOL["MARIA"]` = 9 candidatos) sin repetir slug.
- **Sub-segmentación**: si una intervención dura más de `MAX_CLIP_DUR=10s`,
  la parte en sub-segmentos asignando un clip distinto a cada uno.
- **Fix de solapamientos**: si la escaleta humana tiene TCs que se
  solapan (fin N > inicio N+1), recorta `seg.end = next.start`.
  Crítico: sin esto el body video se "estira" respecto al audio y los
  subtítulos se desincronizan progresivamente.
- **Heurística pizarra**: si no hay marca explícita, invoca pizarra si
  `plano == PIZARRA` o `rich_count >= 2 and dur >= 12s`.
- **Verificación física de archivos**: filtra slugs cuyo `.mp4` ya no
  existe (defiende contra entradas huérfanas en `_scenes_index.json`).

#### `scene_library.py`
- Catálogo persistente de clips.
- Ubicación: `Videos/escenas_biblioteca/_scenes_index.json`
- Categorías: `estudio`, `cierres`, `conceptos`, `transiciones`.
- API: `library.find(slug)`, `library.register(slug, path, ...)`.

#### `overlay_renderer.py`
- Renderiza frames PNG con **PIL** según `scene_timeline.json`.
- 11 tipos de overlay (`templates/overlay_types.py`):
  - `stat_card` · `name_tag` · `hierarchy_diagram` · `two_column_compare`
  - `bar_chart` · `timeline_visual` · `regulation_alert` · `warning_badge`
  - `highlight_quote` · `recap_grid` · `end_card` · `section_indicator`
- Backgrounds: `industrial_grid`, etc. (`background_generators.py`).
- Salida: `outputs/frames_cache/*.png` + `outputs/frames_index.json`.

#### `subtitle_generator.py`
- Genera `.srt` desde **Whisper word-level** directamente.
- Chunks de **~7 palabras / ≤3s** o cierre por puntuación final.
- Skip palabras dentro del rango de la sintonía.
- **Subtítulos 100% blancos** (sin highlight).
- Estilo ffmpeg: `Fontsize=18 (1080p) PrimaryColour=&H00E8E8E8
  BorderStyle=1 Outline=2 MarginV=40 Alignment=2`.

#### `video_compositor.py` — corazón del Layout C
- Combina:
  1. **Body video**: secuencia de segmentos del `scene_track`.
  2. **Audio del episodio** original.
  3. **Intro_overlay**: el `intro_video.mp4` recortado a la duración
     exacta de la sintonía detectada.
  4. **Subtítulos** quemados con filtro `subtitles=`.
- **Layout C (PIP)**: cuando un segmento es `pizarra` y trae
  `pip_source`, compone:
  - Background pizarra a fullscreen.
  - PIP del presentador 25% del ancho (480×270 a 1080p) con borde
    amarillo CAT (`#F5C400`) de 4px, esquina inferior derecha,
    margen 30px.
- **Constantes layout**:
  ```python
  PIP_WIDTH_RATIO   = 0.25
  PIP_ASPECT        = 16/9
  PIP_MARGIN        = 30
  PIP_BORDER_PX     = 4
  PIP_BORDER_COLOR  = "0xF5C400"
  ```
- Filtro vf canónico: `scale={w}:{h}:flags=lanczos,format=yuv420p,fps=30`
  (la coma entre scale y format es crítica; `:` lo rompe).

#### `kling_generator.py`
- Genera clips de estudio con **Kling 1.6 Pro** vía API oficial Kuaishou.
- Auth: **JWT HS256** firmado con `KLING_ACCESS_KEY` + `KLING_SECRET_KEY`.
  El JWT se regenera por petición (exp 30min).
- Endpoints:
  - `POST /v1/videos/image2video`
  - `POST /v1/videos/video-extend` (chain extends)
  - `GET /v1/videos/image2video/{task_id}` (polling)
- **Image-to-video**: usa una URL pública (GitHub raw) como frame
  inicial → Kling mantiene la consistencia facial/escenario.
- **Extend chain**: para clips de >10s, `generate_concept` con
  `target_duration > duration` lanza el base 10s, espera, y encadena
  N extends de ~5s hasta target.
- Polling robusto: timeout HTTP 90s, hasta 5 reintentos consecutivos
  con backoff exponencial.
- Negative prompt anti-alucinación: `"second person appearing,
  duplicate person, CAT logo, lip sync error, frozen face"` — clave
  porque Luma alucinaba una segunda persona en planos individuales.

#### `metadata_generator.py`
- Genera title, description, tags YouTube + Spotify a partir del guion.

---

## 8. Layout visual del videopodcast

### 8.1 Modos de pantalla

**MODO ESTUDIO (fullscreen)** — usado cuando `PIZARRA: NO`:
- Clip Kling del presentador o two-shot ocupa toda la pantalla (1920×1080).
- Subtítulos blancos abajo centrados.
- Name tag del speaker arriba derecha.

**MODO PIZARRA (Layout C, PIP corner)** — usado cuando `PIZARRA: SI`:
```
┌────────────────────────────────────────────────┐
│  Pizarra fullscreen                  ●MARIA    │
│  (industrial grid background)                  │
│                                                │
│  ┌──────────┐                ┌──────────┐     │
│  │stat_card │   bar_chart    │warning   │     │
│  │  88%     │                │ badge    │     │
│  └──────────┘                └──────────┘     │
│                                                │
│           hierarchy_diagram                    │
│                                                │
│  Subtítulos blancos abajo centrados.    ┌────┐│
│                                         │PIP │ │
│  Borde amarillo CAT 4px      bottom-right│Mar │ │
│  alrededor del PIP                       └────┘│
└────────────────────────────────────────────────┘
```

Cada **4s** entra un elemento nuevo en la pizarra. Los elementos
permanecen hasta el final de la intervención (acumulación visual).
Mínimo 15s por bloque pizarra. ≥1 pizarra cada 3 min.

### 8.2 Identidad de marca

| Color | Hex | Uso |
|---|---|---|
| Amarillo CAT | `#F5C400` | María, datos, borde PIP, identidad |
| Azul | `#4DB8FF` | Yago, técnico, micrófonos del set |
| Rojo | `#CC2200` | Regulación, alertas, EU AI Act |
| Gris | `#888888` | Información secundaria |
| Blanco subtítulo | `#E8E8E8` | Subtítulos (no `#FFFFFF` puro para evitar bloom) |

Negro fondo: `#0D0D0D` (industrial dark, no negro absoluto).

### 8.3 Catálogo de clips (estado a 8 mayo 2026)

Pool por speaker (definido en `escaleta_to_pipeline.py · SPEAKER_POOL`):

```
MARIA  →  studio_maria_solo_v1..v4         (4 close-medium frontal)
       +  studio_two_m_active_v1..v5       (5 two-shot Maria activa)
       +  legacy fallbacks
       = 9 clips Kling + 2 legacy

YAGO   →  studio_yago_solo_v1..v4
       +  studio_two_y_active_v1..v5
       = 9 clips Kling + 2 legacy

AMBOS  →  studio_establishing_general
       +  studio_both_complicit
```

Cada clip Kling dura **~20s** (10s base + 2 extends de 5s) y mantiene
consistencia facial. Coste ~$1.40/clip = ~$25 catálogo completo.

`reverse_clips.py` duplica el catálogo gratis con variantes `_rev`
(reverse playback, útil sólo para tomas pasivas).

---

## 9. Operativa: cómo producir un episodio

### 9.1 Flujo completo (M0 = ejemplo)

```bash
# 1. Generar guion (manual, una vez por módulo)
python generar_guion.py --modulo M0

# 2. Generar audio (TTS dual)
python generar_episodio_v2.py --modulo M0

# 3. Generar escaleta de producción
python maquinaria_pesada_pipeline/tools/generate_escaleta.py \
    --episode EP-MOD000 --modulo M0

# 4. (Opcional) Editar la escaleta en escaletas/EP-MOD000_escaleta.md

# 5. Renderizar el video
python maquinaria_pesada_pipeline/tools/render_from_escaleta.py \
    --episode EP-MOD000

#    Modo preview rápido (90s):
python maquinaria_pesada_pipeline/tools/render_from_escaleta.py \
    --episode EP-MOD000 --preview --preview-seconds 90
```

### 9.2 Generación catálogo de clips (una vez)

```bash
# Generar los 18 clips Kling (~7h cola, ~$25)
python maquinaria_pesada_pipeline/tools/generate_studio_clips_kling.py

# Re-rastrear el filesystem si _scenes_index.json se desincronizó
python maquinaria_pesada_pipeline/tools/rescan_library.py

# Duplicar catálogo con reverse playback (gratis)
python maquinaria_pesada_pipeline/tools/reverse_clips.py
```

### 9.3 Recuperación de fallos

Si una task de Kling falla por timeout pero el video se generó en sus
servidores:

```bash
python maquinaria_pesada_pipeline/tools/kling_recover.py \
    --slug studio_maria_solo_v1 \
    --extend-from-video-id 881670742302134272 \
    --extends 2
```

---

## 10. Cockpit (consola web de control)

### 10.1 Propósito

App web Streamlit para **observabilidad y orquestación**, NO ejecución.
Centraliza:
- Inventario de qué hay generado en cada módulo (M0..M14).
- Browser de PDFs, Guiones, Audios, Videos, Logs.
- Generador de prompts CLI listos para Codex.
- Registro modular de conectores (servicios externos como OpenAI,
  ElevenLabs, ffmpeg, Codex).
- Tail viewer de logs de generación.

### 10.2 Estructura

```
cockpit/
├── app.py                    ← entry point (streamlit run)
├── ui.py                     ← sidebar persistente "Producción en vivo"
├── core/
│   ├── paths.py              ← rutas canónicas
│   ├── monitor.py            ← psutil watch de procesos
│   ├── log_parser.py         ← extrae estado de logs
│   ├── prompt_builder.py     ← genera prompts CLI desde forms
│   └── state.py              ← cache global Streamlit
├── connectors/
│   ├── base.py               ← interfaz Connector
│   ├── services/             ← openai, elevenlabs, ffmpeg, codex
│   ├── pipelines/            ← scripts del repo registrados
│   └── sources/              ← pdf, guion, audio, video
└── pages/
    ├── 1_📊_Estado.py
    ├── 2_🔌_Conectores.py
    ├── 3_📝_Generar_Prompt.py
    ├── 4_📚_Fuentes.py
    └── 5_📜_Logs.py
```

### 10.3 Lanzamiento

```bash
pip install -r requirements-cockpit.txt   # streamlit, psutil, streamlit-autorefresh
streamlit run cockpit/app.py
```

Por defecto en http://localhost:8501.

### 10.4 Filosofía

El cockpit **no ejecuta** procesos largos en su request handler (los
disparos pesados van a Codex con prompts CLI generados en la página
"Generar Prompt"). El refresh del sidebar es cada 5s vía
`streamlit-autorefresh`, polling con `psutil` para detectar procesos
python en marcha.

### 10.5 Evolución reciente (sesión APPContenidos · 2026-05-10)

Trabajo absorbido desde la rama `APPContenidos` (commit merge `6040434`).
Diario completo de las decisiones de la sesión cockpit en
[`APPCONTENIDOS.md`](APPCONTENIDOS.md) (16 entradas).

#### Tema visual industrial CAT
- Paleta dark + amarillo CAT (`#F5C400`) + acero gris.
- Tipografías: **Oswald** (titulares uppercase, letter-spacing ancho),
  **Barlow Condensed** (cuerpo), **JetBrains Mono** (numérico/HUD).
- Bordes 2px (esquinas casi cuadradas), H1 con barra amarilla a la
  izquierda (bandera de obra), divisores con degradado amarillo.
- Implementación: `.streamlit/config.toml` (tema base) + `cockpit/theme.py`
  (`inject_theme()` + `render_logo()`). Llamado desde `app.py` y las 5
  páginas tras `set_page_config()`.
- Logo: `Logos/logo sin fondo.png` vía `st.logo()` (Streamlit ≥ 1.35).

#### Sidebar persistente "Producción en vivo"
- En todas las páginas, refresh 5s.
- Procesos Python detectados con `psutil` cuya cmdline contiene un script
  conocido (`generar_guion.py`, `generar_episodio_v2.py`, `run_pipeline.py`,
  etc.). Muestra PID, label, tiempo, RAM, log activo (mtime <5min) + tail
  3 últimas líneas.
- "Generándose ahora": ficheros aparecidos en `episodios/`/`output/`/`Videos/`
  con mtime <10min.
- Read-only: nunca lanza nada.

#### Modal de validaciones en página Estado
- Iconos OK/KO de cada celda (PDF/Guion/Audio/Video/Log) son **clicables**.
- Click → `@st.dialog` con resumen de la última ejecución para esa
  (módulo, categoría): errores, warnings, señales OK, conteo por fase,
  sample, badge de fuente (`📦 estructurado` / `📄 texto`).

#### Observabilidad estructurada con `runlog.py`
- Módulo nuevo en raíz del repo, sin dependencias externas (stdlib).
- API: `with RunLogger(episode, module, script) as log: log.event(phase, **kwargs)`.
- Output: `episodios/{episode}_events.jsonl` (append-only, una línea
  JSON por evento).
- Campos automáticos: `ts`, `episode`, `module`, `script`, `pid`, `phase`,
  `level` (`info`/`warn`/`error`), `category` (`pdf`/`guion`/`audio`/
  `video`/`log`/`system`). Kwargs libres para extras (`block`, `speaker`,
  `ms`, `credits`, `exc`, …).
- `cockpit/core/log_parser.py` ahora usa **prioridad JSONL > regex**:
  si existe `*_events.jsonl` para el módulo, parsea estructurado; si no,
  fallback al regex de logs libres.
- Pendiente: migrar generadores (`generar_guion.py`, `generar_episodio_v2.py`,
  etc.) a `runlog`. Trabajo en sesión `feature/genepisodios`. El fallback
  regex sigue funcionando mientras tanto.

---

## 11.bis QA (Quality Assurance) — políticas de validación

Cada artefacto que el sistema produce pasa por una función `check_X()` en
`pipeline/qa.py` antes de registrarse en la library / entregarse. Si
`check.ok == False`, el artefacto se descarta y NO se contamina el
estado del proyecto.

### Inventario de verificadores

| Función | Artefacto | Reglas |
|---|---|---|
| `check_kling_clip(path, min_dur, max_dur)` | Clip Kling MP4 | existe + tamaño ≥2MB + ffprobe lee duración (moov OK) + duración en rango + aspect 16:9 ±5% |
| `check_escaleta_md(path)` | Escaleta markdown | existe + ≥8 bloques + ≥20 intervenciones + cierre limpio (no truncado) + ≥50% de ivs marcan PIZARRA SI/NO |
| `check_scene_track(path, audio_dur)` | scene_track.json | monotónico (0 solapamientos) + drift vs audio_duration < 1s |
| `check_audio_structure(path)` | audio_structure.json | duración 600-1100s + sintonía detectada (8-12s) + content_start/end coherentes |
| `check_video_final(path, audio_dur)` | MP4 final | tamaño ≥30MB + duración ≈ audio (drift <1.5s) + resolución 1920×1080 |
| `check_library_integrity(library)` | Library completa | cada slug tiene fichero físico + tamaño OK + ffprobe OK |
| `check_srt(path)` | Subtítulos SRT | ≥50 chunks + ningún chunk >6s |

### Persistencia de tareas Kling (`kling_tasks.jsonl`)

Append-only journal con fsync en cada escritura. Eventos:

```jsonl
{"event":"submit","slug":"...","task_id":"...","kind":"base|extend",
 "extend_step":0,"image_url":"...","duration":10,"target_duration":20}
{"event":"complete","slug":"...","task_id":"...","video_id":"...","video_url":"..."}
{"event":"fail","slug":"...","task_id":"...","reason":"..."}
{"event":"download","slug":"...","path":"...","size":12345}
{"event":"qa","slug":"...","ok":true,"checks":{...}}
{"event":"register","slug":"...","ok":true}
```

**Regla crítica**: el `submit` se loguea ANTES de pollear. Si el proceso
muere durante el polling, la tarea queda registrada y `kling_reconcile.py`
puede recuperarla (no se pierden créditos pagados).

### Recuperación de tareas huérfanas

```bash
# Ver qué hay pendiente sin gastar nada
python tools/kling_reconcile.py --dry-run

# Recuperar todo lo huérfano (poll Kling + descarga + QA + register)
python tools/kling_reconcile.py

# Solo un slug
python tools/kling_reconcile.py --slug studio_yago_solo_v1
```

### Lecciones aprendidas (8 mayo 2026)

Tras una sesión cara de generación con Kling:

| Problema | Causa | Mitigación |
|---|---|---|
| 26+ tareas huérfanas pagadas no descargadas | Submits sin persistencia → proceso muere y se pierden | `kling_tasks.jsonl` con fsync ANTES de pollear |
| Clips truncados (4MB en vez de 47MB) | Download timeout sin retry | `_download_video` con 4 retries + verificación moov atom |
| 429 cascading en parallel | Submit demasiado rápido (1.5s) saturó Kling | spacing 5-8s + retry exponencial 10s..120s |
| 429 persistente con submits aislados | Cuota diaria/mensual del plan agotada | Esperar reset (24h UTC+8) antes de relanzar |
| Refs viejas servidas durante batch | `git push` no se hizo antes de generar | Verificar MD5 local↔GitHub raw antes de cada batch |
| Stat_card "202" en vez de "88%" | Regex truncaba años a 3 dígitos | Regex con sufijo obligatorio (%/M/K/B) + lookahead |
| Subtítulos desincronizados crecientes | scene_track con TCs solapados acumulando 30s drift | `escaleta_to_pipeline` recorta `seg.end = next.start` |

---

## 11. Técnicas de IA aplicadas (deep dive)

### 11.1 Generación de texto (LLM)

- **Claude Sonnet 4.5** (anthropic) para guion + escaleta. System
  prompt extenso (5-7KB) con reglas duras.
- **Streaming requerido** para max_tokens > umbral (Anthropic exige
  streaming si la generación estimada > 10 min).
- **Prompt caching de Anthropic**: el system prompt se cachea, baja
  coste en runs subsecuentes.

### 11.2 Extracción de conceptos (LLM con structured output)

- **Claude Haiku 4.5** procesa cada PDF con un schema JSON:
  `[{name, slug, definicion, sinonimos, visual_idea, importance}]`.
- Coste muy bajo (~$0.05 todos los PDFs) por usar Haiku.
- Resultado normalizado y dedupe por slug.

### 11.3 ASR (Whisper)

- `large-v3` para máxima precisión, `medium` para balance, `tiny` para
  test.
- Output con timestamps por palabra, imprescindible para subtítulos
  sincronizados.

### 11.4 TTS multi-speaker

- ElevenLabs `eleven_v3` con dos voces calibradas (María/Yago).
- Etiquetas inline `[ironico]`, `[serio]`, etc. al inicio de cada
  intervención modulan el tono.
- `<silence duration="2s"/>` controla las pausas para que
  `audio_analyzer` pueda detectar la estructura.

### 11.5 Cross-correlation (DSP) — sintonía detection

- Problema: silencedetect no es preciso cuando hay música de fondo
  durante el contenido.
- Solución: `scipy.signal.correlate(audio_episodio, sintonia_mp3)`
  busca el offset exacto donde aparece la sintonía.
- Devuelve `(start, end, confidence)` con precisión sub-segundo.

### 11.6 Image-to-video (Kling diffusion)

- Modelo: Kling 1.6 Pro (Kuaishou). Diffusion-based video generation.
- **Image-to-video**: el frame inicial es una imagen de referencia
  pública. La consistencia facial es ~95% entre clips.
- **Extend feature**: continúa la escena desde el último frame del
  clip previo. Cada extend añade ~5s. Concatenando: 10s base + 5s + 5s
  = 20s. Observación: la cámara orbita ligeramente (no zoom in),
  efecto cinematográfico aceptable.
- Negative prompt anti-alucinación de segunda persona, marcas, lipsync
  errors.

### 11.7 Forced alignment (futuro, no implementado)

- Para subtítulos = texto exacto del guion en lugar de Whisper words,
  se evaluó **WhisperX** (wav2vec2 forced alignment, precisión ~20ms).
- Decisión actual: usar Whisper words directamente — el problema de
  sincronización resultó ser drift de scene_track (corregido), no de
  timestamps Whisper.

### 11.8 Lip-sync (futuro, pendiente API key)

- Sync.so `lipsync-v2` o Hedra Character-3.
- Coste estimado: $1/episodio en HOOK + CIERRE_FINAL · $5/episodio
  entero.

---

## 12. Bugs conocidos y resueltos (cronología)

| Bug | Causa | Fix |
|---|---|---|
| Subtítulos desincronizados crecientes | scene_track con TCs que se solapan acumulando 30s de drift | `escaleta_to_pipeline` recorta `seg.end = next.start` (`d131594`) |
| `studio` vs `estudio` (en/es) | scene_track_builder ponía "studio", compositor checkeaba "estudio" | `seg["type"] in ("estudio", "studio")` (`d131594`) |
| ffmpeg "Option not found scale=...:format=..." | Dos puntos entre filtros | Coma: `scale=…,format=…` |
| Sintonía cortada/desfasada | silencedetect daba 8.54s para 10s | Cross-correlation scipy (`sintonia_detector.py`) |
| Stat_card valor "202" en vez de "88%" | Regex truncaba 2026 a 3 dígitos | Regex con sufijo obligatorio + lookahead (`8b2284d`) |
| Polling Kling timeout 30s | Read timeout corto | 90s + 5 retries con backoff (`b7c1ac4`) |
| Escaleta truncada | max_tokens 12000-16000 insuficientes | 32000 con streaming (`12080e5`) |
| Pool studio resuelve a clips inexistentes | `_scenes_index.json` con entradas huérfanas | `_resolve_speaker_pool` verifica `Path.exists()` (`1b55211`) |
| Subtítulos amarillos en keywords | Highlight automático con keywords | `_highlight()` retorna texto sin modificar (`d131594`) |

---

## 13. Pendientes vivos

1. **17 clips Kling** generándose en background (~6h cola, $24).
2. **Reforzar prompt v2** para que el LLM no ponga texto del guion en
   la pizarra (`highlight_quote` con citas literales).
3. **Wrap de texto** en `warning_badge` / `regulation_alert` (se cortan
   labels >24 chars).
4. **Pizarra rica con imágenes**: integrar `media_finder` (Wikipedia +
   Tenor) en `escaleta_generator` para que las cards no sean sólo texto.
5. **Lip-sync Sync.so** cuando llegue `SYNC_API_KEY` del usuario.
6. **Caja "CAT" residual** en `establishing.png` y `studio.png`
   (fondo izquierdo, logo CAT pequeño en un container amarillo).
7. **Episodios M1..M14** producir en cadena con `lanzar_produccion.py`.

---

## 14. Reglas de oro del sistema

1. **El audio es la verdad temporal**. Nunca cambiar el texto de las
   intervenciones desde el video pipeline; el audio ya está fijado.
2. **Los cortes de plano sólo en pausas naturales** (puntos, fines de
   idea). Nunca a mitad de frase.
3. **No repetir clip** dentro de la misma intervención.
4. **Pizarra = sólo cuando aporta**. Mínimo 15s, elementos cada 4s,
   ≥1 cada 3min, NO cita literal del guion.
5. **El monorepo no es el sistema de filesystem real**: muchos paths
   son absolutos a `C:\Users\Asus\maquinaria_pesada\`. El código asume
   esa raíz.
6. **`override=True` en load_dotenv**: las variables de entorno cargadas
   por Windows NO deben ganar a las del archivo `.env`.
7. **Streaming en Anthropic** cuando max_tokens > 16k.
8. **Los clips de Kling necesitan URL pública** (no localhost, no
   catbox — Kling bloquea catbox.moe). GitHub raw funciona si el repo
   es público.
9. **Trabajar siempre en rama `videopodcast`**. Consolidar a `master`
   sólo cuando un hito está validado.
10. **Idioma de respuesta y commits: español** salvo nombres técnicos
    (que van en inglés).

---

## 15. Anexo: comandos útiles

```bash
# Verificar estado del repo
cd /c/Users/Asus/maquinaria_pesada && git status

# Ver logs en vivo de un render
tail -f maquinaria_pesada_pipeline/outputs/logs/EP-MOD000_pipeline.log

# Inspeccionar la library de clips
cat Videos/escenas_biblioteca/_scenes_index.json | jq 'keys'

# Re-render preview rápido (~5min)
python maquinaria_pesada_pipeline/tools/render_from_escaleta.py \
    --episode EP-MOD000 --preview --preview-seconds 90

# Lanzar cockpit
streamlit run cockpit/app.py

# Generar 1 clip Kling (test crédito)
python maquinaria_pesada_pipeline/tools/generate_studio_clips_kling.py \
    --slug studio_maria_solo_v2

# Recuperar task Kling huérfana
python maquinaria_pesada_pipeline/tools/kling_recover.py \
    --task-id <ID> --kind base --slug recovery_test
```

---

## 16. Glosario

- **Hook**: gancho inicial del episodio, ~30s con un dato/pregunta
  potente y cierre canónico _"Esto es MaquinarIA Pesada. Arrancamos."_
- **Sintonía**: 10s de música identificativa entre HOOK y CONTENIDO.
  Detectada por cross-correlation.
- **Plano**: tipo de toma del scene_track. ESTABLISHING / TWO_SHOT_*_ACTIVE
  / CLOSE_UP_* / DETAIL / BOTH_COMPLICIT / OUTRO / BLACK / PIZARRA.
- **PIP**: Picture-in-Picture, el recuadro 25% bottom-right con el
  presentador cuando la pizarra es fullscreen.
- **scene_track**: lista de segmentos `[{type, start, end, source,
  pip_source, ...}]`. Define qué se muestra en cada momento.
- **scene_timeline**: lista de escenas con sus overlays PIL.
- **Library**: catálogo persistente de clips Kling/Luma con metadata
  por slug.
- **Pool**: subconjunto del library asignado a un speaker, usado por
  el rotador no-repeat.
- **Drift**: desfase progresivo entre audio y video (corregido).
- **Layout C**: pizarra fullscreen + PIP del presentador en esquina.
  Layout activo desde 8 mayo 2026.

---

## Anexo A — Estimación de costes por episodio

> Cifras orientativas para **un episodio de 15 min**. Pueden variar según
> tarifas vigentes de cada API. No incluye Kling B-roll (cobro aparte por
> minuto generado, ~$1-2 por episodio según cantidad de clips).

| Servicio | Modelo | Métrica | Volumen típico | Coste aprox. |
|---|---|---|---|---|
| Anthropic | Claude Sonnet 4.5 (guion + escaleta) | tokens | ~10k in + 8k out | $0.10–$0.20 |
| Anthropic | Claude Haiku (concept_extractor) | tokens | ~3k in + 1k out | $0.005 |
| OpenAI | `whisper-1` | minutos audio | 15 min | $0.09 |
| ElevenLabs | `eleven_v3` | caracteres | ~12k chars (1900 palabras × ~6) | $0.30–$0.60 |
| Kling | 1.6 Pro image-to-video | segundos generados | 30-60s de B-roll | $1.00–$2.00 |
| **Total estimado / episodio** | | | | **~$1.50–$3.00** |

15 episodios completos ≈ **$23–$45**. Coste marginal trivial frente al
trabajo manual equivalente.

---

## Anexo B — Esquema de evento JSONL (`runlog`)

Eventos emitidos por los generadores vía `runlog.RunLogger`. Un objeto
JSON por línea, append-only en `episodios/{episode}_events.jsonl`.

```json
{
  "ts": "ISO 8601 con sufijo Z (UTC)",
  "episode": "string (M3_E_ML | EP001 | …)",
  "module": "M0..M14",
  "script": "filename.py",
  "pid": 4242,
  "phase": "string (start | extract_pdf | parse_blocks | synth_block | mount_audio | validate | end | …)",
  "level": "info | warn | error",
  "category": "pdf | guion | audio | video | log | system",

  "// kwargs libres": "ejemplos comunes:",
  "block": 12,
  "speaker": "IAGO | MARIA",
  "ms": 312,
  "credits": 1024,
  "exc": "string (solo en errores)",
  "traceback": "string truncado (solo en errores)",
  "elapsed_s": 0.01
}
```

Lectura desde la cockpit: `cockpit.core.log_parser.parse(module, category)`
prioriza JSONL si existe; si no, cae a regex sobre `*.log`. Misma API
`CategorySummary` en ambos casos.

---

**FIN BIBLIA · MaquinarIA Pesada**

Mantén este documento actualizado tras cada cambio arquitectónico. Si
añades un módulo nuevo, regla nueva, modelo nuevo, account nueva — entra
aquí. Es la fuente única de verdad del sistema.
