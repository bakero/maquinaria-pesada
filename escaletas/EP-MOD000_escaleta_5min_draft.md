---
episode_id: EP-MOD000
modulo: M0
tema: Introducción Estratégica a la I.A.
audio_duration_total: 813.98s
rango_escaleta: 0:00 - 5:07
version: v4 (handcrafted, primeros 5 min)
fecha: 2026-05-09
estrategia_layout: |
  ESTUDIO fullscreen es el modo dominante. Los presentadores se ven hablar
  como en cualquier videopodcast. La PIZARRA aparece sólo cuando hay un
  bloque conceptual potente que merece visualización (datos, jerarquías,
  comparaciones, líneas de tiempo). Min 10s por pizarra. Ritmo: PIZARRA
  → respiro estudio → PIZARRA. Nunca dos pizarras encadenadas.
paleta:
  amarillo_cat:    "#F5C400"
  azul_yago:       "#4DB8FF"
  rojo_alerta:     "#CC2200"
  gris_secundario: "#888888"
zonas_layout:
  reservadas:
    TOP_RIGHT:           name_tag del speaker activo (siempre)
    BOTTOM_RIGHT_SAFE:   PIP del presentador (cuando PIZARRA: SI, 480×270 borde CAT)
    BOTTOM_CENTER:       subtítulos blancos auto-Whisper
  libres_pizarra:
    TOP_LEFT, TOP_CENTER:    badges, alerts, section indicators
    MID_LEFT, MID_CENTER, MID_RIGHT:  cards conceptuales
    BOTTOM_LEFT:             stickers, memes pequeños
    BOTTOM_FULL_WIDTH:       timeline_visual (200px alto)
  regla_no_overlap: una sola pieza visual por zona en cada momento
---

# ESCALETA DE PRODUCCIÓN · EP-MOD000 · PRIMEROS 5 MINUTOS

> Rango temporal: `00:00.000` → `05:07.400`
> Patrón global: studio dominante, pizarra como bloque conceptual.
> Total pizarras en estos 5 min: **5** (124s pizarra / 307s contenido = 40%).

---

## PRELUDIO · LEAD SILENCE
**TC IN:** `00:00.000`  **TC OUT:** `00:01.928`  **DUR:** 1.93s

### 0.1 — Pantalla negra
- **TC:** `00:00.000 → 00:01.928` · **DUR:** 1.93s
- **TONO:** [silencio]
- **TEXTO:**
  > (sin voz)
- **PLANO:** BLACK
- **PIZARRA:** NO
- **ON-SCREEN:** (vacío)
- **TRANSICION OUT:** corte directo al HOOK.

> **NOTA DIRECCIÓN:** Pantalla negra pura 2s. Sin logo, sin tagline. Es
> el momento en que el oyente se prepara. Audio en silencio.

---

## BLOQUE 1 · HOOK
**TC IN:** `00:01.928`  **TC OUT:** `00:34.050`  **DUR:** 32.12s

### 1.1 — María
- **TC:** `00:02.060 → 00:18.990` · **DUR:** 16.93s
- **TONO:** [ironico]
- **TEXTO:**
  > En 2026, el 88% de las empresas dice que ya usa inteligencia artificial. El otro 12% dice que lo está evaluando. Básicamente, todo el mundo está en el tema, igual que todo el mundo ha leído los términos y condiciones de cada app que instala. Exactamente nadie.
- **PLANO:** TWO_SHOT_M_ACTIVE (María hablando, Yago la escucha asintiendo, plano amplio del estudio)
- **PIZARRA:** SI (entra en t=4.0s, sale al fin de la intervención · 12.9s pizarra)
- **ON-SCREEN:**
  | t (relativo) | Elemento | Posición | Salida |
  |---|---|---|---|
  | 00.0s | name_tag "MARIA" amarillo | TOP_RIGHT | hasta fin |
  | 04.0s | stat_card "ADOPCIÓN 2026 · 88% empresas usan IA" amarillo | MID_LEFT | hasta fin |
  | 08.0s | stat_card "EVALUANDO · 12% siguen estudiándolo" gris | MID_RIGHT | hasta fin |
  | 14.0s | sticker "exactamente_nadie_meme" | BOTTOM_LEFT | hasta fin |
- **TRANSICION OUT:** corte seco en pausa tras "exactamente nadie". La pizarra cae junto con el corte; volvemos a estudio fullscreen para 1.2.

