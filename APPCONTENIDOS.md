# APPCONTENIDOS — Diario del proyecto

Diario cronológico de decisiones, cambios técnicos y contexto de la sesión **APPContenidos** (rama `APPContenidos`, dedicada a la cockpit web del sistema MaquinarIA Pesada).

> **Regla de oro**: toda decisión nueva o cambio relevante se anota aquí con timestamp y rationale **antes o durante** su implementación. La idea es tener un registro consultable de por qué el sistema es como es, no solo qué hace.

---

## Cómo añadir entradas

Una entrada por decisión o cambio significativo. Formato:

```markdown
### YYYY-MM-DD · #N — Título corto

**Tipo**: decisión | implementación | corrección | refactor | doc | git
**Contexto**: 1-2 frases del problema o la pregunta
**Decisión**: qué se elige y por qué (incluyendo alternativas descartadas si las hubo)
**Cambios técnicos**: archivos tocados, comandos clave, commits
**Próximos pasos / impacto**: qué queda pendiente o qué afecta
```

`#N` se incrementa secuencialmente en cada día. Si un cambio implica varios commits/archivos, listalos.

---

## 2026-05-10 — Sesión inicial: nacimiento de la cockpit

### 2026-05-10 · #1 — Elicitación token-optimizer

**Tipo**: decisión
**Contexto**: el usuario pide convertir el sistema CLI Python (producción podcast) en una aplicación web. Antes de implementar, slots de token-optimizer.
**Decisión**: parámetros de la sesión:
- `task_type` = code + refactor
- `scope` = whole-codebase
- `reasoning_need` = medium
- `session_state` = continuing-different (chat nuevo desde otro contexto)
- `output_determinism` = exact-format (código ejecutable en repo)
**Recomendación aceptada**: Sonnet + Plan Mode + `/clear` (saltado para no perder los slots ya elicitados).

### 2026-05-10 · #2 — Plan aprobado: cockpit Streamlit como dashboard, no ejecutor

**Tipo**: decisión
**Contexto**: la web app debe centralizar info; el usuario afina generadores en Claude Code, Codex ejecuta. Necesidad de "qué tengo, qué falta, ver logs, generar prompts para Codex".
**Decisión**:
1. **Framework**: Streamlit (Python puro, dashboards en horas, reusa módulos existentes). Descartados: FastAPI+Jinja+HTMX (más código, sin valor extra para un dashboard local), FastAPI+SPA (sobredimensionado para un solo usuario).
2. **Modo**: solo monitor + generador de prompts. **No ejecuta el pipeline**. Descartado: hybrid execute/monitor (más complejidad sin demanda real).
3. **Conectores modulares de 3 categorías**: services (OpenAI, ElevenLabs, ffmpeg, Codex), pipelines (cada script Python), sources (PDF, Guion, Audio, Video, Log). Patrón unificado con auto-registro.
4. **`REPO_ROOT` env var** con default `C:\Users\Asus\maquinaria_pesada` para apuntar a cualquier checkout sin tocar código.
5. **Flags de pipelines hardcoded** en cada `PipelineConnector` (en lugar de introspectar `argparse`). Razón: evita modificar los scripts del repo principal que tenían cambios sin commitear; la consistencia del flag list es deuda técnica conocida.
**Cambios técnicos**: plan persistido en `C:\Users\Asus\.claude\plans\iterative-rolling-lecun.md`.

### 2026-05-10 · #3 — Implementación cockpit/ (auto-mode)

**Tipo**: implementación
**Contexto**: plan aprobado, auto-mode activado.
**Decisión técnica clave**: imports de `streamlit` **diferidos dentro de los métodos** (no a nivel de módulo) para que el auto-registro de conectores funcione aunque streamlit no esté instalado.
**Cambios técnicos**: 25 archivos creados:
- `cockpit/app.py` (entry point)
- `cockpit/core/` → `paths.py`, `state.py`, `prompt_builder.py`
- `cockpit/connectors/` → `base.py`, `__init__.py` con auto-loader, 4 services + 4 pipelines + 5 sources
- `cockpit/pages/` → 5 páginas Streamlit (Estado, Conectores, Generar Prompt, Fuentes, Logs)
- `requirements-cockpit.txt`
**Smoke test**: 13 conectores registrados (4+4+5), `state.scan()` lee correctamente M0-M14, `build_command()` produce CLI válido con `shlex.quote`.

