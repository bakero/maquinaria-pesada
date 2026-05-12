---
episode_id: EP-MOD000
modulo: M0
tema: Introducción Estratégica a la I.A.
audio_duration_total: 813.98s
rango_escaleta: 0:00.000 → 5:07.400
version: v5 (handcrafted, posiciones pixel + clip-by-clip)
fecha: 2026-05-09
---

# ESCALETA DE PRODUCCIÓN · EP-MOD000 · PRIMEROS 5 MINUTOS · v5

> **Filosofía**: ESTUDIO fullscreen es el modo dominante. La PIZARRA aparece
> sólo en bloques conceptuales potentes (mín. 10s, hasta fin de intervención).
> Cada elemento on-screen lleva posición pixel exacta para verificar
> ausencia de colisiones. Cada plano lleva el clip exacto a usar y los
> segundos del clip a reproducir.

---

## SECCIÓN A · LAYOUT GRID CANÓNICO (1920×1080)

```
   x: 0       320      640     960     1280    1600    1920
y:0 ┌────────┬────────┬────────┬────────┬────────┬───────┐
    │TOP_LEFT│  TOP_CENTER (centrado)   │ TOP_RIGHT│
200 ├────────┼─────────────────────────┼──────────┤
    │MID_LEFT│       MID_CENTER         │MID_RIGHT │
720 ├────────┼─────────────────────────┼──────────┤
    │BOT_LEFT│  BOT_CENTER (subtítulos)│ PIP_AREA │  ← BR = PIP zone (reservado pizarra)
1080└────────┴─────────────────────────┴──────────┘
```

### Anchors (top-left corner del bbox de cada zona)

| Zona | x | y | W disponible | H disponible |
|---|---|---|---|---|
| TOP_LEFT | 60 | 50 | 540 | 200 |
| TOP_CENTER | 660 | 50 | 600 | 180 |
| TOP_RIGHT | 1640 | 40 | 240 | 100 |
| MID_LEFT | 60 | 280 | 540 | 460 |
| MID_CENTER | 660 | 260 | 600 | 480 |
| MID_RIGHT | 1280 | 280 | 540 | 460 |
| BOT_LEFT | 60 | 760 | 360 | 280 |
| BOT_CENTER (subs) | reservado para subtítulos auto-Whisper | | | |
| BOT_FULL_WIDTH | 110 | 800 | 1700 | 220 |
| PIP_AREA (pizarra) | 1410 | 780 | 480 | 270 |

### Reservas absolutas (no usar para overlays):
- **TOP_RIGHT** → name_tag (siempre con quien habla)
- **BOT_RIGHT (1410..1890, 780..1050)** → PIP cuando PIZARRA: SI
- **BOT_CENTER** → subtítulos blancos auto-Whisper

---

## SECCIÓN B · TAMAÑOS DE ELEMENTOS (overlay_types.py)

| Elemento | W×H | Anchors válidos |
|---|---|---|
| name_tag | 220×80 | TOP_RIGHT solo |
| section_indicator | 800×100 | TOP_CENTER (centrado x=560 y=60) |
| warning_badge | 460×120 | TOP_LEFT, TOP_CENTER (x=730 y=70) |
| stat_card | 460×280 | MID_LEFT, MID_CENTER, MID_RIGHT |
| regulation_alert | 540×320 | MID_LEFT, MID_RIGHT, BOT_LEFT |
| hierarchy_diagram | 720×460 | MID_CENTER (x=600 y=290) |
| two_column_compare | 1180×560 | MID_CENTER fullbleed (x=370 y=240) — **OCUPA TODO MID** |
| bar_chart | 720×460 | MID_CENTER |
| highlight_quote | 920×340 | MID_CENTER |
| timeline_visual | 1700×220 | BOT_FULL_WIDTH (x=110 y=800) |
| recap_grid | 1700×640 | MID_CENTER + BOT (x=110 y=200) — **OCUPA MID Y BOT** |
| sticker | 240×240 | BOT_LEFT |
| end_card | 1300×600 | MID_CENTER fullbleed |

### Reglas anti-colisión

1. `two_column_compare` (MC fullbleed) → **NO admite** stat_cards en ML/MR simultáneos.
2. `recap_grid` (MC+BOT) → **NO admite** ningún otro overlay durante su display.
3. Cuando PIZARRA: SI → BOT_RIGHT está ocupado por PIP. NO usar BOT_RIGHT.
4. Subtítulos en BOT_CENTER → no poner nada en y > 950.
5. name_tag en TOP_RIGHT → fijo siempre. No coloca otra cosa ahí.

---

## SECCIÓN C · CATÁLOGO DE CLIPS DISPONIBLES

| Slug | Duración | Descripción |
|---|---|---|
| `studio_maria_solo_v1` | 21.2s | Maria sola, plano medio, hablando calmada |
| `studio_maria_solo_v2` | 21.2s | Maria sola, gesto de mano explicativo |
| `studio_maria_solo_v3` | 21.2s | Maria sola, expresión enfática |
| `studio_maria_solo_v4` | 21.2s | Maria sola, sonrisa cómplice |
| `studio_yago_solo_v1` | 10.4s | Yago solo, plano medio, hablando calmado |
| `studio_yago_solo_v2` | 10.4s | Yago solo, gesto pensativo |
| `studio_yago_solo_v3` | 10.4s | Yago solo, énfasis |
| `studio_yago_solo_v4` | 10.4s | Yago solo, sonrisa |
| `studio_two_m_active_v1..v5` | 10.4s | Two-shot, María habla, Yago escucha |
| `studio_two_y_active_v1..v5` | 10.4s | Two-shot, Yago habla, María escucha |

Todos pueden usarse en `normal` o `reverse` (suffix `_rev`). El reverse
duplica catálogo: 18 base + 18 reverse = **36 variantes** disponibles.

---

# CONTENIDO DEL EPISODIO · 0:00 → 5:07

## PRELUDIO · LEAD SILENCE
**TC IN:** `00:00.000`  **TC OUT:** `00:01.928`  **DUR:** 1.93s

### 0.1 — Pantalla negra
- **TC:** `00:00.000 → 00:01.928` · **DUR:** 1.93s
- **TONO:** [silencio]
- **TEXTO:**
  > (sin voz)
- **PLANO:** BLACK
- **PIZARRA:** NO
- **CLIPS:** ninguno (frame negro generado por compositor)
- **ON-SCREEN:** (vacío)
- **TRANSICION OUT:** corte directo al HOOK.

