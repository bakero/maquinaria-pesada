# Podcast T Spec — MaquinarIA Pesada

Especificación normativa para generar guiones y audio de **episodios T (Temas)**:
los ~100 episodios del corpus del máster, uno por tema individual.

Reemplaza al spec genérico anterior **solo para episodios T**. Los episodios M
(meta-producto de módulo) tienen su propio spec en `PODCAST_M_SPEC.md`; los
Shorts en `PODCAST_S_SPEC.md`.

Versión: 2026-05-14 (**v6** — 25-28 min, 6 bloques de contenido con BLOQUE_CASOS
y BLOQUE_LIMITES y BLOQUE_FUENTES nuevos/recuperados, word count 3700-4500,
invariantes TTS, pausas SSML, -14 LUFS)
Tipo: T
Duración objetivo: 25-28 minutos (rango 25-28 min)

---

## 1. Filosofía del episodio T

Un episodio T es **una pieza formativa-técnica sobre un tema concreto del
máster**, con ejemplos y aplicación empresarial real. Sirve a:

- Estudiantes del máster que cursan ese módulo (audiencia principal).
- Formación sobre el concepto + aplicación empresarial real documentada.
- Publicación agrupada por módulo (M + sus T como unidad coherente).

**Lo que un T NO es:**

- No es una clase. No agota el tema. Tiene un ángulo concreto.
- No es una hot take. Tiene cuerpo divulgativo, no solo postura.
- No es promocional. **No habla del sistema que lo genera** (eso es trabajo del
  M). El T SÍ tiene aplicación empresarial real — casos de empresa, datos de
  adopción, retos — pero de la IA en general, no del sistema de producción.
- **No tiene APLICACION_PRACTICA del sistema generador**: exclusivo del M.

---

## 2. Principios duros

- Priorizar claridad antes que estilo.
- No huir de la explicación técnica, pero aterrizar siempre con ejemplos
  cotidianos antes de la traslación técnica.
- Mantener tono divulgativo-técnico, riguroso y accesible.
- Episodios de **25 a 28 min**. Se prefiere extender duración antes que dejar un
  concepto sin aterrizar; si el primer corte pasa de 30 min, partir en dos
  episodios (`T_xa` / `T_xb`), no comprimir.
- Empezar siempre con hook que cumpla una de las 3 plantillas (§5).
- **Apertura por paridad del número de TEMA (no del módulo):** impares Yago,
  pares Maria. T1 → Yago, T2 → Maria, T3 → Yago, T4 → Maria, etc.
- **Quien abre el episodio también dice el aviso de IA y abre el HOOK.**
- Usar "Yago" dentro del texto hablado, nunca "Iago".
- Aviso de IA dentro del SALUDO_Y_PRESENTACION en versión advertencia (§6).
- **6 bloques de contenido obligatorios**: PANORAMA, COMO, CASOS, LIMITES,
  FUENTES (§3).