### 2026-05-10 · #4 — Bug detectado y corregido: `M1` ⊂ `M10` en regex

**Tipo**: corrección
**Contexto**: el matcher de módulo en `state.py` usaba `if m in n` y M1 capturaba 61 PDFs (todos los M10-M19).
**Decisión**: regex estricta con boundaries: `(?:^|[^A-Z0-9])M(?:OD)?0*{digits}(?=[^0-9]|$)`.
**Cambios técnicos**: `cockpit/core/state.py` — `_has_module()` reescrito.

### 2026-05-10 · #5 — Consolidación masiva del repo en master

**Tipo**: git
**Contexto**: estado caótico:
- `master` local en `d055401` (Luma assets) con dump enorme sin commitear (8 scripts, PDFs renombrados, 142 archivos).
- `origin/master` en `a4cf702` (videopodcast pipeline v2): historia **disjunta** de master local (init hashes distintos: `17ad286` vs `94191ee`).
- 4 worktree branches `claude/*` con cambios únicos en algunas (cockpit en `laughing-leavitt`, pipeline updates en `nervous-neumann`, `dual_debate_maquinaria.py` en `clever-hodgkin`).
- `.env` tracked sin `.gitignore`, secrets en GitHub potencialmente.
**Decisión** (validada con el usuario):
1. **Secrets**: confiar en el `.gitignore` que ya existía en `origin/master` (cubría `.env`, binarios, audio). Sin necesidad de crear uno nuevo.
2. **Reconciliación de master**: tomar `origin/master` como trunk, cherry-pick `d055401` encima (4 PNGs Luma), mirror del main path con `robocopy` filtrando ignorables.
3. **Branches obsoletas**: borrar las 3 abandonadas tras verificar que su trabajo único estaba consolidado.
**Cambios técnicos**:
- Tags de seguridad: `safety/master-before-consolidation`, `safety/origin-master-snapshot`.
- Branch `consolidation` en worktree `nervous-neumann`, cherry-pick + mirror + add + commit.
- Push: `a4cf702..f752777 consolidation -> master` (fast-forward).
- Commit adicional `f45696c` para `normalizar_guiones.py` que se había quedado fuera del mirror.
- Borradas 4 ramas `claude/*` y `consolidation`. Quedan solo `master` + `feature/videopodcast` + `feature/generadores` + `APPContenidos` (creadas más adelante).
- Resultado: **244 archivos tracked** en master, working tree limpio.
**Impacto**: `master` ahora es lineal, descendiente de `origin/master`. Sin secrets en commits. Todos los scripts y assets del usuario en GitHub.

### 2026-05-10 · #6 — Topología de ramas: una sesión = una rama y un worktree

**Tipo**: decisión
**Contexto**: el usuario tiene 3 sesiones simultáneas: generador de episodios, videopodcast, app (esta).
**Decisión**: cada sesión opera en su propia rama dentro de su propio worktree (`.claude/worktrees/<nombre>`). Razones:
- Las 3 zonas de trabajo son disjuntas (`*.py` raíz / `maquinaria_pesada_pipeline/` / `cockpit/`) → conflictos casi nulos al mergear.
- Sin worktrees separados, una sesión hace `git add -A` y arrastra el WIP de otra.
**Cambios técnicos**:
- `feature/videopodcast` → `.claude/worktrees/videopodcast/`
- `feature/generadores` → `.claude/worktrees/generadores/`
- `APPContenidos` → `.claude/worktrees/APPContenidos/`
**Pendiente**: el usuario creó `feature/genepisodios` después en paralelo a `feature/generadores`. Decidir cuál se queda y borrar la otra.