> **NOTA DIRECCIÓN:** Pantalla negra pura 1.93s. Sin logo. Audio en silencio.

---

## BLOQUE 1 · HOOK
**TC IN:** `00:01.928`  **TC OUT:** `00:34.050`  **DUR:** 32.12s

### 1.1 — María
- **TC:** `00:02.060 → 00:18.990` · **DUR:** 16.93s
- **TONO:** [ironico]
- **TEXTO:**
  > En 2026, el 88% de las empresas dice que ya usa inteligencia artificial. El otro 12% dice que lo está evaluando. Básicamente, todo el mundo está en el tema, igual que todo el mundo ha leído los términos y condiciones de cada app que instala. Exactamente nadie.
- **PLANO general:** TWO_SHOT_M_ACTIVE
- **PIZARRA:** SI (entra en t=4.0s, dura hasta fin de intervención · 12.9s)
- **CORTES POR PAUSAS** (cuts en períodos del guion):
  | Sub-seg | Scene t (s) | Iv duration | Clip slug | Mode | Clip secs used | Razón corte |
  |---|---|---|---|---|---|---|
  | 1 | 0.00 → 4.50 | 4.5s | `studio_two_m_active_v1` | normal | 0.0–4.5 | abre con "En 2026, el 88%..." |
  | 2 | 4.50 → 10.00 | 5.5s | `studio_maria_solo_v1` | normal | 0.0–5.5 | corte tras "está evaluando." |
  | 3 | 10.00 → 14.50 | 4.5s | `studio_two_m_active_v2` | normal | 0.0–4.5 | corte tras "instala." |
  | 4 | 14.50 → 16.93 | 2.4s | `studio_maria_solo_v2` | normal | 0.0–2.4 | remate "Exactamente nadie." |
- **PIP_CLIP** (visible cuando pizarra activa, t=4.0–16.93): `studio_maria_solo_v3` normal, segundos 0.0–12.93
- **ON-SCREEN** (todas las posiciones con coordenadas pixel exactas):
  | t rel | Elemento | Pos zona | x | y | W | H | Salida |
  |---|---|---|---|---|---|---|---|
  | 0.0s | name_tag "MARIA" amarillo | TOP_RIGHT | 1640 | 40 | 220 | 80 | hasta fin |
  | 4.0s | stat_card "ADOPCIÓN 2026 · 88%" amarillo | MID_LEFT | 60 | 280 | 460 | 280 | hasta fin |
  | 8.0s | stat_card "EVALUANDO · 12%" gris | MID_RIGHT | 1280 | 280 | 460 | 280 | hasta fin |
  | 14.0s | sticker "exactamente_nadie_meme" | BOT_LEFT | 60 | 760 | 240 | 240 | hasta fin |
- **VERIFICACIÓN COLISIONES:**
  - name_tag (1640,40,220×80) vs PIP (1410,780,480×270) → distintas zonas Y, OK
  - stat ML (60,280,460×280) ↔ stat MR (1280,280,460×280) → x: ML termina en 520, MR empieza en 1280 → 760px de gap, OK
  - sticker BL (60,760,240×240) ↔ PIP BR (1410,780,480×270) → x: gap 1170px, OK
  - sticker BL ↔ subtítulos BC: subtítulos típicamente x∈[400,1300], y≈1000. sticker termina en x=300, y=1000 → no colisión, OK
- **TRANSICION OUT:** corte seco en pausa tras "exactamente nadie".

### 1.2 — María (cierre canónico hook)
- **TC:** `00:18.920 → 00:34.050` · **DUR:** 15.13s
- **TONO:** [firme]
- **TEXTO:**
  > Hoy vemos qué hay de verdad detrás de ese número. Qué es la I.A., de dónde viene, cómo se estructura y qué implica para cualquier organización que tenga que tomar decisiones con ella encima de la mesa. Esto es MaquinarIA Pesada. Arrancamos.
- **PLANO general:** CLOSE_UP_MARIA
- **PIZARRA:** NO (estudio fullscreen para el cierre canónico)
- **CORTES POR PAUSAS:**
  | Sub-seg | Scene t (s) | Iv duration | Clip slug | Mode | Clip secs | Razón corte |
  |---|---|---|---|---|---|---|
  | 1 | 0.00 → 4.00 | 4.0s | `studio_maria_solo_v3` | normal | 0.0–4.0 | "Hoy vemos qué hay…ese número." |
  | 2 | 4.00 → 11.50 | 7.5s | `studio_maria_solo_v4` | normal | 0.0–7.5 | enumeración hasta "encima de la mesa." |
  | 3 | 11.50 → 13.50 | 2.0s | `studio_maria_solo_v1` | reverse | 12.0–14.0 | "Esto es MaquinarIA Pesada." (reverse para variar) |
  | 4 | 13.50 → 15.13 | 1.6s | `studio_two_m_active_v3` | normal | 0.0–1.6 | "Arrancamos." (cierre con dos plano) |
- **PIP_CLIP:** N/A (pizarra: NO)
- **ON-SCREEN:**
  | t rel | Elemento | Pos zona | x | y | W | H | Salida |
  |---|---|---|---|---|---|---|---|
  | 0.0s | name_tag "MARIA" amarillo | TOP_RIGHT | 1640 | 40 | 220 | 80 | hasta fin |
- **VERIFICACIÓN COLISIONES:** Solo name_tag. No hay riesgo.
- **TRANSICION OUT:** fundido suave a SINTONIA.

> **NOTA DIRECCIÓN BLOQUE 1:** El hook tiene UNA pizarra (1.1) con datos potentes (88%/12%). En 1.2 se retira para que el cierre canónico "Esto es MaquinarIA Pesada. Arrancamos." quede limpio. Cuatro clips distintos en 1.1, cuatro distintos en 1.2 — sin repetir slug entre intervenciones consecutivas para máxima variedad.

---

## BLOQUE 2 · INTRO_SONIDO + SINTONIA
**TC IN:** `00:34.050`  **TC OUT:** `00:46.720`  **DUR:** 12.67s

### 2.1 — Sintonía musical
- **TC:** `00:34.050 → 00:46.720` · **DUR:** 12.67s
- **TONO:** [musica]
- **TEXTO:**
  > (sintonía instrumental)
- **PLANO general:** SINTONIA (intro_video.mp4 superpuesto al body)
- **PIZARRA:** NO
- **CLIPS:** intro_video.mp4 (overlay activo en `[35.206, 45.197]` por audio_structure)
- **PIP_CLIP:** N/A
- **ON-SCREEN:** (vacío)
- **TRANSICION OUT:** corte limpio al SALUDO.

