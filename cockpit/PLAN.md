# Plan: Cockpit Web para MaquinarIA Pesada

## Context

El sistema actual es un conjunto de 8 scripts CLI en Python (`generar_guion.py`, `generar_episodio_v2.py`, `producir_episodio.py`, `estado_proyecto.py`, `validar_episodio.py`, `lanzar_produccion.py`, `podcast_spec.py`, `dual_debate.py`) que producen episodios de podcast con OpenAI + ElevenLabs + ffmpeg. El usuario afina los generadores en Claude Code y ejecuta la producción masiva con Codex.

Necesidad: una **app web de observabilidad y centralización** —no un ejecutor— para:
- Ver el estado de producción (qué hay generado, qué falta) por módulo (M0-M14)
- Consultar las fuentes (PDFs, guiones, audios, videos, logs)
- Generar/copiar prompts CLI listos para Codex desde formularios
- Configurar servicios externos como conectores modulares
- Ver logs de las generaciones automáticas

Stack elegido: **Streamlit** (Python puro, dashboards internos en horas, reutiliza módulos existentes sin refactor).

## Estado del repo (importante)

El worktree actual (`laughing-leavitt-33109f`) está en el commit `init` y solo tiene `generar_episodio.py/v2`. El código vivo está en `C:\Users\Asus\maquinaria_pesada\` con cambios sin commitear (8 scripts + spec). **Paso 0 obligatorio antes de implementar:** decidir con el usuario si commiteamos el estado actual a `master` o creamos una rama desde el working tree del path principal. La app no se puede construir sobre el worktree tal cual.

## Arquitectura

```
maquinaria_pesada/
├── (scripts existentes — sin tocar)
├── cockpit/                          # NUEVO
│   ├── app.py                        # entry: streamlit run cockpit/app.py
│   ├── pages/                        # Streamlit multipage
│   │   ├── 1_📊_Estado.py           # dashboard inventario
│   │   ├── 2_🔌_Conectores.py        # registro de conectores
│   │   ├── 3_📝_Generar_Prompt.py    # formularios → prompts CLI para Codex
│   │   ├── 4_📚_Fuentes.py           # browser PDFs/Guiones/Audio/Video
│   │   └── 5_📜_Logs.py              # tail viewer de episodios/*.log
│   ├── connectors/
│   │   ├── __init__.py               # registro: REGISTRY = {}
│   │   ├── base.py                   # clase Connector (interfaz común)
│   │   ├── services/                 # servicios externos
│   │   │   ├── openai.py
│   │   │   ├── elevenlabs.py
│   │   │   ├── ffmpeg.py
│   │   │   └── codex.py
│   │   ├── pipelines/                # scripts del repo
│   │   │   ├── generar_guion.py
│   │   │   ├── generar_episodio.py
│   │   │   ├── validar_episodio.py
│   │   │   └── estado_proyecto.py
│   │   └── sources/                  # tipos de fuente
│   │       ├── pdf.py
│   │       ├── guion.py
│   │       ├── audio.py
│   │       ├── video.py
│   │       └── log.py
│   └── core/
│       ├── paths.py                  # rutas leídas de PODCAST_MASTER_SPEC.md
│       ├── state.py                  # wrapper de estado_proyecto.scan()
│       └── prompt_builder.py         # form values → comando CLI con shlex.quote
├── requirements-cockpit.txt          # streamlit, pdfplumber (ya), pydub (ya), python-dotenv
└── (resto del repo igual)
```

## Patrón conector (interfaz común)

`cockpit/connectors/base.py`:

```python
class Connector:
    id: str          # único, ej "openai", "generar_guion", "pdf"
    category: str    # "service" | "pipeline" | "source"
    label: str       # display name
    icon: str        # emoji o nombre lucide

    def status(self) -> dict: ...      # {ok: bool, detail: str}
    def render_config(self) -> None: ...  # Streamlit UI para config
    def render_card(self) -> None: ...    # tarjeta resumen en /Conectores