### 2026-05-10 · #7 — SESSION_CONTEXT.md + PLAN.md committeados

**Tipo**: doc
**Decisión**: cada sesión guarda su contexto en su rama (decisiones cerradas, slots, pendientes, cómo retomar).
**Cambios técnicos**: `cockpit/SESSION_CONTEXT.md` + `cockpit/PLAN.md` en `APPContenidos` (commit `f0f2313`).

### 2026-05-10 · #8 — Cirugía manual: re-injertar orphan dir como worktree de APPContenidos

**Tipo**: corrección + git
**Contexto**: la sesión actual de Claude Code corre en `.claude/worktrees/laughing-leavitt-33109f/`, cuyo branch original se borró durante la consolidación. El proceso del agente no puede cambiar su `cwd` en runtime, así que esta sesión queda "huérfana" git-wise.
**Decisión**: opción hacky validada por el usuario. Borrar el worktree limpio creado en `.claude/worktrees/APPContenidos/`, recrear manualmente la metadata git (`<repo>/.git/worktrees/laughing-leavitt-33109f/` con `HEAD`/`gitdir`/`commondir`) apuntando a la rama `APPContenidos`, restaurar el archivo `.git` del orphan, y hacer `git reset --hard APPContenidos` para sincronizar working tree.
**Cambios técnicos**: orphan dir ahora es worktree válido sobre rama `APPContenidos`, contenido sincronizado con HEAD (244 archivos).
**Deuda técnica**: el nombre del directorio sigue siendo feo (`laughing-leavitt-33109f`). No se puede renombrar mientras la sesión esté activa. Cuando se cierre, renombrar a `APPContenidos` o aceptar la convivencia.

### 2026-05-10 · #9 — Modal de validaciones por celda en página Estado