### 1.2 — María (cierre canónico hook)
- **TC:** `00:18.920 → 00:34.050` · **DUR:** 15.13s
- **TONO:** [firme]
- **TEXTO:**
  > Hoy vemos qué hay de verdad detrás de ese número. Qué es la I.A., de dónde viene, cómo se estructura y qué implica para cualquier organización que tenga que tomar decisiones con ella encima de la mesa. Esto es MaquinarIA Pesada. Arrancamos.
- **PLANO:** CLOSE_UP_MARIA (plano cerrado para el cierre canónico, contacto visual con cámara)
- **PIZARRA:** NO (estudio fullscreen, atención total en María)
- **ON-SCREEN:**
  | t (relativo) | Elemento | Posición | Salida |
  |---|---|---|---|
  | 00.0s | name_tag "MARIA" amarillo | TOP_RIGHT | hasta fin |
- **TRANSICION OUT:** fundido suave a SINTONIA. María mantiene la mirada en cámara hasta que entra la música.

> **NOTA DIRECCIÓN:** El hook tiene UNA pizarra en 1.1 (los datos potentes 88%/12%) y se RETIRA en 1.2 para que el cierre canónico "Esto es MaquinarIA Pesada. Arrancamos." quede en plano cerrado limpio. Cero overlays distractores en el cierre del hook.

---

## BLOQUE 2 · INTRO_SONIDO + SINTONIA
**TC IN:** `00:34.050`  **TC OUT:** `00:46.720`  **DUR:** 12.67s

### 2.1 — Sintonía musical
- **TC:** `00:34.050 → 00:46.720` · **DUR:** 12.67s (incluye microsilencio pre-sintonía)
- **TONO:** [musica]
- **TEXTO:**
  > (sintonía musical instrumental)
- **PLANO:** SINTONIA (intro_video.mp4 superpuesto al body en `[35.206, 45.197]` por audio_structure)
- **PIZARRA:** NO
- **ON-SCREEN:** (vacío - el intro_video manda)
- **TRANSICION OUT:** corte limpio al SALUDO.

> **NOTA DIRECCIÓN:** El intro_video.mp4 lleva el logo MAQUINARIA PESADA animado. Cero overlays adicionales. Si hay microsilencio antes/después, mantener BLACK.

---

## BLOQUE 3 · SALUDO Y PRESENTACIÓN
**TC IN:** `00:46.720`  **TC OUT:** `01:35.840`  **DUR:** 49.12s

### 3.1 — Yago (bienvenida)
- **TC:** `00:46.720 → 01:02.740` · **DUR:** 16.02s
- **TONO:** [serio acogedor]
- **TEXTO:**
  > Bienvenidos a MaquinarIA Pesada. Soy Yago, y esto es el módulo cero: la introducción estratégica a la I.A. El episodio que nadie quiere admitir que necesita pero que conviene escuchar antes de aprobar cualquier presupuesto de inteligencia artificial en tu empresa.
- **PLANO:** TWO_SHOT_Y_ACTIVE (Yago habla, María lo mira atenta)
- **PIZARRA:** NO (saludo conversacional, sin datos que ilustrar)
- **ON-SCREEN:**
  | t (relativo) | Elemento | Posición | Salida |
  |---|---|---|---|
  | 00.0s | name_tag "YAGO" azul | TOP_RIGHT | hasta fin |
  | 02.0s | section_indicator "MÓDULO 0 · Introducción Estratégica" amarillo | TOP_CENTER | 8.0s |
- **TRANSICION OUT:** corte seco tras "en tu empresa". Cambia plano a María.

### 3.2 — María (advertencia legal)
- **TC:** `01:00.980 → 01:17.390` · **DUR:** 16.41s
- **TONO:** [tecnico serio]
- **TEXTO:**
  > Y yo soy María. Antes de arrancar, la advertencia legal y sensata: este episodio está generado por un sistema automático de inteligencia artificial y puede contener errores. Contrastad con fuentes profesionales. Si algo suena demasiado bueno o demasiado catastrófico, probablemente está exagerado.
- **PLANO:** CLOSE_UP_MARIA (plano cerrado para que la advertencia tenga peso, contacto visual)
- **PIZARRA:** NO (la advertencia es identidad de marca; un solo badge discreto)
- **ON-SCREEN:**
  | t (relativo) | Elemento | Posición | Salida |
  |---|---|---|---|
  | 00.0s | name_tag "MARIA" amarillo | TOP_RIGHT | hasta fin |
  | 03.0s | warning_badge "CONTENIDO GENERADO POR IA" rojo | TOP_LEFT | hasta fin |
