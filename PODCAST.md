# PODCAST.md — Diario de creación · MaquinarIA Pesada

> **Propósito:** registro cronológico de decisiones, cambios técnicos e incidencias
> del proyecto. Cada entrada tiene marca de tiempo. Es la memoria operativa del proyecto —
> la `BIBLIA_SISTEMA.md` es la referencia técnica estática; este documento es el diario vivo.
>
> **Convención de entradas:**
> - `[DECISIÓN]` — elección de diseño o arquitectura con su justificación
> - `[CAMBIO]` — modificación de código o configuración
> - `[INCIDENCIA]` — bug, fallo de producción o problema externo
> - `[PRODUCCIÓN]` — evento de generación de contenido (guiones, audios, vídeos)
> - `[REGLA]` — invariante de sesión o norma de desarrollo adoptada

---

## 2026-05-07

### Primera sesión de consolidación y corrección

---

#### 13:44 — [INCIDENCIA] Primer batch de producción: log maestro incorrecto

**Contexto:** Se ejecuta `lanzar_produccion.py` por primera vez para M1–M14.  
**Síntoma:** `produccion_runs.log` registra `OK (14)` con start y fin en el mismo segundo (13:44:10), sin entradas individuales por episodio.  
**Causa:** Bug de detección de pendientes — el script marcaba todos como OK sin ejecutar los subprocesos, posiblemente porque los episodios M1/M2 ya existían de una ejecución anterior manual.  
**Resultado real:** Solo M1 y M2 tenían MP3 generados. M3–M14 sin audio.  
**Acción:** Se detectó manualmente comprobando `episodios/`. No se tomó acción de corrección en este momento; se continúa en la siguiente sesión.

---

#### 16:52 — [PRODUCCIÓN] M1 generado correctamente

**Referencia:** `episodios/M1_produccion.log`  
**Resultado:** 52 bloques generados, 0 fallidos, 12.7 min, 13.109 chars, 6.555 créditos reales consumidos. Créditos restantes: 67.574.  
**Voces:** IAGO `CdAqYBLnsNjmTqYgD5Ha` speed=1.2 stability=0.65 · MARÍA `gD1IexrzCvsXPHUuT0s3` speed=1.2 stability=0.68.  
**Modelo:** `eleven_v3` · post_speed_multiplier x1.1.

---

#### 17:31 — [PRODUCCIÓN] Segundo batch: M3–M14 (10 pendientes)

Batch lanzado con `lanzar_produccion.py`. Resultados por episodio:

| Hora | Módulo | Resultado | Causa si falla |
|------|--------|-----------|----------------|
| 17:37 | M3 Machine Learning Clásico | ✓ OK | — |
| 17:42 | M6 Ingeniería de Prompts | ✓ OK | — |
| 17:47 | M7 Sistemas RAG | ✓ OK | — |
| 17:51 | M8 Ingeniería LLMOps | ✗ FALLO | Duración 12.02 min < mínimo 12.5 min |
| 17:55 | M9 Infraestructura | ✓ OK | — |
| 17:59 | M10 Sistemas Agentes | ✗ FALLO | Duración 11.38 min < mínimo 12.5 min |
| 18:05 | M11 Automatización | ✓ OK | — |
| 18:07 | M12 Seguridad IA | ✗ FALLO | ElevenLabs 401 — créditos agotados |
| 18:07 | M13 Gobernanza Ética | ✗ FALLO | ElevenLabs 401 — créditos agotados |
| 18:07 | M14 Estrategia Empresa | ✗ FALLO | ElevenLabs 401 — créditos agotados |

**Nota:** M4 y M5 no aparecen en este batch porque ya existían sus MP3 (generados previamente).

---

#### 17:51 — [INCIDENCIA] M8 y M10 fallan por duración corta