**Tipo**: implementación
**Contexto**: el usuario quiere ver validaciones de la última ejecución al pulsar el icono OK/KO de cada categoría.
**Decisión**:
- **Granularidad**: por categoría (current). Descartadas: por archivo individual (jerarquía pesada), híbrido (más código sin valor inmediato).
- **Fuente de datos**: parsear `episodios/*.log` con regex (heurístico). Descartado: re-ejecutar validaciones (lento), store dedicado (todavía no existe).
- **Reconocimiento**: aproximación frágil; la decisión correcta a medio plazo es structured logging (ver #11).
**Cambios técnicos**:
- `cockpit/core/log_parser.py` (nuevo): regex tolerante con keywords por categoría, `CategorySummary` con errores/warnings/timestamps/sample.
- `cockpit/pages/1_📊_Estado.py` reescrito: tabla de `st.button` por celda, `@st.dialog` para el modal.
**Commit**: `ab170df`.

### 2026-05-10 · #10 — Sidebar persistente "Producción en vivo" con psutil

**Tipo**: implementación
**Contexto**: el usuario quiere ver en tiempo real qué script corre y qué se está generando.
**Decisión**:
- **Modo**: monitor-only (sin cambiar el alcance #2). Descartado: añadir ejecución desde la app (cambiaría toda la arquitectura).
- **Ubicación**: sidebar nativa (siempre visible). Descartado: top header (helper compartido en cada página: más código y duplicación).
- **Detección**: `psutil` para procesos Python con un script del pipeline en cmdline + filesystem mtime para log activo y archivos recién creados.
- **Auto-refresh**: 5 s vía `streamlit-autorefresh`.
**Cambios técnicos**:
- `cockpit/core/monitor.py` (nuevo): `scan_running()`, `find_active_log()`, `recent_outputs()`, `tail_lines()`.
- `cockpit/ui.py` (nuevo): `render_status_sidebar()`.
- `app.py` + 5 páginas: llaman `render_status_sidebar()` tras `set_page_config()`.
- `requirements-cockpit.txt`: añade `psutil>=5.9`.
**Commit**: `e6fb347`.
**Smoke test**: detectó en vivo la generación de bloques M1 que estaba en marcha en otra sesión (`M1_E_Fundamentos_Razonamiento_039_IAGO.mp3` apareciendo cada ~5 s).

### 2026-05-10 · #11 — Structured logging via `runlog.py` (decisión arquitectónica)

**Tipo**: decisión + implementación
**Contexto**: el regex sobre logs libres es frágil; cambiar el formato de una línea rompe la cockpit silenciosamente.
**Análisis comparado** (recomendaciones del asistente):
- ✅ **JSONL append-only por run** (elegido): bajo coste, alto valor, sin dependencias.
- ❌ OpenTelemetry: martillo equivocado para single-user local.
- ❌ Loguru/rich: cosmética, no resuelve la fragilidad del parsing.
- ❌ Redis/event bus: requiere proceso adicional.
- ⏳ SQLite a futuro cuando se justifique (>10k eventos).
**Decisión**: introducir `runlog.py` en raíz del repo (importable por cualquier generador, sin dependencias) con API tipo:

```python
with RunLogger(episode="M3_E_ML", module="M3", script="generar_episodio_v2.py") as log:
    log.event("synth_block", category="audio", block=12, speaker="IAGO", ms=312, credits=1024)
```

Output: `episodios/{episode}_events.jsonl`. Campos automáticos (`ts`, `episode`, `module`, `script`, `pid`, `phase`, `level`, `category`) + kwargs libres.

`log_parser.py` actualizado con cadena de prioridad: **JSONL si existe → fallback regex → vacío**. Misma API `CategorySummary` para que la modal no rompa. Cuando es JSONL, además rellena `events` (raw dicts) y `phase_counts` (agregados por fase).

**Cambios técnicos**:
- `runlog.py` (nuevo, raíz del repo): RunLogger context manager + API global `init/event/warn/error/close_global`. Tolerante a errores de I/O (nunca rompe el generador).
- `cockpit/core/log_parser.py` reescrito: prioridad JSONL > texto.
- `cockpit/pages/1_📊_Estado.py`: badge de fuente en modal + expander con phase_counts cuando hay datos estructurados.
**Commit**: `9f62350`.
**Pendiente**: migrar generadores a `runlog`. Trabajo en sesión `feature/genepisodios`. Sin urgencia: el fallback regex sigue funcionando.

### 2026-05-10 · #12 — Bug operativo: psutil "no instalado" en Streamlit

**Tipo**: corrección
**Contexto**: la cockpit mostraba "psutil no está instalado" aunque `pip install psutil` decía OK.
**Causa**: Streamlit cachea imports al arrancar. Si se lanzó antes de instalar `psutil`, mantiene `_HAS_PSUTIL=False` toda la sesión.
**Solución**: refresh del navegador o reinicio de Streamlit. Sin cambios en código.

### 2026-05-10 · #13 — BIBLIA.md: documento maestro del sistema

**Tipo**: doc
**Contexto**: el usuario pide un único documento que explique todo el sistema (proceso, técnicas IA, estructura, scripts, cockpit, tecnologías, cuentas).
**Decisión**: crear `BIBLIA.md` en raíz, organizado en 17 secciones + 3 apéndices:
1. Visión general · 2. Arquitectura · 3. Tecnologías y cuentas · 4. Estructura del repo · 5. Especificación maestra · 6-8. Pipelines 1, 2, 3 · 9. Validación · 10. Observabilidad · 11. Cockpit · 12. Técnicas de IA · 13. Convenciones · 14. Workflow desarrollo · 15. Operaciones · 16. Costes · 17. Roadmap.
**Cambios técnicos**: `BIBLIA.md` (780 líneas, 53 KB).
**Commit**: `009b32e`.

### 2026-05-10 · #14 — APPCONTENIDOS.md: diario del proyecto (este archivo)

**Tipo**: doc + decisión
**Contexto**: el usuario pide un diario cronológico de decisiones para tener trazabilidad de cómo y por qué evoluciona el sistema.
**Decisión**:
- Archivo `APPCONTENIDOS.md` en raíz del repo, separado de `BIBLIA.md` (que es referencia técnica viva).
- Una entrada por decisión o cambio significativo, con timestamp `YYYY-MM-DD · #N`.
- Formato fijo: Tipo / Contexto / Decisión / Cambios técnicos / Próximos pasos.
- Esta sesión (APPContenidos) actualiza el archivo cada vez que se cierre una decisión, antes o durante la implementación.
**Cambios técnicos**: este archivo, generado retroactivamente con las 13 decisiones previas + esta entrada.

### 2026-05-10 · #15 — Tema visual industrial CAT (dark + amarillo + acero)

**Tipo**: decisión + implementación
**Contexto**: el usuario pide apariencia industrial: amarillo CAT corporativo, paleta metalizada (excavadoras, hormigoneras, camiones), tipografías angulares, logo de MaquinarIA Pesada visible.

**Decisión** (commit visual cohesivo, ajustable a posteriori si no convence):

1. **Modo base**: dark. Las máquinas de obra se fotografían en contextos sucios y oscuros; el negro hace que el amarillo CAT pegue duro. Light theme descartado: pierde contundencia.

2. **Paleta**:
   - Fondo: `#0D0D0D` (carbón) y `#1A1A1A` (acero oscuro) para superficies elevadas (cards, sidebar).
   - Bordes / divisores: `#3A3A3A` (acero medio) y `#262626` (panel).
   - Texto: `#F2F2F2` primario, `#A8A8A8` secundario (acero claro).
   - **Primario CAT**: `#F5C400` (consistente con BIBLIA.md). Hover/dark: `#D4A800`.
   - Acentos según spec: IAGO `#4DB8FF` (azul eléctrico), MARIA `#F5C400` (amarillo), alerta `#CC2200`, OK `#00B894`.

3. **Tipografía** (Google Fonts, embedidas vía CSS injection):
   - Display / títulos: **Oswald** SemiBold/Bold, `text-transform: uppercase`, `letter-spacing` ancho.
   - Cuerpo: **Barlow Condensed** Regular/Medium (modernidad técnica condensada).
   - Numérico / código: **JetBrains Mono** (sensación técnica/HUD).
   - Descartadas: Bebas Neue (demasiado gritón para textos largos), Black Ops One (militar > industrial), Stencil (cliché).

4. **Logo**: `st.logo("Logos/logo sin fondo.png", size="large")`. La versión sin fondo es la default por spec; las metálicas y la de fondo amarillo quedan reservadas para producción de assets, no para UI.

5. **Implementación**:
   - `.streamlit/config.toml` en raíz del repo: tema base (primaryColor, backgroundColor, secondaryBackgroundColor, textColor, font).
   - `cockpit/theme.py` (nuevo): función `inject_theme()` que mete CSS custom (Google Fonts + overrides Streamlit + utilidades). Llamada desde `app.py` y cada página tras `set_page_config()`.
   - Bordes amarillos en containers de "Producción en vivo" (sidebar) y en headers de página.
   - Botones con esquinas ligeramente angulares (border-radius 2px), uppercase, hover con borde amarillo.

6. **Constantes de color** centralizadas en `theme.py` (variables CSS y un dict Python para que código futuro reutilice los valores).

**Cambios técnicos** (próximo commit):
- `.streamlit/config.toml` (nuevo)
- `cockpit/theme.py` (nuevo, ~120 líneas CSS embebido)
- `cockpit/ui.py` (modificado: `render_status_sidebar` aplica clases del tema)
- `cockpit/app.py` + 5 páginas (modificadas: `st.logo()` + `inject_theme()` tras `set_page_config()`)
- `BIBLIA.md` actualizable a posteriori con el detalle del tema (deuda menor).

**Próximos pasos / impacto**:
- Si el usuario quiere variantes (paleta más sucia/grunge, fuente más agresiva, light mode), se itera con cambios localizados en `theme.py`.
- El tema NO afecta a la lógica de la cockpit ni al pipeline de generación. Solo presentación.

### 2026-05-10 · #16 — Consolidación final en master: docs untracked + merge APPContenidos + reconciliación de biblias

**Tipo**: git + decisión + doc
**Contexto**: el ecosistema de docs estaba fragmentado en tres áreas con trabajo no consolidado.
1. `PRIMERPODCAST.md` y borradores de escaleta `escaletas/EP-MOD000_*.md` untracked en main path (master).
2. La rama `APPContenidos` con todo el trabajo del cockpit (incluyendo el tema visual #15) nunca llegó a master.
3. Dos "biblias" en paralelo: `BIBLIA_SISTEMA.md` (45 KB, master, canónica del proyecto) y `BIBLIA.md` (53 KB, APPContenidos, mía con cockpit en detalle).

**Decisión** (validada con el usuario: "haz las tres cosas"):

1. **Comprometer los docs untracked** (`PRIMERPODCAST.md` + `escaletas/EP-MOD000_*.md`) directamente en master desde el main path. Son project-level y deben vivir en el trunk.

2. **Mergear `APPContenidos` → `master`** con `--no-ff` para preservar la traza del trabajo de la sesión cockpit. Trae 8+ commits (modal, sidebar, runlog, BIBLIA, APPCONTENIDOS, theme, etc.).

3. **Reconciliar biblias**: `BIBLIA_SISTEMA.md` se queda como canónica. Las secciones únicas de `BIBLIA.md` (cockpit en detalle, técnicas IA listadas, costes orientativos, roadmap) se absorben en `BIBLIA_SISTEMA.md`. `BIBLIA.md` se borra para evitar drift.

**Cambios técnicos** (3+ commits en master):
- Commit A: `docs: PRIMERPODCAST.md + escaletas EP-MOD000` (en main path).
- Commit B: `Merge branch 'APPContenidos'` (--no-ff).
- Commit C: `docs: reconcilia BIBLIA.md en BIBLIA_SISTEMA.md` (edita BIBLIA_SISTEMA.md, borra BIBLIA.md).
- Push final a `origin/master`.

**Próximos pasos / impacto**:
- `BIBLIA_SISTEMA.md` queda como única referencia técnica del sistema.
- La rama `APPContenidos` queda mergeada pero no se borra (sigue siendo el worktree activo de esta sesión).
- Otras sesiones (`feature/genepisodios`, `feature/videopodcast`) deberán hacer `git pull origin master` para ver el cockpit, el tema y la biblia unificada.

### 2026-05-10 · #17 — Planificador de tareas en la cockpit

**Tipo**: decisión + implementación
**Contexto**: el usuario pasa un listado de 236 tareas (semanas pre-lanzamiento + 9 semanas iniciales) con dos tipos de fecha (`LISTA` = fecha límite, `SALE` = fecha pública), ownership, dependencias y marcadores críticos 🔴. Quiere verlas en la app y recibir avisos al cumplirse fechas.

**Decisión**:

1. **Fuente única**: la fuente canónica es markdown (lo que pega el usuario). Se guarda en `planner/source/2026-05-10_lista_inicial.md`. Un parser regenera el JSON estructurado cuando cambia el source.

2. **Storage en 2 ficheros**:
   - `planner/tareas.json` — derivado (lista de tasks con id, title, owner, lista, sale, deps, block, subsection, critical, is_check, etc.). Regenerable desde el source.
   - `planner/_state.json` — mutable (status por task: `pending`/`in_progress`/`done`/`blocked` + completed_at + notes). Se modifica desde la UI.

3. **Parser**: `planner/import_from_md.py` (regex). Soporta `LISTA: dd/mm/aaaa [hh:mm]`, `SALE: dd/mm/aaaa [hh:mm]`, `SALE: —` (vacío), `LISTA: diario SN` / `LISTA: continuo` (recurrente), `DEP: T001, T002`, marcador 🔴 al inicio del título.

4. **Página en la cockpit**: `cockpit/pages/6_📋_Planificador.py` con vistas:
   - **Hoy** (LISTA hoy y no done) — destacado arriba.
   - **Atrasadas** (LISTA < hoy y no done).
   - **Próximas críticas 🔴** (próximos 7 días).
   - **Por bloque/semana** con filtros (owner, status, search).
   - **Marcar done / in_progress / blocked / notes** desde la UI (escribe `_state.json`).

5. **Alertas en sidebar**: `render_status_sidebar()` añade bloque "📋 PLANIFICADOR" con contadores (hoy: N, atrasadas: M, críticas próximas: K). Visible en todas las páginas, refresh 5s.

6. **No push notifications todavía**: avisos solo visibles dentro de la app. Notificaciones OS/email son siguiente paso si lo pide explícitamente.

7. **Recurrentes** (`diario SN`, `continuo`): se almacenan con flag `recurring: true`, no aparecen en "Hoy" ni "Atrasadas" salvo que se marquen manualmente. Se listan aparte.

**Cambios técnicos**:
- `planner/source/2026-05-10_lista_inicial.md` (canonical source)
- `planner/import_from_md.py` (parser)
- `planner/tareas.json` (generado)
- `planner/_state.json` (estado inicial vacío)
- `cockpit/core/planner.py` (loader, mutator, alert calculator)
- `cockpit/pages/6_📋_Planificador.py` (UI)
- `cockpit/ui.py` (sidebar añade bloque planificador)

**Próximos pasos / impacto**:
- Cuando el usuario actualice el listado, edita el source MD y re-ejecuta el parser.
- Si quiere notificaciones OS (toast Windows) o email, se añade en una iteración posterior con `win10toast` o `plyer`.
- El planificador queda en `APPContenidos`; merge a master cuando el usuario lo pida.

---

## Resumen de commits de la sesión (orden cronológico)

| Commit | Mensaje | Decisión |
|---|---|---|
| `3b95086` | assets: imagenes referencia personajes/estudio para Luma image-to-video (cherry-pick) | #5 |
| `f752777` | feat: consolidate podcast generators, video pipeline updates and cockpit dashboard | #5 |
| `f45696c` | feat: add normalizar_guiones.py (formato B legacy → A converter) | #5 |
| `f0f2313` | docs(cockpit): SESSION_CONTEXT + PLAN para retomar el trabajo | #7 |
| `ab170df` | feat(cockpit): modal de validaciones por categoria en pagina Estado | #9 |
| `e6fb347` | feat(cockpit): sidebar 'Produccion en vivo' siempre visible | #10 |
| `9f62350` | feat: structured event logging via runlog.py + JSONL en log_parser | #11 |
| `009b32e` | docs: BIBLIA.md - documento maestro del sistema MaquinarIA Pesada | #13 |
| (próximo) | docs: APPCONTENIDOS.md - diario del proyecto | #14 |

---

## Convenciones del diario (recordatorio)

- **Una entrada por decisión**, no por commit. Si una decisión genera 5 commits, todos van bajo la misma entrada.
- **Decisiones triviales NO entran**: bugfixes pequeños sin impacto arquitectónico, typos, formatting.
- **Decisiones que entran**: cambios de alcance, elección de stack, elección de patrón, deuda técnica creada conscientemente, refactors mayores, decisiones git no obvias.
- **Si una decisión se revierte**, no se borra: se añade una entrada nueva explicando por qué se revierte y se referencia la original.
- **Si hay desacuerdo / pivot mid-implementación**, se documenta el pivot.
- **Cuando esté en duda**, mejor anotar de más que de menos.

---

*Diario activo desde 2026-05-10. Última entrada: #17.*
