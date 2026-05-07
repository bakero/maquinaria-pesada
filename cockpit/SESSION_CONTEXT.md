# Cockpit — Contexto de sesión

Sesión inicial de Claude Code donde se diseñó e implementó la app `cockpit/`. Documento auto-contenido para retomar trabajo en sesiones futuras sin re-elicit.

## Propósito de la app

Dashboard web (no ejecutor) sobre el sistema de podcast MaquinarIA Pesada. Centraliza:
- Estado de producción por módulo M0-M14 (PDFs / Guiones / Audio / Video / Logs).
- Visualización de fuentes (PDFs, guiones, mp3, mp4, logs).
- Generación de comandos CLI listos para pegar en Codex (no ejecuta el pipeline).
- Configuración modular tipo conectores (servicios, pipelines, fuentes).

**No hace**: ejecutar `generar_guion.py` / `generar_episodio_v2.py`, gestionar credenciales, multiusuario, despliegue.

## Decisiones clave (cerradas)

| Decisión | Valor | Razón |
|---|---|---|
| Framework | Streamlit | Python puro, dashboards internos en horas, reutiliza módulos del repo |
| Modo ejecución | Solo prompts (no ejecutor) | El usuario afina en Claude Code, Codex ejecuta |
| Conectores | 3 categorías (service / pipeline / source) | Servicios + scripts + tipos de fuente |
| `REPO_ROOT` | env var, default `C:\Users\Asus\maquinaria_pesada` | Permite apuntar la cockpit a cualquier checkout |
| Flags pipeline | Hardcoded en cada `PipelineConnector` | Evita tocar los scripts del repo (que tenían cambios sin commitear) |
| Imports streamlit | Diferidos dentro de métodos | Permite registrar conectores sin streamlit instalado |
| Auto-registro | `@register` decorator + `_autoload()` en `connectors/__init__.py` | Drop-in: nuevo fichero = nuevo conector |

## Slots token-optimizer (no re-elicitar)

- `task_type`: code + refactor
- `scope`: whole-codebase
- `reasoning_need`: medium
- `session_state`: continuing-different (originalmente)
- `output_determinism`: exact-format

## Arquitectura

```
cockpit/
├── app.py                          # entry: streamlit run cockpit/app.py
├── core/
│   ├── paths.py                    # repo_root() lee REPO_ROOT env var
│   ├── state.py                    # scan() inventario M0-M14
│   └── prompt_builder.py           # form values -> CLI con shlex.quote
├── connectors/
│   ├── base.py                     # Connector / ServiceConnector / PipelineConnector / SourceConnector
│   ├── __init__.py                 # auto-loader + REGISTRY
│   ├── services/   openai · elevenlabs · ffmpeg · codex
│   ├── pipelines/  generar_guion · generar_episodio · validar_episodio · estado_proyecto
│   └── sources/    pdf · guion · audio · video · log
└── pages/  Estado · Conectores · Generar Prompt · Fuentes · Logs
```

**Total**: 13 conectores (4 + 4 + 5).

## Cómo correr

```powershell
cd C:\Users\Asus\maquinaria_pesada\.claude\worktrees\APPContenidos
pip install -r requirements-cockpit.txt
streamlit run cockpit/app.py
```

Override de repo: `$env:REPO_ROOT = "C:\otra\ruta"; streamlit run cockpit/app.py`.

## Verificación

- Smoke test sin streamlit (sólo registro): `python -c "from cockpit import connectors; print(len(connectors.REGISTRY))"` → 13.
- `cockpit.core.state.scan()` contra repo real: M0 [PGAVL] completo, M1-M14 [PG...] con PDF+Guion.
- `prompt_builder.build()` produce comandos válidos con `shlex.quote` para espacios.

## Pendientes / próximos pasos

1. **Probar Streamlit en vivo**: `pip install -r requirements-cockpit.txt` y verificar las 5 páginas en `localhost:8501`.
2. **Editor de guiones in-place** en página Fuentes (validar con `podcast_spec.validate_script_text` y guardar).
3. **Filtro por módulo** en página Fuentes (el dropdown actual es por nombre, falta selector M0-M14).
4. **Botón "regenerar prompt" con plantilla**: pre-rellenar campos comunes (`--master-pdf`, `--modelo`) desde el spec.
5. **Página Estado**: gráfico de progreso temporal cuando haya logs históricos.
6. **Conectores nuevos a añadir**: YouTube uploader, Telegram listener, RSS publisher (cuando el sistema autónomo de `dual_debate.py` se materialice).

## Histórico / origen

- Diseño en Plan Mode, plan en `C:\Users\Asus\.claude\plans\iterative-rolling-lecun.md`.
- Implementación completa en una sola sesión (auto-mode tras aprobar el plan).
- Worktree original: `laughing-leavitt-33109f` (huérfano tras consolidación a master `f45696c`).
- Rama actual: `APPContenidos`, branched desde `master = f45696c`.

## Convenciones del repo (aplican aquí)

- Idioma asistente: español. Términos técnicos: inglés.
- Token optimization: consultar skill `token-optimizer` antes de acciones nuevas; reusar slots si ya están elicitados.
- Trabajo autónomo en auto-mode: ejecutar sin pedir confirmación en cada paso (ver `feedback_autonomy` en memoria global).
- `.gitignore` cubre: `.env`, `*.onnx`, `*.bin`, `*.mp3/.mp4/.wav/.log/.srt`, `output/`, `__pycache__/`, `.claude/worktrees/`. Verificar antes de commits grandes.
