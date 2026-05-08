# BIBLIA DEL SISTEMA — MaquinarIA Pesada
### Sistema de creación automática de contenido con IA

> **Versión:** 2026-05-08  
> **Repositorio:** https://github.com/bakero/maquinaria-pesada  
> **Rama de trabajo activa:** `feature/genepisodios`  
> **Mantenedor:** bkasero@gmail.com

---

## ÍNDICE

1. [Visión general](#1-vision-general)
2. [Tecnologías y cuentas de IA](#2-tecnologias-y-cuentas-de-ia)
3. [Estructura de carpetas](#3-estructura-de-carpetas)
4. [El contenido: qué es MaquinarIA Pesada](#4-el-contenido)
5. [Pipeline de audio: cómo se crea un episodio](#5-pipeline-de-audio)
6. [Pipeline de vídeo: cómo se crea el videopodcast](#6-pipeline-de-video)
7. [Scripts clave — referencia detallada](#7-scripts-clave)
8. [La consola de control: Cockpit](#8-cockpit)
9. [Especificación maestra (PODCAST_MASTER_SPEC.md)](#9-especificacion-maestra)
10. [Estado actual de producción](#10-estado-actual)
11. [Flujo de trabajo con Claude Code + Codex](#11-flujo-de-trabajo)
12. [Gestión de ramas y worktrees](#12-git)
13. [Variables de entorno y credenciales](#13-credenciales)
14. [Convenciones de nomenclatura](#14-nomenclatura)
15. [Reglas de desarrollo (invariantes de sesión)](#15-reglas-de-desarrollo)

---

## 1. VISIÓN GENERAL

**MaquinarIA Pesada** es un podcast (y videopodcast) técnico sobre Inteligencia Artificial dirigido a directivos y profesionales que lideran proyectos de IA en empresa, producido **al 100% con IA**:

- El guion lo genera **OpenAI GPT-4.1** a partir de PDFs de un máster de IA.
- Las voces las sintetiza **ElevenLabs eleven_v3** con dos personajes: Iago y María.
- El vídeo lo produce un pipeline Python que combina **Whisper + Pillow + Claude + ffmpeg**.
- La orquestación, validación y corrección de código la hace **Claude Code** (este asistente).
- La ejecución de producción en máquina la hace **OpenAI Codex CLI**.

El resultado final es un episodio de 12–17 minutos de audio (MP3) y su versión videopodcast (MP4) lista para publicar.

### Flujo de alto nivel

```
PDF del máster
    ↓  generar_guion.py (GPT-4.1)
Guion .txt etiquetado
    ↓  generar_episodio_v2.py (ElevenLabs)
Audio .mp3 con música de fondo y sintonía
    ↓  maquinaria_pesada_pipeline/run_pipeline.py (Whisper + Claude + ffmpeg)
Videopodcast .mp4 con subtítulos, overlays y chapitulos
    ↓
Publicación (YouTube, Spotify, etc.)
```

---

## 2. TECNOLOGÍAS Y CUENTAS DE IA

### Lenguajes y entorno

| Elemento | Detalle |
|----------|---------|
| Lenguaje principal | Python 3.12 |
| Sistema operativo | Windows 11 (ASUS Zenbook S 14 UX5406SA, Intel Lunar Lake) |
| Gestor de paquetes | pip |
| Control de versiones | Git + GitHub |
| IDE / asistente | Claude Code (CLI) |
| Ejecutor de producción | OpenAI Codex CLI |

### APIs de IA

| Servicio | Uso | Modelo activo | Cuenta |
|----------|-----|---------------|--------|
| **OpenAI** | Generación de guiones, revisión, extracción de conceptos | `gpt-4.1` (generación), `gpt-4.1-mini` (revisión/conceptos) | OPENAI_API_KEY en `.env` |
| **ElevenLabs** | Síntesis de voz TTS | `eleven_v3` | ELEVENLABS_API_KEY en `.env` |
| **Anthropic Claude** | Director visual del pipeline de vídeo (scene timeline) | Sonnet (via API) | ANTHROPIC_API_KEY en `.env` |
| **Luma AI** | Generación de clips de vídeo (image-to-video) | Luma Dream Machine | LUMA_API_KEY en `.env` |

### Librerías principales

```
# Audio
elevenlabs          TTS con eleven_v3
pydub               Montaje y manipulación de audio
ffmpeg (Gyan)       Codificación y composición de vídeo (WinGet)

# Guiones
openai              Llamadas a GPT-4.1
pdfplumber          Extracción de texto de PDFs

# Vídeo
Pillow              Overlays PNG (name tags, stat cards, stickers)
openai-whisper      Transcripción con timestamps por palabra
anthropic           Claude como director visual del scene timeline

# Cockpit
streamlit           Dashboard web de control
streamlit-autorefresh  Refresh automático del sidebar
psutil              Detección de procesos activos

# Utilidades
python-dotenv       Carga de variables de entorno
httpx               Llamadas HTTP directas (test de API, créditos)
```

### Voces ElevenLabs (configuración activa en PODCAST_MASTER_SPEC.md)

| Personaje | Voice ID | Stability | Speed | Similarity | Style |
|-----------|----------|-----------|-------|------------|-------|
| **IAGO** | `CdAqYBLnsNjmTqYgD5Ha` | 0.65 | 1.20 | 0.75 | 0.0 |
| **MARÍA** | `gD1IexrzCvsXPHUuT0s3` | 0.68 | 1.20 | 0.75 | 0.0 |

- `post_speed_multiplier`: 1.10 (se aplica en el montaje pydub)
- Output format: `mp3_44100_128`
- Silencios: 300ms entre bloques del mismo speaker, 500ms entre speakers distintos

---

## 3. ESTRUCTURA DE CARPETAS

```
C:\Users\Asus\maquinaria_pesada\          ← REPO ROOT (main path: master)
│
├── .env                                   ← Credenciales (NO en git)
├── .gitignore
├── PODCAST_MASTER_SPEC.md                ← FUENTE ÚNICA DE VERDAD (spec + config JSON)
├── BIBLIA_SISTEMA.md                     ← Este documento
├── SESION_genepisodios.md                ← Contexto sesión de desarrollo activa
├── INSTRUCCIONES.txt                     ← Instrucciones operativas para Codex
├── VOICE_CONFIG_REFERENCE.md            ← Referencia rápida de voces (spec es canónica)
├── WORKFLOW_PAIR_PROGRAMMING.md          ← Protocolo Claude-Codex
│
├── PDFs/                                 ← Fuentes de contenido (resúmenes del máster)
│   ├── M0_T_Introduccion_Estrategica.pdf
│   ├── M1_T_Fundamentos_Razonamiento.pdf
│   └── ... (M0–M14, un PDF por módulo)
│
├── Guiones/                              ← Guiones generados (Formato A)
│   ├── M0_T_Introduccion_Estrategica.txt
│   ├── M1_T_Fundamentos_Razonamiento.txt
│   └── ... (M0–M14, un guion por módulo)
│
├── episodios/                            ← Audios finales y logs de producción
│   ├── M0_E_Introduccion_Estrategica.mp3
│   ├── M0_produccion.log
│   ├── M1_E_Fundamentos_Razonamiento.mp3
│   ├── M1_produccion.log
│   ├── produccion_runs.log               ← Log maestro de sesiones batch
│   ├── M{N}_E_{Titulo}_cmd.log           ← Stdout+stderr completo por episodio
│   └── temp/                             ← Fragmentos MP3 temporales (se borran)
│
├── Videos/                               ← Videopodcasts y assets visuales
│   ├── escenas_biblioteca/               ← Banco de escenas reutilizables
│   │   ├── _scenes_index.json
│   │   ├── estudio/                      ← Fondos de estudio
│   │   ├── b_roll/                       ← B-roll genérico
│   │   ├── conceptos/                    ← Visualizaciones de conceptos
│   │   ├── transiciones/                 ← Clips de transición
│   │   ├── stickers_anim/                ← Stickers animados
│   │   ├── cierres/                      ← Pantallas de cierre
│   │   ├── media/                        ← Imágenes/GIFs por concepto
│   │   └── refs/                         ← Referencias de personajes
│
├── Música/                               ← Assets de audio
│   ├── base podcast.mp3                  ← Música de fondo principal
│   └── Sintonia Maquinaria pesada.mp3    ← Sintonía de apertura (10s)
│
├── intro/                                ← Intro del videopodcast (assets)
├── Logos/                                ← Logos del programa
│   └── logo sin fondo.png
│
├── cockpit/                              ← Dashboard Streamlit de control
│   ├── app.py                            ← Entry point: streamlit run cockpit/app.py
│   ├── ui.py                             ← Sidebar "Producción en vivo"
│   ├── core/
│   │   ├── paths.py                      ← Resolución de rutas del repo
│   │   ├── state.py                      ← Inventario por módulo (PDF/guion/audio/vídeo)
│   │   ├── log_parser.py                 ← Parser de logs de producción
│   │   └── monitor.py                    ← Detector de procesos activos (psutil)
│   ├── pages/
│   │   ├── 1_📊_Estado.py               ← Tabla de estado M0–M14
│   │   ├── 2_🔌_Conectores.py           ← Servicios y pipelines registrados
│   │   ├── 3_📝_Generar_Prompt.py       ← Formularios → comandos CLI para Codex
│   │   ├── 4_📚_Fuentes.py              ← Explorador de PDFs, guiones, audio, vídeo
│   │   └── 5_📜_Logs.py                 ← Visor de logs con auto-refresh
│   └── connectors/
│       ├── pipelines/                    ← Conectores a scripts de generación
│       └── services/                     ← Conectores a APIs (ElevenLabs, OpenAI, etc.)
│
├── maquinaria_pesada_pipeline/           ← Pipeline de videopodcast
│   ├── run_pipeline.py                   ← Orquestador principal (--preview, --from-step)
│   ├── setup_project.py                  ← Setup interactivo de assets
│   ├── pipeline/                         ← Módulos del pipeline (ver sección 6)
│   │   ├── asset_validator.py
│   │   ├── transcriber.py                ← Whisper
│   │   ├── audio_analyzer.py             ← Análisis de silencios y estructura
│   │   ├── content_extractor.py          ← Stats y keywords del guion+PDF
│   │   ├── scene_builder.py              ← Claude como director visual
│   │   ├── scene_library.py              ← Banco de escenas reutilizables
│   │   ├── scene_track_builder.py        ← Construcción del track de escenas
│   │   ├── overlay_renderer.py           ← Frames PNG con overlays (Pillow)
│   │   ├── subtitle_generator.py         ← SRT desde guion + Whisper
│   │   ├── video_compositor.py           ← Composición final con ffmpeg
│   │   ├── luma_generator.py             ← Clips Luma AI (image-to-video)
│   │   ├── media_finder.py               ← Buscador de imágenes/GIFs para conceptos
│   │   └── metadata_generator.py         ← Chapters JSON + thumbnail
│   └── templates/                        ← Overlays, fondos, stickers, prompts LLM
│
├── # Scripts de producción de audio (raíz)
├── generar_guion.py                      ← Genera guion desde PDF con GPT-4.1
├── generar_episodio_v2.py                ← Sintetiza audio con ElevenLabs
├── producir_episodio.py                  ← Pipeline completo guion+audio en un comando
├── lanzar_produccion.py                  ← Batch runner: genera todos los pendientes
├── validar_episodio.py                   ← Validador post-generación
├── normalizar_guiones.py                 ← Convierte guiones Formato B → Formato A
├── podcast_spec.py                       ← Validador y parser de guiones
├── estado_proyecto.py                    ← Estado de producción por módulo
│
└── .claude/
    ├── worktrees/
    │   ├── genepisodios/                 ← Worktree activo de feature/genepisodios
    │   ├── videopodcast/                 ← Worktree de feature/videopodcast
    │   └── laughing-leavitt-*/           ← Worktree de APPContenidos
    └── projects/.../memory/              ← Memoria persistente del proyecto
```

---

## 4. EL CONTENIDO

### El podcast

**MaquinarIA Pesada** cubre los 15 módulos de un máster de IA para empresa (M0–M14):

| Módulo | Tema |
|--------|------|
| M0 | Introducción Estratégica |
| M1 | Fundamentos del Razonamiento IA |
| M2 | Matemáticas para IA |
| M3 | Machine Learning Clásico |
| M4 | Deep Learning |
| M5 | NLP y LLMs |
| M6 | Ingeniería de Prompts |
| M7 | Sistemas RAG |
| M8 | Ingeniería y LLMOps |
| M9 | Infraestructura y Despliegue |
| M10 | Sistemas Agentes |
| M11 | Automatización con IA |
| M12 | Seguridad en IA |
| M13 | Gobernanza y Ética |
| M14 | Estrategia Empresarial con IA |

### Los presentadores

- **Iago** (pronunciado "Yago" en el audio): voz grave, contundente, técnico. Abre los episodios impares.
- **María**: voz clara, analítica, directa. Abre los episodios pares.

Formato: conversación a dos voces, dialéctica, que alterna explicación y debate.

### Audiencia objetivo

Profesionales cercanos a tecnología que lideran o participan en proyectos de IA en empresa. Tono: divulgativo técnico, riguroso pero accesible.

---

## 5. PIPELINE DE AUDIO

### Paso 1 — Generación del guion: `generar_guion.py`

**Entrada:** PDF del módulo + `PODCAST_MASTER_SPEC.md`  
**Salida:** `Guiones/M{N}_T_{Titulo}.txt`  
**Tecnología:** OpenAI `gpt-4.1`

**Proceso:**
1. Extrae el texto completo del PDF con `pdfplumber`
2. Extrae fragmentos relevantes del máster con búsqueda por keywords (`extract_relevant_master_context`)
3. Llama a GPT-4.1 con un prompt que incluye la spec completa, el texto del PDF y el contexto del máster
4. GPT-4.1 genera el guion en Formato A con las secciones obligatorias
5. El guion pasa por `normalize_generated_script()` para limpiar etiquetas y formato
6. Se valida con `validate_script_text()` de `podcast_spec.py`
7. Si hay errores, GPT-4.1-mini hace una revisión y corrección (`review_model`)
8. Se añade el bloque `# VERIFICACIONES` con métricas automáticas

**Formato de guion generado (Formato A):**
```
# HOOK
IAGO: [tenso] Texto del hook...
MARIA: [serio] Respuesta...
...
Esto es MaquinarIA Pesada. Arrancamos.

# INTRO_SONIDO
# [INTRO - SONIDO DE MAQUINAS ARRANCANDO - 8-10 segundos]

# SALUDO_Y_PRESENTACION
MARIA: [conversacional] Bienvenidos...

# BLOQUE_1
...
# BLOQUE_2
...
# INSERCION_1
...
# BLOQUE_3
...
# BLOQUE_4
...
# CIERRE_CONCEPTOS
No te puedes ir de este capitulo sin haber entendido estos conceptos
...

# CIERRE_FINAL
...Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada.
Siguenos para nuevos capitulos donde la I.A. crea contenido sobre I.A.

# VERIFICACIONES
Palabras totales: X
Bloques de contenido: Y
...
```

---

### Paso 2 — Validación y normalización: `podcast_spec.py` + `normalizar_guiones.py`

**`podcast_spec.py`** es el validador central. Expone:

- `load_master_spec()`: parsea el JSON embebido en `PODCAST_MASTER_SPEC.md`
- `validate_script_text()`: valida estructura, orden de secciones, paridad de speaker en HOOK, frases obligatorias, etiquetas TTS
- `parse_script_blocks()`: convierte el guion en una lista de bloques `{speaker, text, index, section, tag}`
- `normalize_text_for_match()`: elimina acentos, normaliza espacios (usado para comparación fuzzy)

**Validaciones estructurales (fatales — bloquean la generación):**
- Secciones requeridas en orden correcto
- HOOK abierto por el speaker correcto según paridad (impar=IAGO, par=MARÍA)
- Frases literales obligatorias presentes (hook closing, intro comment, concepts opening, final closing)
- Mínimo 4 bloques de contenido, máximo 6

**Validaciones de calidad (WARN — no bloquean):**
- Palabras totales 1.800–2.200
- Mínimo 2 frases por bloque
- Media de palabras por intervención
- Número de inserciones

**`normalizar_guiones.py`** convierte guiones en Formato B (legacy, con secciones `# INTRO`, `# NÚCLEO TEMÁTICO`, `# CIERRE CON CTA`) al Formato A requerido. Se usó para convertir los 15 guiones generados en sesiones anteriores.

---

### Paso 3 — Síntesis de audio: `generar_episodio_v2.py`

**Entrada:** Guion `.txt` + `PODCAST_MASTER_SPEC.md`  
**Salida:** `episodios/M{N}_E_{Titulo}.mp3` + log de producción  
**Tecnología:** ElevenLabs `eleven_v3` + pydub + ffmpeg

**Proceso detallado:**

1. **Setup**: detecta ffmpeg (WinGet o CapCut), carga `.env` con `override=True`
2. **Parseo del guion**: `parsear_guion()` → llama a `validate_script_text()`, separa issues hard/soft, extrae bloques con `parse_script_blocks()`
3. **Snapshot inicial**: consulta créditos ElevenLabs disponibles antes de generar
4. **Generación bloque a bloque**:
   - Para cada bloque del guion: llama a `client.text_to_speech.convert()` con voz, modelo y VoiceSettings del speaker
   - 3 reintentos por bloque
   - Errores 401/403 → `SystemExit` inmediato (no reintentar)
   - Errores 429 (rate limit) → espera exponencial
   - Guarda fragmento MP3 temporal en `episodios/temp/`
5. **Montaje con pydub**:
   - Concatena todos los fragmentos con silencios entre speakers
   - Aplica `post_speed_multiplier` (1.10x)
   - Mezcla la sintonía de apertura al inicio
   - Mezcla la música de fondo al nivel configurado (-20dB)
6. **Verificación de audio**: comprueba que el MP3 existe, es legible y tiene duración razonable (WARN si fuera de rango, no ERROR)
7. **Log de producción**: escribe `episodios/M{N}_produccion.log` con escaleta, métricas, consumo de créditos
8. **Limpieza**: borra los fragmentos temporales

**Tipos de error y su tratamiento:**

| Error | Tratamiento |
|-------|-------------|
| Validación estructural del guion | `SystemExit` (aborta antes de gastar créditos) |
| Validación de calidad del guion | `[WARN]` + continúa |
| ElevenLabs 401/403 | `SystemExit` inmediato |
| ElevenLabs 429 rate limit | Retry con backoff |
| Bloque TTS falla 3 veces | Registra como fallido, continúa con el resto |
| Duración fuera de rango | `[WARN]` en log y consola, no falla |
| Bloques generados < total | ERROR en validación final |

---

### Paso 4 — Batch runner: `lanzar_produccion.py`

Detecta automáticamente los módulos con guion pero sin audio (`pendientes()`) y los genera en serie.

- Log por episodio: `episodios/M{N}_E_{Titulo}_cmd.log` (stdout+stderr completo)
- Log maestro: `episodios/produccion_runs.log` (acumula todas las sesiones)
- Timeout: 30 minutos por episodio
- Extrae el error más informativo del output en caso de fallo

```bash
python lanzar_produccion.py                    # todos los pendientes
python lanzar_produccion.py --ep M5_E_NLP_LLMs # episodio concreto
python lanzar_produccion.py --dry-run          # muestra comandos sin ejecutar
```

---

### Paso 5 — Validación post-generación: `validar_episodio.py`

Valida un episodio ya generado con 6 checks:

| # | Check | Tipo |
|---|-------|------|
| 1 | MP3 existe y > 1 MB | ERROR |
| 2 | Audio cargable con pydub | ERROR |
| 3 | Duración entre 8 y 60 min | WARN |
| 4 | Log existe y contiene "Produccion completada" | ERROR |
| 5 | Log sin errores críticos (ERROR/FAILED/Exception) | ERROR |
| 6 | Bloques procesados == bloques en guion | ERROR si incompleto |

Muestra barra de progreso ASCII de bloques y estimación de créditos ElevenLabs consumidos.

```bash
python validar_episodio.py --ep M3_E_Machine_Learning_Clasico \
    --guion Guiones/M3_T_Machine_Learning_Clasico.txt
```

---

## 6. PIPELINE DE VÍDEO

El pipeline de videopodcast está en `maquinaria_pesada_pipeline/` y produce un MP4 listo para publicar a partir del audio y el guion.

### Orquestador: `run_pipeline.py`

```bash
python run_pipeline.py                   # render completo 1080p
python run_pipeline.py --preview         # primer minuto a 720p (validación rápida)
python run_pipeline.py --from-step 5     # reanudar desde paso 5
python run_pipeline.py --force           # ignorar caches
python run_pipeline.py --no-llm          # forzar heurístico (sin Claude)
```

### Pasos del pipeline

| Paso | Módulo | Tecnología | Output |
|------|--------|------------|--------|
| 0 | `asset_validator` | stdlib | Verifica rutas y formatos |
| 1 | `transcriber` | OpenAI Whisper | `transcription_raw.json` (timestamps por palabra) |
| 2 | `content_extractor` | GPT-4.1-mini | `content_data.json` (stats, keywords, conceptos) |
| 3 | `audio_analyzer` | pydub | `audio_structure.json` (silencios, sintonía, hook) |
| 4 | `scene_builder` | **Claude Sonnet** | `scene_timeline.json` (qué escena va en cada momento) |
| 5 | `scene_track_builder` | Python | Track sincronizado de escenas + duración |
| 6 | `overlay_renderer` | **Pillow** | Frames PNG con name tags, stat cards, stickers |
| 7 | `subtitle_generator` | Whisper + guion | `*_subtitulos.srt` con keywords resaltadas |
| 8 | `video_compositor` | **ffmpeg** | MP4 final (intro + cuerpo + subtítulos) |
| 9 | `metadata_generator` | GPT-4.1-mini | Chapters JSON + thumbnail |

### Claude como director visual (scene_builder)

Claude Sonnet recibe el audio structure JSON (silencios, secciones, momentos clave) y el content data (conceptos, keywords) y genera el `scene_timeline.json`: para cada segmento del episodio, qué tipo de escena visual usar (estudio, b-roll conceptual, sticker de concepto, transición, cierre).

Puede forzarse a modo heurístico con `--no-llm` para no gastar créditos.

### Banco de escenas (`Videos/escenas_biblioteca/`)

Biblioteca de assets visuales reutilizables indexada en `_scenes_index.json`:
- **estudio**: fondos del estudio de grabación virtual
- **b_roll**: clips B-roll genéricos
- **conceptos**: visualizaciones de conceptos técnicos
- **transiciones**: clips de transición entre secciones
- **stickers_anim**: stickers animados de refuerzo
- **cierres**: pantallas de cierre y CTA
- **media**: imágenes y GIFs por concepto (generadas por `media_finder.py`)
- **refs**: referencias de personajes para Luma AI

### Luma AI (luma_generator)

Genera clips cortos (5–10s) de vídeo con Luma Dream Machine a partir de imágenes de referencia de los personajes, para crear B-roll con consistencia visual de Iago y María.

---

## 7. SCRIPTS CLAVE — REFERENCIA DETALLADA

### `podcast_spec.py`

Motor central de validación. **No genera nada — solo valida y parsea.**

```python
from podcast_spec import load_master_spec, validate_script_text, parse_script_blocks

spec = load_master_spec("PODCAST_MASTER_SPEC.md")
issues = validate_script_text(guion_text, ep_code, spec)
bloques = parse_script_blocks(guion_text, spec)
```

Funciones principales:
- `load_master_spec(path)` → dict con toda la config
- `validate_script_text(text, ep_code, spec)` → list[str] de issues
- `parse_script_blocks(text, spec)` → list[dict] con speaker, text, index, section, tag
- `normalize_text_for_match(text)` → str sin acentos, lowercase
- `opening_speaker(ep_code, spec)` → "IAGO" | "MARIA"
- `next_episode_code(guiones_dir, spec)` → siguiente código de episodio disponible
- `build_script_stats(bloques, spec)` → métricas del guion

### `generar_guion.py`

Genera guiones con GPT-4.1. Admite contexto adicional de otros PDFs.

```bash
python generar_guion.py --pdf PDFs/M5_T_NLP_LLMs.pdf
python generar_guion.py --pdf PDFs/M5_T_NLP_LLMs.pdf --contexto PDFs/master_completo.pdf
```

### `generar_episodio_v2.py`

Motor de síntesis de audio.

```bash
python generar_episodio_v2.py \
    --guion Guiones/M5_T_NLP_LLMs.txt \
    --ep M5_E_NLP_LLMs

# Opciones
--solo-bloque 7      # generar solo el bloque 7 (debug)
--dry-run            # parsear guion sin sintetizar
```

### `estado_proyecto.py`

Estado de producción por módulo. **Ejecutar siempre desde el main path.**

```bash
python estado_proyecto.py              # tabla completa
python estado_proyecto.py --pendiente  # solo módulos incompletos
python estado_proyecto.py --codex      # comandos CLI para Codex
python estado_proyecto.py --assets     # verificar assets de audio/música
```

### `normalizar_guiones.py`

Convierte guiones Formato B (legacy) al Formato A requerido. Genera `.bak` antes de sobreescribir.

```bash
python normalizar_guiones.py            # todos los guiones M*.txt
python normalizar_guiones.py --dry-run  # simular sin escribir
python normalizar_guiones.py --file Guiones/M5_T_NLP_LLMs.txt  # uno concreto
```

---

## 8. COCKPIT

Dashboard Streamlit para monitorizar y controlar la producción.

### Arrancar

```bash
cd C:\Users\Asus\maquinaria_pesada
streamlit run cockpit/app.py
```

O con repo alternativo:
```bash
REPO_ROOT=C:\otro\repo streamlit run cockpit/app.py
```

### Páginas

**📊 Estado (página principal)**
- Tabla por módulo M0–M14 con estado de PDF/Guion/Audio/Vídeo
- Métricas globales en tiempo real
- Click en ✅/❌ → modal con resumen de validaciones del último log

**🔌 Conectores**
- Lista de conectores registrados: servicios (ElevenLabs, OpenAI, ffmpeg, Codex), pipelines (generar_guion, generar_episodio, validar_episodio), fuentes (PDF, guion, audio, log, vídeo)
- Test de conectividad por conector

**📝 Generar Prompt**
- Formularios para construir comandos CLI listos para pegar en Codex
- Selección de módulo, opciones de generación, configuración de voz

**📚 Fuentes**
- Explorador de archivos por categoría (PDFs, guiones, episodios, vídeos, logs)
- Preview de contenido

**📜 Logs**
- Visor de `produccion_runs.log` y logs individuales
- Auto-refresh configurable
- Resaltado de errores y WARNs

### Sidebar: Producción en vivo

Se muestra en todas las páginas. Detecta en tiempo real (via `psutil`) si hay algún script del pipeline corriendo:
- Muestra PID, RAM, tiempo transcurrido
- Tail del log activo (últimas 3 líneas)
- Lista de archivos generándose en este momento
- Refresh cada 5 segundos (`streamlit-autorefresh`)

Scripts monitorizados: `generar_guion.py`, `generar_episodio_v2.py`, `lanzar_produccion.py`, `validar_episodio.py`, `normalizar_guiones.py`, `run_pipeline.py`, `dual_debate.py` y más.

---

## 9. ESPECIFICACIÓN MAESTRA

`PODCAST_MASTER_SPEC.md` es la **fuente única de verdad** del proyecto. Contiene:

1. **Texto en markdown**: reglas narrativas, principios editoriales, instrucciones operativas
2. **Bloque JSON embebido** (entre `<!-- PODCAST_SPEC_JSON_START -->` y `<!-- PODCAST_SPEC_JSON_END -->`): configuración estructurada que consumen todos los scripts

El JSON incluye:
- `directories`: rutas relativas de PDFs, guiones, audios, vídeos, música, etc.
- `openai`: modelos GPT y parámetros de generación
- `episode_defaults`: duración objetivo, audiencia, tono, límites de audio
- `speakers`: config de IAGO y MARÍA (display_name, etiquetas permitidas, paridad)
- `script_rules`: secciones requeridas/opcionales, frases obligatorias literales
- `audio_rules`: modelo ElevenLabs, voces, VoiceSettings, silencios, música

**Nunca editar el JSON directamente** si se hace desde Claude Code: el JSON debe ser consistente con el texto markdown. Si hay discrepancia, el JSON gana (es lo que leen los scripts).

---

## 10. ESTADO ACTUAL DE PRODUCCIÓN

*(Actualizado: 2026-05-08)*

| Módulo | PDF | Guion | Audio | Vídeo | Notas |
|--------|-----|-------|-------|-------|-------|
| M0 | ✓ | ✓ | ✓ | ✓ | **COMPLETO** |
| M1 | ✓ | ✓ | ✓ | — | Falta vídeo |
| M2 | ✓ | ✓ | ✓ | — | Falta vídeo |
| M3 | ✓ | ✓ | ✓ | — | Falta vídeo |
| M4 | ✓ | ✓ | ✓ | — | Falta vídeo |
| M5 | ✓ | ✓ | ✓ | — | Falta vídeo |
| M6 | ✓ | ✓ | ✓ | — | Falta vídeo |
| M7 | ✓ | ✓ | ✓ | — | Falta vídeo |
| M8 | ✓ | ✓ | ✓ | — | Falta vídeo. Duración 12 min (WARN) |
| M9 | ✓ | ✓ | ✓ | — | Falta vídeo |
| M10 | ✓ | ✓ | ✓ | — | Falta vídeo. Duración 11.4 min (WARN) |
| M11 | ✓ | ✓ | ✓ | — | Falta vídeo |
| M12 | ✓ | ✓ | — | — | **Créditos ElevenLabs agotados** |
| M13 | ✓ | ✓ | — | — | **Créditos ElevenLabs agotados** |
| M14 | ✓ | ✓ | — | — | **Créditos ElevenLabs agotados** |

**Créditos ElevenLabs**: agotados (límite del plan: 232.959 chars). Necesario recargar para generar M12–M14.

---

## 11. FLUJO DE TRABAJO CON CLAUDE CODE + CODEX

### División de responsabilidades

| Claude Code (este asistente) | Codex CLI |
|------------------------------|-----------|
| Diseña y modifica scripts | Ejecuta los scripts |
| Valida lógica y estructura | Genera guiones (`generar_guion.py`) |
| Gestiona git (commits, merges) | Genera audios (`lanzar_produccion.py`) |
| Detecta y corrige bugs | Lanza pipelines de vídeo |
| Actualiza specs y documentación | Reporta resultados |

### Workflow típico de producción de un módulo nuevo

```bash
# 1. [Codex] Ver qué hay pendiente
python estado_proyecto.py --codex

# 2. [Codex] Generar guion desde PDF
python generar_guion.py --pdf PDFs/M12_T_Seguridad_IA.pdf

# 3. [Claude Code] Revisar guion si falla validación
#    → normalizar_guiones.py o editar directamente

# 4. [Codex] Generar audio (cuando haya créditos)
python lanzar_produccion.py --ep M12_E_Seguridad_IA

# 5. [Codex] Validar resultado
python validar_episodio.py --ep M12_E_Seguridad_IA \
    --guion Guiones/M12_T_Seguridad_IA.txt

# 6. [Codex] Generar vídeo
cd maquinaria_pesada_pipeline
python run_pipeline.py --preview   # validar primero
python run_pipeline.py             # render completo

# 7. [Claude Code] Commit y consolidar en master
```

---

## 12. GESTIÓN DE RAMAS Y WORKTREES

```
master  ←  rama estable, producción
  ├── feature/genepisodios  ←  generación audio, guiones, validación
  ├── feature/videopodcast  ←  pipeline de vídeo, Luma, escenas
  └── APPContenidos         ←  cockpit Streamlit
```

### Worktrees activos

| Path | Rama | Propósito |
|------|------|-----------|
| `C:\...\maquinaria_pesada` | `master` | Trunk — scripts de producción, no tocar desde aquí |
| `.claude\worktrees\genepisodios` | `feature/genepisodios` | Desarrollo activo de audio/guiones |
| `.claude\worktrees\videopodcast` | `feature/videopodcast` | Pipeline de vídeo |
| `.claude\worktrees\laughing-leavitt-*` | `APPContenidos` | Cockpit |

### Regla de consolidación

Desarrollar en feature → cuando funcione, merge en master con `--no-ff` → push.

### ⚠️ Los scripts de producción se ejecutan desde el main path

`estado_proyecto.py`, `lanzar_produccion.py`, `generar_episodio_v2.py` usan `Path(__file__).parent` para resolver `episodios/`, `Guiones/`, etc. Desde un worktree, estas rutas apuntan al directorio del worktree (que no tiene los archivos generados). **Siempre ejecutar producción desde `C:\Users\Asus\maquinaria_pesada`**.

---

## 13. VARIABLES DE ENTORNO Y CREDENCIALES

Archivo: `C:\Users\Asus\maquinaria_pesada\.env` (NO en git)

```env
ELEVENLABS_API_KEY=sk_...      # TTS — eleven_v3
OPENAI_API_KEY=sk-...          # GPT-4.1 para guiones
ANTHROPIC_API_KEY=sk-ant-...   # Claude para scene_builder
LUMA_API_KEY=...               # Luma AI para clips de vídeo

# Opcional
REPO_ROOT=C:\Users\Asus\maquinaria_pesada   # para el cockpit
```

**Todos los scripts usan `load_dotenv(override=True)`** para que el `.env` tenga prioridad sobre variables de entorno del shell (evita problemas con keys cacheadas en la sesión).

### Límites de API a vigilar

| API | Límite | Estado actual |
|-----|--------|---------------|
| ElevenLabs | 232.959 chars/ciclo | **0 restantes — recargar** |
| OpenAI | Según plan | OK |
| Anthropic | Según plan Max 5x | OK |
| Luma | Según plan | OK |

---

## 14. CONVENCIONES DE NOMENCLATURA

| Tipo de archivo | Patrón | Ejemplo |
|-----------------|--------|---------|
| PDF fuente | `M{N}_T_{Titulo}.pdf` | `M3_T_Machine_Learning_Clasico.pdf` |
| Guion | `M{N}_T_{Titulo}.txt` | `M3_T_Machine_Learning_Clasico.txt` |
| Audio final | `M{N}_E_{Titulo}.mp3` | `M3_E_Machine_Learning_Clasico.mp3` |
| Vídeo final | `M{N}_V_{Titulo}.mp4` | `M3_V_Machine_Learning_Clasico.mp4` |
| Log de producción | `M{N}_produccion.log` | `M3_produccion.log` |
| Log de comando | `M{N}_E_{Titulo}_cmd.log` | `M3_E_Machine_Learning_Clasico_cmd.log` |

Donde `{N}` es el número de módulo (0–14) y `{Titulo}` es el nombre del tema en CamelCase con guiones bajos.

La letra intermedia indica la etapa:
- `_T_` = Texto/Guion
- `_E_` = Episodio (audio)
- `_V_` = Vídeo

---

## 15. REGLAS DE DESARROLLO (invariantes de sesión)

### Regla principal: cambio + verificación siempre juntos

> **Todo cambio introducido en la generación (`generar_episodio_v2.py`, `generar_guion.py`, `podcast_spec.py`, etc.) DEBE tener su contraparte en `validar_episodio.py`: un check que confirme que ese cambio se aplica correctamente en todos los episodios producidos.**
>
> Sin verificación → el cambio no está completo.

### Otras reglas operativas

1. **Commits atómicos**: un commit por cambio funcional. Mensaje claro con prefijo (`fix:`, `feat:`, `chore:`, `docs:`).
2. **Nunca editar `.env`** desde los scripts. Solo leer con `load_dotenv(override=True)`.
3. **`PODCAST_MASTER_SPEC.md` es canónica**: cualquier cambio de configuración (voces, límites, secciones) va primero ahí, luego se propaga al código.
4. **Hard vs Soft en validación**: errores estructurales (secciones, speaker, frases obligatorias) = `SystemExit`. Problemas de calidad (word count, duración, frases cortas) = `[WARN]` + continuar.
5. **Producción siempre desde el main path**: `lanzar_produccion.py` y `estado_proyecto.py` desde `C:\Users\Asus\maquinaria_pesada`, nunca desde un worktree.
6. **No mezclar scopes entre ramas**: `genepisodios` no toca `cockpit/` ni `maquinaria_pesada_pipeline/`. `videopodcast` no toca `Guiones/`. `APPContenidos` no toca scripts de audio.

---

*Documento generado automáticamente por Claude Code — MaquinarIA Pesada 2026*