- **TRANSICION OUT:** corte suave a Yago.

### 3.3 — Yago (objetivo del episodio)
- **TC:** `01:20.600 → 01:35.840` · **DUR:** 15.24s
- **TONO:** [didactico]
- **TEXTO:**
  > El objetivo de hoy: que al terminar tengas el mapa mental básico de la I.A. Qué tipos existen, por qué el momento actual es diferente a todos los intentos anteriores y qué impacto real tiene esto en las organizaciones.
- **PLANO:** TWO_SHOT_Y_ACTIVE (Yago en posición principal, María a la escucha)
- **PIZARRA:** NO (los tres pilares aparecen como pie discreto, sin invadir)
- **ON-SCREEN:**
  | t (relativo) | Elemento | Posición | Salida |
  |---|---|---|---|
  | 00.0s | name_tag "YAGO" azul | TOP_RIGHT | hasta fin |
  | 03.0s | recap_grid "TIPOS · MOMENTO · IMPACTO" amarillo | BOTTOM_FULL_WIDTH | hasta fin |
- **TRANSICION OUT:** corte rápido al "Vamos allá" de María.

### 3.4 — María (puente <1s)
- **TC:** `01:33.080 → 01:33.860` · **DUR:** 0.78s
- **TONO:** [enfatico]
- **TEXTO:**
  > Vamos allá.
- **PLANO:** ESTABLISHING (plano amplio, ambos visibles, cierre del saludo)
- **PIZARRA:** NO
- **ON-SCREEN:** (vacío - es un puente <1s)
- **TRANSICION OUT:** corte seco al BLOQUE 1.

> **NOTA DIRECCIÓN:** SALUDO entero es estudio puro. Sin pizarra. Solo el name_tag rotando con quien habla, el section_indicator del MÓDULO 0 al inicio (8s), warning_badge advertencia legal con María (hasta fin), y recap_grid de pies de Yago (hasta fin). Total tres overlays distintos, todos en zonas exteriores (TOP_LEFT, TOP_CENTER, BOTTOM_FULL_WIDTH), JAMÁS solapando.

---

## BLOQUE 4 · BLOQUE_1 · HISTORIA DE LA I.A.
**TC IN:** `01:34.660`  **TC OUT:** `03:51.680`  **DUR:** 137.02s

### 4.1 — María (los inviernos)
- **TC:** `01:34.660 → 02:14.910` · **DUR:** 40.25s
- **TONO:** [didactico]
- **TEXTO:**
  > Para entender dónde estamos hay que saber de dónde venimos. Y la historia de la I.A. tiene un patrón que se repite con asombrosa regularidad: promesa enorme, entusiasmo masivo, resultados que no llegan a la velocidad prometida y financiación que se corta. Eso se llama invierno de la I.A. Hemos tenido dos antes de este momento. El primero a finales de los 70, cuando los sistemas basados en reglas no escalaron más allá de dominios muy acotados. El segundo a finales de los 90, cuando las redes neuronales de los 80 no podían entrenarse por falta de datos y de potencia de cálculo.
- **PLANO:** TWO_SHOT_M_ACTIVE → cambia a CLOSE_UP_MARIA en t=15s al entrar la pizarra
- **PIZARRA:** SI (entra en t=15.0s, sale al fin · 25.3s pizarra)
- **ON-SCREEN:**
  | t (relativo) | Elemento | Posición | Salida |
  |---|---|---|---|
  | 00.0s | name_tag "MARIA" amarillo | TOP_RIGHT | hasta fin |
  | 15.0s | timeline_visual "1956 Dartmouth · 1970s 1ER INVIERNO · 1990s 2DO INVIERNO · 2017 Transformers · HOY" amarillo | BOTTOM_FULL_WIDTH | hasta fin |
  | 19.0s | regulation_alert "INVIERNO IA · promesa > resultado → corte de financiación" rojo | MID_LEFT | hasta fin |
  | 26.0s | warning_badge "2 INVIERNOS PREVIOS" rojo | TOP_CENTER | hasta fin |
  | 33.0s | stat_card "1970s · sistemas reglas · no escalan" gris | MID_RIGHT | hasta fin |
- **TRANSICION OUT:** corte a Yago en pausa post "potencia de cálculo".