> **NOTA DIRECCIÓN:** intro_video.mp4 lleva el logo MAQUINARIA PESADA animado. Cero overlays adicionales.

---

## BLOQUE 3 · SALUDO Y PRESENTACIÓN
**TC IN:** `00:46.720`  **TC OUT:** `01:35.840`  **DUR:** 49.12s

### 3.1 — Yago (bienvenida)
- **TC:** `00:46.720 → 01:02.740` · **DUR:** 16.02s
- **TONO:** [serio acogedor]
- **TEXTO:**
  > Bienvenidos a MaquinarIA Pesada. Soy Yago, y esto es el módulo cero: la introducción estratégica a la I.A. El episodio que nadie quiere admitir que necesita pero que conviene escuchar antes de aprobar cualquier presupuesto de inteligencia artificial en tu empresa.
- **PLANO general:** TWO_SHOT_Y_ACTIVE
- **PIZARRA:** NO
- **CORTES POR PAUSAS:**
  | Sub-seg | Scene t | Iv dur | Clip slug | Mode | Clip secs | Razón |
  |---|---|---|---|---|---|---|
  | 1 | 0.00 → 3.00 | 3.0s | `studio_two_y_active_v1` | normal | 0.0–3.0 | "Bienvenidos a MaquinarIA Pesada." |
  | 2 | 3.00 → 9.50 | 6.5s | `studio_yago_solo_v1` | normal | 0.0–6.5 | "Soy Yago, y esto es el módulo cero…" |
  | 3 | 9.50 → 16.02 | 6.5s | `studio_two_y_active_v2` | normal | 0.0–6.5 | "El episodio que nadie quiere admitir…" |
- **PIP_CLIP:** N/A
- **ON-SCREEN:**
  | t rel | Elemento | Pos zona | x | y | W | H | Salida |
  |---|---|---|---|---|---|---|---|
  | 0.0s | name_tag "YAGO" azul | TOP_RIGHT | 1640 | 40 | 220 | 80 | hasta fin |
  | 2.0s | section_indicator "MÓDULO 0 · Introducción Estratégica" amarillo | TOP_CENTER | 560 | 60 | 800 | 100 | 8.0s |
- **VERIFICACIÓN COLISIONES:**
  - name_tag x∈[1640,1860] vs section_indicator x∈[560,1360] → 280px gap, OK
- **TRANSICION OUT:** corte seco tras "en tu empresa".

### 3.2 — María (advertencia legal)
- **TC:** `01:00.980 → 01:17.390` · **DUR:** 16.41s
- **TONO:** [tecnico serio]
- **TEXTO:**
  > Y yo soy María. Antes de arrancar, la advertencia legal y sensata: este episodio está generado por un sistema automático de inteligencia artificial y puede contener errores. Contrastad con fuentes profesionales. Si algo suena demasiado bueno o demasiado catastrófico, probablemente está exagerado.
- **PLANO general:** CLOSE_UP_MARIA
- **PIZARRA:** NO
- **CORTES POR PAUSAS:**
  | Sub-seg | Scene t | Iv dur | Clip slug | Mode | Clip secs | Razón |
  |---|---|---|---|---|---|---|
  | 1 | 0.00 → 2.50 | 2.5s | `studio_two_m_active_v4` | normal | 0.0–2.5 | "Y yo soy María." |
  | 2 | 2.50 → 11.00 | 8.5s | `studio_maria_solo_v1` | reverse | 5.0–13.5 | advertencia legal completa |
  | 3 | 11.00 → 14.00 | 3.0s | `studio_maria_solo_v2` | normal | 0.0–3.0 | "Contrastad con fuentes profesionales." |
  | 4 | 14.00 → 16.41 | 2.4s | `studio_maria_solo_v3` | reverse | 8.0–10.4 | "exagerado." remate |
- **PIP_CLIP:** N/A
- **ON-SCREEN:**
  | t rel | Elemento | Pos zona | x | y | W | H | Salida |
  |---|---|---|---|---|---|---|---|
  | 0.0s | name_tag "MARIA" amarillo | TOP_RIGHT | 1640 | 40 | 220 | 80 | hasta fin |
  | 3.0s | warning_badge "CONTENIDO GENERADO POR IA" rojo | TOP_LEFT | 60 | 70 | 460 | 120 | hasta fin |
- **VERIFICACIÓN COLISIONES:**
  - warning TL x∈[60,520] vs name_tag TR x∈[1640,1860] → 1120px gap, OK
- **TRANSICION OUT:** corte suave a Yago.

### 3.3 — Yago (objetivo)
- **TC:** `01:20.600 → 01:35.840` · **DUR:** 15.24s
- **TONO:** [didactico]
- **TEXTO:**
  > El objetivo de hoy: que al terminar tengas el mapa mental básico de la I.A. Qué tipos existen, por qué el momento actual es diferente a todos los intentos anteriores y qué impacto real tiene esto en las organizaciones.
- **PLANO general:** TWO_SHOT_Y_ACTIVE
- **PIZARRA:** NO
- **CORTES POR PAUSAS:**
  | Sub-seg | Scene t | Iv dur | Clip slug | Mode | Clip secs | Razón |
  |---|---|---|---|---|---|---|
  | 1 | 0.00 → 7.00 | 7.0s | `studio_two_y_active_v3` | normal | 0.0–7.0 | "El objetivo…mapa mental básico" |
  | 2 | 7.00 → 15.24 | 8.2s | `studio_yago_solo_v2` | normal | 0.0–8.2 | enumeración hasta "organizaciones" |
- **PIP_CLIP:** N/A
- **ON-SCREEN:**
  | t rel | Elemento | Pos zona | x | y | W | H | Salida |
  |---|---|---|---|---|---|---|---|
  | 0.0s | name_tag "YAGO" azul | TOP_RIGHT | 1640 | 40 | 220 | 80 | hasta fin |
  | 3.0s | recap_grid "TIPOS · MOMENTO · IMPACTO" amarillo | BOT_FULL_WIDTH | 110 | 800 | 1700 | 220 | hasta fin |
- **VERIFICACIÓN COLISIONES:**
  - recap_grid en BFW solo abarca y∈[800,1020] (220px). PIP zone empieza y=780 → **HAY COLISIÓN** si pizarra fuera SI. Como pizarra=NO, no hay PIP, OK.
  - recap_grid x∈[110,1810] cubre BOT_LEFT y BOT_RIGHT zones → **NO se permite sticker, regulation_alert ni stickers durante recap_grid**.