```

Subclases:
- `ServiceConnector` — añade `check_credentials()`, lee `.env`
- `PipelineConnector` — declara `argparse` flags como `List[Field]`, `build_command(values) -> str`
- `SourceConnector` — añade `list_items() -> List[Path]`, `render_viewer(path)`

Registro en `connectors/__init__.py`: cada submódulo se auto-registra al importarse vía decorador `@register`. Añadir un servicio/script/fuente nuevo = un fichero nuevo en la subcarpeta correcta. Cero cambios al código del dashboard.

## Páginas Streamlit (lo que ve el usuario)

1. **Estado** — reutiliza `estado_proyecto.scan()` y `print_estado_resumen()`. Tabla por módulo M0-M14: PDF ✓/✗, Guion ✓/✗, Audio ✓/✗, Video ✓/✗. Botones "ver pendientes" y "ver assets" replican `--codex` y `--assets`.
2. **Conectores** — grid de tarjetas agrupadas por categoría. Cada tarjeta muestra `status()` y enlaza a su `render_config()` en un `st.expander`.
3. **Generar Prompt** — selector de pipeline → formulario auto-generado a partir de los flags declarados → vista previa del comando con `st.code(cmd, language="bash")` + botón copiar. **No ejecuta nada.** Diseñado para pegar en Codex.
4. **Fuentes** — selector de tipo (PDF/Guion/Audio/Video/Log) + selector de módulo → viewer adecuado: pdfplumber para PDFs, `st.text_area` editable para guiones (con validación vía `podcast_spec.validate_script_text`), `st.audio` para mp3, `st.video` para mp4, `st.code` con tail para logs.
5. **Logs** — listado de `episodios/*.log`, viewer con `st.code` + auto-refresh opcional vía `streamlit-autorefresh` (poll cada 5s).

## Reutilización de código existente

| Necesidad | Reutiliza |
|---|---|
| Inventario por módulo | `estado_proyecto.scan()` |
| Validar guion | `podcast_spec.validate_script_text()` |
| Parsear bloques guion | `podcast_spec.parse_script_blocks()` |
| Conteo palabras | `podcast_spec.count_words()` |
| Rutas/voces/reglas | `podcast_spec.load_master_spec()` (single source of truth) |
| Flags de pipelines | introspección del `argparse.ArgumentParser` de cada script |

Para los `PipelineConnector`, en vez de duplicar a mano la lista de flags, se importa el script y se inspecciona su `ArgumentParser` (refactor menor: extraer cada `parser = argparse.ArgumentParser(...)` a una función `build_parser()` reutilizable). Esto evita que la app se desincronice del CLI.

## Generación de prompts para Codex

`prompt_builder.py` toma `(connector_id, form_values)` y devuelve un string ejecutable:

```
python generar_guion.py --pdf "PDFs/RESUMEN_M3_Machine_Learning_Clasico.pdf" --ep M3_T_ML --modulo M3 ...
```

Reglas:
- Usa `shlex.quote` para rutas con espacios
- Resuelve rutas relativas al directorio del repo
- Añade un encabezado con la fecha y el módulo: `# Codex prompt — M3 — 2026-05-07`
- Ofrece copiar al portapapeles vía `st.code` (botón nativo de Streamlit)

## Configuración

- `.env` se lee con `python-dotenv` (ya en uso). El cockpit muestra qué claves están presentes (sin revelar el valor) en cada `ServiceConnector`.
- `PODCAST_MASTER_SPEC.md` queda como fuente única de verdad para rutas, voces, reglas. El cockpit no las duplica.
- `cockpit/core/paths.py` carga el spec una vez por sesión (`@st.cache_resource`).

## Archivos a crear (lista exacta)

- `cockpit/app.py`
- `cockpit/pages/1_📊_Estado.py`, `2_🔌_Conectores.py`, `3_📝_Generar_Prompt.py`, `4_📚_Fuentes.py`, `5_📜_Logs.py`
- `cockpit/connectors/__init__.py`, `base.py`
- `cockpit/connectors/services/openai.py`, `elevenlabs.py`, `ffmpeg.py`, `codex.py`
- `cockpit/connectors/pipelines/generar_guion.py`, `generar_episodio.py`, `validar_episodio.py`, `estado_proyecto.py`
- `cockpit/connectors/sources/pdf.py`, `guion.py`, `audio.py`, `video.py`, `log.py`
- `cockpit/core/paths.py`, `state.py`, `prompt_builder.py`
- `requirements-cockpit.txt`

## Archivos a modificar (mínimo, no invasivo)

- `generar_guion.py`, `generar_episodio_v2.py`, `validar_episodio.py`, `estado_proyecto.py` — extraer `build_parser()` para que el cockpit pueda introspectar los flags. Sin cambiar comportamiento CLI.

## Verificación end-to-end

1. `pip install -r requirements-cockpit.txt`
2. `streamlit run cockpit/app.py` → abre `http://localhost:8501`
3. **Estado**: la tabla M0-M14 coincide con `python estado_proyecto.py` ejecutado en CLI
4. **Conectores**: las cuatro fichas de servicios muestran ✓ si las API keys están en `.env`, ✗ si faltan
5. **Generar Prompt**: rellenar formulario para `generar_guion` con M3 → el comando mostrado se ejecuta sin error si lo pegas en terminal
6. **Fuentes**: abrir un PDF de `PDFs/`, abrir un guion existente, reproducir un mp3 de `episodios/`, abrir un log
7. **Logs**: tail de `episodios/M0_produccion.log` muestra contenido y auto-refresca al añadir líneas (test con `echo>>`)
8. Añadir un conector dummy nuevo en `connectors/services/dummy.py` → aparece en /Conectores sin tocar otros archivos (test del patrón modular)

## Fuera de scope (deliberado)

- No ejecuta el pipeline (decisión del usuario: solo prompts para Codex)
- No edita el spec maestro desde la web
- No gestiona credenciales (las pone el usuario en `.env`)
- No multiusuario / no auth (uso local)
- No despliega (corre en `localhost`)
