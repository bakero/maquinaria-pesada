# PRIMERPODCAST.md — Diario de producción de MaquinarIA Pesada

Registro cronológico de decisiones técnicas, cambios de código y resolución de problemas
durante la creación del sistema automatizado de producción de podcast.

> **Regla:** cada decisión relevante queda documentada aquí con marca de tiempo.
> Este archivo es un diario vivo — se actualiza en cada sesión de trabajo.

---

## FASE 1 — Diseño del sistema (anterior a 2026-05-07)

### Concepto del proyecto

**MaquinarIA Pesada** es un podcast de IA generado automáticamente para el máster.
Dos presentadores con voces ElevenLabs: **IAGO** (voz masculina, episodios impares)
y **MARÍA** (voz femenina, episodios pares). 15 módulos (M0–M14).

### Stack tecnológico definido

| Componente | Elección | Motivo |
|---|---|---|
| TTS | ElevenLabs eleven_v3 | Calidad conversacional superior |
| Montaje audio | pydub + ffmpeg | Control total sobre silencios y mezcla |
| ffmpeg | WinGet (Gyan.FFmpeg) | Encoder MP3 completo; CapCut no lo tiene |
| LLM guiones | OpenAI GPT-4.1 | Calidad + contexto largo para PDFs |
| Hardware | ASUS Zenbook S 14 UX5406SA | Equipo del proyecto |

### Voces ElevenLabs — configuración definitiva

| Parámetro | IAGO | MARÍA |
|---|---|---|
| voice_id | `CdAqYBLnsNjmTqYgD5Ha` | `gD1IexrzCvsXPHUuT0s3` |
| stability | 0.65 | 0.68 |
| style | 0.0 | 0.0 |
| speed | 1.20 | 1.20 |
| post_speed_multiplier | 1.10 | 1.10 |
| Modelo | eleven_v3 | eleven_v3 |

**Nota:** `use_speaker_boost` desactivado — no disponible en eleven_v3.

---

## FASE 2 — Construcción del motor y guiones (2026-05-07)

### 2026-05-07 — Rama feature/genepisodios

Se crea la rama de desarrollo dedicada al motor de generación de audio.
**Regla de sesión establecida:** todo cambio en generación debe tener su
contraparte en `validar_episodio.py`. Sin verificación = cambio incompleto.

---

### 2026-05-07 — Decisión: nomenclatura de ficheros

**Problema:** la nomenclatura antigua `EP-MOD000_guion_etiquetas_v1.txt` /
`EP-MOD000_MaquinarIaPesada_final.mp3` no escalaba ni permitía identificar
el módulo y el tipo de fichero a golpe de vista.

**Decisión adoptada:** nueva nomenclatura `M{N}_{tipo}_{titulo}`:

| Tipo | Patrón | Ejemplo |
|---|---|---|
| PDF fuente | `M{N}_T_{Titulo}.pdf` | `M3_T_Machine_Learning_Clasico.pdf` |
| Guión | `M{N}_T_{Titulo}.txt` | `M3_T_Machine_Learning_Clasico.txt` |
| Audio episodio | `M{N}_E_{Titulo}.mp3` | `M3_E_Machine_Learning_Clasico.mp3` |
| Vídeo episodio | `M{N}_V_{Titulo}.mp4` | `M3_V_Machine_Learning_Clasico.mp4` |

**Código afectado:** `estado_proyecto.py` — patrones de regex actualizados:
```python
PDF_RE   = re.compile(r"^M(\d+)_T_(.+)\.pdf$",  re.IGNORECASE)
GUION_RE = re.compile(r"^M(\d+)_T_(.+)\.txt$",  re.IGNORECASE)
AUDIO_RE = re.compile(r"^M(\d+)_E_(.+)\.mp3$",  re.IGNORECASE)
VIDEO_RE = re.compile(r"^M(\d+)_V_(.+)\.mp4$",  re.IGNORECASE)
```

El modo `--codex` deriva el ep_code del guión automáticamente:
```python
ep_code = guiones[mod].stem.replace("_T_", "_E_", 1)
# M3_T_Machine_Learning_Clasico → M3_E_Machine_Learning_Clasico
```

---

### 2026-05-07 — Reglas de guión definitivas

Se fijan las reglas que rigen todos los guiones del máster:

**Longitud:** 1900–2100 palabras por episodio (~14–16 min de audio).

**Pronunciación y ortografía:**
- `IA` → siempre `I.A.` (con puntos) para que el TTS deletree correctamente
- Siglas → deletreadas en español + nombre completo la primera vez.
  Ejemplo: *"ele ele emes, grandes modelos de lenguaje"*
- Anglicismos → mantener en inglés + traducción al español.
  Ejemplo: *"machine learning, o aprendizaje automático"*

**Etiquetas TTS permitidas (solo 5):**
`[conversacional]` `[explicativo]` `[directo]` `[ironico]` `[serio]`

