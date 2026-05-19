# MaquinarIA Pesada

Sistema de produccion automatizada de un videopodcast sobre IA, generado **al 100% con IA**:

- **Guion** etiquetado por bloques, speakers y tonos.
- **Voces** Maria e Iago generadas con ElevenLabs (`eleven_v3`).
- **Video** producido por un pipeline Python que combina:
  - Whisper (transcripcion con timestamps por palabra)
  - Pillow (overlays, stat cards, name tags, stickers)
  - Anthropic Claude (director visual del timeline)
  - ffmpeg (composicion final, subtitulos, intro, watermark)

## Estructura

```
.
├── EP001_guion_etiquetas_*.txt        Guiones del episodio 1
├── Guiones/                           Guiones por episodio
├── PDFs/                              Material fuente del curso
├── generar_episodio_v2.py             Produccion de audio (ElevenLabs)
├── VOICE_CONFIG_REFERENCE.md          Configuracion validada de voces
└── maquinaria_pesada_pipeline/        Pipeline de videopodcast
    ├── setup_project.py               Setup interactivo de assets
    ├── run_pipeline.py                Orquestador (--preview, --from-step)
    ├── pipeline/                      Pasos 00..07
    └── templates/                     Overlays, fondos, stickers, prompt LLM
```

## Arrancar la cabina web (cockpit)

La cabina (`web_server.py` + `vite_app/`) se levanta con un único script:

```bash
bash start_cockpit.sh
```

Tras los pasos automáticos (deps Python, deps Node, build de Vite si está
desactualizado) imprime:

```
  Cockpit listo · abre en el navegador:
      http://localhost:8765/
```

Esa URL sirve todas las funcionalidades (Producción, Datos, Sistema,
Shorts) — UI, API JSON, SSE y archivos del repo (`/files/...`).

Banderas útiles:

```bash
bash start_cockpit.sh --dev         # además levanta vite dev (HMR) en :5173
bash start_cockpit.sh --skip-build  # no rehace el build aunque src haya cambiado
bash start_cockpit.sh --port 9000   # cambia el puerto del backend
```

El script es idempotente: relánzalo cuantas veces quieras, sólo (re)hace
lo necesario y mata el `web_server` previo en el mismo puerto antes de
arrancar el nuevo.

## Setup rapido

```bash
# 1) Clonar y dependencias
git clone https://github.com/bakero/maquinaria-pesada.git
cd maquinaria-pesada
pip install -r maquinaria_pesada_pipeline/requirements.txt

# 2) Variables de entorno
cp .env.example .env
# Edita .env y pon tus claves reales (NO se sube a git)

# 3) Configurar assets del proyecto
cd maquinaria_pesada_pipeline
python setup_project.py
# Te pedira interactivamente las rutas de logo, intro, sintonia, guion, audio, etc.

# 4) Lanzar pipeline
python run_pipeline.py --preview        # primer minuto a 720p (validacion rapida)
python run_pipeline.py                  # render completo 1080p
```

## Pasos del pipeline

| # | Modulo                   | Output                              |
|---|--------------------------|-------------------------------------|
| 0 | `asset_validator`        | Verifica rutas y formatos           |
| 1 | `transcriber`            | `transcription_raw.json`            |
| 2 | `content_extractor`      | `content_data.json` (stats, kw)     |
| 3 | `scene_builder`          | `scene_timeline.json` (LLM o heur)  |
| 4 | `overlay_renderer`       | PNGs por keyframe                   |
| 5 | `subtitle_generator`     | `*_subtitulos.srt` con keywords     |
| 6 | `video_compositor`       | `*_videopodcast.mp4`                |
| 7 | `metadata_generator`     | YouTube metadata + thumbnail        |

## Identidad visual

- Amarillo CAT `#F5C400` para Maria / datos positivos
- Azul electrico `#4DB8FF` para Iago / lo tecnico
- Negro `#0D0D0D` de base, gris rejilla `#1A1A1A`
- Rojo `#CC2200` para alertas / regulacion / multas

## Licencia

Privado. Todos los derechos reservados.