### 4.2 — Yago (escepticismo legítimo · respiro)
- **TC:** `02:12.660 → 02:24.780` · **DUR:** 12.12s
- **TONO:** [ironico controlado]
- **TEXTO:**
  > Lo que significa que tienes todo el derecho histórico del mundo a mirar con escepticismo a quien te diga que esta vez es diferente. Dicho eso, esta vez realmente lo es.
- **PLANO:** CLOSE_UP_YAGO (estudio fullscreen, expresión cómplice)
- **PIZARRA:** NO (RESPIRO entre dos pizarras densas; estudio limpio para que el "lo es" tenga peso)
- **ON-SCREEN:**
  | t (relativo) | Elemento | Posición | Salida |
  |---|---|---|---|
  | 00.0s | name_tag "YAGO" azul | TOP_RIGHT | hasta fin |
- **TRANSICION OUT:** corte seco a María en "esta vez realmente lo es".

### 4.3 — María (los 3 factores que convergen)
- **TC:** `02:22.360 → 02:55.970` · **DUR:** 33.61s
- **TONO:** [tecnico crescendo]
- **TEXTO:**
  > La diferencia es una convergencia de tres factores que nunca antes habían coincidido al mismo tiempo. Primero, potencia de cómputo: las ge pe us, unidades de procesamiento gráfico, actuales son miles de veces más potentes que las de los años 90. Segundo, datos masivos: internet generó cantidades de texto, comportamiento e imágenes que hace veinte años eran inimaginables. Y tercero, un salto arquitectónico concreto: la llegada de los Transformers, o arquitectura de atención, en 2017 con el paper, o artículo científico, "Attention is All You Need".
- **PLANO:** TWO_SHOT_M_ACTIVE
- **PIZARRA:** SI (entra en t=2.0s, sale al fin · 31.6s pizarra)
- **ON-SCREEN:** (la pizarra construye los 3 factores progresivamente)
  | t (relativo) | Elemento | Posición | Salida |
  |---|---|---|---|
  | 00.0s | name_tag "MARIA" amarillo | TOP_RIGHT | hasta fin |
  | 02.0s | hierarchy_diagram "3 FACTORES · CÓMPUTO · DATOS · ARQUITECTURA" amarillo | TOP_CENTER | hasta fin |
  | 09.0s | stat_card "1. CÓMPUTO · GPUs miles× años 90" amarillo | MID_LEFT | hasta fin |
  | 16.0s | stat_card "2. DATOS · internet 20× volumen" amarillo | MID_CENTER | hasta fin |
  | 24.0s | stat_card "3. ARQUITECTURA · Transformers 2017" amarillo | MID_RIGHT | hasta fin |
  | 28.0s | regulation_alert "PAPER 'Attention is All You Need' · 2017" rojo | BOTTOM_LEFT | hasta fin |
- **TRANSICION OUT:** corte a Yago en cierre del paper.

### 4.4 — Yago (qué resolvió Transformers · respiro)
- **TC:** `03:01.820 → 03:24.880` · **DUR:** 23.06s
- **TONO:** [tecnico]
- **TEXTO:**
  > Ese paper resolvió el problema que había bloqueado todos los modelos anteriores: procesar texto de forma paralela y capturar relaciones entre palabras muy separadas dentro de un mismo documento. Gracias a esa arquitectura, desde 2020 tenemos los grandes modelos de lenguaje que hoy todo el mundo conoce. Sin los Transformers, el salto de la I.A. generativa no habría existido.
- **PLANO:** CLOSE_UP_YAGO (estudio fullscreen, plano cerrado para la explicación técnica)
- **PIZARRA:** NO (RESPIRO; el cómputo paralelo se entiende mejor en plano cerrado del gesto técnico de Yago que en una pizarra abstracta)
- **ON-SCREEN:**
  | t (relativo) | Elemento | Posición | Salida |
  |---|---|---|---|
  | 00.0s | name_tag "YAGO" azul | TOP_RIGHT | hasta fin |
- **TRANSICION OUT:** corte a María cuando dice "no habría existido".

### 4.5 — María (aceleración 2022→hoy · respiro estudio)
- **TC:** `03:23.540 → 03:51.680` · **DUR:** 28.14s
- **TONO:** [enfatico]
- **TEXTO:**
  > Y la aceleración desde entonces no paró ni un trimestre. En 2022 llegó ChatGPT con los primeros cien millones de usuarios en dos meses, batiendo todos los récords de adopción tecnológica de la historia. En 2023 y 2024, los grandes laboratorios compitiendo abiertamente en capacidades. En 2026, el debate ya no es si adoptar I.A., sino qué hacer con el 70% del código que muchos equipos ya generan con ayuda de modelos.