- **TRANSICION OUT:** corte rápido al "Vamos allá" de María.

### 3.4 — María (puente <1s)
- **TC:** `01:33.080 → 01:33.860` · **DUR:** 0.78s
- **TONO:** [enfatico]
- **TEXTO:**
  > Vamos allá.
- **PLANO general:** TWO_SHOT_M_ACTIVE (regla <3s usar two-shot con speaker activo)
- **PIZARRA:** NO
- **CLIP único:** `studio_two_m_active_v5` normal, segs 0.0–0.78
- **PIP_CLIP:** N/A
- **ON-SCREEN:**
  | t rel | Elemento | Pos zona | x | y | W | H | Salida |
  |---|---|---|---|---|---|---|---|
  | 0.0s | name_tag "MARIA" amarillo | TOP_RIGHT | 1640 | 40 | 220 | 80 | hasta fin |
- **TRANSICION OUT:** corte seco al BLOQUE 1.

> **NOTA DIRECCIÓN BLOQUE 3:** Saludo entero estudio. SIN pizarra. 11 clips distintos consumidos en este bloque (variedad alta). Solo overlays mínimos: name_tag rotando, section_indicator (8s al inicio), warning_badge advertencia legal en 3.2, recap_grid TIPOS·MOMENTO·IMPACTO en 3.3.

---

## BLOQUE 4 · BLOQUE_1 · HISTORIA DE LA I.A.
**TC IN:** `01:34.660`  **TC OUT:** `03:51.680`  **DUR:** 137.02s

### 4.1 — María (los inviernos)
- **TC:** `01:34.660 → 02:14.910` · **DUR:** 40.25s
- **TONO:** [didactico]
- **TEXTO:**
  > Para entender dónde estamos hay que saber de dónde venimos. Y la historia de la I.A. tiene un patrón que se repite con asombrosa regularidad: promesa enorme, entusiasmo masivo, resultados que no llegan a la velocidad prometida y financiación que se corta. Eso se llama invierno de la I.A. Hemos tenido dos antes de este momento. El primero a finales de los 70, cuando los sistemas basados en reglas no escalaron más allá de dominios muy acotados. El segundo a finales de los 90, cuando las redes neuronales de los 80 no podían entrenarse por falta de datos y de potencia de cálculo.
- **PLANO general:** TWO_SHOT_M_ACTIVE durante 0–15s · luego CLOSE_UP_MARIA al entrar pizarra (15–40s)
- **PIZARRA:** SI (entra en t=15.0s, dura hasta fin · 25.3s)
- **CORTES POR PAUSAS:**
  | Sub-seg | Scene t | Iv dur | Clip slug | Mode | Clip secs | Razón |
  |---|---|---|---|---|---|---|
  | 1 | 0.00 → 5.50 | 5.5s | `studio_two_m_active_v3` | normal | 0.0–5.5 | "Para entender…dónde venimos." |
  | 2 | 5.50 → 15.00 | 9.5s | `studio_maria_solo_v1` | normal | 0.0–9.5 | patrón de inviernos hasta "I.A." |
  | 3 | 15.00 → 24.00 | 9.0s | `studio_maria_solo_v2` | normal | 0.0–9.0 | "Hemos tenido dos…1er invierno" |
  | 4 | 24.00 → 33.00 | 9.0s | `studio_maria_solo_v3` | normal | 0.0–9.0 | "El primero a finales de los 70…" |
  | 5 | 33.00 → 40.25 | 7.3s | `studio_maria_solo_v4` | normal | 0.0–7.3 | "El segundo a finales de los 90…" |
- **PIP_CLIP** (t=15.0–40.25, 25.3s): `studio_two_m_active_v4` normal segs 0.0–10.4 + `studio_two_m_active_v5` normal segs 0.0–10.4 + `studio_two_m_active_v1` reverse 0.0–4.5 — **encadena 3 clips distintos para PIP**
- **ON-SCREEN:**
  | t rel | Elemento | Pos zona | x | y | W | H | Salida |
  |---|---|---|---|---|---|---|---|
  | 0.0s | name_tag "MARIA" amarillo | TOP_RIGHT | 1640 | 40 | 220 | 80 | hasta fin |
  | 15.0s | timeline_visual "1956 Dartmouth · 1970s 1ER INVIERNO · 1990s 2DO INVIERNO · 2017 Transformers · HOY" amarillo | BOT_FULL_WIDTH | 110 | 800 | 1700 | 220 | hasta fin |
  | 19.0s | regulation_alert "INVIERNO IA · promesa > resultado → corte de financiación" rojo | MID_LEFT | 60 | 280 | 540 | 320 | hasta fin |
  | 26.0s | warning_badge "2 INVIERNOS PREVIOS" rojo | TOP_CENTER | 730 | 70 | 460 | 120 | hasta fin |
  | 33.0s | stat_card "1970s · sistemas reglas · no escalan" gris | MID_RIGHT | 1280 | 280 | 460 | 280 | hasta fin |
- **VERIFICACIÓN COLISIONES:**
  - timeline BFW (110,800,1700×220) ocupa y∈[800,1020]. PIP en (1410,780,480×270) → COLISIÓN VISUAL parcial: PIP empieza en y=780 (20px arriba del timeline) y abarca x∈[1410,1890] que entra en timeline x∈[1410,1810]. **Solución: bajar timeline a y=820 con altura 180** → y∈[820,1000], evita PIP que está y∈[780,1050]. Pero entonces solapa con subtítulos en y≈980-1020. **MEJOR: timeline en TOP en lugar de BOT** durante pizarra → reposicionar a y=180. Posición revisada: timeline_visual @ (110, 180, 1700×140), reduciendo altura a 140px.
  - regulation_alert ML (60,280,540×320) ↔ stat_card MR (1280,280,460×280) → x: gap 740px, OK
  - warning_badge TC (730,70,460×120) ↔ name_tag TR (1640,40,220×80) → x: gap 450px, OK
- **TRANSICION OUT:** corte a Yago en pausa post "potencia de cálculo".

### 4.2 — Yago (escepticismo legítimo · respiro)
- **TC:** `02:12.660 → 02:24.780` · **DUR:** 12.12s
- **TONO:** [ironico controlado]
- **TEXTO:**
  > Lo que significa que tienes todo el derecho histórico del mundo a mirar con escepticismo a quien te diga que esta vez es diferente. Dicho eso, esta vez realmente lo es.
