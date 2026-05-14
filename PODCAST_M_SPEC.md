# Podcast M Spec — MaquinarIA Pesada

Especificación normativa para generar guiones y audio de **episodios M (Módulos)**:
los 14 episodios meta-producto que cierran cada bloque de Ts.

Reemplaza al spec genérico anterior **solo para episodios M**. Los episodios T
(temas individuales) tienen su propio spec en `PODCAST_T_SPEC.md`; los Shorts en
`PODCAST_S_SPEC.md`.

Versión: 2026-05-14 (**v6** — 18-22 min, 4 bloques de contenido con BLOQUE_FUENTES
nuevo, word count 2700-3300, invariantes TTS, pausas SSML, -14 LUFS)
Tipo: M
Duración objetivo: 18-22 minutos (rango 17-22 min)

---

## 1. Filosofía del episodio M

Un episodio M es **el meta-producto de cada módulo**: la pieza más larga, de
carácter promocional/marketing, que cubre los 2-3 conceptos más impactantes del
módulo **y los conecta con el sistema real que genera el podcast**. Es el motor
de la estrategia de posicionamiento en LinkedIn ("construyendo en público un
podcast de IA con IA, módulo a módulo"). Sirve a:

- Captación de oyentes nuevos (pieza-marca multi-plataforma).
- Construcción de autoridad técnica concreta a través de la propia obra.
- Diferenciación del corpus respecto al panorama saturado de podcasts IA.
- **Publicación**: agrupada con los T del mismo módulo (unidad coherente).

**La diferencia clave con un T:**

Un M no es un T más largo. Es estructuralmente distinto. Un T forma sobre un
tema del máster. Un M selecciona los 2-3 conceptos más impactantes del módulo y
los conecta con el sistema real. El bloque `APLICACION_PRACTICA` carga el peso
de la marca y de la diferenciación — en versión high-level (tipo B), sin
detalles técnicos de implementación.

**CTA obligatoria en CIERRE_FINAL**: mencionar que los episodios T del módulo
están disponibles en plataformas. Integrar de forma natural, no como anuncio.

---

## 2. Principios duros

- Priorizar claridad antes que estilo.
- Mantener tono divulgativo-técnico, riguroso y accesible.
- Episodios de **17 a 22 min**, objetivo práctico **18-22 min**. Se prefiere
  extender duración antes que dejar conceptos sin aterrizar.
- Empezar siempre con hook que cumpla una de las 3 plantillas (§5).
- **Apertura por paridad del número de MÓDULO:** impares Yago, pares Maria.
  M0 → Maria, M1 → Yago, M2 → Maria, M3 → Yago, etc.
- **Quien abre el episodio también dice el aviso de IA y abre el HOOK.**
- Usar "Yago" dentro del texto hablado, nunca "Iago".
- Aviso de IA dentro del SALUDO_Y_PRESENTACION en versión enganche (§6).
- **4 bloques de contenido obligatorios**: PANORAMA, DESTACADO,
  APLICACION_PRACTICA, FUENTES (§3).
- `APLICACION_PRACTICA` se construye consultando los 4 documentos vivos del
  proyecto (BIBLIA_SISTEMA, PRIMERPODCAST, VIDEOPODCAST, PODCAST) — ver §8.
- `BLOQUE_FUENTES` se construye desde `PDFs/auxiliares/fuentes_marco_modulo_M{n}.md`
  (fichero por módulo, obligatorio) — ver §9.
- **3 a 5 conceptos** en CIERRE_CONCEPTOS según riqueza del módulo (rango fijo).
- **El guion debe respetar el invariante de calidad TTS sintética** (§2B).
- Verificaciones reales del guion al final del archivo generado.
- Validación real del audio y reporte de créditos en el log.

---

## 2B. Invariante de calidad TTS sintética

Los episodios se generan con voces de IA. No valen los parámetros de un podcast
humano. Toda intervención y bloque debe respetar:

| Parámetro | Regla |
|---|---|
| Longitud intervención máxima | 40-60s seguidos del mismo speaker (≤200 palabras; zona óptima 60-120) |
| Muletillas | Cero muletillas no escriptadas |
| Frases cortas seguidas | Máximo 2-3 frases <12 palabras seguidas del mismo speaker |
| Frases largas | Máximo 28-32 palabras por frase |
| Densidad conceptual | 1 concepto técnico nuevo cada 30-40s; máx. 2 tecnicismos seguidos sin aterrizaje |
| Cambio de speaker | Pausa SSML 400-600ms obligatoria |
| Pausa intra-bloque | Cada 60-90s, pausa SSML 300-500ms explícita |
| Variación entonativa | Limitada → se compensa con cambio de speaker |

**Pausas SSML explícitas (nuevas en v6):** entre bloques 800-1200ms; entre
subtemas dentro de bloque 400-600ms; al final del HOOK 600ms; antes y después
del aviso de IA 400ms.

---

## 3. Estructura obligatoria del guion

```
1.  # HOOK
2.  # INTRO_SONIDO
3.  # SALUDO_Y_PRESENTACION
4.  # BLOQUE_PANORAMA
5.  # BLOQUE_DESTACADO
6.  # APLICACION_PRACTICA
7.  # BLOQUE_FUENTES
8.  # CIERRE_CONCEPTOS
9.  # CIERRE_FINAL  (con CTA a episodios T)
10. # VERIFICACIONES
```

**Función y duración de cada bloque** (objetivo de episodio: 20 min de referencia):

| Bloque | Duración | Palabras (obj/min/max) | Función | Líder |
|---|---|---|---|---|
| HOOK | 30-60s | 90-180 / 75 / 200 | Gancho + cita canónica | Por paridad del módulo |
| INTRO_SONIDO | 8-10s | 0 (música) | Stinger sonoro, no genera audio | — |
| SALUDO_Y_PRESENTACION | 60-90s | 175-220 / 150 / 240 | Saludo + aviso de IA enganche | Quien abre |
| BLOQUE_PANORAMA | 3.5-4.5 min | 525-675 / 450 / 720 | Qué cubre el módulo, por qué importa | Yago ≥65% |
| BLOQUE_DESTACADO | 4.5-5.5 min | 675-825 / 600 / 900 | 2-3 conceptos más impactantes del módulo | Compartido 40-60% |
| APLICACION_PRACTICA | 4-5 min | 600-750 / 540 / 825 | El sistema generador como caso de uso real | Maria abre/cierra 30-40%, Yago detalla 60-70% |
| BLOQUE_FUENTES | 2-3 min | 300-450 / 270 / 495 | 3-4 fuentes-marco del módulo entero | Compartido |
| CIERRE_CONCEPTOS | 1-2 min | 200-300 / 150 / 330 | 3-5 conceptos canónicos | Por paridad |
| CIERRE_FINAL | 30-60s | 90-180 / 75 / 200 | Cierre canónico + CTA a episodios T | Por paridad |
| VERIFICACIONES | — | — | Validación interna (no audio) | — |

**Total word count: objetivo 2700-3300 · hard-fail < 2400 o > 3680.**

Criterios de selección de conceptos en BLOQUE_DESTACADO (en orden):
1. El más contraintuitivo (lo que la mayoría no sabe).
2. El más relevante para profesionales no técnicos (CTOs/CEOs).
3. El que mejor conecta con la APLICACION_PRACTICA.

**M no lleva BLOQUE_LIMITES.** Los límites técnicos del módulo son territorio
del T. El M conecta conceptos con el sistema real y cierra con fuentes-marco.

---

## 4. Roles de los presentadores (líder por bloque)

### 4.1 Asignación de líder por bloque

| Bloque | Líder | Apoyo | Lógica |
|---|---|---|---|
| HOOK | Por paridad del nº de MÓDULO | El otro | M impares Yago, M pares Maria |
| SALUDO_Y_PRESENTACION | Quien abre | El otro | Aviso de IA enganche dicho por quien abre |
| BLOQUE_PANORAMA | **Yago** | Maria | Mapa del módulo entero: territorio explicador |
| BLOQUE_DESTACADO | **Compartido por concepto** | — | Líder rota por concepto, 40-60% global |
| APLICACION_PRACTICA | **Maria abre, Yago detalla** | — | Reparto explícito en 3 momentos, ver §8 |
| BLOQUE_FUENTES | **Compartido** | — | 2 fuentes Yago + 1-2 Maria, o alternar |
| CIERRE_CONCEPTOS | Por paridad | El otro | 3-5 conceptos alternando |
| CIERRE_FINAL | Por paridad | El otro | Cita canónica + CTA a episodios T |

### 4.2 "Compartido por concepto" en BLOQUE_DESTACADO

El M cubre solo 2-3 conceptos (los más impactantes, no todos). El generador
asigna líder por concepto alternando. Con 2 conceptos: Yago - Maria. Con 3:
Yago - Maria - Yago. El líder del concepto da la explicación principal (4-8
frases); el otro hace 1-2 intervenciones de pregunta o matiz por concepto.
**Reparto global de BLOQUE_DESTACADO entre 40% y 60% para cada speaker.**

### 4.3 Perfiles de los presentadores

- **Yago = explicador técnico.** Profundidad, terminología precisa, mecanismo.
  Lleva BLOQUE_PANORAMA y el detalle high-level (momento 2) de APLICACION_PRACTICA.
- **Maria = oyente exigente + conductora de marca.** Cuestiona, tensa, pide
  aterrizar. Abre y cierra APLICACION_PRACTICA (momentos 1 y 3).
  **No es asistente.** No valida, no aplaude, no asiente.

### 4.4 Lista negra de interjecciones (anti-NotebookLM)

**Prohibido en todos los episodios M (hard-fail si aparece):**
"Exactamente", "Claro que sí", "Muy bien dicho", "Tienes toda la razón",
"Exacto", "Por supuesto", "Eso es", "Totalmente".

### 4.5 Reglas de longitud y reparto

- Intervenciones de desarrollo: **mínimo 4 frases** en bloques centrales.
- En APLICACION_PRACTICA se permiten intervenciones largas (hasta 10 frases /
  250 palabras en el momento 2) cuando el caso lo requiera.
- Reacciones: máximo 12 palabras, máximo 3 por bloque.
- **Conteo de palabras por bloque y speaker (hard-fail si se incumple):**
  - BLOQUE_PANORAMA: Yago ≥65%.
  - BLOQUE_DESTACADO compartido: 40-60% globalmente.
  - APLICACION_PRACTICA: Maria 30-40%, Yago 60-70%.
- **Anti-pingpong:** apoyo máximo 1 cada 3 intervenciones del líder.
- **Apertura del bloque:** el líder siempre abre.

### 4.6 Tecnicismos

- Traducir y aterrizar al castellano cualquier término técnico relevante.
- No acumular más de dos tecnicismos seguidos sin frase de aterrizaje.

---

## 5. Hook: menú de 3 plantillas

Plantillas A (dato), B (pregunta-incómoda), C (caso). En M, el hook puede tirar
fuerte de la estadística-marco del módulo entero porque el episodio cubre más
territorio.

**Reglas duras del hook:**
- 30-60 segundos hablados.
- Cierra exactamente con: `Esto es MaquinarIA Pesada. Arrancamos.`
- **Apertura por paridad del número de MÓDULO:** M0→Maria, M1→Yago, M2→Maria,
  M3→Yago, M4→Maria, M5→Yago, M6→Maria, M7→Yago, M8→Maria, M9→Yago, M10→Maria,
  M11→Yago, M12→Maria, M13→Yago, M14→Maria.
- La aplicación práctica del sistema **NO debe aparecer en el HOOK** (hard-fail).

---

## 6. Aviso de generación por IA — versión enganche

**Dentro de SALUDO_Y_PRESENTACION**, justo después de la presentación. Lo dice
**el mismo speaker que abrió el HOOK por paridad del módulo**.

### 6.0 Formato obligatorio del SALUDO_Y_PRESENTACION

Mínimo **3 intervenciones separadas**, en este orden:
1. `{opener}: [tag] Bienvenidos/Hola/etc. + Soy {opener_name}.`
2. `{otro}: [tag] Y yo soy {otro_name}.`
3. `{opener}: [tag] Antes de empezar, lo de siempre... {aviso completo}`

**Hard-fail si:** una sola intervención contiene los dos nombres; o el aviso lo
dice un speaker distinto del opener.

**Prohibido: apellidos.** Los presentadores se llaman **Maria** y **Yago**, sin
apellidos. Hard-fail con regex `\b(Maria|Yago)\s+[A-ZÁÉÍÓÚÑ][a-zñáéíóú]+\b`.

### Forma para episodios M (versión enganche, 18-25s)

> "Antes de empezar, lo de siempre: este episodio lo genera un sistema
> automático de inteligencia artificial. Puede contener errores. Si oyes algo
> que no te cuadra, contrástalo. El sistema que produce este podcast también es
> contenido del podcast — al final del episodio veremos cómo se aplica lo de
> hoy a ese sistema."

**Reglas:**
- Obligatorio en todos los M. **Hard-fail si falta.**
- Debe contener literalmente **"sistema automatico"** y **"puede contener
  errores"** (hard-fail si faltan).
- **Lo dice el mismo speaker que abrió el HOOK** (hard-fail si lo dice el otro).
- Debe contener una frase que conecte el aviso con APLICACION_PRACTICA
  (soft-check).
- Duración 18-25 segundos. Pausa SSML de 400ms antes y después.

---

## 7. Reglas de contenido y fuentes

### 7.1 Pre-escritura obligatoria

Antes de escribir el guion, el generador rellena internamente esta tabla:

```
Del PDF RESUMEN del módulo:
- 4 datos numéricos con cifra concreta
- 3 casos con nombre propio
- 1 frase-fuerza del resumen ejecutivo
- 3 contraintuitivos del módulo

De los 4 documentos vivos del proyecto (extraídos para el módulo M{n}):
- 1 problema concreto del sistema relacionado con el módulo
- 1 decisión técnica tomada con justificación
- 1 cifra/dato verificable del sistema (logs, costes, métricas)

De PDFs/auxiliares/fuentes_marco_modulo_M{n}.md:
- 3-4 fuentes-marco del módulo entero
```

**Regla dura:** al menos uno del PDF debe aparecer dentro de los **primeros 90
segundos hablados**. La aplicación práctica del sistema **NO en el HOOK**.

### 7.2 Fuentes del generador

**Fuente primaria para conceptos (obligatoria, hard-fail si no se lee):**
- PDF RESUMEN del módulo en `PDFs/resumenes/RESUMEN_M{n}_*.pdf`.
- El generador DEBE leerlo como input; los tokens deben quedar en
  VERIFICACIONES (`tokens > 0`). Cobertura ≥75%. Hard-fail si `tokens=0` o
  cobertura<75%.

**Fuente primaria para APLICACION_PRACTICA — los 4 documentos vivos:**

| Documento | Tipo | Prioridad por módulo |
|---|---|---|
| `BIBLIA_SISTEMA.md` | Referencia técnica estática | M1, M5, M6, M7, M9, M10 |
| `PRIMERPODCAST.md` | Diario producción audio | M5, M6, M8, M11, M12 |
| `VIDEOPODCAST.md` | Diario producción video | M2, M4, M8, M9, M10 |
| `PODCAST.md` | Diario operativo unificado (marcas DECISIÓN/CAMBIO/INCIDENCIA/PRODUCCIÓN/REGLA) | Todos, esp. M8, M12, M13 |

El generador construye la "ficha de aplicación" y la guarda en
`episodios/temp/aplicacion_extraida_M{n}.md`. **Fallback** si no encuentra
1 problema + 1 decisión + 1 cifra: hard-fail, pide intervención humana o
override en `PDFs/aplicacion_practica/M{n}.md`.

**Fuente primaria para BLOQUE_FUENTES (obligatoria, hard-fail si no existe):**
- `PDFs/auxiliares/fuentes_marco_modulo_M{n}.md` — fichero por módulo con las
  fuentes-marco del módulo entero. Ver §9.

**Fuentes secundarias:**
1. `PDFs/auxiliares/glosario_unificado.md` — definiciones canónicas. Hard-fail
   si no existe el archivo.
2. `PDFs/auxiliares/benchmarks_academicos.md` — máximo 1 mención por episodio.
3. `PDFs/auxiliares/fuentes_directas.md` — máximo 3 menciones por episodio.
4. PDFs de los temas T del módulo, en `PDFs/temas/M{n}_T*.pdf` — consulta
   opcional.

**Regla anti-relleno:** las fuentes secundarias sustituyen contenido genérico
por específico, no añaden volumen.

**Prioridad ante conflicto:** secundaria vs RESUMEN → prevalece RESUMEN
(soft-warn). Documentos vivos vs RESUMEN en APLICACION_PRACTICA → prevalecen
documentos vivos (soft-warn).

### 7.3 Reglas generales de contenido

- Cubrir al menos el **75%** de los conceptos clave del PDF RESUMEN.
- Cada concepto técnico complejo va seguido de una **analogía cotidiana en ≤2
  frases** antes de la traslación corporativa. Marcadores libres: "imagina
  que", "es como cuando", "piensa en", "el equivalente sería", "en tu día a
  día", "igual que", "lo mismo que pasa cuando".
- Soft-warn si un concepto del PDF aparece en BLOQUE_DESTACADO o BLOQUE_PANORAMA
  sin ningún marcador de analogía en las 6 frases siguientes.

### 7.4 Referencias temporales

- **Año por defecto: 2026.** El estado actual del mercado/modelos/práctica **no
  cita año**; usa "hoy", "actualmente", "ahora mismo".
- **Excepción — publicaciones/informes/papers/eventos**: se conserva el año real
  acompañado de autor o publicación con nombre propio.
- **Prohibido** 2024/2025 como presente. Hard-warn si `\b(2024|2025|dos mil
  veint(icuatro|icinco))\b` y en las 6 palabras anteriores no aparece: paper,
  informe, estudio, reporte, publicación, encuesta, según, lanzamiento,
  McKinsey, Hugging Face, Anthropic, OpenAI, Google, Meta, Gartner, IBM, IDC,
  Lucid, Forrester, Stanford, MIT.

---

## 8. APLICACION_PRACTICA: el bloque distintivo del M

### 8.1 Función

Conectar el módulo entero con un caso de uso real verificable: el sistema que
genera el podcast. NO es promoción. ES aplicación didáctica del concepto a un
sistema real que el oyente puede inspeccionar.

### 8.2 Estructura interna — 3 momentos

- **Momento 1 — Maria plantea (~45-60s).** Abre conectando el módulo con el
  sistema; plantea la pregunta operativa del módulo aplicada al sistema real.
- **Momento 2 — Yago detalla en formato high-level / tipo B (~2.5-3 min).**
  Conecta los conceptos del módulo con el sistema de forma conceptual, NO
  técnica. Patrón: "esto que acabas de aprender es exactamente lo que hace
  posible que [X del sistema]". No citar componentes, archivos, funciones,
  parámetros, costes ni métricas técnicas específicas.
- **Momento 3 — Cierre conjunto (~30-45s).** Maria pregunta o señala el
  aprendizaje; Yago lo aterriza; frase final que conecta de vuelta con el
  módulo entero.

### 8.3 Reglas específicas

- Duración 4-5 min total (240-300s).
- Reparto de palabras: **Maria 30-40%, Yago 60-70%**.
- El contenido de Yago debe basarse en hechos verificables de los 4 documentos
  vivos o del override manual. **No inventar** — hard-fail si falta material.
- Debe conectar al menos **2 conceptos** del módulo con el caso del sistema
  (soft-warn si solo conecta 1).

### 8.4 Material fuente: extracción automática + override opcional

Modo automático: el generador construye la "ficha de aplicación" extrayendo de
los 4 documentos vivos (estructura: pregunta operativa / problema concreto /
decisión tomada / cifras verificables / conexión con conceptos / fuentes
consultadas) y la guarda en `episodios/temp/aplicacion_extraida_M{n}.md`.
Modo override: si existe `PDFs/aplicacion_practica/M{n}.md`, se usa como fuente
prioritaria con la misma estructura.

---

## 9. BLOQUE_FUENTES: fuentes-marco del módulo (nuevo en v6)

### 9.1 Función

Cerrar el M entregando una bibliografía del **módulo entero**, citable y
verificable. Refuerza el posicionamiento "el máster destilado" y diferencia
frente a podcasts sintéticos que no citan fuentes con rigor.

### 9.2 Fuente: fichero por módulo (Variante A)

`PDFs/auxiliares/fuentes_marco_modulo_M{n}.md` — **obligatorio, hard-fail si no
existe**. Contiene las 3-4 fuentes-marco del módulo entero (el libro/curso de
referencia, el paper que define el campo, la encuesta de adopción más citada,
la fuente oficial). Son **distintas** de las fuentes específicas de los T del
módulo: complementan, no duplican.

### 9.3 Reglas del bloque

- Duración 2-3 min, 300-450 palabras.
- Citar **exactamente 3 o 4 fuentes** (hard-fail si <3 o >5).
- Cada fuente lleva: nombre canónico (autor + año + título), una frase de por
  qué importa para este módulo, y el bloque del módulo donde aplica.
- Toda fuente citada debe estar en `fuentes_marco_modulo_M{n}.md` (hard-fail si
  el LLM inventa una fuente).
- **No leer URLs en audio** (soft-warn si aparece "https" o "punto com"). Las
  URLs van solo en la descripción del episodio.
- Compartido entre voces. Idealmente al menos 1 fuente conecta con
  APLICACION_PRACTICA (soft-warn si ninguna lo hace).

---

## 10. Cierre

### 10.1 CIERRE_CONCEPTOS

- Abre con: `No te puedes ir de este capitulo sin haber entendido estos conceptos`
- **3 a 5 conceptos** según riqueza del módulo (hard-fail si <3 o >5).
- Cada concepto en una frase, no expandidos.
- Al menos uno debe conectarse con APLICACION_PRACTICA.

### 10.2 CIERRE_FINAL

Debe incluir literalmente:
> "Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada. Siguenos para
> nuevos capitulos donde la I.A. crea contenido sobre I.A."

**CTA obligatoria (WARN si falta, no hard-fail):** el speaker de cierre menciona
de forma natural que los episodios T del módulo están disponibles. Validación:
regex flexible `episodio[s]?.{0,30}(módulo|disponible|plataforma|escucha)`.

---

## 11. Etiquetas TTS

- Una sola etiqueta por intervención, al inicio del texto.
- Las etiquetas son instrucciones de tono, no separadores de microfrases.
- Lista cerrada: didactico, explicativo, directo, serio, firme, contundente,
  grave, tenso, conversacional, reflexivo, curioso, ironico, esceptico, natural,
  pausado, calido, claro, analitica.

---

## 12. Reglas de producción de audio

El guion debe cumplirlas antes de enviarse a síntesis (ElevenLabs eleven_v3 a
1.20× + 1.10× post = **1.32× total**).

- **Audio-Regla 1 — Números siempre en palabras.** A 1.32×, "3.7%" o "$3M" son
  ininteligibles. Conversión de números >100 vía `num2words`. Excepción: años de
  papers donde el año es parte del nombre.
- **Audio-Regla 2 — Longitud óptima de intervención.** 60-120 palabras zona
  óptima; reacción/pregunta 5-12 palabras (hard-fail si >15); máximo absoluto
  200 palabras (excepción APLICACION_PRACTICA momento 2: 250).
- **Audio-Regla 3 — Tags TTS guían el estilo de escritura**, no los parámetros
  de ElevenLabs (`style=0.0` hardcodeado).
- **Audio-Regla 4 — Tecnicismos acelerados: introducción obligatoria.** "El
  algoritmo clave, que llamamos backpropagation, es..." (no "backpropagation
  es...").
- **Audio-Regla 5 — INTRO_SONIDO: documentación, no generación.** La línea
  `[INTRO - SONIDO DE MAQUINAS ARRANCANDO - 8-10 segundos]` es obligatoria en
  validación pero NO genera audio.
- **Audio-Regla 6 (nueva v6) — Pausas SSML explícitas.** Entre bloques
  800-1200ms; intra-bloque 400-600ms; fin de HOOK 600ms; aviso de IA 400ms
  antes y después; cambio de speaker 400-600ms.
- **Audio-Regla 7 (nueva v6) — Loudness -14 LUFS.** Normalización a -14 LUFS
  integrated, -1 dBTP (estándar Spotify).

---

## 13. Configuración (JSON)

<!-- PODCAST_M_SPEC_JSON_START -->
```json
{
  "version": "2026-05-14-v6",
  "spec_type": "M",
  "project_name": "MaquinarIA Pesada",
  "language": "es",
  "directories": {
    "pdfs_dir": "PDFs",
    "pdfs_temas_dir": "PDFs/temas",
    "pdfs_resumenes_dir": "PDFs/resumenes",
    "pdfs_auxiliares_dir": "PDFs/auxiliares",
    "pdfs_aplicacion_practica_dir": "PDFs/aplicacion_practica",
    "scripts_dir": "Guiones",
    "output_dir": "episodios",
    "temp_dir": "episodios/temp",
    "videos_dir": "Videos",
    "music_dir": "Música",
    "intro_dir": "intro",
    "logos_dir": "Logos",
    "default_logo": "Logos/logo sin fondo.png",
    "live_docs_dir": "."
  },
  "anthropic": {
    "default_generation_model": "claude-sonnet-4-5",
    "default_concept_model": "claude-haiku-4-5-20251001",
    "temperature": 0.7,
    "max_output_tokens": 10000,
    "stream": true,
    "retry_on_hard_fail": {
      "max_retries": 1,
      "strategy": "explicit_feedback_to_llm"
    }
  },
  "episode_defaults": {
    "duration_minutes": 20,
    "duration_range_minutes": [17, 22],
    "target_audience": "Profesionales tecnicos curiosos sobre como funciona la IA por dentro. CTOs/CIOs/CEOs y profesionales de IT como audiencia secundaria. Pieza meta-producto del modulo. Todo concepto complejo se aterriza con analogia cotidiana antes de la traslacion tecnica/corporativa.",
    "tone": "divulgativo tecnico, riguroso pero accesible, con momento de ingenieria-real en APLICACION_PRACTICA",
    "hook_style": "menu_3_plantillas",
    "minimum_audio_minutes": 17.0,
    "maximum_audio_minutes": 22.5
  },
  "tts_invariants": {
    "max_intervention_seconds": 60,
    "max_intervention_words": 200,
    "optimal_intervention_words": [60, 120],
    "no_unscripted_fillers": true,
    "max_consecutive_short_sentences": 3,
    "max_words_per_sentence": 32,
    "new_concept_every_seconds": [30, 40],
    "max_consecutive_technicisms_without_landing": 2,
    "ssml_pauses_ms": {
      "between_blocks": [800, 1200],
      "between_subtopics": [400, 600],
      "after_hook": 600,
      "around_ia_warning": 400,
      "speaker_change": [400, 600]
    }
  },
  "parity_rules": {
    "applies_to": "module_number",
    "rule": "M_par_maria_abre__M_impar_yago_abre",
    "opener_does_hook_and_aviso": true,
    "explicit_table": {
      "M0": "Maria", "M1": "Yago", "M2": "Maria", "M3": "Yago",
      "M4": "Maria", "M5": "Yago", "M6": "Maria", "M7": "Yago",
      "M8": "Maria", "M9": "Yago", "M10": "Maria", "M11": "Yago",
      "M12": "Maria", "M13": "Yago", "M14": "Maria"
    }
  },
  "speakers": {
    "IAGO": {
      "display_name": "Iago",
      "spoken_name": "Yago",
      "opens_odd_modules": true,
      "opens_even_modules": false,
      "role": "explicador_tecnico",
      "leads_blocks": ["BLOQUE_PANORAMA"],
      "shares_blocks": ["BLOQUE_DESTACADO", "BLOQUE_FUENTES"],
      "supports_blocks": [],
      "aplicacion_role": "detalla_highlevel_momento_2_tipo_B",
      "traits": ["grave", "contundente", "tecnico"],
      "allowed_tags": ["didactico", "explicativo", "directo", "serio", "firme", "contundente", "grave", "tenso", "conversacional", "reflexivo", "curioso", "ironico", "esceptico", "natural", "pausado", "calido", "claro", "analitica"]
    },
    "MARIA": {
      "display_name": "Maria",
      "spoken_name": "Maria",
      "opens_odd_modules": false,
      "opens_even_modules": true,
      "role": "oyente_exigente_y_conductora_marca",
      "leads_blocks": [],
      "shares_blocks": ["BLOQUE_DESTACADO", "BLOQUE_FUENTES"],
      "supports_blocks": ["BLOQUE_PANORAMA"],
      "aplicacion_role": "abre_y_cierra_momentos_1_y_3",
      "traits": ["clara", "analitica", "incisiva"],
      "allowed_tags": ["didactico", "explicativo", "directo", "serio", "firme", "contundente", "grave", "tenso", "conversacional", "reflexivo", "curioso", "ironico", "esceptico", "natural", "pausado", "calido", "claro", "analitica"]
    }
  },
  "script_rules": {
    "required_sections": [
      "HOOK", "INTRO_SONIDO", "SALUDO_Y_PRESENTACION",
      "BLOQUE_PANORAMA", "BLOQUE_DESTACADO", "APLICACION_PRACTICA",
      "BLOQUE_FUENTES", "CIERRE_CONCEPTOS", "CIERRE_FINAL", "VERIFICACIONES"
    ],
    "forbidden_sections": [
      "BLOQUE_1", "BLOQUE_2", "BLOQUE_3", "BLOQUE_4",
      "BLOQUE_QUE", "BLOQUE_COMO", "BLOQUE_LIMITES",
      "BLOQUE_TEMAS_CLAVE", "BLOQUE_REALIDAD", "BLOQUE_CASOS",
      "INSERCION_1", "INSERCION_2", "INSERCION_3", "INSERCION_EMPRESA"
    ],
    "max_consecutive_blocks_same_speaker": 2,
    "key_concepts_block_count_min": 3,
    "key_concepts_block_count_max": 5,
    "minimum_word_count": 2700,
    "maximum_word_count": 3300,
    "hard_fail_word_count_min": 2400,
    "hard_fail_word_count_max": 3680,
    "minimum_sentences_per_intervention": 4,
    "maximum_sentences_per_intervention": 10,
    "reaction_word_limit": 30,
    "max_reactions_per_block": 3,
    "target_avg_words_per_intervention_min": 60,
    "target_avg_words_per_intervention_max": 120,
    "target_max_words_per_single_intervention": 200,
    "hard_fail_on_digits_in_dialogue": false,
    "hard_fail_on_missing_cta_in_final": false,
    "minimum_pdf_coverage_percent": 75,
    "leader_share_min_percent": 65,
    "shared_block_balance_range_percent": [40, 60],
    "support_intervention_ratio_max": "1_per_3_leader",
    "leader_opens_block": true,
    "block_word_targets": {
      "HOOK": {"min": 90, "target": 130, "max": 200},
      "SALUDO_Y_PRESENTACION": {"min": 150, "target": 200, "max": 240},
      "BLOQUE_PANORAMA": {"min": 450, "target": 600, "max": 720},
      "BLOQUE_DESTACADO": {"min": 600, "target": 750, "max": 900},
      "APLICACION_PRACTICA": {"min": 540, "target": 675, "max": 825},
      "BLOQUE_FUENTES": {"min": 270, "target": 375, "max": 495},
      "CIERRE_CONCEPTOS": {"min": 150, "target": 250, "max": 330},
      "CIERRE_FINAL": {"min": 75, "target": 130, "max": 200}
    },
    "aplicacion_practica": {
      "duration_seconds_min": 240,
      "duration_seconds_max": 300,
      "maria_share_percent_range": [30, 40],
      "yago_share_percent_range": [60, 70],
      "must_connect_concepts_min": 2,
      "no_invention_allowed": true,
      "extraction_mode": "automatic_from_live_docs_with_optional_override",
      "momento_2_max_words": 250,
      "min_facts_required": {
        "problema_concreto": 1,
        "decision_tecnica": 1,
        "cifra_verificable": 1
      }
    },
    "bloque_fuentes": {
      "duration_seconds_min": 120,
      "duration_seconds_max": 180,
      "sources_count_min": 3,
      "sources_count_max": 4,
      "source_file_pattern": "PDFs/auxiliares/fuentes_marco_modulo_M{n}.md",
      "source_file_required": true,
      "no_invented_sources": true,
      "no_urls_in_speech": true,
      "should_connect_aplicacion": true
    },
    "hook_closing_phrase": "Esto es MaquinarIA Pesada. Arrancamos.",
    "hook_duration_seconds": [30, 60],
    "intro_comment": "[INTRO - SONIDO DE MAQUINAS ARRANCANDO - 8-10 segundos]",
    "warning_phrase_keywords_required": ["sistema automatico", "puede contener errores"],
    "warning_must_be_said_by_opener": true,
    "warning_duration_seconds": [18, 25],
    "warning_phrase_keywords_softcheck": ["sistema que produce", "parte del podcast", "veremos como se aplica"],
    "concepts_closing_phrase": "No te puedes ir de este capitulo sin haber entendido estos conceptos",
    "final_closing_phrase": "Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada. Siguenos para nuevos capitulos donde la I.A. crea contenido sobre I.A.",
    "speaker_aliases": {"MARIA": ["MARIA", "MARÍA"], "IAGO": ["IAGO"]},
    "blacklist_validation_interjections": ["exactamente", "claro que sí", "muy bien dicho", "tienes toda la razón", "exacto", "por supuesto", "eso es", "totalmente"],
    "blacklist_placeholder_phrases": [
      "Bien apuntado. Déjame añadir la perspectiva técnica aquí. Hay una capa de implementación",
      "La pregunta que planteas toca algo crítico del diseño. El contexto cambia todo en estos sistemas distribuidos",
      "Hay algo que me genera curiosidad en este punto. ¿Cómo conecta esto con lo que acabamos de ver? Porque la secuencia conceptual importa mucho aquí",
      "Eso me plantea una pregunta concreta. ¿Cómo se traslada esto al entorno real de producción? Hay una distancia entre el diseño en papel",
      "Déjame entender bien este punto antes de seguir. ¿Qué implica esto en la práctica concreta para las organizaciones"
    ],
    "hook_templates": ["dato", "pregunta_incomoda", "caso"],
    "preescritura_required": {
      "datos_numericos_min": 4,
      "casos_nombre_propio_min": 3,
      "frase_fuerza_min": 1,
      "contraintuitivos_min": 3,
      "aplicacion_problema_min": 1,
      "aplicacion_decision_min": 1,
      "aplicacion_cifra_min": 1,
      "fuentes_marco_min": 3,
      "must_appear_pdf_in_first_seconds": 90,
      "aplicacion_NOT_in_hook": true
    },
    "sources": {
      "primary_for_concepts": {
        "resumen_path_pattern": "PDFs/resumenes/RESUMEN_M{n}_*.pdf",
        "required": true,
        "must_be_read_by_generator": true,
        "min_concept_coverage_percent": 75,
        "min_input_tokens_reported": 5000
      },
      "primary_for_aplicacion": {
        "live_docs": [
          {"name": "BIBLIA_SISTEMA", "path": "BIBLIA_SISTEMA.md", "type": "static_reference", "priority_modules": ["M1", "M5", "M6", "M7", "M9", "M10"]},
          {"name": "PRIMERPODCAST", "path": "PRIMERPODCAST.md", "type": "production_diary_audio", "priority_modules": ["M5", "M6", "M8", "M11", "M12"]},
          {"name": "VIDEOPODCAST", "path": "VIDEOPODCAST.md", "type": "production_diary_video", "priority_modules": ["M2", "M4", "M8", "M9", "M10"]},
          {"name": "PODCAST", "path": "PODCAST.md", "type": "operational_diary_unified", "structured_markers": ["DECISIÓN", "CAMBIO", "INCIDENCIA", "PRODUCCIÓN", "REGLA"], "priority_modules": ["M8", "M12", "M13"]}
        ],
        "extraction_strategy": "search_by_module_concepts_and_keywords",
        "extraction_artifact_path": "episodios/temp/aplicacion_extraida_M{n}.md",
        "fallback_on_insufficient_material": "hard_fail_request_human_input",
        "manual_override": {"path_pattern": "PDFs/aplicacion_practica/M{n}.md", "priority": "overrides_automatic_extraction"}
      },
      "primary_for_fuentes": {
        "path_pattern": "PDFs/auxiliares/fuentes_marco_modulo_M{n}.md",
        "required": true,
        "variant": "A_fuentes_marco_modulo_entero"
      },
      "secondary": {
        "glossary": {"path": "PDFs/auxiliares/glosario_unificado.md", "required": true},
        "benchmarks": {"path": "PDFs/auxiliares/benchmarks_academicos.md", "required": false, "max_uses_per_episode": 1},
        "direct_sources": {"path": "PDFs/auxiliares/fuentes_directas.md", "required": false, "max_uses_per_episode": 3},
        "temas_modulo": {"path_pattern": "PDFs/temas/M{n}_T*.pdf", "required": false}
      },
      "anti_inflation_rule": "auxiliary_sources_replace_not_add",
      "conflict_resolution": {
        "secondary_vs_primary_concepts": "primary_wins_softwarn",
        "live_docs_vs_resumen_in_aplicacion": "live_docs_win_softwarn"
      }
    }
  },
  "audio_rules": {
    "model": "eleven_v3",
    "output_format": "mp3_44100_128",
    "export_bitrate": "192k",
    "initial_silence_ms": 2000,
    "same_speaker_pause_ms": 250,
    "different_speaker_pause_ms": 500,
    "background_music_db": -20,
    "background_bed_path": "Música/base podcast.mp3",
    "intro_theme_path": "Música/Sintonia Maquinaria pesada.mp3",
    "pre_hook_bed_ms": 2000,
    "post_hook_bed_ms": 2000,
    "post_hook_bed_fade_out_ms": 2000,
    "post_intro_bed_ms": 2000,
    "final_bed_tail_ms": 3000,
    "final_bed_tail_fade_out_ms": 3000,
    "music_fade_in_ms": 3000,
    "music_fade_out_ms": 5000,
    "normalization_target_lufs": -14,
    "true_peak_target_dbtp": -1.0,
    "post_speed_multiplier": 1.10,
    "ssml_pauses_enabled": true,
    "voices": {
      "IAGO": {"voice_id": "CdAqYBLnsNjmTqYgD5Ha", "stability": 0.65, "similarity_boost": 0.65, "style": 0.0, "use_speaker_boost": false, "speed": 1.20},
      "MARIA": {"voice_id": "gD1IexrzCvsXPHUuT0s3", "stability": 0.68, "similarity_boost": 0.55, "style": 0.0, "use_speaker_boost": false, "speed": 1.20}
    }
  },
  "qa_rules": {
    "hard_fail_on_blacklist_interjection": true,
    "hard_fail_on_forbidden_section": true,
    "hard_fail_on_missing_warning_keyword": true,
    "hard_fail_on_warning_said_by_wrong_speaker": true,
    "hard_fail_on_leader_share_below_min": true,
    "hard_fail_on_wrong_opener_by_parity": true,
    "hard_fail_on_concepts_count_out_of_range": true,
    "hard_fail_on_missing_resumen_source": true,
    "hard_fail_on_zero_input_tokens": true,
    "hard_fail_on_pdf_coverage_below_75": true,
    "hard_fail_on_missing_glossary": true,
    "hard_fail_on_aplicacion_in_hook": true,
    "hard_fail_on_insufficient_aplicacion_material": true,
    "hard_fail_on_missing_fuentes_marco_file": true,
    "hard_fail_on_fuentes_count_out_of_range": true,
    "hard_fail_on_invented_source": true,
    "hard_fail_on_word_count_out_of_hard_range": true,
    "hard_fail_on_saludo_collapsed_single_block": true,
    "hard_fail_on_presenter_surname_invented": true,
    "hard_fail_on_shared_block_balance": true,
    "hard_fail_on_intervention_over_max_words": true,
    "soft_warn_on_missing_warning_softcheck": true,
    "soft_warn_on_missing_preescritura_evidence": true,
    "soft_warn_on_pingpong_pattern": true,
    "soft_warn_on_aplicacion_single_concept_only": true,
    "soft_warn_on_secondary_vs_primary_conflict": true,
    "soft_warn_on_live_docs_vs_resumen_conflict": true,
    "soft_warn_on_module_with_low_live_docs_coverage": true,
    "soft_warn_on_temporal_reference_without_publication_context": true,
    "soft_warn_on_missing_everyday_analogy_after_complex_concept": true,
    "soft_warn_on_missing_cta_in_cierre_final": true,
    "soft_warn_on_digit_numbers_in_dialogue": true,
    "soft_warn_on_intervention_over_200_words": true,
    "soft_warn_on_urls_in_fuentes_speech": true,
    "soft_warn_on_fuentes_not_connecting_aplicacion": true,
    "soft_warn_on_sentence_over_32_words": true,
    "soft_warn_on_too_many_consecutive_short_sentences": true
  },
  "saludo_format": {
    "min_blocks": 3,
    "block_1": "opener_intro_with_own_name",
    "block_2": "other_intro_with_own_name",
    "block_3": "opener_aviso_ia",
    "forbidden_patterns": ["soy maria.*y yo soy yago", "soy yago.*y yo soy maria"]
  },
  "presenter_names": {
    "allow_only": ["Maria", "Yago"],
    "forbid_surnames": true,
    "forbidden_surname_regex": "\\b(Maria|Yago)\\s+[A-ZÁÉÍÓÚÑ][a-zñáéíóú]+"
  },
  "temporal_references": {
    "default_year": 2026,
    "current_state_uses_no_year": true,
    "publication_context_markers": ["paper", "informe", "estudio", "reporte", "publicacion", "encuesta", "segun", "lanzamiento", "McKinsey", "Hugging Face", "Anthropic", "OpenAI", "Google", "Meta", "Gartner", "IBM", "IDC", "Lucid", "Forrester", "Stanford", "MIT"],
    "forbidden_present_year_patterns": ["\\b2024\\b", "\\b2025\\b", "dos mil veinticuatro", "dos mil veinticinco"],
    "context_window_words": 6
  },
  "everyday_analogy_rule": {
    "applies_to_blocks": ["BLOQUE_DESTACADO", "BLOQUE_PANORAMA"],
    "required_per_complex_concept": 1,
    "max_sentences_per_analogy": 2,
    "marker_phrases": ["imagina que", "es como cuando", "piensa en", "el equivalente seria", "en tu dia a dia", "igual que", "lo mismo que pasa cuando", "como si", "es como", "como cuando"]
  },
  "reporting": {
    "require_script_validation": true,
    "require_audio_validation": true,
    "print_anthropic_tokens": true,
    "print_elevenlabs_credits": true,
    "report_sources_used": true,
    "report_parity_check": true,
    "report_leader_share_per_block": true,
    "save_aplicacion_extraction_artifact": true,
    "cost_tracking_log": "costes_generacion.log"
  }
}
```
<!-- PODCAST_M_SPEC_JSON_END -->