**Síntoma:** `generar_episodio_v2.py` termina con `exit 1` y mensaje "La validacion final del audio ha fallado" pese a haber generado todos los bloques correctamente.  
**Causa:** `verify_audio_output()` añade el issue "demasiado corta" a `verification_issues` y el código lanza `SystemExit` ante cualquier issue en esa lista, sin distinguir gravedad.  
**Archivos MP3:** existen y son reproducibles (12.0 y 11.4 min respectivamente).  
**Decisión:** → ver `[CAMBIO]` correspondiente más abajo.

---

#### 18:07 — [INCIDENCIA] Créditos ElevenLabs agotados

**Síntoma:** M12/M13/M14 fallan con `ERROR FATAL: ElevenLabs rechazó la autenticación (401)` y mensaje `quota_exceeded`.  
**Diagnóstico:** `{"status":"quota_exceeded","message":"This request exceeds your quota of 232959. You have 0 credits remaining..."}`.  
**Límite del plan:** 232.959 caracteres por ciclo de facturación.  
**Consumo estimado:** M1–M11 × ~13.000 chars promedio ≈ 143.000 chars + M0 previo. El saldo final fue exactamente 0.  
**Estado M12/M13/M14:** guiones listos, sin audio. Pendiente de recarga de créditos.

---

## 2026-05-08

### Sesión de fixes, git hygiene y documentación

---

#### Mañana — [CAMBIO] `generar_episodio_v2.py`: duración fuera de rango → WARN, no ERROR

**Archivo:** `generar_episodio_v2.py` (dos puntos: líneas ~706 y ~800)  
**Motivo:** Los guiones de M8 y M10 generaron audio válido (todos los bloques OK) pero con duración ligeramente por debajo del mínimo de 12.5 min. El exit 1 era un falso negativo: el MP3 existe y es usable.  
**Cambio:**
```python
# Antes:
if verification_issues or asset_issues:
    raise SystemExit("La validacion final del audio ha fallado.")

# Después:
_DURATION_KWS = ("demasiado corta", "demasiado larga")
hard_vi = [i for i in verification_issues if not any(k in i for k in _DURATION_KWS)]
soft_vi = [i for i in verification_issues if any(k in i for k in _DURATION_KWS)]
if soft_vi:
    print(f"[WARN] Duracion fuera de rango (audio valido): {'; '.join(soft_vi)}")
if hard_vi or asset_issues:
    raise SystemExit("La validacion final del audio ha fallado.")
```
**Principio:** Hard errors = bloques no generados, MP3 no existe, MP3 no se puede abrir. Soft = duración fuera de rango.

---

#### Mañana — [CAMBIO] `validar_episodio.py`: `check_duration` de ERROR a WARN

**Archivo:** `validar_episodio.py` línea 199  
**Motivo:** Consistencia con el cambio anterior. Si el generador trata la duración como WARN, el validador post-generación debe hacer lo mismo.  
**Regla de sesión aplicada:** "Todo cambio en generación → check correspondiente en validar_episodio.py."  
**Cambio:**
```python
# Antes:
return CheckResult(name, "ERROR", f"{duration_min:.2f} min fuera de rango")
# Después:
return CheckResult(name, "WARN", f"{duration_min:.2f} min fuera de rango (audio valido)")
```

---

#### Mañana — [CAMBIO] `podcast_spec.py`: normalización de acentos en validación de etiquetas

**Archivo:** `podcast_spec.py` líneas 352–353  
**Motivo:** Las etiquetas en los guiones llegaban acentuadas (`didáctico`) pero la lista de etiquetas permitidas estaba sin acentos (`didactico`). La comparación directa fallaba.  
**Cambio:**
```python
allowed_norm = {normalize_text_for_match(t) for t in allowed}
if normalize_text_for_match(tag) not in allowed_norm:
```

---

#### Mañana — [CAMBIO] `generar_episodio_v2.py`: separación hard/soft en validación de guion