- **PLANO:** TWO_SHOT_M_ACTIVE
- **PIZARRA:** NO (suficientes datos en pizarra de 4.3; aquí volvemos a estudio para que María cierre el bloque cara a cara con el oyente. UN solo badge emocional al final como golpe)
- **ON-SCREEN:**
  | t (relativo) | Elemento | Posición | Salida |
  |---|---|---|---|
  | 00.0s | name_tag "MARIA" amarillo | TOP_RIGHT | hasta fin |
  | 06.0s | warning_badge "RÉCORD · 100M USUARIOS EN 2 MESES" amarillo | TOP_CENTER | 14.0s |
- **TRANSICION OUT:** corte seco a Yago para abrir BLOQUE 2.

> **NOTA DIRECCIÓN:** Bloque 1 sigue patrón **PIZARRA → respiro → PIZARRA → respiro → respiro**. Las dos pizarras (4.1 timeline-history y 4.3 tres-factores) son densas pero los respiros estudio entre ellas dan ritmo. NUNCA dos pizarras encadenadas. La transición entre 4.3 (pizarra) y 4.4 (estudio close-up Yago) es un corte de cámara natural.

---

## BLOQUE 5 · BLOQUE_2 · TAXONOMÍA
**TC IN:** `03:52.940`  **TC OUT:** `05:07.400`  **DUR:** 74.46s

### 5.1 — Yago (jerarquía 4 niveles)
- **TC:** `03:52.940 → 04:26.940` · **DUR:** 34.00s
- **TONO:** [didactico claro]
- **TEXTO:**
  > Necesitamos el mapa de taxonomía, porque nada genera más confusión en este campo que usar los mismos términos para cosas distintas. La I.A. es el campo más amplio. Dentro está el machine learning, o aprendizaje automático, que aprende patrones de datos. Dentro del machine learning está el deep learning, o aprendizaje profundo, con redes neuronales profundas. Y dentro del deep learning están los ele ele emes, grandes modelos de lenguaje. ChatGPT no es I.A. a secas: es la capa más específica de una jerarquía de cuatro niveles.
- **PLANO:** TWO_SHOT_Y_ACTIVE
- **PIZARRA:** SI (entra en t=4.0s, sale al fin · 30.0s pizarra)
- **ON-SCREEN:** (la pizarra ESTRELLA del episodio: el diagrama de 4 niveles)
  | t (relativo) | Elemento | Posición | Salida |
  |---|---|---|---|
  | 00.0s | name_tag "YAGO" azul | TOP_RIGHT | hasta fin |
  | 04.0s | hierarchy_diagram "IA ⊃ ML ⊃ DL ⊃ LLMs" azul | MID_CENTER | hasta fin |
  | 11.0s | stat_card "ML · aprende patrones" gris | MID_LEFT | hasta fin |
  | 18.0s | stat_card "DL · redes neuronales profundas" gris | MID_LEFT | hasta fin |
  | 24.0s | stat_card "LLMs · ChatGPT, GPT-4, Claude" amarillo | MID_RIGHT | hasta fin |
  | 30.0s | warning_badge "4 NIVELES · NO son sinónimos" rojo | TOP_CENTER | hasta fin |
- **TRANSICION OUT:** corte irónico a María.

### 5.2 — María (la realidad LinkedIn · respiro irónico)
- **TC:** `04:26.460 → 04:40.530` · **DUR:** 14.07s
- **TONO:** [ironico]
- **TEXTO:**
  > Lo cual no impide que en LinkedIn todo el mundo use los cuatro términos como si fueran exactamente lo mismo. Pero a partir de hoy tú ya no lo harás. Eso ya es ventaja competitiva inmediata.
- **PLANO:** CLOSE_UP_MARIA (estudio fullscreen, plano cerrado para el remate irónico)
- **PIZARRA:** NO (chiste, plano cerrado da más fuerza, sticker pequeño en bottom_left refuerza ironía)
- **ON-SCREEN:**
  | t (relativo) | Elemento | Posición | Salida |
  |---|---|---|---|
  | 00.0s | name_tag "MARIA" amarillo | TOP_RIGHT | hasta fin |
  | 04.0s | sticker "linkedin_buzzword_meme" | BOTTOM_LEFT | hasta fin |