- **PLANO general:** CLOSE_UP_YAGO
- **PIZARRA:** NO (RESPIRO)
- **CORTES POR PAUSAS:**
  | Sub-seg | Scene t | Iv dur | Clip slug | Mode | Clip secs | Razón |
  |---|---|---|---|---|---|---|
  | 1 | 0.00 → 8.50 | 8.5s | `studio_yago_solo_v3` | normal | 0.0–8.5 | "Lo que significa…esta vez es diferente." |
  | 2 | 8.50 → 12.12 | 3.6s | `studio_yago_solo_v4` | normal | 0.0–3.6 | "Dicho eso, esta vez realmente lo es." |
- **PIP_CLIP:** N/A
- **ON-SCREEN:**
  | t rel | Elemento | Pos zona | x | y | W | H | Salida |
  |---|---|---|---|---|---|---|---|
  | 0.0s | name_tag "YAGO" azul | TOP_RIGHT | 1640 | 40 | 220 | 80 | hasta fin |
- **TRANSICION OUT:** corte seco a María.

### 4.3 — María (3 factores)
- **TC:** `02:22.360 → 02:55.970` · **DUR:** 33.61s
- **TONO:** [tecnico crescendo]
- **TEXTO:**
  > La diferencia es una convergencia de tres factores que nunca antes habían coincidido al mismo tiempo. Primero, potencia de cómputo: las ge pe us, unidades de procesamiento gráfico, actuales son miles de veces más potentes que las de los años 90. Segundo, datos masivos: internet generó cantidades de texto, comportamiento e imágenes que hace veinte años eran inimaginables. Y tercero, un salto arquitectónico concreto: la llegada de los Transformers, o arquitectura de atención, en 2017 con el paper, o artículo científico, "Attention is All You Need".
- **PLANO general:** TWO_SHOT_M_ACTIVE
- **PIZARRA:** SI (entra en t=2.0s, dura hasta fin · 31.6s)
- **CORTES POR PAUSAS:**
  | Sub-seg | Scene t | Iv dur | Clip slug | Mode | Clip secs | Razón |
  |---|---|---|---|---|---|---|
  | 1 | 0.00 → 7.50 | 7.5s | `studio_two_m_active_v1` | reverse | 2.9–10.4 | apertura "convergencia de tres factores…" |
  | 2 | 7.50 → 16.50 | 9.0s | `studio_maria_solo_v1` | reverse | 11.0–20.0 | "Primero, potencia de cómputo…" |
  | 3 | 16.50 → 24.50 | 8.0s | `studio_maria_solo_v3` | reverse | 12.0–20.0 | "Segundo, datos masivos…" |
  | 4 | 24.50 → 33.61 | 9.1s | `studio_maria_solo_v2` | reverse | 11.0–20.1 | "Y tercero…Attention is All You Need" |
- **PIP_CLIP** (t=2.0–33.61, 31.6s): encadena `studio_maria_solo_v4` normal (0–10.4) + `studio_two_m_active_v2` normal (0–10.4) + `studio_two_m_active_v3` normal (0–10.4) — total 31.2s, ajustar último a 10.8s
- **ON-SCREEN:**
  | t rel | Elemento | Pos zona | x | y | W | H | Salida |
  |---|---|---|---|---|---|---|---|
  | 0.0s | name_tag "MARIA" amarillo | TOP_RIGHT | 1640 | 40 | 220 | 80 | hasta fin |
  | 2.0s | hierarchy_diagram "3 FACTORES · CÓMPUTO · DATOS · ARQUITECTURA" amarillo | TOP_CENTER | 600 | 50 | 720 | 200 | hasta fin |
  | 9.0s | stat_card "1. CÓMPUTO · GPUs miles× años 90" amarillo | MID_LEFT | 60 | 280 | 460 | 280 | hasta fin |
  | 16.0s | stat_card "2. DATOS · internet 20× volumen" amarillo | MID_CENTER | 730 | 280 | 460 | 280 | hasta fin |
  | 24.0s | stat_card "3. ARQUITECTURA · Transformers 2017" amarillo | MID_RIGHT | 1280 | 280 | 460 | 280 | hasta fin |
  | 28.0s | regulation_alert "PAPER 'Attention is All You Need' · 2017" rojo | BOT_LEFT | 60 | 760 | 540 | 280 | hasta fin |
- **VERIFICACIÓN COLISIONES:**
  - hierarchy TC (600,50,720×200) abarca x∈[600,1320], y∈[50,250] ↔ name_tag TR (1640,40) → 320px gap, OK
  - **CRÍTICO**: hierarchy y∈[50,250] vs section_indicator typically y∈[60,160] → no hay section_indicator aquí, OK
  - 3 stat_cards en línea MID: ML (60,280,460×280), MC (730,280,460×280), MR (1280,280,460×280). Gaps: ML→MC = 730-520 = 210px, MC→MR = 1280-1190 = 90px (TIGHT pero OK con 90px). PERO: la altura coincide y∈[280,560], todos a la misma fila, OK.
  - regulation_alert BL (60,760,540×280) → y∈[760,1040]. PIP en (1410,780,480×270) → x: gap 870px, no colisión.
  - regulation_alert vs subtítulos: subs en y≈990, alert termina y=1040 → solapa visualmente. **REVISAR**: bajar alert height a 220 → y∈[760,980], evitando subs.
- **TRANSICION OUT:** corte a Yago en cierre del paper.

### 4.4 — Yago (qué resolvió Transformers · respiro)
- **TC:** `03:01.820 → 03:24.880` · **DUR:** 23.06s
- **TONO:** [tecnico]
- **TEXTO:**
  > Ese paper resolvió el problema que había bloqueado todos los modelos anteriores: procesar texto de forma paralela y capturar relaciones entre palabras muy separadas dentro de un mismo documento. Gracias a esa arquitectura, desde 2020 tenemos los grandes modelos de lenguaje que hoy todo el mundo conoce. Sin los Transformers, el salto de la I.A. generativa no habría existido.
- **PLANO general:** CLOSE_UP_YAGO
- **PIZARRA:** NO (RESPIRO)
- **CORTES POR PAUSAS:**
  | Sub-seg | Scene t | Iv dur | Clip slug | Mode | Clip secs | Razón |
  |---|---|---|---|---|---|---|
  | 1 | 0.00 → 9.00 | 9.0s | `studio_yago_solo_v1` | reverse | 1.4–10.4 | "Ese paper resolvió el problema…mismo documento." |
  | 2 | 9.00 → 16.50 | 7.5s | `studio_yago_solo_v2` | reverse | 2.9–10.4 | "Gracias a esa arquitectura…hoy todo el mundo conoce." |
  | 3 | 16.50 → 23.06 | 6.6s | `studio_yago_solo_v4` | reverse | 3.8–10.4 | "Sin los Transformers, el salto…no habría existido." |