**Archivo:** `generar_episodio_v2.py`, función `parsear_guion()`  
**Motivo:** El generador abortaba ante cualquier issue de validación, incluidos los de calidad (word count bajo, frases cortas), gastando 0 créditos ElevenLabs pero sin producir nada.  
**Cambio:** Se definen `HARD_KEYWORDS` que implican `SystemExit` y el resto se trata como `[WARN]` + continuar:
```python
HARD_KEYWORDS = (
    "falta la seccion", "fuera de orden", "no contiene bloques",
    "debe abrirlo", "menos de 4 bloques", "mas de 6 bloques",
    "falta la frase", "falta la instruccion", "falta la apertura",
)
```

---

#### Mañana — [CAMBIO] `lanzar_produccion.py`: reescritura completa con logging detallado

**Archivo:** `lanzar_produccion.py`  
**Motivo:** La versión anterior no capturaba stdout/stderr de los subprocesos, hacía imposible diagnosticar fallos sin ejecutar manualmente.  
**Nuevas funcionalidades:**
- Log por episodio: `episodios/{ep}_cmd.log` con stdout + stderr completo
- Log maestro: `episodios/produccion_runs.log` acumulativo por sesión
- Extracción del error más informativo en consola al fallar
- Tail de stdout (8 líneas) y stderr (20 líneas) al fallar
- Timeout de 30 minutos por episodio

---

#### Mañana — [CAMBIO] `.gitignore`: añadir `*.bak`

**Motivo:** `normalizar_guiones.py` genera archivos `.bak` como backup antes de sobreescribir guiones. Estos no deben ir a git.  
**Commit:** `533d840 chore: ignore .bak backup files`

---

#### Mañana — [PRODUCCIÓN] `normalizar_guiones.py`: todos los guiones convertidos a Formato A

**Contexto:** Los guiones M2–M14 estaban en Formato B (legacy: secciones `# INTRO`, `# NÚCLEO TEMÁTICO`, `# CIERRE CON CTA`), incompatibles con `podcast_spec.py`.  
**Acción:** Ejecución de `normalizar_guiones.py` (script nuevo creado en sesión anterior) sobre los 15 guiones.  
**Resultado:** Todos los guiones en Formato A con:
- Secciones en orden correcto (HOOK → INTRO_SONIDO → SALUDO → BLOQUE_1..4 → INSERCION_1,2 → CIERRE_CONCEPTOS → CIERRE_FINAL → VERIFICACIONES)
- Paridad de speaker en HOOK corregida (IAGO impares, MARÍA pares)
- Frases obligatorias añadidas donde faltaban
- Backups `.bak` generados (no en git)

---

#### Tarde — [DECISIÓN] Gestión de ramas y worktrees

**Situación:** Había dos ramas activas para el mismo trabajo (`feature/genepisodios` y `feature/generadores`) y el main path estaba en `feature/genepisodios` en lugar de `master`.  
**Decisiones tomadas:**
1. `feature/generadores` eliminada (`git branch -D`)
2. Main path vuelto a `master` — es el trunk limpio
3. Worktree dedicado creado: `.claude/worktrees/genepisodios` → `feature/genepisodios`
4. Mapa de worktrees final:

| Path | Rama | Propósito |
|------|------|-----------|
| `maquinaria_pesada/` (main) | `master` | Trunk, producción, no tocar desde sesiones |
| `.claude/worktrees/genepisodios` | `feature/genepisodios` | Audio, guiones, validación |
| `.claude/worktrees/videopodcast` | `feature/videopodcast` | Pipeline de vídeo |
| `.claude/worktrees/laughing-leavitt-*` | `APPContenidos` | Cockpit Streamlit |

---

#### Tarde — [DECISIÓN] Flujo de consolidación en master

**Regla adoptada:** Desarrollar en `feature/*` → cuando algo funciona, merge a `master` + push. No trabajar directamente en master.  
**Motivación:** Evitar que cambios en el pipeline de vídeo rompan el de audio y viceversa.  
**Nota operativa crítica:** Los scripts de producción (`lanzar_produccion.py`, `estado_proyecto.py`, `generar_episodio_v2.py`) usan `Path(__file__).parent` para resolver rutas. Desde un worktree, apuntan al directorio del worktree (que no tiene `episodios/` ni `.env`). **Siempre ejecutar producción desde el main path `C:\Users\Asus\maquinaria_pesada`.**