- **TRANSICION OUT:** corte a Yago para abrir distinción siguiente.

### 5.3 — Yago (estrecha vs general)
- **TC:** `04:37.700 → 05:07.400` · **DUR:** 29.70s
- **TONO:** [didactico tecnico]
- **TEXTO:**
  > Otra distinción clave: I.A. estrecha frente a I.A. general. Toda la I.A. que existe hoy, sin excepción, es I.A. estrecha. Sistemas extraordinariamente potentes dentro de su dominio específico, pero incapaces de generalizar fuera de él. Un modelo que genera imágenes no conduce un coche. Un chatbot que escribe código no diagnostica una radiografía. La I.A. general, esa que razona en cualquier dominio como lo haría un humano, sigue siendo un horizonte teórico sin fecha de llegada.
- **PLANO:** TWO_SHOT_Y_ACTIVE → CLOSE_UP_YAGO en t=18s para el cierre conceptual
- **PIZARRA:** SI (entra en t=4.0s, sale al fin · 25.7s pizarra)
- **ON-SCREEN:** (pizarra de comparación binaria)
  | t (relativo) | Elemento | Posición | Salida |
  |---|---|---|---|
  | 00.0s | name_tag "YAGO" azul | TOP_RIGHT | hasta fin |
  | 04.0s | two_column_compare "IA ESTRECHA vs IA GENERAL" azul | MID_CENTER | hasta fin |
  | 12.0s | stat_card "ESTRECHA · 100% de la IA hoy" azul | MID_LEFT | hasta fin |
  | 19.0s | stat_card "GENERAL · horizonte teórico" gris | MID_RIGHT | hasta fin |
  | 25.0s | regulation_alert "AGI · sin fecha de llegada" rojo | BOTTOM_LEFT | hasta fin |
- **TRANSICION OUT:** corte a fin de los primeros 5 min del episodio.

> **NOTA DIRECCIÓN:** BLOQUE 2 sigue mismo patrón: **PIZARRA jerarquía → respiro irónico LinkedIn → PIZARRA estrecha-vs-general**. La pizarra de 5.1 es la más memorable del episodio (hierarchy_diagram + 3 stat_cards de la cadena IA→ML→DL→LLMs). 5.2 da respiro emocional. 5.3 cierra los primeros 5 min con la dicotomía conceptual estrecha vs general.

---

# RESUMEN DE LOS PRIMEROS 5 MIN

| Tiempo (s) | Bloque | Plano dominante | Pizarra |
|---|---|---|---|
| 0.0-1.9 | Lead silence | BLACK | — |
| 1.9-19.0 | HOOK 1.1 | TWO_SHOT_M_ACTIVE | **SI 12.9s** — 88%/12% |
| 19.0-34.0 | HOOK 1.2 | CLOSE_UP_MARIA | NO |
| 34.0-46.7 | SINTONÍA | intro_video overlay | — |
| 46.7-77.0 | SALUDO 3.1+3.2 | TWO_SHOT_Y / CLOSE_UP_M | NO |
| 77.0-95.0 | SALUDO 3.3+3.4 | TWO_SHOT_Y / ESTABLISHING | NO |
| 94.7-134.9 | BLOQUE_1 4.1 | TWO_SHOT_M → CLOSE_UP_M | **SI 25.3s** — TIMELINE inviernos |
| 132.7-144.8 | BLOQUE_1 4.2 | CLOSE_UP_YAGO | NO (respiro) |
| 142.4-176.0 | BLOQUE_1 4.3 | TWO_SHOT_M_ACTIVE | **SI 31.6s** — 3 FACTORES |
| 181.8-204.9 | BLOQUE_1 4.4 | CLOSE_UP_YAGO | NO (respiro) |
| 203.5-231.7 | BLOQUE_1 4.5 | TWO_SHOT_M_ACTIVE | NO (respiro) |
| 232.9-266.9 | BLOQUE_2 5.1 | TWO_SHOT_Y_ACTIVE | **SI 30.0s** — JERARQUÍA 4 niveles |
| 266.5-280.5 | BLOQUE_2 5.2 | CLOSE_UP_MARIA | NO (respiro irónico) |
| 277.7-307.4 | BLOQUE_2 5.3 | TWO_SHOT_Y → CLOSE_UP_Y | **SI 25.7s** — ESTRECHA vs GENERAL |