**Estructura:**
- IAGO abre episodios **impares** (M1, M3, M5…)
- MARÍA abre episodios **pares** (M0, M2, M4…)
- Sin referencias al próximo módulo en el cierre
- Frase fija de cierre (obligatoria, siempre igual):
  > *"Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada.
  > Siguenos para nuevos capitulos donde la I.A. crea contenido sobre I.A."*

---

### 2026-05-07 — Fix: `podcast_spec.py` — sentence_count con números decimales

**Problema:** la función `sentence_count()` contaba puntos en números decimales
(`360.000`, `GPT-5.4`) y en siglas (`I.A.`) como separadores de frase, produciendo
falsos positivos que hacían fallar la validación de bloques.

**Solución:** sustitución de placeholders antes del split:
```python
_SENT_PLACEHOLDER = "\x01"

def sentence_count(text):
    plain = remove_leading_tag(text)
    # Proteger decimales: 360.000 → 360\x010\x010
    plain = re.sub(r"(\d)\.(\d)",
        lambda m: m.group(1) + _SENT_PLACEHOLDER + m.group(2), plain)
    # Proteger siglas: I.A. → I\x01A\x01
    plain = re.sub(r"\b([A-ZÁÉÍÓÚÜ])\.\s*([A-ZÁÉÍÓÚÜ]\.?)",
        lambda m: m.group().replace(".", _SENT_PLACEHOLDER), plain)
    parts = [p.strip() for p in re.split(r"[.!?]+", plain) if p.strip()]
    return len(parts)
```

**Nota técnica:** se usaron funciones lambda (no strings de reemplazo) porque
`\x01` en strings de reemplazo de `re.sub` no es válido en Python.

---

### 2026-05-07 — Nuevo script: `normalizar_guiones.py`

**Propósito:** convertir guiones Formato B (legacy) → Formato A (estándar actual).

**Capacidades:**
- Detecta automáticamente el formato: A, A_hybrid, B, unknown
- Corrige la paridad de speaker en el HOOK (IAGO impares, MARÍA pares)
- Añade frases obligatorias faltantes (frase de cierre)
- Genera backup `.bak` antes de sobreescribir
- Modo `--dry-run` para previsualizar sin modificar

**Resultado:** guiones M0–M14 todos convertidos y normalizados a Formato A.

---

### 2026-05-07 — Nuevo script: `lanzar_produccion.py`

**Propósito:** lanzador de producción masiva con logging robusto.

**Características:**
- Descubre episodios pendientes dinámicamente desde `estado_proyecto.py`
- Log por episodio: `episodios/{ep_code}_cmd.log` (stdout + stderr completo)
- Log maestro acumulativo: `episodios/produccion_runs.log`
- Extracción automática del hint de error más informativo en consola
- Timeout de 30 minutos por episodio
- Opción `--ep` para episodio individual, `--dry-run` para previsualizar

**Uso:**
```bash
python lanzar_produccion.py              # todos los pendientes
python lanzar_produccion.py --ep M3_E_Machine_Learning_Clasico
python lanzar_produccion.py --dry-run
```

---

### 2026-05-07 — Mejora: `generar_episodio_v2.py` — validación hard vs soft

Se introduce la distinción entre errores que bloquean la generación y
advertencias que no la bloquean:

| Tipo | Acción | Ejemplos |
|---|---|---|
| **Hard error** | `SystemExit` — detiene todo | Secciones obligatorias ausentes, speaker incorrecto, frase de cierre faltante |
| **Soft warning** | `[WARN]` + continúa | Word count fuera de rango, sentence count alto |

---

### 2026-05-07 — Mejora: `podcast_spec.py` — normalización de acentos en etiquetas

La validación de etiquetas TTS ahora normaliza acentos antes de comparar
(`normalize_text_for_match`), evitando falsos negativos por variantes
con/sin tilde en los guiones.

---

## FASE 3 — Primer episodio completo y arranque del pipeline (2026-05-10)

### 2026-05-10 — Primer episodio terminado: M0 Introducción Estratégica

**Hito:** se completa el primer episodio de audio del podcast.

- Guión: `Guiones/M0_T_Introduccion_Estrategica.txt`
- Audio: `episodios/EP-MOD000_MaquinarIaPesada_final.mp3` *(nomenclatura antigua)*
- Duración: dentro del rango objetivo (13–17 min)

**Incidencias durante la generación:**
1. Los créditos de ElevenLabs se agotaron a mitad de la generación (bloque ~32).
   → Solución: recarga de créditos y relanzamiento del proceso.
2. La pronunciación de `IA` resultaba distorsionada con la notación `i a` (dos palabras).
   → Decisión: cambiar a `I.A.` (mayúsculas con puntos) para forzar el deletreo correcto.