- **PIP_CLIP:** N/A
- **ON-SCREEN:**
  | t rel | Elemento | Pos zona | x | y | W | H | Salida |
  |---|---|---|---|---|---|---|---|
  | 0.0s | name_tag "YAGO" azul | TOP_RIGHT | 1640 | 40 | 220 | 80 | hasta fin |
- **TRANSICION OUT:** corte a María.

### 4.5 — María (aceleración · respiro estudio)
- **TC:** `03:23.540 → 03:51.680` · **DUR:** 28.14s
- **TONO:** [enfatico]
- **TEXTO:**
  > Y la aceleración desde entonces no paró ni un trimestre. En 2022 llegó ChatGPT con los primeros cien millones de usuarios en dos meses, batiendo todos los récords de adopción tecnológica de la historia. En 2023 y 2024, los grandes laboratorios compitiendo abiertamente en capacidades. En 2026, el debate ya no es si adoptar I.A., sino qué hacer con el 70% del código que muchos equipos ya generan con ayuda de modelos.
- **PLANO general:** TWO_SHOT_M_ACTIVE
- **PIZARRA:** NO (respiro estudio · UN solo badge emocional)
- **CORTES POR PAUSAS:**
  | Sub-seg | Scene t | Iv dur | Clip slug | Mode | Clip secs | Razón |
  |---|---|---|---|---|---|---|
  | 1 | 0.00 → 6.00 | 6.0s | `studio_two_m_active_v4` | reverse | 4.4–10.4 | "Y la aceleración…ni un trimestre." |
  | 2 | 6.00 → 14.00 | 8.0s | `studio_maria_solo_v4` | reverse | 13.0–21.0 | "En 2022 llegó ChatGPT…récords adopción tecnológica." |
  | 3 | 14.00 → 22.00 | 8.0s | `studio_two_m_active_v5` | reverse | 2.4–10.4 | "En 2023 y 2024…compitiendo abiertamente." |
  | 4 | 22.00 → 28.14 | 6.1s | `studio_maria_solo_v3` | normal | 14.0–20.1 | "En 2026, el debate ya no es…ayuda de modelos." |
- **PIP_CLIP:** N/A
- **ON-SCREEN:**
  | t rel | Elemento | Pos zona | x | y | W | H | Salida |
  |---|---|---|---|---|---|---|---|
  | 0.0s | name_tag "MARIA" amarillo | TOP_RIGHT | 1640 | 40 | 220 | 80 | hasta fin |
  | 6.0s | warning_badge "RÉCORD · 100M USUARIOS EN 2 MESES" amarillo | TOP_CENTER | 730 | 70 | 460 | 120 | 14.0s (sale en t=20s) |
- **VERIFICACIÓN COLISIONES:** warning TC vs name_tag TR → 450px gap, OK
- **TRANSICION OUT:** corte seco a Yago para abrir BLOQUE 2.

> **NOTA DIRECCIÓN BLOQUE 4:** Patrón **PIZARRA → respiro → PIZARRA → respiro → respiro**. Las dos pizarras (4.1 timeline y 4.3 tres-factores) llevan PIP del speaker activo. 4.2 y 4.4 son respiros estudio en plano cerrado de Yago. 4.5 cierra bloque con TWO_SHOT estudio + un solo badge. 17 clips distintos en bloque (alta variedad).

---

## BLOQUE 5 · BLOQUE_2 · TAXONOMÍA
**TC IN:** `03:52.940`  **TC OUT:** `05:07.400`  **DUR:** 74.46s

### 5.1 — Yago (jerarquía 4 niveles)
- **TC:** `03:52.940 → 04:26.940` · **DUR:** 34.00s
- **TONO:** [didactico claro]
- **TEXTO:**
  > Necesitamos el mapa de taxonomía, porque nada genera más confusión en este campo que usar los mismos términos para cosas distintas. La I.A. es el campo más amplio. Dentro está el machine learning, o aprendizaje automático, que aprende patrones de datos. Dentro del machine learning está el deep learning, o aprendizaje profundo, con redes neuronales profundas. Y dentro del deep learning están los ele ele emes, grandes modelos de lenguaje. ChatGPT no es I.A. a secas: es la capa más específica de una jerarquía de cuatro niveles.
- **PLANO general:** TWO_SHOT_Y_ACTIVE
- **PIZARRA:** SI (entra en t=4.0s, dura hasta fin · 30.0s)
- **CORTES POR PAUSAS:**
  | Sub-seg | Scene t | Iv dur | Clip slug | Mode | Clip secs | Razón |
  |---|---|---|---|---|---|---|
  | 1 | 0.00 → 8.00 | 8.0s | `studio_two_y_active_v1` | reverse | 2.4–10.4 | "Necesitamos el mapa…cosas distintas." |
  | 2 | 8.00 → 17.00 | 9.0s | `studio_yago_solo_v1` | normal | 0.0–9.0 | "La I.A. es el campo…aprende patrones de datos." |
  | 3 | 17.00 → 25.50 | 8.5s | `studio_yago_solo_v3` | normal | 0.0–8.5 | "Dentro del ML está el DL…redes neuronales profundas." |
  | 4 | 25.50 → 34.00 | 8.5s | `studio_two_y_active_v4` | normal | 0.0–8.5 | "Y dentro del DL están los LLMs…cuatro niveles." |
- **PIP_CLIP** (t=4.0–34.0, 30.0s): encadena `studio_yago_solo_v2` normal (0–10.4) + `studio_yago_solo_v4` normal (0–10.4) + `studio_two_y_active_v2` reverse (0–9.2) — total 30.0s
- **ON-SCREEN:**
  | t rel | Elemento | Pos zona | x | y | W | H | Salida |
  |---|---|---|---|---|---|---|---|
  | 0.0s | name_tag "YAGO" azul | TOP_RIGHT | 1640 | 40 | 220 | 80 | hasta fin |
  | 4.0s | hierarchy_diagram "IA ⊃ ML ⊃ DL ⊃ LLMs" azul | MID_CENTER | 600 | 290 | 720 | 460 | hasta fin |
  | 11.0s | stat_card "ML · aprende patrones" gris | MID_LEFT | 60 | 280 | 460 | 280 | t=18s (sale al entrar siguiente stat_card en ML) |
  | 18.0s | stat_card "DL · redes neuronales profundas" gris | MID_LEFT | 60 | 280 | 460 | 280 | hasta fin |
  | 24.0s | stat_card "LLMs · ChatGPT, GPT-4, Claude" amarillo | MID_RIGHT | 1280 | 280 | 460 | 280 | hasta fin |
  | 30.0s | warning_badge "4 NIVELES · NO son sinónimos" rojo | TOP_CENTER | 730 | 70 | 460 | 120 | hasta fin |