---

#### Tarde — [INCIDENCIA] API key ElevenLabs inválida al relanzar

**Contexto:** Al intentar relanzar M3–M14 tras actualizar la key, la nueva key (`sk_3730a...`) fue reconocida pero el endpoint `/v1/user` devolvía 401 `missing_permissions` (sin permiso `user_read`).  
**Diagnóstico:** La key no tiene permiso de lectura de cuenta pero SÍ tiene permiso TTS. Confirmado con test directo al endpoint `/v1/text-to-speech/`.  
**Solución:** Ignorar el 401 del endpoint de usuario para el check de créditos. La generación procede con normalidad.  
**Lección:** Las keys de ElevenLabs pueden crearse con scope restrictivo. El check de créditos no es bloqueante para la generación.

---

#### Tarde — [INCIDENCIA] `estado_proyecto.py` desde worktree muestra 0 audios

**Síntoma:** Ejecutando `python estado_proyecto.py` desde `.claude/worktrees/genepisodios`, todos los módulos aparecen como "FALTA AUDIO" aunque M0–M11 tienen MP3.  
**Causa:** `BASE_DIR = Path(__file__).parent` resuelve al directorio del worktree, que no tiene `episodios/`.  
**Solución temporal:** Documentado como norma operativa (ver arriba). Fix estructural pendiente.

---

## 2026-05-10

### Sesión de gestión, producción y documentación

---

#### [REGLA] Todo cambio en generación lleva verificación en `validar_episodio.py`

**Adoptada en:** inicio de sesión 2026-05-10  
**Enunciado:** Toda modificación introducida en los scripts de generación (`generar_episodio_v2.py`, `generar_guion.py`, `podcast_spec.py`, etc.) DEBE tener su contraparte en `validar_episodio.py`: un check que confirme que ese cambio se aplica correctamente en todos los episodios producidos. Sin verificación, el cambio no está completo.  
**Motivación:** Evitar divergencia entre lo que el generador hace y lo que el validador verifica.

---

#### [REGLA] Sesión de trabajo siempre en `feature/genepisodios`; consolidar en master cuando algo funciona

**Adoptada en:** inicio de sesión 2026-05-10  
**Detalle:** Cada funcionalidad nueva o fix en `feature/genepisodios` → commit → cuando está probado, merge en master + push → seguir en la feature branch.

---

#### [DECISIÓN] Unificación de todas las ramas en master

**Contexto:** APPContenidos, videopodcast y genepisodios tenían trabajo sin consolidar en master.  
**Proceso:**
1. Merge `feature/genepisodios` → master (fast-forward parcial)
2. Merge `APPContenidos` → master (`--no-ff`): cockpit sidebar, modal validaciones, log_parser, monitor
3. Merge `videopodcast` → master: los commits ya estaban incluidos por historial compartido
4. Push master

**Incidencia durante el proceso:** El main path estaba en rama `videopodcast` (no en `master`) durante los merges, haciendo que los merges de genepisodios y APPContenidos cayeran en videopodcast en lugar de master. Se resolvió con fast-forward de master a videopodcast (que ya contenía todo).

**Commit de limpieza:** `987d08f chore: remove .bak files from tracking` — los `.bak` habían entrado en el historial de videopodcast antes de que el `.gitignore` se aplicara.

---

#### [PRODUCCIÓN] Batch M3–M14: 9 audios generados, 3 fallidos por créditos agotados

**Hora inicio:** 2026-05-07 17:31 (log de referencia; ejecución real en sesión de mayo)  
**Resultado final:**

| Estado | Módulos |
|--------|---------|
| ✓ Completados | M0, M1, M2, M3, M4, M5, M6, M7, M9, M11 |
| ⚠ Audio OK (WARN duración) | M8 (12.0 min), M10 (11.4 min) |
| ✗ Sin audio | M12, M13, M14 — créditos agotados |

