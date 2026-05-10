# 📖 La Biblia de MaquinarIA Pesada

**Sistema autónomo de producción de podcast/videopodcast con I.A.**

> *"Generamos al 100% con I.A. contenido sobre I.A. para directivos y profesionales."*

---

## Índice

1. [Visión general](#1-visión-general)
2. [Arquitectura del sistema](#2-arquitectura-del-sistema)
3. [Tecnologías, cuentas y APIs](#3-tecnologías-cuentas-y-apis)
4. [Estructura del repositorio](#4-estructura-del-repositorio)
5. [La especificación maestra: `PODCAST_MASTER_SPEC.md`](#5-la-especificación-maestra-podcast_master_specmd)
6. [Pipeline 1 — De PDF a guion](#6-pipeline-1--de-pdf-a-guion)
7. [Pipeline 2 — De guion a audio](#7-pipeline-2--de-guion-a-audio)
8. [Pipeline 3 — De audio a videopodcast](#8-pipeline-3--de-audio-a-videopodcast)
9. [Validación, estado y normalización](#9-validación-estado-y-normalización)
10. [Observabilidad: `runlog` y eventos JSONL](#10-observabilidad-runlog-y-eventos-jsonl)
11. [La consola de control (cockpit)](#11-la-consola-de-control-cockpit)
12. [Técnicas de I.A. en uso](#12-técnicas-de-ia-en-uso)
13. [Convenciones del sistema](#13-convenciones-del-sistema)
14. [Workflow de desarrollo](#14-workflow-de-desarrollo)
15. [Operaciones diarias](#15-operaciones-diarias)
16. [Costes y consumo](#16-costes-y-consumo)
17. [Roadmap y deuda técnica](#17-roadmap-y-deuda-técnica)

---

## 1. Visión general

**MaquinarIA Pesada** es un podcast/videopodcast sobre Inteligencia Artificial dirigido a directivos y profesionales del Máster en I.A. Su rasgo distintivo: **el 100% de la producción está automatizada por I.A.** — guion, voces, mezcla audio, vídeo, subtítulos, miniaturas y metadata.

### Concepto editorial

- **Dos presentadores virtuales**: María (voz cálida, didáctica, datos y contexto, color **amarillo CAT** `#F5C400`) e Iago (voz directa, técnica, escepticismo, color **azul eléctrico** `#4DB8FF`). Negro base `#0D0D0D`, rojo de alerta `#CC2200`.
- **15 módulos temáticos** de un máster de I.A.: M0 (introducción estratégica) a M14 (estrategia empresarial), pasando por fundamentos, ML clásico, deep learning, NLP/LLMs, prompt engineering, RAG, LLMOps, infraestructura, agentes, automatización, seguridad y gobernanza.
- **Cada módulo se subdivide en temas** (M3_T1 ... M3_T9) además de un episodio "maestro" del módulo (`M3_T_Deep_Learning`).
- **Duración objetivo del episodio**: 14–17 min; mínimo 1900 palabras de guion.
- **Reglas de estilo fijas**: I.A. siempre con puntos en el texto hablado, anglicismos traducidos, siglas deletreadas, alternancia de speakers (paridad: M0/M2/M4… abre María; M1/M3… abre Iago), frase de cierre canónica.

### El sistema en una línea

> **PDF temático ➜ guion etiquetado ➜ audio sintetizado ➜ vídeo compuesto ➜ subido**, con un dashboard web para observar el progreso y generar los comandos que ejecuta Codex.

### Quién es quién en la cadena

| Rol | Quién | Para qué |
|---|---|---|
| Director / arquitecto | **Claude (humano + Claude Code)** | Diseña pipelines, afina prompts, escribe los scripts |
| Ejecutor del lote | **Codex CLI (OpenAI)** | Lanza los scripts en cadena cuando hay que generar varios episodios |
| Operador humano | El usuario | Aporta los PDFs fuente, supervisa, corrige |

---

## 2. Arquitectura del sistema

```
┌──────────────────────────────────────────────────────────────────────┐
│                          ENTRADA HUMANA                              │
│  PDFs académicos por módulo y por tema (uno o varios por episodio)   │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────┐   ┌────────────────────────┐
│  PIPELINE 1: GUION     │   │  generar_guion.py      │
│  PDF → guion .txt      │◄──│  OpenAI gpt-4.1        │
│  • extracción texto    │   │  + gpt-4.1-mini review │
│  • prompt + spec       │   │  + pdfplumber          │
│  • generación + revisión│  │  + podcast_spec        │
└────────────────────────┘   └────────────────────────┘
                                  │
                                  ▼  Guiones/M3_T_Deep_Learning.txt
┌────────────────────────┐   ┌────────────────────────┐
│  PIPELINE 2: AUDIO     │   │  generar_episodio_v2.py│
│  guion → mp3 final     │◄──│  ElevenLabs eleven_v3  │
│  • bloques por speaker │   │  + pydub + ffmpeg      │
│  • síntesis TTS        │   │  + música de fondo     │
│  • montaje + master    │   │  + sintonía intro      │
└────────────────────────┘   └────────────────────────┘
                                  │
                                  ▼  episodios/M3_E_Deep_Learning.mp3
┌────────────────────────┐   ┌──────────────────────────────────┐
│  PIPELINE 3: VIDEO     │   │  maquinaria_pesada_pipeline/     │
│  mp3 → mp4 + .srt      │◄──│  Whisper → Claude → Pillow → ffmpeg │
│  • transcripción       │   │  + Luma (image-to-video)         │
│  • timeline visual     │   │                                  │
│  • overlays + subs     │   │                                  │
│  • composición final   │   │                                  │
└────────────────────────┘   └──────────────────────────────────┘
                                  │
                                  ▼  Videos/M3_V_Deep_Learning.mp4

┌──────────────────────────────────────────────────────────────────────┐
│                       VALIDACIÓN Y ESTADO                            │
│  validar_episodio.py · estado_proyecto.py · podcast_spec.py          │
│  normalizar_guiones.py (formato B legacy → A)                         │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                    OBSERVABILIDAD (transversal)                      │
│  runlog.py emite JSONL estructurado en episodios/{ep}_events.jsonl   │
│  Cada generador escribe eventos: ts, phase, level, category, kwargs  │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                       COCKPIT WEB (Streamlit)                        │
│  cockpit/ — 5 páginas: Estado · Conectores · Prompt · Fuentes · Logs │
│  Sidebar persistente "Producción en vivo" (psutil + recent files)    │
│  Modal de validaciones por celda                                     │
│  No ejecuta scripts. Genera prompts CLI para Codex.                  │
└──────────────────────────────────────────────────────────────────────┘
```

### Flujo end-to-end por episodio

1. **Operador** coloca el PDF temático en `PDFs/` (p.ej. `PDFs/M3_T1_redes_neuronales_conv.pdf`).
2. **`producir_episodio.py`** se invoca (o `generar_guion.py` + `generar_episodio_v2.py` por separado) — desde la cockpit se obtiene el comando listo para Codex.
3. **`generar_guion.py`**: extrae texto del PDF (pdfplumber), construye un prompt que incluye `PODCAST_MASTER_SPEC.md` + el PDF maestro del módulo + parámetros (duración, objetivo, estudios), llama a `gpt-4.1` para borrador, llama a `gpt-4.1-mini` para revisión, valida con `podcast_spec.validate_script_text()`, escribe `Guiones/{ep}_guion_etiquetas_v{N}.txt`.
4. **`generar_episodio_v2.py`**: parsea el guion en bloques (cada bloque es una intervención de un speaker con etiqueta TTS), pide a ElevenLabs `eleven_v3` que sintetice cada bloque con la voz correspondiente (IAGO/MARIA), guarda mp3 por bloque en `episodios/temp/`, monta con pydub aplicando ffmpeg post-speed, mezcla música de fondo y sintonía, escribe `episodios/{ep}_E_{tema}.mp3` y `{ep}_produccion.log` + `{ep}_events.jsonl`.
5. **`maquinaria_pesada_pipeline/run_pipeline.py`**: pasa el mp3 por Whisper para timestamps a nivel de palabra, llama a Claude Sonnet para que diseñe el timeline visual a partir del guion, renderiza overlays con Pillow (tarjetas de speaker, stat boxes, stickers, subtítulos), compone el mp4 final con ffmpeg, opcionalmente genera escenas de fondo con Luma Dream Machine (image-to-video desde 4 PNGs ancla: María, Yago, estudio, plano amplio).
6. **`validar_episodio.py`** corre 6 checks (mp3 existe y > 1 MB, duración 8–60 min, log presente con "Producción completada", sin ERROR/Exception, conteo de bloques cuadra, audio reproducible).
7. **`estado_proyecto.py`** y la **cockpit** muestran qué módulos están completos y qué falta.

---

## 3. Tecnologías, cuentas y APIs

### Lenguaje

- **Python 3.9+** (recomendado **3.12** — el sistema está testeado ahí). Sin TypeScript, sin Node, sin frontend SPA.

### APIs externas (cuentas necesarias)

| Servicio | Modelos en uso | Variable `.env` | Para qué |
|---|---|---|---|
| **OpenAI** | `gpt-4.1`, `gpt-4.1-mini`, `gpt-4o`, `gpt-4o-mini`, `whisper-1` | `OPENAI_API_KEY` | Generación de guiones, revisión, transcripción Whisper, debate dual |
| **ElevenLabs** | `eleven_v3` (multilingual TTS) | `ELEVENLABS_API_KEY` | Síntesis de voces María e Iago |
| **Anthropic Claude** | `claude-sonnet-4-7` (o variante actual) | `ANTHROPIC_API_KEY` | Director visual del pipeline de vídeo (timeline + concept extraction) |
| **Luma Dream Machine** | Image-to-video | `LUMA_API_KEY` | Escenas de B-roll generadas a partir de PNGs ancla |
| **OpenAI Codex CLI** | (usa `OPENAI_API_KEY`) | (mismo) | Ejecución desatendida del pipeline en lote |

### Repositorio

- **GitHub**: [`bakero/maquinaria-pesada`](https://github.com/bakero/maquinaria-pesada)
- **Rama por defecto**: `master` (= origin/master)
- **Ramas activas** (cada una en su propio worktree):
  - `master` — trunk consolidado
  - `feature/genepisodios` — sesión de generadores audio (guion + síntesis)
  - `feature/videopodcast` — sesión del pipeline de vídeo
  - `APPContenidos` — sesión de la cockpit (este documento vive aquí)
  - `feature/generadores` — pendiente de borrar (duplicada con genepisodios)

### Servidores y despliegue

- **Sin servidores remotos**. El sistema corre en local: una máquina ASUS Zenbook S 14 UX5406SA (Intel Lunar Lake), Windows 11, Python 3.12 system-installed.
- **Cockpit**: Streamlit en `localhost:8501`. Un solo usuario. No hay auth, no hay DNS, no hay TLS — uso exclusivamente personal.
- **Codex CLI**: corre local en otra terminal, llama a OpenAI por la red.

### Librerías Python clave

| Categoría | Librería | Versión mín. | Para qué |
|---|---|---|---|
| LLM clients | `openai`, `anthropic` | latest | OpenAI/Claude API |
| TTS | `elevenlabs` | latest | ElevenLabs SDK |
| PDF | `pdfplumber` | ≥ 0.11 | Extracción de texto |
| Audio | `pydub` | ≥ 0.25 | Mezcla, normalización, montaje |
| Audio (sistema) | `ffmpeg` (CLI) | latest | Encoding, post-speed, video |
| Imagen | `Pillow` (PIL) | latest | Overlays, tarjetas, miniaturas |
| Transcripción | `openai-whisper` | latest | Timestamps por palabra |
| Web UI | `streamlit` | ≥ 1.32 | Cockpit |
| Auto-refresh | `streamlit-autorefresh` | ≥ 1.0 | Sidebar 5s |
| Procesos | `psutil` | ≥ 5.9 | Detección de scripts en ejecución |
| Env vars | `python-dotenv` | ≥ 1.0 | Carga `.env` |

### Herramientas externas (CLI)

- **`ffmpeg`** (instalado vía `winget install Gyan.FFmpeg`)
- **`codex`** (OpenAI Codex CLI)
- **`claude`** (Anthropic Claude Code CLI — donde corre todo este desarrollo)
- **`git`** + **GitHub Desktop / VS Code Git**

### Hardware

- ASUS Zenbook S 14 UX5406SA, Intel Lunar Lake (NPU para inferencia local cuando aplique).
- Disco con espacio holgado para audio/vídeo (los `.mp4` finales pueden pesar 200-400 MB).

---

## 4. Estructura del repositorio

```
maquinaria_pesada/
├── BIBLIA.md                          ← este documento
├── README.md                          ← visión general (corto)
├── PODCAST_MASTER_SPEC.md             ← FUENTE ÚNICA DE VERDAD
├── INSTRUCCIONES.txt                  ← comandos maestros
├── VOICE_CONFIG_REFERENCE.md          ← resumen voces (legacy, ver SPEC)
├── WORKFLOW_PAIR_PROGRAMMING.md       ← workflow Claude + Codex
├── .env.example                       ← plantilla de keys (sin valores)
├── .gitignore                         ← cubre .env, *.mp3, *.mp4, output/, etc.
│
├── generar_guion.py                   ← Pipeline 1 (PDF → guion)
├── generar_episodio_v2.py             ← Pipeline 2 (guion → audio)
├── producir_episodio.py               ← orquestador 1+2
├── validar_episodio.py                ← 6 checks de integridad
├── estado_proyecto.py                 ← inventario M0-M14
├── lanzar_produccion.py               ← batch runner
├── podcast_spec.py                    ← parser/validador de la spec y guiones
├── normalizar_guiones.py              ← migración formato B → A
├── dual_debate.py                     ← debate Claude+ChatGPT inline
├── dual_debate_maquinaria.py          ← variante con foco MaquinarIA
├── runlog.py                          ← logger estructurado JSONL (transversal)
│
├── PDFs/                              ← 142 archivos fuente
│   ├── M{N}_T{n}_{slug}.pdf           ← un PDF por tema
│   └── M{N}_T_{tema}.pdf              ← maestro del módulo
│
├── Guiones/                           ← guiones .txt etiquetados
│   └── M{N}_T_{tema}.txt
│
├── episodios/                         ← outputs audio + logs + eventos
│   ├── M{N}_E_{tema}.mp3              ← audio final
│   ├── M{N}_produccion.log            ← log libre (texto)
│   ├── {ep}_events.jsonl              ← eventos estructurados (runlog)
│   └── temp/                          ← bloques intermedios por speaker
│
├── Videos/                            ← outputs vídeo + assets
│   ├── M{N}_V_{tema}.mp4              ← videopodcast final
│   └── escenas_biblioteca/
│       ├── refs/                      ← anclajes Luma
│       │   ├── Maria.png
│       │   ├── Yago.png
│       │   ├── studio.png
│       │   └── establishing.png
│       └── _concepts_index.json
│
├── Música/                            ← bases musicales
│   ├── base podcast.mp3
│   └── Sintonia Maquinaria pesada.mp3
│
├── intro/                             ← intro de videopodcast
├── Logos/                             ← logos para overlays
│   └── logo sin fondo.png             ← default
├── RRSS/                              ← assets para redes sociales
│   └── LinkedIn/
├── _archivo/                          ← código legacy
│   └── generar_episodio.py            ← v1, archivada
│
├── maquinaria_pesada_pipeline/        ← Pipeline 3 (vídeo)
│   ├── run_pipeline.py                ← entrypoint orquestador
│   ├── setup_project.py               ← configuración interactiva
│   ├── generate_placeholders.py
│   ├── pipeline/
│   │   ├── asset_validator.py
│   │   ├── transcriber.py             ← Whisper word-level
│   │   ├── content_extractor.py       ← PDF + guion → stats
│   │   ├── concept_extractor.py       ← Claude → JSON conceptos
│   │   ├── scene_builder.py           ← Claude → scene_timeline.json
│   │   ├── scene_library.py           ← cache de escenas
│   │   ├── overlay_renderer.py        ← Pillow → PNGs por keyframe
│   │   ├── subtitle_generator.py      ← .srt + keywords destacadas
│   │   ├── video_compositor.py        ← ffmpeg → mp4 final
│   │   ├── metadata_generator.py      ← YouTube metadata + thumbnail
│   │   ├── audio_analyzer.py          ← detección silencios, hook
│   │   ├── production_log_parser.py   ← lee {ep}_events.jsonl
│   │   ├── luma_generator.py          ← image-to-video con Luma
│   │   ├── brand.py                   ← constantes color/estilo
│   │   └── logger.py
│   ├── templates/
│   │   ├── overlay_types.py           ← speaker cards, stat boxes
│   │   ├── sticker_manager.py         ← stickers + emoji
│   │   ├── background_generators.py   ← gradientes, rejillas
│   │   └── system_prompt_timeline.txt ← prompt Claude director visual
│   └── tools/
│       ├── analyze_concepts.py
│       └── generate_studio_clips.py
│
└── cockpit/                           ← consola de control web
    ├── app.py                         ← entrypoint streamlit run
    ├── ui.py                          ← render_status_sidebar()
    ├── BIBLIA.md (este doc se referencia)
    ├── PLAN.md                        ← plan original aprobado
    ├── SESSION_CONTEXT.md             ← decisiones, slots, pendientes
    ├── core/
    │   ├── paths.py                   ← REPO_ROOT env var, rutas oficiales
    │   ├── state.py                   ← scan() inventario M0-M14
    │   ├── prompt_builder.py          ← form values → CLI con shlex.quote
    │   ├── monitor.py                 ← psutil scan + log activo + recent files
    │   └── log_parser.py              ← JSONL > regex, CategorySummary
    ├── connectors/
    │   ├── base.py                    ← Connector / Service / Pipeline / Source
    │   ├── __init__.py                ← REGISTRY + auto-loader
    │   ├── services/   {openai, elevenlabs, ffmpeg, codex}.py
    │   ├── pipelines/  {generar_guion, generar_episodio, validar_episodio, estado_proyecto}.py
    │   └── sources/    {pdf, guion, audio, video, log}.py
    └── pages/
        ├── 1_📊_Estado.py
        ├── 2_🔌_Conectores.py
        ├── 3_📝_Generar_Prompt.py
        ├── 4_📚_Fuentes.py
        └── 5_📜_Logs.py
```

### Tamaño actual

- **244 archivos tracked** (post-consolidación a master).
- **~142 PDFs**, ~14 guiones, audio/vídeo dinámicos.
- Archivos pesados (`*.onnx`, `*.bin`, `*.mp3`, `*.mp4`) están **gitignored** y nunca se suben.

---

## 5. La especificación maestra: `PODCAST_MASTER_SPEC.md`

Este archivo es la **única fuente de verdad** para todo el sistema. Contiene un bloque JSON embebido (entre marcadores HTML) que `podcast_spec.load_master_spec()` extrae y usa.

### Qué define exactamente

#### Estructura obligatoria del episodio (11 secciones)

```
# HOOK                  → cierre fijo: "Esto es MaquinarIA Pesada. Arrancamos."
# INTRO_SONIDO          → 8-10 s de máquinas arrancando
# SALUDO_Y_PRESENTACION → incluye advertencia de generación I.A.
# BLOQUE_1, BLOQUE_2, BLOQUE_3, BLOQUE_4   (mín 4, máx 6)
# INSERCION_1, _2, _3   (opcionales: noticia, caso de uso, anecdota)
# CIERRE_CONCEPTOS      → abre con "No te puedes ir de este capítulo sin..."
# CIERRE_FINAL          → frase fija canónica
# VERIFICACIONES        → bloque generado al final por el validador
```

#### Métricas de duración

- Objetivo: **15 min**
- Rango aceptable: **14–17 min** (audio final)
- Mínimo audio: 12.5 min · Máximo: 18.5 min
- Mínimo guion: **1900 palabras** (sin contar headers ni nombres de speaker)

#### Voces (ElevenLabs `eleven_v3`)

| Speaker | `voice_id` | stability | style | speed | post_speed_multiplier |
|---|---|---|---|---|---|
| **IAGO** | `CdAqYBLnsNjmTqYgD5Ha` | 0.65 | 0.0 | 1.20 | 1.10 |
| **MARIA** | `gD1IexrzCvsXPHUuT0s3` | 0.68 | 0.0 | 1.20 | 1.10 |

Reglas: en el texto hablado siempre se escribe **"Yago"**, nunca "Iago" (la **i** seguida de **a** distorsiona la pronunciación). Episodios impares abre Iago, pares María.

#### Etiquetas TTS soportadas

Una etiqueta al inicio de cada intervención. Lista cerrada: `[didáctico] [explicativo] [directo] [serio] [firme] [contundente] [grave] [tenso] [conversacional] [reflexivo] [reflexiva] [curioso] [irónico] [escéptico] [natural] [pausado] [cálido] [cálida] [claro] [clara] [analítica]`.

(Set legacy más reducido sigue documentado en `VOICE_CONFIG_REFERENCE.md`: `[directo] [conversacional] [ironico-suave] [claro] [cercano] [didactico-suave]`. La spec maestra es la que manda).

#### Reglas de diálogo

- Intervención de desarrollo: 2-6 frases, ~32 palabras objetivo (expandible si el concepto lo requiere).
- Intervención de reacción: máx 12 palabras.
- No acumular > 2 tecnicismos sin frase de aterrizaje en castellano.
- Máx 3 intervenciones consecutivas del mismo speaker.
- Alternar intercambios cortos cada 4-5 intervenciones largas.

#### Reglas de léxico

- **I.A. siempre con puntos** ("la I.A. está cambiando…"), nunca "IA" hablada.
- **Siglas deletreadas** en español + nombre completo: "ele ele emes, grandes modelos de lenguaje".
- **Anglicismos siempre traducidos** en su primera aparición: "machine learning, o aprendizaje automático".

#### Frases fijas

| Sección | Texto exacto |
|---|---|
| Hook (cierre) | *"Esto es MaquinarIA Pesada. Arrancamos."* |
| Cierre conceptos (apertura) | *"No te puedes ir de este capítulo sin haber entendido estos conceptos."* |
| Cierre final | *"Y hasta aquí ha llegado nuestro episodio de MaquinarIA Pesada. Síguenos para nuevos capítulos donde la I.A. crea contenido sobre I.A."* |

#### Modelos OpenAI declarados

```json
{
  "guion":   "gpt-4.1",       "max_output_tokens": 7000,
  "review":  "gpt-4.1-mini",  "max_review_tokens": 2200,
  "concepts":"gpt-4.1-mini",  "max_concept_tokens": 900,
  "temperature": 0.7
}
```

#### Directorios oficiales

| Asset | Ruta |
|---|---|
| PDFs fuente | `PDFs/` |
| Guiones | `Guiones/` |
| Audio output | `episodios/` |
| Audio temp | `episodios/temp/` |
| Videos | `Videos/` |
| Música | `Música/` |
| Intro | `intro/` |
| Logos | `Logos/` (default `Logos/logo sin fondo.png`) |

### Cómo se usa la spec en código

```python
from podcast_spec import load_master_spec, validate_script_text

spec = load_master_spec("PODCAST_MASTER_SPEC.md")
ok, errors = validate_script_text(open(guion_path).read(), spec)
```

Cualquier script (incluida la cockpit) puede leerla y reusar las reglas. **Modificar la spec implica recompilar mentalmente todos los pipelines** — por eso vive en raíz y se referencia siempre por nombre.

---

## 6. Pipeline 1 — De PDF a guion

### `generar_guion.py` (~51 KB)

**Misión**: producir un guion `.txt` etiquetado, validado por la spec, listo para sintetizar.

#### Flags CLI

| Flag | Tipo | Para qué |
|---|---|---|
| `--ep` | str | Código episodio (`M3_T_ML` o `EP001`) |
| `--pdf` | path | PDF temático fuente (obligatorio) |
| `--master-pdf` | path | PDF índice del módulo |
| `--modulo` | `M0..M14` | Módulo de pertenencia |
| `--tema` | str | Título del episodio |
| `--objetivo` | str | Aprendizaje esperado |
| `--duracion-min` | int | Minutos objetivo (default 15) |
| `--contexto-file` | path | `.txt`/`.md` con contexto extra |
| `--estudios` | str | Estudios/citas de investigación |
| `--aplicacion-empresarial` | str | Caso de uso dominante |
| `--modelo` | str | OpenAI model (default `gpt-4.1`) |
| `--modelo-review` | str | Review model (default `gpt-4.1-mini`) |
| `--token-budget` | int | Tope de tokens del guion |
| `--max-attempts` | int | Reintentos si la validación falla |

#### Inputs / Outputs

- **Lee**: PDF temático (`pdfplumber`), PDF maestro, `PODCAST_MASTER_SPEC.md`, `.env`.
- **Escribe**: `Guiones/{ep}_guion_etiquetas_v{N}.txt`. Si la validación falla, vuelve a llamar al modelo (max 3 intentos por defecto).

#### Cómo funciona internamente

1. **Extracción**: `pdfplumber` saca el texto de los PDFs (temático + maestro). Se concatena con metadata por página.
2. **Construcción del prompt**: incluye la spec maestra completa, la estructura obligatoria, las reglas de léxico, las etiquetas TTS, el speaker que abre (paridad), el tema, el objetivo, los estudios y la aplicación empresarial — junto con extractos del PDF.
3. **Llamada a `gpt-4.1`** con `temperature=0.7` y `max_output_tokens=7000`.
4. **Revisión** con `gpt-4.1-mini`: pasa el borrador + las reglas y devuelve correcciones (es un segundo prompt aparte).
5. **Validación local** con `podcast_spec.validate_script_text()`: comprueba secciones obligatorias, conteo de palabras, frases fijas, etiquetas dentro del set permitido, paridad de speakers.
6. **Reparación** (`repair_generated_script`): si la validación falla, se inyecta el error al modelo y se le pide arreglo. Hasta `--max-attempts` veces.
7. **Persistencia**: el archivo se guarda con sufijo `_v{N}` para mantener historial.

---

## 7. Pipeline 2 — De guion a audio

### `generar_episodio_v2.py` (~31 KB)

**Misión**: convertir el guion en un mp3 final con voces, música de fondo, sintonía y normalización de volumen.

#### Flags CLI

| Flag | Tipo | Para qué |
|---|---|---|
| `--guion` | path | Ruta al guion `.txt` (obligatorio) |
| `--ep` | str | Código episodio (obligatorio) |
| `--spec` | path | Spec maestra (default `PODCAST_MASTER_SPEC.md`) |
| `--solo-bloque` | int | Regenerar solo el bloque N |
| `--solo-speaker` | `IAGO`/`MARIA` | Regenerar solo bloques de un speaker |
| `--solo-montar` | bool | Saltar síntesis y solo montar |
| `--generar-musica` | bool | Música procedural via Luma (experimental) |
| `--musica-bg` | path | Música de fondo (default `Música/base podcast.mp3`) |
| `--sintonia` | path | Sintonía intro (default `Música/Sintonia Maquinaria pesada.mp3`) |

#### Pipeline interno

1. **Parseo del guion** (`parsear_guion`): trocea por bloques etiquetados con speaker + tag TTS.
2. **Síntesis bloque a bloque** (`generar_bloque`): por cada bloque, llama a ElevenLabs `eleven_v3` con la voz correspondiente y los parámetros de la spec (stability, style, speed). Guarda `episodios/temp/{ep}_NNN_{SPEAKER}.mp3`.
3. **Post-speed con ffmpeg**: cada bloque se acelera con `ffmpeg -filter:a "atempo=1.10"` (`post_speed_multiplier`).
4. **Montaje** (`montar_audio`): pydub concatena bloques, intercala sintonía al inicio, mezcla música de fondo a -22 dB durante el cuerpo, fade-in/fade-out.
5. **Normalización**: `pydub.effects.normalize` ajusta el peak final.
6. **Verificación**: `verify_audio_output` comprueba que el mp3 final sea reproducible y dure dentro del rango.
7. **Eventos JSONL**: a través de `runlog.py`, escribe en `episodios/{ep}_events.jsonl` cada bloque sintetizado con `block`, `speaker`, `ms`, `credits` (créditos ElevenLabs consumidos), errores.
8. **Snapshot de subscription** (`get_subscription_snapshot`): consulta a ElevenLabs los créditos restantes al inicio y al final, lo registra.

#### Outputs

- `episodios/{ep}_E_{tema}.mp3` (audio final)
- `episodios/{ep}_produccion.log` (log libre, retro-compatible)
- `episodios/{ep}_events.jsonl` (eventos estructurados — preferido)
- `episodios/temp/*.mp3` (bloques intermedios — gitignored)

---

## 8. Pipeline 3 — De audio a videopodcast

### `maquinaria_pesada_pipeline/run_pipeline.py`

**Misión**: a partir del mp3 final + el guion, construir un mp4 1080p con overlays, subtítulos, intro, miniatura y metadata para YouTube.

#### Flags

| Flag | Para qué |
|---|---|
| `--preview` | Render del primer minuto a 720p (validación rápida) |
| `--from-step N` | Reanudar desde el paso N |
| `--force` | Ignorar caches |
| `--no-llm` | Heurístico sin Anthropic (modo offline) |

#### Pasos (00–08)

| # | Módulo | Qué hace | Tecnología |
|---|---|---|---|
| 0 | `asset_validator.py` | Verifica que existan: mp3, guion, logos, intro, música, refs Luma | Pillow |
| 1 | `transcriber.py` | Whisper sobre el mp3 → `transcription_raw.json` con timestamps por palabra | OpenAI Whisper |
| 2 | `content_extractor.py` | Extrae stats del guion + texto del PDF | pdfplumber + OpenAI |
| 3 | `concept_extractor.py` | Pide a Claude un JSON con conceptos clave del episodio (para tarjetas) | Anthropic Claude |
| 4 | `scene_builder.py` | Genera `scene_timeline.json`: qué overlay/escena va en cada timestamp | Anthropic Claude (director visual) |
| 5 | `overlay_renderer.py` | Renderiza PNGs de overlay por keyframe (speaker cards, stat boxes, banners, stickers) | Pillow |
| 6 | `subtitle_generator.py` | Genera `.srt` con keywords destacadas, alineado por palabra | (puro Python) |
| 7 | `video_compositor.py` | Compone el mp4 final: intro + cuerpo + overlays + subs + fade | ffmpeg |
| 8 | `metadata_generator.py` | YouTube metadata: título, descripción, capítulos, miniatura | Pillow + ffmpeg |

#### Módulos auxiliares

- **`audio_analyzer.py`**: detecta silencios, identifica el hook y el inicio del primer bloque (por si hay que ajustar el timing del overlay).
- **`production_log_parser.py`**: lee `episodios/{ep}_events.jsonl` (output de `runlog`) para extraer metadatos del run de audio.
- **`scene_library.py`**: cache de escenas pre-renderizadas para no re-generar lo mismo entre episodios.
- **`luma_generator.py`**: image-to-video con Luma Dream Machine usando como `frame0` los 4 PNGs ancla (`Maria.png`, `Yago.png`, `studio.png`, `establishing.png`). Esto da consistencia visual entre tomas.

#### `templates/`

- `overlay_types.py`: define tipos de overlay (speaker tag, stat card, warning banner, concept card).
- `sticker_manager.py`: stickers/iconografía recurrente.
- `background_generators.py`: fondos procedurales (gradientes, rejillas técnicas).
- `system_prompt_timeline.txt`: el prompt completo que se envía a Claude para que actúe de director visual.

#### `tools/`

- `analyze_concepts.py`: analiza palabras clave en la transcripción.
- `generate_studio_clips.py`: extrae clips de audio por concepto para reels/RRSS.

---

## 9. Validación, estado y normalización

### `podcast_spec.py` (el cerebro de la spec)

Parser y validador. Funciones públicas que reusan los demás scripts y la cockpit:

```python
load_master_spec(path)        # → dict (JSON entre markers HTML)
parse_script_blocks(text)     # → lista de bloques con (speaker, tag, text)
validate_script_text(text, spec) → (ok: bool, errors: list[str])
build_script_stats(text)      # → dict con conteos
extract_theme_concepts(...)   # → conceptos con OpenAI
count_words(text)             # → palabras útiles (regex Unicode + acentos)
normalize_speaker(name)       # → "IAGO" o "MARIA"
opening_speaker(ep_number)    # → IAGO (impar) | MARIA (par)
```

### `validar_episodio.py`

6 checks por episodio:

1. MP3 existe y > 1 MB.
2. Duración entre 8 y 60 min (lectura con pydub).
3. `episodios/{ep}_produccion.log` existe y contiene "Producción completada".
4. Sin líneas con `ERROR`, `FAILED`, `Exception`, `Traceback` críticas.
5. Conteo de bloques del guion = conteo de bloques sintetizados en el log.
6. Audio se carga sin lanzar excepción (verificación de integridad).

Salida: tabla colorida + estimación de créditos ElevenLabs gastados.

### `estado_proyecto.py`

Inventario por módulo M0-M14: qué hay, qué falta. Modos:

- por defecto: tabla resumen.
- `--codex`: imprime los comandos pendientes para que Codex los ejecute (pares `generar_guion` / `generar_episodio_v2` que faltan).
- `--pendiente`: solo módulos incompletos.
- `--assets`: lista archivos por módulo (rutas absolutas).

Función `scan()` y `print_estado_resumen()` se reusan en la cockpit.

### `lanzar_produccion.py`

Batch runner: para cada guion en `Guiones/` que no tenga audio en `episodios/`, ejecuta `generar_episodio_v2.py`. Captura stdout+stderr en `episodios/{ep}_cmd.log`. Soporta `--ep` (uno solo) y `--dry-run`.

### `normalizar_guiones.py`

Migra guiones del formato B (legado, generado por una versión antigua de Codex sin secciones obligatorias) al formato A (validado). Inserta secciones que falten, reordena, fija las frases de cierre. Soporta `--file` y `--dry-run`.

---

## 10. Observabilidad: `runlog` y eventos JSONL

### El problema

Los scripts de pipeline históricamente escribían un `.log` libre de texto. La cockpit lo parseaba con regex (`ERROR`, `WARN`, palabras clave). **Frágil**: cambias el formato de una línea y la cockpit deja de detectar nada.

### La solución: `runlog.py`

Un módulo en raíz (sin dependencias externas) que cualquier generador importa:

```python
from runlog import RunLogger

with RunLogger(episode="M3_E_ML", module="M3", script="generar_episodio_v2.py") as log:
    log.event("extract_pdf", category="pdf", path="...", pages=42)
    log.event("synth_block", category="audio", block=12, speaker="IAGO",
              ms=312, credits=1024)
    log.warn("retry", category="audio", block=15, attempt=2, reason="503")
    try:
        ...
    except Exception as e:
        log.error("synth_block", category="audio", block=15, exc=str(e))
        raise
```

### Formato de salida: JSONL append-only

Archivo: `episodios/{episode}_events.jsonl`

```jsonl
{"ts":"2026-05-08T14:23:01Z","episode":"M3_E_ML","module":"M3","script":"generar_episodio_v2.py","pid":4242,"phase":"start","level":"info","category":"system","elapsed_s":0}
{"ts":"2026-05-08T14:23:02Z",..."phase":"synth_block","category":"audio","block":1,"speaker":"IAGO","ms":305,"credits":1024}
{"ts":"2026-05-08T14:23:09Z",..."phase":"synth_block","category":"audio","block":2,"speaker":"MARIA","ms":287,"credits":1011}
...
{"ts":"2026-05-08T14:38:14Z",..."phase":"end","category":"system","status":"ok","elapsed_s":913.21}
```

### Campos automáticos

`ts`, `episode`, `module`, `script`, `pid`, `phase`, `level` (`info`/`warn`/`error`), `category` (`pdf`/`guion`/`audio`/`video`/`log`/`system`).

Cualquier `**kwargs` extra que pases (`block`, `speaker`, `ms`, `credits`, `exc`, etc.) se serializa tal cual.

### Cómo lo consume la cockpit

`cockpit/core/log_parser.py` define una **cadena de prioridad**:

1. Busca `episodios/*_events.jsonl` para el módulo (mtime más reciente). Si existe → fuente `jsonl`, parser estructurado.
2. Si no, busca `episodios/*.log` y aplica regex (fallback). Fuente `text`.
3. Si tampoco, devuelve `CategorySummary` vacío. Fuente `none`.

La modal de validaciones muestra un badge `📦 estructurado (runlog)` o `📄 texto (regex)` según la fuente, y un expander con conteos por fase cuando hay JSONL.

### Estado actual de migración

- ✅ `runlog.py` integrado en la rama `APPContenidos` y disponible para todos los generadores (al estar en raíz, basta `from runlog import RunLogger`).
- ⏳ Los generadores (`generar_guion.py`, `generar_episodio_v2.py`, `validar_episodio.py`) **aún escriben texto libre**. La migración se hace en la sesión `feature/genepisodios` cuando el operador esté listo, sin urgencia: el fallback regex sigue funcionando.

---

## 11. La consola de control (cockpit)

### Qué es

Una app web local con **Streamlit** que centraliza:
- el estado de producción por módulo,
- la consulta de fuentes (PDFs, guiones, audio, vídeo, logs),
- la generación de comandos CLI listos para Codex,
- la configuración de servicios externos (conectores),
- la observación de procesos en marcha.

**Lo que no hace**: ejecutar el pipeline. Codex ejecuta. La cockpit observa y prepara.

### Cómo arrancarla

```powershell
cd C:\Users\Asus\maquinaria_pesada\.claude\worktrees\APPContenidos
pip install -r requirements-cockpit.txt
streamlit run cockpit/app.py
```

Abre `http://localhost:8501`.

Variable de entorno opcional: `REPO_ROOT` (default `C:\Users\Asus\maquinaria_pesada`) para apuntar a otro checkout.

### Las 5 páginas

| Página | Qué muestra |
|---|---|
| **📊 Estado** | Tabla M0-M14 con iconos clicables ✅/❌ por categoría (PDF, Guion, Audio, Vídeo, Log). Click → modal con resumen de validaciones de la última ejecución (errores, warnings, conteo por fase). |
| **🔌 Conectores** | Grid de tarjetas: 4 servicios (OpenAI, ElevenLabs, ffmpeg, Codex), 4 pipelines (los scripts), 5 fuentes (PDF, Guion, Audio, Vídeo, Log). Cada tarjeta muestra status (credenciales OK?, binario en PATH?) y configuración. |
| **📝 Generar Prompt** | Selector de pipeline → formulario con todos los flags → vista previa del comando CLI (con `shlex.quote` para espacios) listo para copiar a Codex. |
| **📚 Fuentes** | Explorador de contenido: PDF (visor pdfplumber), guion (textarea + validación con `podcast_spec`), audio (`st.audio`), vídeo (`st.video`), log (tail viewer). |
| **📜 Logs** | Listado de `episodios/*.log` con tail viewer y auto-refresh opcional. |

### Sidebar persistente "🎬 Producción en vivo"

Aparece en **todas** las páginas, refresh cada 5 s:

- Procesos Python detectados con un script del pipeline en su línea de comandos (vía `psutil`): PID, label, tiempo transcurrido, RAM, log activo + tail de últimas 3 líneas.
- "Generándose ahora": ficheros aparecidos en `episodios/`, `output/`, `Videos/` en los últimos 10 minutos (mtime + tamaño + edad).
- Si no hay procesos: estado "Inactivo" + ficheros recientes (60 s).
- Si falta `psutil` o `streamlit-autorefresh`: avisos explícitos.

### El patrón "conector"

Toda la cockpit está construida sobre una jerarquía simple en `cockpit/connectors/`:

```python
class Connector:
    id, category, label, icon, description
    def status() -> Status
    def render_card()
    def render_config()

class ServiceConnector(Connector):  # OpenAI, ElevenLabs, ffmpeg, Codex
    env_keys: tuple[str, ...]

class PipelineConnector(Connector): # generar_guion, etc.
    script: str; fields: list[Field_]
    def build_command(values) -> str

class SourceConnector(Connector):   # PDF, Guion, Audio, Video, Log
    suffixes: tuple[str, ...]
    def list_items() -> list[Path]
    def render_viewer(path)
```

**Auto-registro**: el `__init__.py` de `connectors/` importa todos los submódulos y cada `@register` decora una clase para meterla en `REGISTRY`. **Añadir un conector = un fichero nuevo, cero cambios al código del dashboard**.

### Módulos `core/`

| Módulo | Función |
|---|---|
| `paths.py` | `repo_root()` (env var `REPO_ROOT`), rutas oficiales |
| `state.py` | `scan()` inventario M0-M14, `pendientes()`, regex robusta para evitar `M1 ⊂ M10` |
| `prompt_builder.py` | `build(script, flags, cwd, header)` con `shlex.quote` |
| `monitor.py` | `scan_running()` (psutil), `find_active_log()`, `recent_outputs()`, `tail_lines()` |
| `log_parser.py` | `parse(module, category)` con prioridad JSONL > regex texto |

### Documentación de la cockpit

- `cockpit/SESSION_CONTEXT.md` — decisiones cerradas, slots token-optimizer, pendientes.
- `cockpit/PLAN.md` — plan original aprobado.

---

## 12. Técnicas de I.A. en uso

| Técnica | Dónde | Cómo se aplica |
|---|---|---|
| **Two-stage generation + review** | `generar_guion.py` | Borrador con `gpt-4.1` → revisión con `gpt-4.1-mini`. Reduce errores y abarata (revisión es más corta y con modelo menor). |
| **Self-repair loop** | `generar_guion.py` (`repair_generated_script`) | Si la validación local falla, se inyecta el error al modelo y se le pide arreglo. Hasta `--max-attempts` veces. |
| **Spec-as-prompt** | Todo `generar_guion.py` | La `PODCAST_MASTER_SPEC.md` (con su JSON embebido) se inserta literalmente en el prompt. El modelo aprende reglas duras desde ahí. |
| **RAG-light** (PDF como contexto) | `generar_guion.py`, `content_extractor.py` | Extracción del PDF temático y maestro con `pdfplumber` → se mete el texto completo en el prompt. No hay vector store; el contexto cabe. |
| **Structured JSON output** | `concept_extractor.py`, `scene_builder.py` | Claude devuelve JSON parseable con conceptos / timeline. Validación con jsonschema (light) y reintento. |
| **TTS con control de estilo via etiquetas** | `generar_episodio_v2.py` + `eleven_v3` | Cada bloque empieza con `[didáctico]`, `[serio]`, etc. El modelo modula prosodia. |
| **Word-level alignment** | `transcriber.py` (Whisper) | Subtítulos exactos por palabra y disparo de overlays sincronizado. |
| **Claude as visual director** | `scene_builder.py` | Claude recibe el guion + el JSON de conceptos y devuelve un timeline (`[{start:0, end:8, type:'speaker_card', speaker:'MARIA', emphasis:'concept_X'}, ...]`). Reglas de estilo en `system_prompt_timeline.txt`. |
| **Image-to-video con anclajes** | `luma_generator.py` (Luma Dream Machine) | Para mantener consistencia entre tomas, se usan 4 PNGs como `frame0`: `Maria.png`, `Yago.png`, `studio.png`, `establishing.png`. Luma genera B-roll partiendo de esos anclajes. |
| **Heuristic fallback** | `scene_builder.py` con `--no-llm` | Cuando Anthropic no está disponible, se usa un heurístico: alternancia speaker cards cada N segundos, tarjetas de concepto en los hits del extractor de conceptos. |
| **Dual-model debate** | `dual_debate.py` | Dos LLM (Claude inline + ChatGPT) discuten un problema en rondas, se sintetiza al final. Sirve para diseño/arquitectura, no para producción. |
| **Process-as-signal** | `cockpit/core/monitor.py` | `psutil` detecta scripts del pipeline corriendo. Filesystem mtime indica logs activos y outputs recién creados. Polling pull, sin event bus. |
| **Structured event logging** | `runlog.py` | Eventos JSONL append-only, leíbles en streaming por la cockpit. |

---

## 13. Convenciones del sistema

### Naming de ficheros

| Tipo | Patrón | Ejemplo |
|---|---|---|
| PDF tema | `M{N}_T{n}_{slug}.pdf` | `M3_T2_redes_neuronales_conv.pdf` |
| PDF maestro | `M{N}_T_{tema_largo}.pdf` | `M3_T_Deep_Learning.pdf` |
| Guion | `M{N}_T_{tema}.txt` o `M{N}_T_{tema}_v{N}.txt` | `M3_T_Deep_Learning_v1.txt` |
| Audio final | `M{N}_E_{tema}.mp3` | `M3_E_Deep_Learning.mp3` |
| Log libre | `M{N}_produccion.log` | `M3_produccion.log` |
| Eventos JSONL | `{episode}_events.jsonl` | `M3_E_Deep_Learning_events.jsonl` |
| Vídeo | `M{N}_V_{tema}.mp4` | `M3_V_Deep_Learning.mp4` |

### Convenciones git

- **`master`** = trunk. Nadie commitea aquí directamente; se mergea desde feature branches.
- **`feature/<nombre>`** = trabajo nuevo de una sesión.
- **Una sesión de Claude Code = una rama y un worktree**. Cada worktree vive en `.claude/worktrees/<nombre>/` y está gitignored como path.
- **Tags `safety/*`** se crean antes de operaciones destructivas (consolidación de ramas, fuerza de pushes).

### Convenciones de prompt

- Idioma de respuesta al usuario: **español**.
- Términos técnicos: **inglés** (`prompt`, `worktree`, `subprocess`, `dialog`, `JSONL`).
- Modelos y comandos: **inglés exacto** (`gpt-4.1`, `eleven_v3`, `git worktree add`).

### Convenciones de código

- **Idioma del código**: inglés (variables, funciones, comentarios). Strings de UI en español.
- **Sin frameworks de LLM "todo-en-uno"** (LangChain, LlamaIndex, Haystack). Se llama a las APIs directamente. Más control, menos magia.
- **Sin servidores adicionales** (Redis, Postgres, etc.) salvo necesidad demostrada.
- **Stdlib first**: `runlog.py` no tiene dependencias externas. Cada nueva dependencia debe justificarse.

---

## 14. Workflow de desarrollo

### Pair programming Claude + Codex

| Quién | Para qué |
|---|---|
| **Claude Code** (este entorno) | Diseña pipelines, escribe scripts, refina prompts, revisa especificaciones. Trabajo "por pieza", calidad alta. |
| **Codex CLI** (`codex --approval-mode full-auto`) | Ejecuta el pipeline en lote sin supervisión humana fina. Genera 5 episodios mientras tú ves Netflix. |

Documentado en `WORKFLOW_PAIR_PROGRAMMING.md`. Las tareas que se le pasan a Codex tienen formato fijo (`TAREA / CONTEXTO / OBJETIVO / RESTRICCIONES / ENTREGABLE`).

### Multi-sesión, multi-rama

En cualquier momento se trabajan en paralelo:

- **`feature/genepisodios`** → afinar generadores audio (guion + síntesis).
- **`feature/videopodcast`** → afinar pipeline de vídeo.
- **`APPContenidos`** → la cockpit (esta rama).
- **`master`** → trunk consolidado (no se trabaja aquí).

Cada rama está en su propio worktree (`.claude/worktrees/<nombre>/`) para que las sesiones no se pisen los archivos. Los cambios se mergean a master vía PR (o `git merge --no-ff` local) cuando una pieza está lista.

### Ciclo típico de un cambio

1. Desde la rama de la sesión, hacer cambios y commits granulares.
2. `git push -u origin feature/<nombre>`.
3. Verificar con la cockpit y/o smoke tests.
4. Mergear a master (PR en GitHub o `git merge --no-ff` local).
5. `git push origin master`.
6. Las otras sesiones hacen `git pull --rebase origin master` cuando necesitan.

### Skills y memoria

El asistente Claude usa varias skills configuradas:

- **`token-optimizer`**: antes de cada acción nueva, elicit slots (task_type, scope, reasoning_need, session_state, output_determinism) → recomendación de modelo + modo + comando previo.
- **`feedback_autonomy`**: trabajar de forma autónoma sin pedir confirmación en cada paso (auto-mode).
- Memoria persistente en `C:\Users\Asus\.claude\projects\C--Users-Asus-maquinaria-pesada\memory\` (ver `MEMORY.md` índice, `voice_config.md`, `project_context.md`, `feedback_autonomy.md`).

---

## 15. Operaciones diarias

### Setup inicial (máquina nueva)

```powershell
# 1. Clonar
git clone https://github.com/bakero/maquinaria-pesada.git
cd maquinaria-pesada

# 2. Variables de entorno
Copy-Item .env.example .env
# editar .env con OPENAI_API_KEY, ELEVENLABS_API_KEY, ANTHROPIC_API_KEY, LUMA_API_KEY

# 3. Dependencias
pip install pdfplumber pydub openai elevenlabs anthropic Pillow streamlit psutil python-dotenv
pip install -r requirements-cockpit.txt
winget install Gyan.FFmpeg

# 4. Whisper (opcional, para vídeo)
pip install openai-whisper

# 5. Codex CLI (para ejecución desatendida)
npm install -g @openai/codex

# 6. Cockpit
streamlit run cockpit/app.py
```

### Generar un episodio nuevo (manual)

```powershell
# Desde la sesión feature/genepisodios:
python producir_episodio.py `
    --ep M3_E_Deep_Learning `
    --modulo M3 `
    --tema "Deep Learning" `
    --pdf PDFs/M3_T_Deep_Learning.pdf `
    --master-pdf PDFs/M3_T1_redes_neuronales_conv.pdf `
    --duracion-min 15
```

O desde la cockpit: página **📝 Generar Prompt** → seleccionar `producir_episodio` → rellenar formulario → copiar el comando → pegar en Codex.

### Validar después

```powershell
python validar_episodio.py --ep M3_E_Deep_Learning --guion Guiones/M3_T_Deep_Learning.txt
```

### Ver estado global

```powershell
python estado_proyecto.py --pendiente   # módulos incompletos
python estado_proyecto.py --codex       # comandos pendientes para Codex
```

O directamente la página **📊 Estado** de la cockpit.

### Componer el videopodcast

```powershell
cd maquinaria_pesada_pipeline
python run_pipeline.py --preview      # validación rápida (1er minuto, 720p)
python run_pipeline.py                # render completo 1080p
```

### Troubleshooting frecuente

| Síntoma | Causa probable | Solución |
|---|---|---|
| Cockpit no detecta procesos | `psutil` instalado en otro Python que el de Streamlit | Verificar con `where streamlit` y `where python`; instalar `psutil` en ese entorno |
| Validación falla por palabras | El guion < 1900 palabras | Re-generar con `--max-attempts` mayor, o expandir manualmente |
| ElevenLabs 503 | Rate limit / overload | El script reintenta con backoff. Si persiste, esperar y relanzar con `--solo-bloque N` para no resintetizar todo |
| Audio fuera de rango (>17 min) | Modelo se enrolla | Reducir `--duracion-min`, o pedir a `gpt-4.1-mini` review más estricto |
| Whisper lento | Modelo `large-v3` por defecto | Cambiar a `medium` para preview |
| ffmpeg no encontrado | No en PATH | `winget install Gyan.FFmpeg` y reabrir terminal |

---

## 16. Costes y consumo

> Cifras orientativas para 1 episodio de 15 min. Pueden variar con tarifas de cada API.

| Servicio | Modelo | Métrica | Volumen típico/episodio | Coste aprox. |
|---|---|---|---|---|
| OpenAI | `gpt-4.1` | tokens | ~7000 in + 5000 out | $0.05–$0.15 |
| OpenAI | `gpt-4.1-mini` | tokens | ~3000 (review) | $0.005 |
| OpenAI | `whisper-1` | minutos audio | 15 min | $0.09 |
| ElevenLabs | `eleven_v3` | caracteres | ~12,000 chars (1900 palabras × ~6) | $0.30–$0.60 |
| Anthropic | `claude-sonnet` | tokens | ~5000 in + 1500 out (vídeo) | $0.05 |
| Luma | image-to-video | escenas | 5-10 escenas de 5s | $0.50–$1.50 |
| **Total estimado** | | | | **~$1–$2.50 por episodio** |

15 episodios completos = **~$15–$40**. Por debajo de cualquier subscriptionbasado en una persona generándolos manualmente.

---

## 17. Roadmap y deuda técnica

### Pendientes documentados

- ⏳ **Migrar generadores a `runlog`**: hoy escriben texto libre en `*.log`. La cockpit lo absorbe vía fallback regex pero pierde calidad. Trabajo en `feature/genepisodios`.
- ⏳ **Editor de guiones in-place** en la cockpit (página 📚 Fuentes), con validación contra `podcast_spec`.
- ⏳ **Selector de módulo** en la página Fuentes (hoy es por nombre del archivo).
- ⏳ **Gráfico temporal de progreso** en página Estado cuando haya histórico.
- ⏳ **Conectores nuevos**: YouTube uploader, Telegram listener, RSS publisher (cuando el sistema autónomo de `dual_debate.py` se materialice).
- ⏳ **Histórico real**: pasar de JSONL a SQLite cuando los volúmenes lo justifiquen (>10k eventos). Ya está justificado el JSONL como solución intermedia.

### Deuda técnica conocida

- **Flags de pipelines hardcoded** en cada `PipelineConnector` (en lugar de introspectar el `argparse.ArgumentParser` de cada script). Decisión consciente: evita coupling y modificaciones invasivas a los scripts. Coste: si se añade un flag al script, hay que actualizarlo también en el conector.
- **Worktree huérfano `laughing-leavitt-33109f`**: cuando se consolidaron las ramas, se hizo cirugía manual para que esta sesión opere como worktree de `APPContenidos`. La carpeta tiene un nombre feo. Cuando se cierre la sesión, renombrar (o seguir conviviendo: no afecta al funcionamiento).
- **`_archivo/generar_episodio.py`**: la versión 1 del generador de audio. Se mantiene por si una validación antigua la requiere; debería eliminarse cuando se confirme que ningún módulo lo invoca.
- **Sin tests automatizados**. El proyecto se valida en producción (cada episodio es su propio test). Para una v2, conviene un suite mínimo (smoke tests del cockpit + validación de spec contra ejemplos canónicos).

---

## Apéndice A — Comandos exprés

```powershell
# Estado del sistema
python estado_proyecto.py
python estado_proyecto.py --pendiente

# Generar guion + audio en un comando
python producir_episodio.py --ep M3_E_ML --modulo M3 --tema "ML Clasico" --pdf PDFs/M3_T_Machine_Learning_Clasico.pdf

# Solo audio desde un guion existente
python generar_episodio_v2.py --guion Guiones/M3_T_ML.txt --ep M3_E_ML

# Validar
python validar_episodio.py --ep M3_E_ML --guion Guiones/M3_T_ML.txt

# Cockpit
streamlit run cockpit/app.py

# Pipeline vídeo
cd maquinaria_pesada_pipeline; python run_pipeline.py --preview
```

## Apéndice B — Variables de entorno

```bash
# .env (gitignored, no subir)
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...
LUMA_API_KEY=...

# Opcionales (cockpit)
REPO_ROOT=C:\Users\Asus\maquinaria_pesada
EVENTS_DIR=C:\Users\Asus\maquinaria_pesada\episodios
```

## Apéndice C — Esquema de evento JSONL (`runlog`)

```json
{
  "ts": "ISO 8601 con Z",
  "episode": "string (M{N}_E_{tema} | EP001 | ...)",
  "module": "M0..M14",
  "script": "filename.py",
  "pid": 4242,
  "phase": "string (start | extract_pdf | parse_blocks | synth_block | mount_audio | validate | end | ...)",
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

---

**Documento maestro · Sistema MaquinarIA Pesada · v1**

*Actualizar este documento cuando cambien: la spec maestra, el set de scripts, los modelos de I.A. usados, el repositorio o la estructura de cuentas. Si lo modificas, hazlo en una rama de feature y mergea a master para que las otras sesiones lo vean.*