- **Exactamente 3 conceptos** en CIERRE_CONCEPTOS, ni más ni menos.
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
5.  # BLOQUE_COMO
6.  # BLOQUE_CASOS
7.  # BLOQUE_LIMITES
8.  # BLOQUE_FUENTES
9.  # CIERRE_CONCEPTOS
10. # CIERRE_FINAL
11. # VERIFICACIONES
```

**Función y duración de cada bloque** (objetivo de episodio: 27 min de referencia):

| Bloque | Duración | Palabras (obj/min/max) | Función | Líder |
|---|---|---|---|---|
| HOOK | 30-60s | 90-110 / 75 / 120 | Gancho + cita canónica | Por paridad del tema |
| INTRO_SONIDO | 5-10s | 0 (música) | Stinger sonoro, no genera audio | — |
| SALUDO_Y_PRESENTACION | 60-90s | 175-220 / 150 / 240 | Saludo + aviso de IA advertencia | Quien abre |
| BLOQUE_PANORAMA | 3-4 min | 525-600 / 450 / 660 | Qué es, dónde encaja, por qué importa | Yago ≥65% |
| BLOQUE_COMO | 5-6 min | 825-900 / 750 / 990 | Mecanismo, cómo funciona técnicamente | Compartido 40-60% |
| BLOQUE_CASOS | 4-5 min | 660-750 / 600 / 825 | Casos reales de empresa con nombre propio | Maria ≥60% |
| BLOQUE_LIMITES | 3-4 min | 525-600 / 450 / 660 | Qué NO es, confusiones, cuándo no usarlo | Yago ≥55% |
| BLOQUE_FUENTES | 2-3 min | 360-450 / 300 / 495 | Las 3 fuentes que más importan del tema | Compartido |
| CIERRE_CONCEPTOS | 1-2 min | 200-300 / 150 / 330 | Exactamente 3 conceptos canónicos | Por paridad |
| CIERRE_FINAL | 30-60s | 90-150 / 75 / 165 | Cierre canónico + puente al siguiente T | Por paridad |
| VERIFICACIONES | — | — | Validación interna (no audio) | — |

**Total word count: objetivo 3700-4500 · hard-fail < 2925 o > 4485.**

No hay `APLICACION_PRACTICA` (prohibido en T). No hay `INSERCION`.

---

## 4. Roles de los presentadores (líder por bloque)

### 4.1 Asignación de líder por bloque

| Bloque | Líder | Apoyo | Lógica |
|---|---|---|---|
| HOOK | Por paridad del nº de TEMA | El otro | T impares Yago, T pares Maria |
| SALUDO_Y_PRESENTACION | Quien abre | El otro | Aviso de IA dicho por quien abre |
| BLOQUE_PANORAMA | **Yago ≥65%** | Maria | Mapa, definición, contexto: territorio explicador |
| BLOQUE_COMO | **Compartido 40-60%** | — | Líder rota por subtema, ver §4.2 |
| BLOQUE_CASOS | **Maria ≥60%** | Yago | Casos de empresa con nombre propio: territorio escéptica experta |
| BLOQUE_LIMITES | **Yago ≥55%** | Maria | Qué NO es / cuándo no usarlo: territorio explicador crítico |
| BLOQUE_FUENTES | **Compartido** | — | 3 fuentes del tema, alternando |
| CIERRE_CONCEPTOS | Por paridad | El otro | 3 conceptos, alternando 1-a-1 |
| CIERRE_FINAL | Por paridad | El otro | Cita canónica + puente al siguiente T |

### 4.2 "Compartido por subtema" en BLOQUE_COMO

No es turno-a-turno corto. Es por subtema. Si el bloque cubre 2-3 mecanismos,
cada subtema tiene un líder claro; el líder da la explicación principal (4-8
frases), el otro hace 1-2 intervenciones de pregunta o matiz.
**Reparto global de BLOQUE_COMO entre 40% y 60% para cada speaker.**

### 4.3 Perfiles de los presentadores

- **Yago = explicador técnico.** Profundidad, terminología precisa, mecanismo.
  Lleva BLOQUE_PANORAMA y BLOQUE_LIMITES, y buena parte de BLOQUE_COMO.
- **Maria = voz experta de empresa + oyente exigente.** En BLOQUE_CASOS es la
  voz principal: presenta casos reales, datos de adopción y retos documentados
  (mínimo 5 intervenciones de desarrollo, ≥4 frases cada una). Yago aporta
  contexto técnico breve (máximo 2 intervenciones, ≤3 frases). Si Yago habla más
  que Maria en BLOQUE_CASOS, el guion está incorrecto. **No es asistente.**

### 4.4 Lista negra de interjecciones (anti-NotebookLM)

**Prohibido en todos los episodios (hard-fail):**
"Exactamente", "Claro que sí", "Muy bien dicho", "Tienes toda la razón",
"Exacto", "Por supuesto", "Eso es", "Totalmente".

Sí están permitidas: respuestas que matizan, repreguntan, discrepan o cambian
de ángulo. La lista negra es solo para validación-coro.

### 4.5 Reglas de longitud y reparto

- Intervenciones de desarrollo: **mínimo 4 frases** en bloques centrales.
- Intervenciones de reacción o pregunta: máximo 12 palabras, máximo 3 por bloque.
- **Conteo de palabras por bloque y speaker (hard-fail si se incumple):**
  - BLOQUE_PANORAMA: Yago ≥65%.
  - BLOQUE_COMO: cada uno entre 40-60% globalmente.
  - BLOQUE_CASOS: Maria ≥60%.
  - BLOQUE_LIMITES: Yago ≥55%.
- **Anti-pingpong:** apoyo máximo 1 cada 3 intervenciones del líder.
- **Apertura del bloque:** quien lidera siempre abre el bloque.

### 4.6 Tecnicismos

- Traducir y aterrizar al castellano cualquier término técnico o inglés
  relevante en la misma intervención.
- No acumular más de dos tecnicismos seguidos sin frase de aterrizaje.

---

## 5. Hook: menú de 3 plantillas

El generador elige la plantilla que mejor sostiene el tema del PDF. No hay
plantilla por defecto; si el PDF no soporta ninguna, se regenera.

- **Plantilla A — Hook-dato.** Una cifra contundente, su consecuencia, la
  promesa del episodio.
- **Plantilla B — Hook-pregunta-incómoda.** Una afirmación que el oyente quiere
  refutar pero no puede.
- **Plantilla C — Hook-caso.** Un evento concreto con nombre propio y fecha.

**Reglas duras del hook:**
- 30-60 segundos hablados.
- Cierra exactamente con: `Esto es MaquinarIA Pesada. Arrancamos.`
- **Apertura por paridad del número de TEMA:** T impares Yago abre, T pares
  Maria abre.

---

## 6. Aviso de generación por IA — versión advertencia

**Dentro de SALUDO_Y_PRESENTACION**, justo después de la presentación de
nombres. Lo dice **el mismo speaker que abrió el HOOK por paridad**.

### 6.0 Formato obligatorio del SALUDO_Y_PRESENTACION

Mínimo **3 intervenciones separadas**, en este orden:
1. `{opener}: Soy {opener_name}.`
2. `{otro}: Y yo soy {otro_name}.`
3. `{opener}: [tag] Antes de empezar... {aviso completo}`

**Hard-fail si:** una sola intervención contiene los dos nombres; o el aviso lo
dice un speaker distinto del opener.

**Prohibido: apellidos.** Hard-fail con regex
`\b(Maria|Yago)\s+[A-ZÁÉÍÓÚÑ][a-zñáéíóú]+\b`.

### Forma para episodios T (versión advertencia, 12-18s)

> "Antes de empezar, el aviso de siempre: este episodio lo genera un sistema
> automático de inteligencia artificial. Puede contener errores. Si oyes algo
> que no te cuadra, contrástalo."

**Reglas:**
- Obligatorio en todos los T. **Hard-fail si falta.**
- Debe contener literalmente **"sistema automatico"** y **"puede contener
  errores"** (hard-fail si faltan).
- **Lo dice el mismo speaker que abrió el HOOK** (hard-fail si lo dice el otro).
- Duración 12-18 segundos. Aquí el aviso advierte, no engancha (eso es del M).
  Pausa SSML de 400ms antes y después.

---

## 7. Reglas de contenido y fuentes

### 7.1 Pre-escritura obligatoria

Antes de escribir el guion, el generador rellena internamente esta tabla a
partir del PDF del tema:

```
- 3 datos numéricos con cifra concreta (porcentajes, $, años)
- 2 casos con nombre propio (empresa, paper, autor)
- 1 frase-fuerza del resumen ejecutivo del PDF
- 2 contraintuitivos del tema (lo que el oyente NO esperaría)
```

**Regla dura:** al menos uno de cada categoría debe aparecer dentro de los
**primeros 90 segundos hablados**.

### 7.2 Fuentes del generador

**Fuente primaria (obligatoria, hard-fail si no se lee):**
- PDF del tema en `PDFs/temas/M{n}_T{x}_*.pdf`.
- El generador DEBE leerlo como input; los tokens deben quedar en VERIFICACIONES
  (`tokens > 0`). Cobertura ≥75%. Hard-fail si `tokens=0` o cobertura<75%.

**Fuentes secundarias (uso obligatorio cuando aplique):**
1. `PDFs/auxiliares/glosario_unificado.md` — definiciones canónicas. Regla dura:
   cualquier término técnico que esté en el glosario debe respetar su
   definición canónica. Hard-fail si no existe el archivo.
2. `PDFs/auxiliares/casos_empresariales_ia.md` — **fuente obligatoria para
   BLOQUE_CASOS.** Usar antes que inventar datos.
3. `PDFs/auxiliares/benchmarks_academicos.md` — máximo 1 mención por episodio,
   preferiblemente en el HOOK.
4. `PDFs/auxiliares/fuentes_directas.md` — papers, documentación oficial.
   Alimenta `BLOQUE_FUENTES`; máximo según las 3 fuentes del bloque.

**Regla anti-relleno:** las fuentes secundarias sustituyen contenido genérico
por específico, no añaden volumen.

**Prioridad ante conflicto:** si una fuente secundaria contradice al PDF
principal, prevalece el PDF principal (soft-warn).

### 7.3 Reglas generales de contenido

- Cubrir al menos el **75%** de los conceptos clave del PDF del tema.
- Cada concepto técnico complejo va seguido de una **analogía cotidiana en ≤2
  frases** antes de la traslación corporativa. Marcadores libres: "imagina
  que", "es como cuando", "piensa en", "el equivalente sería", "en tu día a
  día", "igual que", "lo mismo que pasa cuando".
- Soft-warn si un término técnico denso aparece en BLOQUE_COMO sin ningún
  marcador de analogía en las 6 frases siguientes.
- Si un concepto del PDF es muy visual para audio, justificar su ausencia en
  VERIFICACIONES.

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

## 8. BLOQUE_CASOS (nuevo en v6)

### 8.1 Función

Aterrizar el tema en casos reales de empresa con nombre propio. Reemplaza y
expande al antiguo `BLOQUE_REALIDAD`, con foco puramente en casos individuales
(no en datos agregados de adopción, que pueden aparecer como contexto).

### 8.2 Reglas del bloque

- Duración 4-5 min, 660-750 palabras. Lidera **Maria ≥60%**.
- **Mínimo 2 casos de empresa con nombre propio** + resultado concreto
  (soft-warn si solo hay 1, hard-fail si hay 0).
- Fuente obligatoria: `PDFs/auxiliares/casos_empresariales_ia.md`. Usar antes
  que inventar.
- Regla de datos: solo citar fuentes verificables; si no hay certeza, usar
  "según estudios recientes de [institución]" sin inventar cifras exactas.

---

## 9. BLOQUE_LIMITES (recuperado en v6)

### 9.1 Función

Cerrar el tratamiento del tema con "qué NO es esto / cuándo no usarlo". Ningún
competidor sintético se atreve con este bloque porque les complica el guion; a
MaquinarIA Pesada lo diferencia y lo protege de comentarios tipo "no es
exactamente así".

### 9.2 Reglas del bloque

- Duración 3-4 min, 525-600 palabras. Lidera **Yago ≥55%**.
- Contenido tipo "qué NO es": confusiones comunes, cuándo el concepto NO aplica,
  alternativas mejores en ciertos casos.
- Validador semántico: el bloque debe contener patrones tipo "no es", "no debe
  confundirse con", "el error común es", "cuándo no" (soft-warn si no aparece
  ninguno).

---

## 10. BLOQUE_FUENTES (nuevo en v6)

### 10.1 Función

Cerrar el T entregando **las 3 fuentes que más importan del tema**, citables y
verificables. Convierte el T en pieza de autoridad técnica.

### 10.2 Reglas del bloque

- Duración 2-3 min, 360-450 palabras. Compartido entre voces.
- Citar **exactamente 3 fuentes** del tema (hard-fail si ≠3).
- Cada fuente lleva nombre canónico (autor + año + título) y una frase de por
  qué importa.
- **No leer URLs ni rutas en audio** (soft-warn). Las URLs van en la descripción
  del episodio.
- Fuente: `PDFs/auxiliares/fuentes_directas.md` + las fuentes citadas en el PDF
  del tema.

---

## 11. Cierre

### 11.1 CIERRE_CONCEPTOS

- Abre con: `No te puedes ir de este capitulo sin haber entendido estos conceptos`
- **EXACTAMENTE 3 conceptos**, ni 4 ni 5 (hard-fail si hay otra cantidad).
- Cada concepto en una frase, no expandidos.
- Los 3 conceptos se alternan entre Yago y Maria.

### 11.2 CIERRE_FINAL

Debe incluir literalmente:
> "Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada. Siguenos para
> nuevos capitulos donde la I.A. crea contenido sobre I.A."

Incluye un **puente al siguiente T** del módulo (conexión natural, no anuncio).

---

## 12. Etiquetas TTS

- Una sola etiqueta por intervención, al inicio del texto.
- Las etiquetas son instrucciones de tono, no separadores de microfrases.
- Lista cerrada: didactico, explicativo, directo, serio, firme, contundente,
  grave, tenso, conversacional, reflexivo, curioso, ironico, esceptico, natural,
  pausado, calido, claro, analitica.

---

## 13. Reglas de producción de audio

El guion debe cumplirlas antes de enviarse a síntesis (ElevenLabs eleven_v3 a
1.20× + 1.10× post = **1.32× total**).

- **Audio-Regla 1 — Números siempre en palabras** (conversión >100 vía
  `num2words`). Excepción: años de papers.
- **Audio-Regla 2 — Longitud óptima de intervención.** 60-120 palabras zona
  óptima; reacción/pregunta 5-12 palabras (hard-fail si >15); máximo absoluto
  200 palabras.
- **Audio-Regla 3 — Tags TTS guían el estilo de escritura**, no los parámetros
  de ElevenLabs (`style=0.0` hardcodeado).
- **Audio-Regla 4 — Tecnicismos acelerados: introducción obligatoria.**
- **Audio-Regla 5 — INTRO_SONIDO: documentación, no generación.**
- **Audio-Regla 6 (nueva v6) — Pausas SSML explícitas.** Entre bloques
  800-1200ms; intra-bloque 400-600ms; fin de HOOK 600ms; aviso de IA 400ms;
  cambio de speaker 400-600ms.
- **Audio-Regla 7 (nueva v6) — Loudness -14 LUFS** integrated, -1 dBTP.

---

## 14. Configuración (JSON)

<!-- PODCAST_T_SPEC_JSON_START -->
```json
{
  "version": "2026-05-14-v6",
  "spec_type": "T",
  "project_name": "MaquinarIA Pesada",
  "language": "es",
  "directories": {
    "pdfs_dir": "PDFs",
    "pdfs_temas_dir": "PDFs/temas",
    "pdfs_auxiliares_dir": "PDFs/auxiliares",
    "scripts_dir": "Guiones",
    "output_dir": "episodios",
    "temp_dir": "episodios/temp",
    "videos_dir": "Videos",
    "music_dir": "Música",
    "intro_dir": "intro",
    "logos_dir": "Logos",
    "default_logo": "Logos/logo sin fondo.png"
  },
  "anthropic": {
    "default_generation_model": "claude-sonnet-4-6",
    "default_concept_model": "claude-haiku-4-5-20251001",
    "temperature": 0.7,
    "max_output_tokens": 12000,
    "stream": true,
    "retry_on_hard_fail": {
      "max_retries": 1,
      "strategy": "explicit_feedback_to_llm"
    }
  },
  "episode_defaults": {
    "duration_minutes": 27,
    "duration_range_minutes": [25, 28],
    "target_audience": "Profesionales tecnicos curiosos sobre como funciona la IA por dentro. CTOs/CIOs/CEOs y profesionales de IT como audiencia secundaria. Toda concepto complejo se aterriza con analogia cotidiana antes de la traslacion tecnica.",
    "tone": "divulgativo tecnico, riguroso pero accesible",
    "hook_style": "menu_3_plantillas",
    "minimum_audio_minutes": 24.0,
    "maximum_audio_minutes": 30.0,
    "split_if_over_minutes": 30
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
    "applies_to": "tema_number",
    "rule": "T_impar_yago_abre__T_par_maria_abre",
    "opener_does_hook_and_aviso": true,
    "examples": {
      "M1_T1": "Yago abre", "M1_T2": "Maria abre", "M3_T2": "Maria abre",
      "M7_T1": "Yago abre", "M8_T1": "Yago abre", "M10_T5": "Yago abre",
      "M12_T2": "Maria abre"
    }
  },
  "speakers": {
    "IAGO": {
      "display_name": "Iago",
      "spoken_name": "Yago",
      "opens_odd_temas": true,
      "opens_even_temas": false,
      "role": "explicador_tecnico",
      "leads_blocks": ["BLOQUE_PANORAMA", "BLOQUE_LIMITES"],
      "shares_blocks": ["BLOQUE_COMO", "BLOQUE_FUENTES"],
      "supports_blocks": ["BLOQUE_CASOS"],
      "traits": ["grave", "contundente", "tecnico"],
      "allowed_tags": ["didactico", "explicativo", "directo", "serio", "firme", "contundente", "grave", "tenso", "conversacional", "reflexivo", "curioso", "ironico", "esceptico", "natural", "pausado", "calido", "claro", "analitica"]
    },
    "MARIA": {
      "display_name": "Maria",
      "spoken_name": "Maria",
      "opens_odd_temas": false,
      "opens_even_temas": true,
      "role": "voz_experta_empresa_y_oyente_exigente",
      "leads_blocks": ["BLOQUE_CASOS"],
      "shares_blocks": ["BLOQUE_COMO", "BLOQUE_FUENTES"],
      "supports_blocks": ["BLOQUE_PANORAMA", "BLOQUE_LIMITES"],
      "traits": ["clara", "analitica", "incisiva"],
      "allowed_tags": ["didactico", "explicativo", "directo", "serio", "firme", "contundente", "grave", "tenso", "conversacional", "reflexivo", "curioso", "ironico", "esceptico", "natural", "pausado", "calido", "claro", "analitica"]
    }
  },
  "script_rules": {
    "required_sections": [
      "HOOK", "INTRO_SONIDO", "SALUDO_Y_PRESENTACION",
      "BLOQUE_PANORAMA", "BLOQUE_COMO", "BLOQUE_CASOS", "BLOQUE_LIMITES",
      "BLOQUE_FUENTES", "CIERRE_CONCEPTOS", "CIERRE_FINAL", "VERIFICACIONES"
    ],
    "forbidden_sections": [
      "BLOQUE_1", "BLOQUE_2", "BLOQUE_3", "BLOQUE_4",
      "BLOQUE_QUE", "BLOQUE_TEMAS_CLAVE", "BLOQUE_DESTACADO", "BLOQUE_REALIDAD",
      "INSERCION_1", "INSERCION_2", "INSERCION_3", "INSERCION_EMPRESA",
      "APLICACION_PRACTICA"
    ],
    "max_consecutive_blocks_same_speaker": 2,
    "key_concepts_block_count_exact": 3,
    "minimum_word_count": 3700,
    "maximum_word_count": 4500,
    "hard_fail_word_count_min": 2925,
    "hard_fail_word_count_max": 4485,
    "minimum_sentences_per_intervention": 4,
    "maximum_sentences_per_intervention": 9,
    "reaction_word_limit": 30,
    "max_reactions_per_block": 3,
    "target_avg_words_per_intervention_min": 60,
    "target_avg_words_per_intervention_max": 120,
    "target_max_words_per_single_intervention": 200,
    "hard_fail_on_digits_in_dialogue": false,
    "minimum_pdf_coverage_percent": 75,
    "leader_share_min_percent": 65,
    "leader_share_min_percent_casos": 60,
    "leader_share_min_percent_limites": 55,
    "shared_block_balance_range_percent": [40, 60],
    "support_intervention_ratio_max": "1_per_3_leader",
    "leader_opens_block": true,
    "block_word_targets": {
      "HOOK": {"min": 75, "target": 100, "max": 120},
      "SALUDO_Y_PRESENTACION": {"min": 150, "target": 200, "max": 240},
      "BLOQUE_PANORAMA": {"min": 450, "target": 560, "max": 660},
      "BLOQUE_COMO": {"min": 750, "target": 860, "max": 990},
      "BLOQUE_CASOS": {"min": 600, "target": 700, "max": 825},
      "BLOQUE_LIMITES": {"min": 450, "target": 560, "max": 660},
      "BLOQUE_FUENTES": {"min": 300, "target": 400, "max": 495},
      "CIERRE_CONCEPTOS": {"min": 150, "target": 250, "max": 330},
      "CIERRE_FINAL": {"min": 75, "target": 120, "max": 165}
    },
    "bloque_casos": {
      "duration_seconds_min": 240,
      "duration_seconds_max": 300,
      "leader": "MARIA",
      "leader_share_min_percent": 60,
      "min_company_cases_with_proper_name": 2,
      "source_required": "PDFs/auxiliares/casos_empresariales_ia.md"
    },
    "bloque_limites": {
      "duration_seconds_min": 180,
      "duration_seconds_max": 240,
      "leader": "IAGO",
      "leader_share_min_percent": 55,
      "semantic_patterns_expected": ["no es", "no debe confundirse con", "el error comun es", "cuando no"]
    },
    "bloque_fuentes": {
      "duration_seconds_min": 120,
      "duration_seconds_max": 180,
      "sources_count_exact": 3,
      "no_urls_in_speech": true,
      "source_files": ["PDFs/auxiliares/fuentes_directas.md"]
    },
    "hook_closing_phrase": "Esto es MaquinarIA Pesada. Arrancamos.",
    "hook_duration_seconds": [30, 60],
    "intro_comment": "[INTRO - SONIDO DE MAQUINAS ARRANCANDO - 8-10 segundos]",
    "warning_phrase_keywords_required": ["sistema automatico", "puede contener errores"],
    "warning_must_be_said_by_opener": true,
    "warning_duration_seconds": [12, 18],
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
      "datos_numericos_min": 3,
      "casos_nombre_propio_min": 2,
      "frase_fuerza_min": 1,
      "contraintuitivos_min": 2,
      "must_appear_in_first_seconds": 90
    },
    "sources": {
      "primary": {
        "path_pattern": "PDFs/temas/M{n}_T{x}_*.pdf",
        "required": true,
        "must_be_read_by_generator": true,
        "min_concept_coverage_percent": 75,
        "min_input_tokens_reported": 5000
      },
      "secondary": {
        "glossary": {"path": "PDFs/auxiliares/glosario_unificado.md", "required": true, "rule": "respect_canonical_definitions"},
        "casos_empresariales": {"path": "PDFs/auxiliares/casos_empresariales_ia.md", "required": true, "rule": "use_prioritarily_in_BLOQUE_CASOS", "note": "Fuente obligatoria para BLOQUE_CASOS. Usar antes que inventar datos."},
        "benchmarks": {"path": "PDFs/auxiliares/benchmarks_academicos.md", "required": false, "max_uses_per_episode": 1, "preferred_location": "HOOK"},
        "direct_sources": {"path": "PDFs/auxiliares/fuentes_directas.md", "required": false, "rule": "feeds_BLOQUE_FUENTES", "note": "Alimenta las 3 fuentes de BLOQUE_FUENTES."}
      },
      "anti_inflation_rule": "auxiliary_sources_replace_not_add",
      "conflict_resolution": {"secondary_vs_primary": "primary_wins_softwarn"}
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
    "hard_fail_on_concepts_count_not_exact_3": true,
    "hard_fail_on_missing_primary_source": true,
    "hard_fail_on_zero_input_tokens": true,
    "hard_fail_on_pdf_coverage_below_75": true,
    "hard_fail_on_missing_glossary": true,
    "hard_fail_on_missing_casos_empresariales_source": true,
    "hard_fail_on_zero_company_cases_in_casos": true,
    "hard_fail_on_fuentes_count_not_exact_3": true,
    "hard_fail_on_word_count_out_of_hard_range": true,
    "hard_fail_on_saludo_collapsed_single_block": true,
    "hard_fail_on_presenter_surname_invented": true,
    "hard_fail_on_shared_block_balance": true,
    "hard_fail_on_intervention_over_max_words": true,
    "hard_fail_on_missing_cta_in_final": false,
    "soft_warn_on_missing_preescritura_evidence": true,
    "soft_warn_on_pingpong_pattern": true,
    "soft_warn_on_secondary_vs_primary_conflict": true,
    "soft_warn_on_unused_benchmark_when_relevant": true,
    "soft_warn_on_temporal_reference_without_publication_context": true,
    "soft_warn_on_missing_everyday_analogy_after_complex_concept": true,
    "soft_warn_on_digit_numbers_in_dialogue": true,
    "soft_warn_on_intervention_over_200_words": true,
    "soft_warn_on_single_company_case_in_casos": true,
    "soft_warn_on_limites_without_semantic_patterns": true,
    "soft_warn_on_urls_in_fuentes_speech": true,
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
    "applies_to_blocks": ["BLOQUE_PANORAMA", "BLOQUE_COMO"],
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
    "cost_tracking_log": "costes_generacion.log"
  }
}
```
<!-- PODCAST_T_SPEC_JSON_END -->