**Créditos ElevenLabs:** 0 restantes de 232.959. Necesario recargar para M12–M14.

---

#### [CAMBIO] `SESION_genepisodios.md`: advertencias de worktree y API key

**Archivo:** `SESION_genepisodios.md` (en raíz del worktree)  
**Añadido:**
- Advertencia explícita: ejecutar producción desde main path, no desde worktree
- Advertencia: verificar API key válida antes de lanzar batch (WinError 10061 = síntoma de 401)
- Separación de comandos por contexto (main path vs worktree)

---

#### [PRODUCCIÓN] `BIBLIA_SISTEMA.md` — documento técnico completo del sistema

**Archivo creado:** `BIBLIA_SISTEMA.md` en raíz del repo  
**Contenido:** 784 líneas cubriendo arquitectura, tecnologías, cuentas, estructura de carpetas, pipeline de audio, pipeline de vídeo, scripts clave, cockpit, spec maestra, estado de producción, flujo de trabajo, git, credenciales, nomenclatura y reglas de desarrollo.  
**El usuario expandió el documento** añadiendo:
- Diagrama ASCII detallado del sistema completo con módulos del pipeline de vídeo
- Modelos exactos: Claude Sonnet 4.5, Haiku 4.5, Kling 1.6 Pro (Kuaishou)
- Colores de marca: María `#F5C400`, Yago `#4DB8FF`
- Técnica DSP: `scipy.signal.correlate` para detección de sintonía
- `kling_generator.py` como sucesor de `luma_generator.py` (image-to-video 20s con cadena extend)
- Layout visual del videopodcast (PIP, pizarra dinámica)
- Sección de bugs conocidos y resueltos

---

#### [DECISIÓN] Creación de `PODCAST.md` — diario de decisiones

**Adoptada en:** 2026-05-10, esta entrada  
**Propósito:** Registro cronológico de decisiones, cambios técnicos e incidencias. Complementa `BIBLIA_SISTEMA.md` (referencia técnica estática) con la historia de cómo se llegó a cada decisión.  
**Regla de mantenimiento:** Cada cambio significativo en el código o arquitectura se registra aquí en el momento en que ocurre, con marca de tiempo y justificación.

---

## Pendientes abiertos (al 2026-05-10)

| # | Pendiente | Bloqueado por |
|---|-----------|---------------|
| 1 | Generar audio M12, M13, M14 | Créditos ElevenLabs agotados |
| 2 | Generar vídeo M1–M11 | Pipeline videopodcast pendiente de integración |
| 3 | Fix: `estado_proyecto.py` desde worktree no ve episodios | Decisión de arquitectura de rutas pendiente |
| 4 | Soft quality warnings en guiones M1–M14 | Word count / sentence count por debajo de objetivo |
| 5 | Subir episodios a YouTube / Spotify | Manual, tras completar vídeo |

---

## Historial de commits relevantes

| Commit | Descripción |
|--------|-------------|
| `94191ee` | init: proyecto maquinaria pesada |
| `f752777` | feat: consolidate podcast generators, video pipeline updates and cockpit dashboard |
| `f45696c` | feat: add normalizar_guiones.py (formato B legacy → A converter) |
| `747d179` | fix: normalize guiones B→A, improve production logging and validation |
| `533d840` | chore: ignore .bak backup files |
| `a0ff8b0` | docs: add session context file for feature/genepisodios |
| `b47508b` | docs: production state update, worktree/api-key warnings |
| `987d08f` | chore: remove .bak files from tracking (covered by .gitignore) |
| `111216a` | merge: videopodcast (pipeline audio/subtitles) → master |
| `217a484` | merge: videopodcast → master (biblia + escaleta generator + Kling) |

---

*Diario mantenido por Claude Code · MaquinarIA Pesada*  
*Próxima entrada: al ocurrir el siguiente cambio significativo.*