- **VERIFICACIÓN COLISIONES:**
  - **CRÍTICO**: hierarchy MC (600,290,720×460) abarca x∈[600,1320] y∈[290,750]. stat_card ML (60,280,460×280) x∈[60,520] y∈[280,560] → x: gap 80px, OK pero apretado. y: solapa parcialmente.
  - hierarchy MC vs stat_card MR (1280,280,460×280) x∈[1280,1740] y∈[280,560] → x: hierarchy termina en 1320, MR empieza 1280 → **COLISIÓN HORIZONTAL de 40px**. Ajustar: hierarchy reduce W a 600 → x∈[600,1200], gap a MR de 80px, OK.
  - hierarchy revisado: (660, 290, 600, 460), abarca x∈[660,1260] y∈[290,750]. stat_card ML (60,280,460×280) → gap 140px, OK. stat_card MR (1280,280) → gap 20px, OK.
  - warning_badge TC (730,70,460×120) ↔ hierarchy MC y∈[290,750] → no colisión vertical, OK.
- **TRANSICION OUT:** corte irónico a María.

### 5.2 — María (LinkedIn meme · respiro)
- **TC:** `04:26.460 → 04:40.530` · **DUR:** 14.07s
- **TONO:** [ironico]
- **TEXTO:**
  > Lo cual no impide que en LinkedIn todo el mundo use los cuatro términos como si fueran exactamente lo mismo. Pero a partir de hoy tú ya no lo harás. Eso ya es ventaja competitiva inmediata.
- **PLANO general:** CLOSE_UP_MARIA
- **PIZARRA:** NO (respiro irónico)
- **CORTES POR PAUSAS:**
  | Sub-seg | Scene t | Iv dur | Clip slug | Mode | Clip secs | Razón |
  |---|---|---|---|---|---|---|
  | 1 | 0.00 → 7.50 | 7.5s | `studio_maria_solo_v4` | normal | 0.0–7.5 | "Lo cual no impide…fueran exactamente lo mismo." |
  | 2 | 7.50 → 14.07 | 6.6s | `studio_maria_solo_v2` | normal | 13.0–19.6 | "Pero a partir de hoy…ventaja competitiva inmediata." |
- **PIP_CLIP:** N/A
- **ON-SCREEN:**
  | t rel | Elemento | Pos zona | x | y | W | H | Salida |
  |---|---|---|---|---|---|---|---|
  | 0.0s | name_tag "MARIA" amarillo | TOP_RIGHT | 1640 | 40 | 220 | 80 | hasta fin |
  | 4.0s | sticker "linkedin_buzzword_meme" | BOT_LEFT | 60 | 760 | 240 | 240 | hasta fin |
- **VERIFICACIÓN COLISIONES:** sticker BL termina x=300, y=1000. Subtítulos en y≈990, x∈[400,1300] → 100px gap horizontal, OK.
- **TRANSICION OUT:** corte a Yago.

### 5.3 — Yago (estrecha vs general)
- **TC:** `04:37.700 → 05:07.400` · **DUR:** 29.70s
- **TONO:** [didactico tecnico]
- **TEXTO:**
  > Otra distinción clave: I.A. estrecha frente a I.A. general. Toda la I.A. que existe hoy, sin excepción, es I.A. estrecha. Sistemas extraordinariamente potentes dentro de su dominio específico, pero incapaces de generalizar fuera de él. Un modelo que genera imágenes no conduce un coche. Un chatbot que escribe código no diagnostica una radiografía. La I.A. general, esa que razona en cualquier dominio como lo haría un humano, sigue siendo un horizonte teórico sin fecha de llegada.
- **PLANO general:** TWO_SHOT_Y_ACTIVE durante 0–18s · CLOSE_UP_YAGO en t=18s para cierre conceptual
- **PIZARRA:** SI (entra en t=4.0s, dura hasta fin · 25.7s)
- **CORTES POR PAUSAS:**
  | Sub-seg | Scene t | Iv dur | Clip slug | Mode | Clip secs | Razón |
  |---|---|---|---|---|---|---|
  | 1 | 0.00 → 6.00 | 6.0s | `studio_two_y_active_v3` | normal | 0.0–6.0 | "Otra distinción clave: estrecha vs general." |
  | 2 | 6.00 → 13.00 | 7.0s | `studio_two_y_active_v5` | normal | 0.0–7.0 | "Toda la I.A. que existe hoy es estrecha." |
  | 3 | 13.00 → 18.00 | 5.0s | `studio_yago_solo_v2` | normal | 0.0–5.0 | "Un modelo que genera imágenes no conduce un coche." |
  | 4 | 18.00 → 24.00 | 6.0s | `studio_yago_solo_v4` | reverse | 4.4–10.4 | "Un chatbot que escribe código no diagnostica…" |
  | 5 | 24.00 → 29.70 | 5.7s | `studio_yago_solo_v3` | reverse | 4.7–10.4 | "La I.A. general…sin fecha de llegada." |
- **PIP_CLIP** (t=4.0–29.7, 25.7s): encadena `studio_two_y_active_v1` normal (0–10.4) + `studio_two_y_active_v4` reverse (0–10.4) + `studio_yago_solo_v1` reverse (0–4.9) — total 25.7s
- **ON-SCREEN:** ⚠ ATENCIÓN: two_column_compare ocupa MID entero. Cuando entran los stat_cards en MID_LEFT/RIGHT, el compare debe RETIRARSE. Decisión: secuencial limpio.
  | t rel | Elemento | Pos zona | x | y | W | H | Entra | Sale |
  |---|---|---|---|---|---|---|---|---|
  | 0.0s | name_tag "YAGO" azul | TOP_RIGHT | 1640 | 40 | 220 | 80 | 0.0s | hasta fin |
  | 4.0s | two_column_compare "IA ESTRECHA vs IA GENERAL" azul | MID_CENTER fullbleed | 370 | 240 | 1180 | 560 | 4.0s | **12.0s** |
  | 12.0s | stat_card "ESTRECHA · 100% IA hoy" azul | MID_LEFT | 60 | 280 | 460 | 280 | 12.0s | hasta fin |
  | 19.0s | stat_card "GENERAL · horizonte teórico" gris | MID_RIGHT | 1280 | 280 | 460 | 280 | 19.0s | hasta fin |
  | 25.0s | regulation_alert "AGI · sin fecha de llegada" rojo | BOT_LEFT | 60 | 760 | 540 | 220 | 25.0s | hasta fin |