3. La música de fondo no se estaba aplicando en la primera versión.
   → Se verificó que `PODCAST_MASTER_SPEC.md` tiene configuradas las rutas de música
   y sintonía, y que `generar_episodio_v2.py` las aplica automáticamente.

**Nota:** el audio de M0 tiene la nomenclatura antigua (`EP-MOD000_*`).
Cuando Codex regenere M0, producirá `M0_E_Introduccion_Estrategica.mp3`
con la nomenclatura nueva.

---

### 2026-05-10 — Decisión de workflow: Claude Code genera, Codex ejecuta

**División de responsabilidades definida:**

| Rol | Herramienta | Tarea |
|---|---|---|
| Generar y ajustar guiones | Claude Code | Lee PDFs, aplica reglas, valida calidad |
| Ejecutar audio en modo churrera | Codex | Corre `generar_episodio_v2.py` en serie |
| Verificar resultado | Claude Code | Revisa logs, valida episodios |

**Flujo de trabajo:**
```
Claude Code: python estado_proyecto.py          → ver estado completo
Claude Code: python estado_proyecto.py --assets → verificar música/logos
Codex:       python lanzar_produccion.py        → generar todos los audios pendientes
Claude Code: python estado_proyecto.py          → verificar resultado
```

---

### 2026-05-10 — Decisión: `estado_proyecto.py` como fuente dinámica de verdad

El script `estado_proyecto.py` es la fuente única que determina qué hay que generar.
**No se hardcodean rutas ni listas de episodios en Codex.**

Modos de uso:
```bash
python estado_proyecto.py              # tabla completa PDF/guión/audio/vídeo
python estado_proyecto.py --pendiente  # solo módulos incompletos
python estado_proyecto.py --codex      # comandos listos para ejecutar
python estado_proyecto.py --assets     # verifica música, sintonía, logos
```

La función `print_estado_resumen()` se llama al final de cada script de producción
(`generar_guion.py`, `generar_episodio_v2.py`, `producir_episodio.py`,
`generar_episodio.py`) para mostrar el estado actualizado tras cada ejecución.

---

### 2026-05-10 — Estado de producción al cierre de sesión

| Módulo | PDF | Guión | Audio | Vídeo |
|--------|-----|-------|-------|-------|
| M0 | ✓ | ✓ | EP-MOD000 (viejo) | — |
| M1–M14 | ✓ | ✓ | — | — |

→ `python estado_proyecto.py --codex` reporta **15 episodios pendientes** (M0–M14).

---

### 2026-05-10 — Problema: ELEVENLABS_API_KEY no heredada por Codex

**Síntoma:** `setx ELEVENLABS_API_KEY sk_...` guarda la clave en el registro
de Windows, pero la sesión de Codex (entorno sandbox) devuelve `NOT_SET`.

**Causa:** `setx` aplica solo a sesiones futuras del shell del sistema;
los entornos sandbox de Codex no heredan variables del registro en tiempo real.

**Solución adoptada:** crear fichero `.env` en la raíz del proyecto.
`generar_episodio_v2.py` ya tiene `from dotenv import load_dotenv; load_dotenv()`
al inicio, por lo que lee `.env` automáticamente sin modificar el código.

```bash
# PowerShell — crear .env
Add-Content -Path "C:\Users\Asus\maquinaria_pesada\.env" `
  -Value "ELEVENLABS_API_KEY=tu_key_aqui" -Encoding UTF8
```

**Verificación:**
```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('ELEVENLABS_API_KEY','NOT_SET')[:8]+'...')"
# Debe mostrar: sk_8936d...
```

---

### 2026-05-10 — Pendientes al cerrar sesión

- [ ] Crear `.env` con `ELEVENLABS_API_KEY` y verificar que Codex la lee
- [ ] Ejecutar `python lanzar_produccion.py` para los 15 episodios pendientes
- [ ] Verificar episodios generados con `python estado_proyecto.py`
- [ ] Generar episodios de vídeo (rama `videopodcast`, fuera del scope actual)

---

## Archivos clave del proyecto

| Archivo | Rol |
|---|---|
| `PODCAST_MASTER_SPEC.md` | Fuente única de verdad: rutas, voces, reglas |
| `podcast_spec.py` | Validador y parser de guiones |
| `generar_guion.py` | Genera guiones con GPT-4.1 desde PDF |
| `generar_episodio_v2.py` | Motor de audio: ElevenLabs + montaje + verificación |
| `lanzar_produccion.py` | Lanzador masivo con logging robusto |
| `estado_proyecto.py` | Estado de producción; descubre pendientes dinámicamente |
| `normalizar_guiones.py` | Convierte guiones formato B → A |
| `validar_episodio.py` | Validador de episodios ya generados |
| `producir_episodio.py` | Pipeline completo guión + audio en un comando |

---

*Última actualización: 2026-05-10 — sesión de arranque de pipeline Codex*