**Pizarras totales en 5 min:** 5 bloques · 125.5s pizarra (40%) / 187s estudio puro (60%) / silencios y sintonía (15s).

**Patrón rítmico:** P → E → SINT → E E E E → P → E → P → E → E → P → E → P
(P=pizarra, E=estudio, SINT=sintonía). Nunca dos pizarras encadenadas.

# REGLAS DE LAYOUT — VERIFICACIÓN ANTI-OVERLAP

| Posición | Tamaño aprox (1080p) | Conflictos | Reservada |
|---|---|---|---|
| TOP_LEFT | 400×100 | warning_badge | — |
| TOP_CENTER | 400-600×100 | section_indicator, warning_badge, hierarchy(small) | — |
| TOP_RIGHT | 200×80 | name_tag (siempre) | name_tag |
| MID_LEFT | 400×220 | stat_card, hierarchy_diagram, regulation_alert | — |
| MID_CENTER | 600×400 | hierarchy_diagram, two_column_compare, bar_chart | conflicto con MID_LEFT y MID_RIGHT si compare |
| MID_RIGHT | 400×220 | stat_card | — |
| BOTTOM_LEFT | 250×150 | sticker, regulation_alert | — |
| BOTTOM_CENTER | (auto) | subtítulos Whisper | subtitles |
| BOTTOM_RIGHT_SAFE | 480×270 | PIP del presentador (cuando PIZARRA) | PIP |
| BOTTOM_FULL_WIDTH | 1200×200 | timeline_visual, recap_grid (caso especial 600 alto) | conflicto con MID si recap_grid |

**Verificación de no-overlap intervención por intervención:**

- **1.1 (pizarra):** name_tag (TR) + stat_card (ML) + stat_card (MR) + sticker (BL). Ninguna zona compartida. PIP en BR. OK.
- **4.1 (pizarra):** name_tag (TR) + warning_badge (TC) + timeline (BFW) + regulation_alert (ML) + stat_card (MR). Cuidado: timeline_visual está en BOTTOM_FULL_WIDTH 200px alto, no choca con MID. OK.
- **4.3 (pizarra):** name_tag (TR) + hierarchy (TC) + stat (ML) + stat (MC) + stat (MR) + alert (BL). 3 stat_cards en fila mid. Cuidado: stat_card es 400px ancho; ML+MC+MR juntos suman 1200px en 1920 → cabe con margen 720px (180+180+180+180 márgenes). OK pero apretado.
- **5.1 (pizarra):** name_tag (TR) + warning (TC) + hierarchy (MC) + stat (ML) + stat (ML t=18!) + stat (MR). **CONFLICTO**: stat_card t=11 en ML y stat_card t=18 también en ML. El segundo desplaza al primero. Es intencional (van apareciendo en secuencia, ML rota). Documentado.
- **5.3 (pizarra):** name_tag (TR) + two_column_compare (MC). El compare ocupa MID entero (1000×500), por lo que MID_LEFT y MID_RIGHT NO pueden coexistir. Cuidado: stat_card t=12 en ML y t=19 en MR — superpondrían al compare. **REVISAR**: o bien quitar el two_column_compare en t=12-19 o bien posicionar stats fuera de MID (e.g. TOP_LEFT y TOP_CENTER). RECOMIENDO: cuando aparezcan los stat_cards, el two_column_compare se RETIRA. Editar: en t=12s sale el two_column_compare y entran los stat_cards. Esto requiere modelar la salida del compare → cambio en la tabla.

---

# CHANGELOG vs ESCALETA v3 LLM

- ❌ **Eliminado**: highlight_quote con preguntas literales del guion ("¿Qué es la IA?" etc.). Sustituido por hierarchy / timeline / stats con datos reales.
- ❌ **Eliminado**: pizarra continua. Pasamos de 87% pizarra a 40% pizarra.
- ✅ **Añadido**: respiros estudio fullscreen entre pizarras (4.2, 4.4, 4.5, 5.2).
- ✅ **Añadido**: planos CLOSE_UP en momentos clave (cierres canónicos, advertencias, ironías).
- ✅ **Añadido**: verificación anti-overlap explícita por zona.
- ⚠ **Pendiente revisar**: conflicto two_column_compare vs stat_cards en 5.3 (ver REGLAS DE LAYOUT).

**FIN DRAFT v4 · PRIMEROS 5 MINUTOS**