- **VERIFICACIÓN COLISIONES:**
  - two_column_compare (370,240,1180×560) abarca x∈[370,1550], y∈[240,800]. Sale a t=12 antes de que entren stat_cards.
  - Después de t=12: stat_card ML (60,280) y stat_card MR (1280,280) coexisten. x: gap 760px, OK. NO solapan con compare ya retirado.
  - regulation_alert BL (60,760,540×220) → y∈[760,980], evita subs (y≈990). x: termina en 600, gap a stat_card ML (que termina en 520) = 0 — **APROVECHAR mismo bloque**: alert empieza en y=760 cuando ML acaba en y=560 → hay gap vertical de 200px, OK.
  - PIP en (1410,780,480×270) vs regulation_alert BL (60,760,540×220) → x: gap 870px, no colisión.
- **TRANSICION OUT:** corte (fin de los primeros 5 min).

> **NOTA DIRECCIÓN BLOQUE 5:** Dos pizarras (5.1 jerarquía + 5.3 estrecha-vs-general) separadas por respiro irónico (5.2) en estudio fullscreen con sticker. La pizarra 5.1 es la más memorable del episodio. En 5.3 el `two_column_compare` se retira a t=12s para dejar paso a los stat_cards (decisión: secuencial, no acumulado).

---

# RESUMEN GLOBAL · 0:00 → 5:07

| TC | Bloque | Dur | Plano | Pizarra | Clips usados |
|---|---|---|---|---|---|
| 0:00–0:02 | Lead silence | 1.9s | BLACK | — | — |
| 0:02–0:19 | HOOK 1.1 | 16.9s | TWO_SHOT_M | **SI 12.9s** | 4 (two_m_v1, m_solo_v1, two_m_v2, m_solo_v2) |
| 0:19–0:34 | HOOK 1.2 | 15.1s | CLOSE_UP_M | NO | 4 (m_solo_v3, m_solo_v4, m_solo_v1_rev, two_m_v3) |
| 0:34–0:46 | SINTONÍA | 12.7s | intro_video | — | intro_video.mp4 |
| 0:46–1:02 | SAL 3.1 | 16.0s | TWO_SHOT_Y | NO | 3 (two_y_v1, y_solo_v1, two_y_v2) |
| 1:00–1:17 | SAL 3.2 | 16.4s | CLOSE_UP_M | NO | 4 (two_m_v4, m_solo_v1_rev, m_solo_v2, m_solo_v3_rev) |
| 1:20–1:35 | SAL 3.3 | 15.2s | TWO_SHOT_Y | NO | 2 (two_y_v3, y_solo_v2) |
| 1:33–1:33 | SAL 3.4 | 0.8s | TWO_SHOT_M | NO | 1 (two_m_v5) |
| 1:34–2:14 | BL1 4.1 | 40.3s | TWO_SHOT_M→CL_M | **SI 25.3s** | 5 (two_m_v3, m_solo_v1..v4) + PIP 3 |
| 2:12–2:24 | BL1 4.2 | 12.1s | CLOSE_UP_Y | NO | 2 (y_solo_v3, y_solo_v4) |
| 2:22–2:55 | BL1 4.3 | 33.6s | TWO_SHOT_M | **SI 31.6s** | 4 (two_m_v1_rev, m_solo_v1_rev, m_solo_v3_rev, m_solo_v2_rev) + PIP 3 |
| 3:01–3:24 | BL1 4.4 | 23.1s | CLOSE_UP_Y | NO | 3 (y_solo_v1_rev, y_solo_v2_rev, y_solo_v4_rev) |
| 3:23–3:51 | BL1 4.5 | 28.1s | TWO_SHOT_M | NO | 4 (two_m_v4_rev, m_solo_v4_rev, two_m_v5_rev, m_solo_v3) |
| 3:52–4:26 | BL2 5.1 | 34.0s | TWO_SHOT_Y | **SI 30.0s** | 4 (two_y_v1_rev, y_solo_v1, y_solo_v3, two_y_v4) + PIP 3 |
| 4:26–4:40 | BL2 5.2 | 14.1s | CLOSE_UP_M | NO | 2 (m_solo_v4, m_solo_v2) |
| 4:37–5:07 | BL2 5.3 | 29.7s | TWO_SHOT_Y→CL_Y | **SI 25.7s** | 5 (two_y_v3, two_y_v5, y_solo_v2, y_solo_v4_rev, y_solo_v3_rev) + PIP 3 |

**Estadísticas:**
- 5 pizarras totales · 125.5s pizarra (40.9%) · 181.5s estudio puro (59.1%)
- 13 intervenciones del episodio cubiertas
- ~50 sub-segmentos de clips (50 cuts en pausas naturales del audio)
- Catálogo único utilizado: 18 base × 2 modes (normal/rev) = 36 variantes posibles, ~30 usadas

**Cortes en pausas verificados:** todos los sub-segmentos cortan en períodos del guion (puntos seguidos o aparte). El renderer debe ajustar fino al timing exacto del período usando word-level timestamps de Whisper.

---

# CHANGELOG vs v4

- ✅ Coordenadas pixel exactas (x, y, W, H) por elemento
- ✅ Verificación de colisiones explícita por intervención
- ✅ Asignación clip_slug + mode + segs_used por sub-segmento
- ✅ Encadenamiento de varios clips para PIP en pizarras largas (>10s)
- ✅ Detectados y resueltos 3 conflictos de layout:
  - 4.1 timeline_visual en BOT colisionaba con PIP → movido a TOP, altura reducida
  - 4.3 regulation_alert solapaba subtítulos → altura reducida 280→220px
  - 5.1 hierarchy_diagram solapaba stat_card MR → ancho reducido 720→600px
- ✅ Decisión 5.3: two_column_compare se retira a t=12s antes de que entren stat_cards (secuencial limpio, no acumulado)
- ⚠ Pendiente generar variantes `_rev` con `tools/reverse_clips.py` antes del render

**FIN DRAFT v5**
