# VIDEOPODCAST.md · Diario del proyecto MaquinarIA Pesada

> Bitácora cronológica de todas las decisiones, cambios técnicos y aprendizajes
> del sistema de producción automática del videopodcast. Cada entrada lleva
> marca de tiempo y, cuando aplique, el commit Git asociado.
>
> **Inicio del diario:** 2026-05-09 13:30 (consolidación retrospectiva)
> **Mantenedor:** bkasero@gmail.com · rama activa `videopodcast` (consolidaciones a `master`)

---

## ÍNDICE

1. [Resumen ejecutivo del proyecto](#resumen-ejecutivo)
2. [Bitácora cronológica](#bitácora-cronológica)
3. [Estado actual](#estado-actual)
4. [Pendientes vivos](#pendientes-vivos)
5. [Reglas de producción consolidadas](#reglas-de-producción-consolidadas)
6. [Inventario de assets](#inventario-de-assets)

---

## Resumen ejecutivo

**Objetivo**: producir 14 episodios (M0..M14) de un videopodcast educativo
sobre IA con dos presentadores ficticios (María, Yago), íntegramente
generados con IA. Resultado por episodio: MP4 1080p para YouTube + MP3
para Spotify, 14-17 min de duración.

**Stack actual** (consolidado a 2026-05-09):
- Generación guion: Claude Sonnet 4.5
- TTS: ElevenLabs `eleven_v3` multi-speaker (Iago/María calibrados)
- Transcripción: Whisper local (medium o large-v3)
- Generación clips estudio: Kling 1.6 Pro vía API oficial Kuaishou (JWT)
- Composición video: ffmpeg + PIL (overlays en frames PNG)
- Detección sintonía: cross-correlation scipy
- Lip-sync: pendiente (Sync.so cuando llegue API key)

**Arquitectura visual decidida (Layout C, 2026-05-08)**:
- Por defecto: clip de estudio fullscreen con presentador hablando
- Pizarra: invocada solo en bloques conceptuales (≥10s, ≥1 cada 3min)
- Cuando pizarra activa: pizarra fullscreen + PIP del presentador
  bottom-right 25% con borde amarillo CAT 4px

---

## Bitácora cronológica

### 2026-05-07 · Construcción inicial del pipeline

**Commit base anterior**: `aab2951 feat(escaleta): render desde escaleta markdown como input canonico`

Antes del inicio de este diario, en sesiones previas se había construido:
- Pipeline de video con 11 módulos (`maquinaria_pesada_pipeline/pipeline/`)
- Sistema de escaletas markdown como input canónico
- Detección de sintonía por cross-correlation con `scipy.signal.correlate`
- Generación de clips iniciales con Luma Dream Machine (descartado después)
- Catálogo inicial de 8 clips estudio (luego eliminados por marca CAT visible)
- Cockpit Streamlit (`cockpit/app.py`) para observabilidad

---

### 2026-05-08 ~10:30 · Diagnóstico del bug de subtítulos desincronizados

**Problema reportado por usuario**: subtítulos van saliendo durante la
intervención del presentador pero NO sincronizados con las palabras dichas.

**Diagnóstico**: revisión del `subtitle_generator.py` reveló que el código
usaba correctamente palabras de Whisper con timestamps reales. El problema
no estaba en los subtítulos sino en el **scene_track**: tenía 14 solapamientos
de TCs que sumaban 30s de drift acumulado entre body video y audio.

**Causa raíz**: la escaleta humana tenía intervenciones con TCs que se
solapaban (fin de N > inicio de N+1). El compositor concatenaba segmentos
sin recortar, "estirando" el body video respecto al audio.

**Decisión**: en `escaleta_to_pipeline.py`, recortar `seg.end = next.start`
para forzar track monotónico.

**Resultado**:
- Antes: drift=30.15s, 14 solapamientos
- Después: drift=0.00s, 0 solapamientos, 42 segmentos monotónicos

---

### 2026-05-08 ~11:00 · Subtítulos blancos

**Decisión usuario**: subtítulos 100% blancos, sin highlight de keywords
en amarillo.

**Cambio técnico**: `subtitle_generator.py · _highlight()` retorna texto
sin modificar. Mantener firma para compatibilidad.

---

### 2026-05-08 ~11:15 · Diagnóstico problemas con clips Luma

**Problemas reportados por usuario**:
1. Mismas escenas repetidas en muchos momentos
2. En clips de Yago aparecía una mujer que NO era María
3. Plano cerrado evidencia desincronización de boca con audio
4. Clips muy cortos (5s) → muchos cambios de cámara

**Decisión usuario**: generar 18 clips nuevos con duración >20s, mejor
calidad y consistencia facial.

**Listado solicitado**:
- 4 escenas María sola hablando
- 4 escenas Yago solo hablando
- 5 escenas two-shot María activa
- 5 escenas two-shot Yago activo

---

### 2026-05-08 ~11:30 · Decisión: Layout C (PIP corner)

**Pregunta clave**: ¿cómo conviven estudio + pizarra en pantalla?

**Opciones discutidas**:
- A: split 50/50
- B: side panel 65/35
- C: pizarra fullscreen + PIP esquinero del presentador

**Decisión usuario**: **Layout C** con presentador en PIP bottom-right.

**Geometría aprobada**:
- PIP_WIDTH_RATIO = 0.25 (25% del ancho = 480px en 1080p)
- PIP_ASPECT = 16:9 (270px alto)
- PIP_MARGIN = 30px
- PIP_BORDER_PX = 4
- PIP_BORDER_COLOR = `#F5C400` (amarillo CAT)

**Implementación**: `video_compositor.py · _build_body_from_track`. Cuando
seg.type == "pizarra" y trae `pip_source`, compone:
1. Background pizarra fullscreen
2. PIP del presentador 480×270 bottom-right con borde amarillo

---

### 2026-05-08 ~12:00 · Reglas de pizarra v2

**Decisión usuario**:
- Pizarra mínimo 15s una vez activada (aunque la intervención sea más corta)
- Elementos visuales nuevos cada 4 segundos
- ≥1 pizarra cada 3 minutos del podcast como mínimo
- Contenido de pizarra DEBE estar vinculado al párrafo dicho
- **NUNCA poner texto del guion en la pizarra** (sólo datos, gráficos, imágenes, memes)

**Implementación**: system prompt v2 en `escaleta_generator.py` con sección
"PROHIBIDO ABSOLUTAMENTE EN LA PIZARRA" y ejemplos GOOD/BAD.

**Refs nuevas (sin marca CAT)**: Maria.png, Yago.png, establishing.png,
studio.png — el usuario las regeneró sin la marca comercial.

---

### 2026-05-08 ~12:30 · Cambio a Kling 1.6 Pro

**Decisión usuario**: descartar Luma (alucinaba personajes) y migrar a
Kling 1.6 Pro.

**Primera implementación**: `kling_generator.py` contra fal.ai (proxy
con FAL_KEY).

**Cambio posterior**: usuario tenía credenciales oficiales Kuaishou
(KLING_ACCESS_KEY + KLING_SECRET_KEY). Refactor a API oficial con JWT
HS256 firmado, regenerado por petición (exp 30min).

**Endpoints**:
- `POST /v1/videos/image2video` (base 10s)
- `POST /v1/videos/video-extend` (chain +5s)
- `GET /v1/videos/image2video/{task_id}` (polling)

**Coste validado**:
- Pro 10s base: 8 unidades = $0.78 con pack -30%
- Pro 5s extend: 6 unidades = $0.59

**Commit**: `b7c1ac4 feat(kling): API oficial Kuaishou con JWT + extend para clips de 20s`

---

### 2026-05-08 ~14:00 · Primera tanda Kling: 4 Maria, refs viejas

**Eventos**:
1. Submitté 18 clips en paralelo. 4 Maria completaron (4×$2.80 con extends 20s = ~$11.20).
2. Las restantes fallaron con 429 (rate limit Kling agresivo).
3. **Issue crítico**: las 4 Marias generadas tenían marca **CAT** visible
   en una caja amarilla del fondo.

**Causa raíz**: el `git push` de los refs nuevos no se hizo hasta las 23:24.
Durante el batch, GitHub raw servía la versión ANTIGUA de los refs (con CAT).

**Decisión**: borrar los 4 Maria + library wipe + push refs + relanzar.

**Aprendizaje documentado**: verificar MD5 local↔GitHub raw antes de cada
batch Kling. Añadido a `BIBLIA_SISTEMA.md` lecciones aprendidas.

---

### 2026-05-08 ~23:30 · Sistema de persistencia + QA + recovery

**Causa motivadora**: en la sesión cara perdimos ~$15-21 en Kling con solo
4 clips usables. ~26 tareas exitosas quedaron huérfanas (pagadas pero no
descargadas) por dos causas:
1. Submits sin persistencia → proceso muere y se pierden task_ids
2. Sin QA: clips truncados/corruptos pasaban silenciosamente

**Decisión usuario**: "deja todo listo para que cada cosa que se genere
en kling la tengamos en nuestro sistema en cuanto se genere. Instala
políticas de QA para cada cosa que generes".

**Implementación**:

1. `pipeline/kling_tasks.py` (NUEVO): KlingTaskTracker append-only JSONL
   con fsync por línea. Eventos: `submit`, `complete`, `fail`, `download`,
   `qa`, `register`. Registro ANTES del poll → recovery-friendly.

2. `pipeline/qa.py` (NUEVO): 7 verificadores
   - `check_kling_clip`: tamaño + moov + duración + aspect 16:9
   - `check_escaleta_md`: bloques, ivs, PIZARRA SI/NO, no truncado
   - `check_scene_track`: monotonía + drift vs audio
   - `check_audio_structure`: duración, sintonía, content range
   - `check_video_final`: tamaño, duración ~ audio, resolución
   - `check_library_integrity`: cada slug tiene archivo + integridad
   - `check_srt`: min chunks + ningún chunk muy largo

3. `tools/kling_reconcile.py` (NUEVO): rescata tareas huérfanas. Por cada
   slug huérfano: poll, descarga, QA, register, todo loggeado.

4. `kling_generator.py` integrado: `generate_concept` y
   `generate_batch_parallel` ahora loguean al tracker + QA antes de register.

**Commit**: `ac1c61b feat(qa+tracker): persistencia tasks Kling + QA en cada artefacto`

**Recuperación inmediata**: rescaté `studio_yago_solo_v1` (10s base) de
una task huérfana sin gastar créditos extra.

---

### 2026-05-09 ~00:00 · Diagnóstico rate-limit Kling

**Problema**: tras varias tandas con 429 cascade, decisión de probar
submit aislado de 1 sola tarea de 5s (el más barato) → 429 PERSISTENTE
incluso tras 6 reintentos con backoff hasta 120s.

**Verificación**: tareas viejas en estado `succeed`, no hay nada
pendiente bloqueando.

**Conclusión**: el plan tenía cuota diaria/mensual agotada. El 429 con
submit aislado significa quota cap, no rate limit clásico.

**Recomendación al usuario**: esperar reset de cuota (24h UTC+8) antes
de relanzar.

---

### 2026-05-09 ~10:30 · Decisión: clips de 10s (no 20s)

**Decisión usuario**: "viendo lo generado, 10s es suficiente para cada
escena". Y: "no voy a gastarme más dinero. Habrá que hacer los cambios
y el lipsync sobre lo que salga de Kling".

**Implicación de coste**:
- 14 clips × 10s × 0.8 unidades/s = **112 unidades = ~$15.68**
  (en lugar de 280 unidades = ~$39.20 si fueran 20s)

**Pack recargado**: $14 × 2 trial = $28 = 200 unidades. Suficiente con
buffer (88 unidades sobrantes).

---

### 2026-05-09 ~10:45 · Generación final del catálogo

**Resultado**:
- 13 clips faltantes generados secuencialmente en 81 min
- 0 errores
- 4 Maria solo (21.2s con extends, generadas antes a 20s)
- 4 Yago solo (10.4s)
- 5 two-shot M-active (10.4s)
- 5 two-shot Y-active (10.4s)
- **Total: 18 clips · 100% QA OK · ~$10.14 esta tanda**

**Inventario library**:
```
studio_maria_solo_v1..v4          (4 × 21.2s)
studio_yago_solo_v1..v4           (4 × 10.4s)
studio_two_m_active_v1..v5        (5 × 10.4s)
studio_two_y_active_v1..v5        (5 × 10.4s)
```

---

### 2026-05-09 ~11:30 · Análisis del render v3 LLM

**Problema observado**: tras render con escaleta v3 (LLM regenerada), el
LLM seguía poniendo texto del guion en la pizarra (preguntas literales
como "¿Qué es la IA?", "¿De dónde viene?" como `concept_card`).

**Decisión usuario**: "Texto del guion en pizarra esto debe estar
corregido al generar la escaleta. Porque en la escaleta debe estar el
contenido completo de cada frame del video".

**Implementación QA semántico**:
- `qa.py · check_escaleta_semantic`: detecta n-gramas solapando >40%
  con texto del guion + patrón "?" en highlight_quote/concept_card
- Auto-heal: si QA falla, lanza segundo pass a Claude para corregir
  solo los overlays malos manteniendo el resto

**Resultado QA sobre escaleta v3**: detectados 3 overlays mal puestos
(preguntas literales).

**Commit**: `12080e5 feat(escaleta): v2 streaming + 32k tokens + PIZARRA: SI/NO marcado`

---

### 2026-05-09 ~12:00 · Cambio fundamental de estrategia: estudio dominante

**Decisión usuario**: "todo el video es con ventana pequeña abajo del
estudio. Pero eso obliga a tener mucho contenido visual en la pizarra.
La idea era alternar pizarra con videos del estudio. solo una pizarra
cada 3 minutos. Y la pizarra dura toda al menos 10 segundos, hasta que
termine la intervención del presentador".

**Cambio fundamental**:
- ANTES (v3 LLM): pizarra ~87% del tiempo, fullscreen
- AHORA (v4+): estudio fullscreen como modo dominante, pizarra como
  excepción ≥10s sólo en bloques conceptuales

**Plan**: rehacer escaleta de los primeros 5 min a mano para validar el
patrón antes de extenderlo al episodio completo.

**Drafts producidos**:
- `escaletas/EP-MOD000_escaleta_5min_draft.md` (v4) — primer intento
- `escaletas/EP-MOD000_5min_draft_v5.md` (v5) — coords pixel + clip-by-clip
- `escaletas/REVIEW_v5_audit.md` — auditoría
- `tools/render_5min_v6.py` (v6) — script Python ejecutable

---

### 2026-05-09 ~12:50 · Generación variantes reverse

**Decisión**: usar `tools/reverse_clips.py --all` para duplicar el
catálogo gratis con `_rev`. Cuando la cámara orbita en una dirección en
el original, el reverse equivale a una toma con la cámara orbitando en
la otra dirección.

**Resultado**: 18 reverses generados con ffmpeg en ~3 min. Catálogo total:
**36 variantes** (18 base + 18 reverse).

---

### 2026-05-09 ~13:00 · Render v6 5min con escaleta handcrafted

**Estructura v6**:
- 5 pizarras totales · 125.5s pizarra (40.9%) · 181.5s estudio (59.1%)
- Patrón rítmico: pizarra → respiro estudio → pizarra (nunca encadenadas)
- Coords pixel exactas por overlay
- Clip slug + mode (normal/reverse) + segs explícitos por sub-segmento
- Cuts solo cuando duración exige (Maria solos 21s cubren la mayoría
  de intervenciones de un solo speaker sin cortes)

**Optimización de cortes** (decisión usuario):
- v5: 50 sub-segmentos · 36 cuts internos
- v6: ~25 sub-segmentos · ~13 cuts internos
- Maria 1.1 (16.93s): de 4 cuts a 0 (1 clip Maria solo cubre toda)
- Maria 1.2 (15.13s): de 4 cuts a 0
- Maria 4.1 (40.25s): de 5 cuts a 1 (2 Maria solos chained)

**Pizarras seleccionadas (5)**:
1. HOOK 1.1 (12.9s): stat_cards 88%/12%
2. BLOQUE_1 4.1 (25.3s): timeline_visual de los 2 inviernos IA
3. BLOQUE_1 4.3 (31.6s): hierarchy 3 factores + stat_cards
4. BLOQUE_2 5.1 (30s): hierarchy IA⊃ML⊃DL⊃LLMs
5. BLOQUE_2 5.3 (25.7s): two_column_compare estrecha vs general

**Ejecución**: `tools/render_5min_v6.py` se ejecuta en ~2 min,
genera scene_track + scene_timeline directamente sin pasar por
escaleta_parser/escaleta_to_pipeline (rotación heurística).

**Validación visual** (frames extraídos):
- t=11: pizarra HOOK con stat_card 88% + PIP María ✓
- t=14: stat_card 12% entra ✓
- t=150: hierarchy "3 FACTORES · CÓMPUTO · DATOS · ARQUITECTURA" ✓
- t=200: estudio fullscreen Yago close-up ✓
- t=250: hierarchy "TAXONOMÍA IA / IA / ML / DL / LLMs" + stat_card "ML patrones" ✓
- t=290: two_column_compare "IA ESTRECHA vs IA GENERAL" ✓

**Issues menores detectados**:
- name_tag no aparece en segmentos studio fullscreen (sólo en pizarra).
  Razón técnica: overlays se hornean en frames PNG que sólo se usan como
  background en pizarra. Pendiente de decidir si fix con `drawtext`/overlay
  burned o se acepta así.

---

### 2026-05-09 ~13:30 · Inicio del diario VIDEOPODCAST.md

**Decisión usuario**: "cada decisión que tomemos debe quedar documentada.
Crea en la raíz del proyecto un archivo VIDEOPODCAST.md donde vayas
documentando toda esta conversación y las decisiones que tomamos".

**Implementación**: este archivo. Consolidación retrospectiva de la
sesión + diario continuo a partir de aquí.

---

## Estado actual

### Catálogo de clips (36 variantes)

```
Studio
├── 4 Maria solo (21.2s)              + 4 reverses
├── 4 Yago solo (10.4s)               + 4 reverses
├── 5 two-shot M-active (10.4s)       + 5 reverses
└── 5 two-shot Y-active (10.4s)       + 5 reverses
   = 18 base + 18 reverse = 36 total
```

### Escaletas

- `escaletas/EP-MOD000_escaleta.md` — escaleta v3 LLM regenerada (con
  bugs de texto-en-pizarra detectados; pendiente reescritura)
- `escaletas/EP-MOD000_5min_draft_v5.md` — v5 handcrafted con pixel coords
- `tools/render_5min_v6.py` — v6 ejecutable (canónica para los primeros 5 min)

### Renders

- `Videos/M0_V_Introduccion_Estrategica_preview.mp4` — preview 310s
  (5:10) con escaleta v6, 50.5MB. Pendiente revisión visual del usuario.

### Sistema de QA y persistencia

- `outputs/kling_tasks.jsonl` — journal append-only de todas las tareas
  Kling submitidas (recovery-friendly)
- 7 verificadores QA en `pipeline/qa.py`
- `tools/kling_reconcile.py` para rescatar huérfanas

### Commits recientes (rama `master`)

```
ac1c61b feat(qa+tracker): persistencia tasks Kling + QA en cada artefacto
61db6df fix(kling): retry 429 + spacing 8s + fallback secuencial
b7c1ac4 feat(kling): API oficial Kuaishou con JWT + extend para clips de 20s
12080e5 feat(escaleta): v2 streaming + 32k tokens + PIZARRA: SI/NO marcado
1b55211 fix(scene_track): verificar existencia fisica del .mp4 al resolver pool
8b2284d fix(stat_card): extraer valor con sufijo (%/M/K/B/€/$) en vez de truncar
d131594 feat(video): layout C (PIP corner) + sync drift fix + Kling generator
6f7d512 docs: BIBLIA_SISTEMA.md actualizada al estado 8-may-2026
```

### Costes Kling acumulados

| Tanda | Clips OK | Coste real | Notas |
|---|---|---|---|
| 1ª (4 Maria 20s con extends) | 4 | ~$11.20 | Refs viejas con CAT, descartados |
| Recovery yago_v1 (10s base) | 1 | $0 | Rescatado de huérfano |
| Final (13 clips 10s) | 13 | ~$10.14 | Refs limpias, todos QA OK |
| **Total facturado** | | **~$21** | + reverses gratis con ffmpeg |

**Saldo restante**: ~88 unidades = ~$8.62 de buffer para futuras
regeneraciones puntuales.

---

## Pendientes vivos

1. **Validación visual del v6 5min** por usuario antes de extender al
   episodio completo
2. **Decidir name_tag en estudio fullscreen**: añadir overlay con
   `drawtext`/PNG burned o aceptar como está (~30 min de cambio)
3. **Extender v6 al resto del episodio** (5:07 → 13:33)
4. **Lip-sync con Sync.so**: pendiente `SYNC_API_KEY` del usuario.
   Plan inicial: aplicar selectivamente a segs studio fullscreen
   (~50s/episodio = ~$12 todo el podcast)
5. **Episodios M1..M14**: producir en cadena con `lanzar_produccion.py`
   reutilizando el catálogo de clips (zero coste Kling adicional)

---

## Reglas de producción consolidadas

### El audio es la verdad temporal
Nunca cambiar el texto de las intervenciones desde el video pipeline; el
audio ya está fijado.

### Cortes de plano
- Sólo en pausas naturales (puntos, fines de idea)
- Nunca a mitad de frase
- No repetir clip dentro de la misma intervención
- Maximizar uso de cada clip antes de cambiar
- Para intervenciones <3s: usar two-shot con speaker activo coincidente

### Pizarra (Layout C)
- Estudio fullscreen es el default
- Pizarra sólo cuando aporta (≥1 cada 3min, ≥10s, hasta fin de intervención)
- Elementos nuevos cada 4s
- NO citas literales del guion (NO `highlight_quote` con preguntas/frases)
- Datos, gráficos, imágenes, memes, comparaciones — sí

### Layout pixel-exacto
- TOP_RIGHT: name_tag (siempre del speaker activo)
- BOTTOM_RIGHT_SAFE: PIP del presentador (cuando pizarra)
- BOTTOM_CENTER: subtítulos blancos auto-Whisper
- Una sola pieza visual por zona en cada momento

### Identidad de marca
| Color | Hex | Uso |
|---|---|---|
| Amarillo CAT | `#F5C400` | María, datos, borde PIP, identidad |
| Azul | `#4DB8FF` | Yago, técnico, micrófonos del set |
| Rojo | `#CC2200` | Regulación, alertas, EU AI Act |
| Gris | `#888888` | Información secundaria |
| Blanco subs | `#E8E8E8` | Subtítulos |

---

## Inventario de assets

### Archivos clave
- `.env` (gitignored): API keys ANTHROPIC, ELEVENLABS, KLING_ACCESS_KEY, KLING_SECRET_KEY
- `escaletas/`: markdown por episodio
- `episodios/`: MP3 generado por episodio
- `Videos/`: MP4 final + biblioteca clips
- `Videos/escenas_biblioteca/refs/`: imágenes referencia Kling (Maria, Yago, establishing, studio) — sin marca CAT
- `Videos/escenas_biblioteca/estudio/`: 18 clips Kling + 18 reverses
- `Videos/escenas_biblioteca/_concepts_index.json`: 1614 conceptos PDF M0..M14
- `Videos/escenas_biblioteca/_scenes_index.json`: catálogo persistente library

### Cuentas activas
- Anthropic Console: saldo activo
- ElevenLabs: voces clonadas para María/Yago
- Kling AI / Kuaishou Cloud: pack $14×2 (200 unidades · ~88 buffer restante)
- GitHub público `bakero/maquinaria-pesada`

### Documentación complementaria
- `BIBLIA_SISTEMA.md` — referencia técnica completa del sistema
- `PODCAST_MASTER_SPEC.md` — reglas normativas del guion
- `VOICE_CONFIG_REFERENCE.md` — configuración voces ElevenLabs
- `cockpit/PLAN.md` — plan del cockpit Streamlit
- `escaletas/REVIEW_v5_audit.md` — auditoría v5

---

# DIARIO ABIERTO · A PARTIR DE AQUÍ

> Cada nueva decisión, cambio técnico o aprendizaje añade una entrada
> con fecha + hora + descripción. Mantener orden cronológico inverso
> (las más recientes arriba) o directo (cronológico) — a elegir.

## 2026-05-09 13:35 · Diario VIDEOPODCAST.md creado

Consolidación retrospectiva completada. A partir de ahora, cada cambio
queda registrado aquí. Siguiente entrada esperada: feedback del usuario
sobre el render v6 de los primeros 5 min.
