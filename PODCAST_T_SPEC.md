# Podcast T Spec — MaquinarIA Pesada

Especificación normativa para generar guiones y audio de **episodios T (Temas)**:
los ~100 episodios del corpus del máster, uno por tema individual.

Reemplaza al spec genérico anterior **solo para episodios T**. Los episodios M
(resúmenes de módulo) tienen su propio spec en `PODCAST_M_SPEC.md`.

Versión: 2026-05-12 (v5 — rediseño de bloques: BLOQUE_PANORAMA + BLOQUE_REALIDAD, reglas audio TTS, word count 1400-1800)
Tipo: T
Duración objetivo: 11 minutos (rango 10-13 min)

---

## 1. Filosofía del episodio T

Un episodio T es **una pieza formativa-técnica corta sobre un tema concreto**
del máster. Sirve a:

- Estudiantes del máster que cursan ese módulo (audiencia principal).
- Formación sobre el concepto + aplicación empresarial real documentada.
- Publicación agrupada por módulo (todos los T de un módulo a la vez).

**Lo que un T NO es:**

- No es una clase. No agota el tema.
- No es una hot take. Tiene cuerpo divulgativo, no solo postura.
- No es promocional. No habla del sistema que lo genera (eso es trabajo del M).
- No es genérico. Cada T tiene un ángulo concreto, no es "todo sobre X".
- **No tiene APLICACION_PRACTICA del sistema generador**: eso es exclusivo del M.
  El T SÍ tiene aplicación empresarial real (casos de empresa, datos de adopción,
  retos y oportunidades), pero de la IA en general, no del sistema de producción.

---

## 2. Principios duros

- Priorizar claridad antes que estilo.
- No huir de la explicación técnica, pero aterrizar siempre con ejemplos cotidianos antes de la traslación técnica.
- Mantener tono divulgativo-técnico, riguroso y accesible.
- Episodios de **10 a 13 min**, objetivo práctico **11 min**. Se prefiere extender duración antes que dejar un concepto sin aterrizar.
- Empezar siempre con hook que cumpla una de las 3 plantillas (§5).
- **Apertura por paridad del número de TEMA (no del módulo):** impares Yago,
  pares Maria. T1 → Yago, T2 → Maria, T3 → Yago, T4 → Maria, etc.
- **Quien abre el episodio también dice el aviso de IA y abre el HOOK.** Si
  por paridad le toca Maria abrir, Maria lee el HOOK y el aviso.
- Usar "Yago" dentro del texto hablado, nunca "Iago".
- Aviso de IA dentro del SALUDO_Y_PRESENTACION en versión advertencia (§6).
- El bloque INSERCION_EMPRESA del spec viejo desaparece en el T.
- **Exactamente 3 conceptos** en CIERRE_CONCEPTOS, ni más ni menos.
- Verificaciones reales del guion al final del archivo generado.
- Validación real del audio y reporte de créditos en el log.

---

## 3. Estructura obligatoria del guion

```
1.  # HOOK
2.  # INTRO_SONIDO
3.  # SALUDO_Y_PRESENTACION
4.  # BLOQUE_PANORAMA
5.  # BLOQUE_COMO
6.  # BLOQUE_REALIDAD
7.  # CIERRE_CONCEPTOS
8.  # CIERRE_FINAL
9.  # VERIFICACIONES
```

**Tres bloques de contenido, función diferenciada:**

- **BLOQUE_PANORAMA** (~2-2.5 min): qué es el tema, definición operativa, por qué
  importa. Apertura del aprendizaje. Lidera Yago.
- **BLOQUE_COMO** (~3-4 min): cómo funciona por dentro, el mecanismo. Es el
  núcleo del episodio. Compartido 40-60% entre ambos.
- **BLOQUE_REALIDAD** (~2-3 min): fusiona los límites técnicos del concepto con
  la aplicación empresarial real documentada. Lidera Maria (≥60%).
  **Contenido obligatorio** — mínimo 2 de los 4 elementos:
  1. Dato de adopción de IA con fuente reconocida (Gartner, McKinsey, WEF, IDC, MIT, Stanford)
  2. Caso real de empresa usando el concepto (nombre de empresa + resultado concreto)
  3. Reto documentado que enfrentan las empresas con este concepto
  4. Oportunidad concreta de negocio derivada del concepto
  **Fuente obligatoria**: usar prioritariamente `PDFs/auxiliares/casos_empresariales_ia.md`.
  **Regla de datos**: solo citar fuentes verificables; si no hay certeza, usar
  "según estudios recientes de [institución]" sin inventar cifras exactas.

No hay BLOQUE_4 ni INSERCION. No hay APLICACION_PRACTICA (prohibido en T).

---

## 4. Roles de los presentadores (líder por bloque)

Los dos presentadores **no son intercambiables**. Cada uno tiene territorio
asignado por bloque.

### 4.1 Asignación de líder por bloque

| Bloque | Líder | Apoyo | Lógica |
|---|---|---|---|
| HOOK | Por paridad del nº de TEMA | El otro | T impares Yago, T pares Maria |
| SALUDO_Y_PRESENTACION | Quien abre | El otro | Aviso de IA dicho por quien abre |
| **BLOQUE_PANORAMA** | **Yago** | Maria | Mapa, definición, contexto: territorio explicador |
| **BLOQUE_COMO** | **Compartido por subtema** | — | Líder rota por subtema, ver §4.2 |
| **BLOQUE_REALIDAD** | **Maria** | Yago | Casos empresa, datos adopción, retos: territorio escéptica experta |
| CIERRE_CONCEPTOS | Por paridad | El otro | 3 conceptos, alternando 1-a-1 entre ambos |
| CIERRE_FINAL | Por paridad | El otro | Cita canónica |

### 4.2 Cómo funciona "compartido por subtema" en BLOQUE_COMO

No es turno-a-turno corto. Es por subtema. Si el bloque cubre 2-3 mecanismos,
cada subtema tiene un líder claro:

- Subtema 1 → Yago lidera, Maria pregunta de aterrizaje.
- Subtema 2 → Maria lidera con ángulo más concreto/aplicado.
- Subtema 3 → Yago si hay otro mecanismo abstracto.

Regla operativa: el líder del subtema da la explicación principal (4-8 frases).
El otro hace 1-2 intervenciones de pregunta o matiz dentro del subtema.
**Reparto global de BLOQUE_COMO debe quedar entre 40% y 60% para cada speaker.**

### 4.3 Perfiles de los presentadores

- **Yago = explicador técnico.** Profundidad, terminología precisa, mecanismo.
  Lleva la mayor parte del peso conceptual de BLOQUE_PANORAMA y BLOQUE_COMO.
- **Maria = voz experta de empresa + oyente exigente.** En BLOQUE_REALIDAD,
  Maria es la voz principal: presenta casos reales, datos de adopción y retos
  documentados (mínimo 5 intervenciones de desarrollo, ≥4 frases cada una).
  Yago aporta contexto técnico breve cuando sea necesario (máximo 2 intervenciones,
  ≤3 frases cada una). Si Yago habla más que Maria en BLOQUE_REALIDAD, el guion
  está incorrecto. En otros bloques cuestiona, tensa, pide aterrizar.
  **No es asistente.** No valida, no aplaude, no asiente.

### 4.4 Lista negra de interjecciones (anti-NotebookLM)

**Prohibido en todos los episodios:**

- "Exactamente"
- "Claro que sí"
- "Muy bien dicho"
- "Tienes toda la razón"
- "Exacto"
- "Por supuesto"
- "Eso es"
- "Totalmente"

Si el generador produce una de estas como interjección de validación, el
episodio se rechaza en QA y se regenera. **Hard-fail.**

Sí están permitidas: respuestas que matizan, repreguntan, discrepan o cambian
de ángulo. La lista negra es solo para validación-coro.

### 4.5 Reglas de longitud y reparto

- Intervenciones de desarrollo: **mínimo 4 frases** en BLOQUE_QUE, BLOQUE_COMO,
  BLOQUE_LIMITES.
- Intervenciones de reacción o pregunta: máximo 12 palabras, máximo 3 por bloque.
- **Conteo de palabras por bloque y speaker (hard-fail si se incumple):**
  - En BLOQUE_PANORAMA: Yago ≥65% de palabras del bloque.
  - En BLOQUE_REALIDAD: Maria ≥60% de palabras del bloque.
  - En BLOQUE_COMO: cada uno entre 40-60% globalmente.
- **Anti-pingpong:** dentro de bloque liderado por uno, intervenciones del apoyo
  máximo 1 cada 3 intervenciones del líder.
- **Apertura del bloque:** quien lidera siempre abre el bloque con su intervención.

### 4.6 Tecnicismos

- Traducir y aterrizar al castellano cualquier término técnico o inglés
  relevante en la misma intervención.
- No acumular más de dos tecnicismos seguidos sin frase de aterrizaje.

---

## 5. Hook: menú de 3 plantillas

El generador elige la plantilla que mejor sostiene el tema del PDF. **No hay
plantilla por defecto.** Si el PDF no soporta ninguna, se regenera con
parámetros distintos antes de aceptar.

### Plantilla A — Hook-dato

Una cifra contundente, su consecuencia, la promesa del episodio.

> "El 88% de las empresas usa IA. Solo el 33% la ha escalado. Hoy explicamos
> por qué la mayoría se queda en el camino."

### Plantilla B — Hook-pregunta-incómoda

Una afirmación que el oyente quiere refutar pero no puede.

> "Los modelos de lenguaje no razonan. Predicen. Y entender exactamente qué
> significa eso cambia cómo los usas en tu empresa."

### Plantilla C — Hook-caso

Un evento concreto con nombre propio y fecha, qué reveló.

> "PoisonGPT, 2023. Investigadores modificaron quirúrgicamente los pesos de
> un LLM para que mintiera sobre temas concretos. Pasó todos los benchmarks
> estándar."

**Reglas duras del hook:**

- 30-45 segundos hablados.
- Cierra exactamente con: `Esto es MaquinarIA Pesada. Arrancamos.`
- **Apertura por paridad del número de TEMA: T impares Yago abre, T pares Maria abre.**

---

## 6. Aviso de generación por IA

**Dentro de SALUDO_Y_PRESENTACION**, justo después de la presentación de
nombres. Lo dice **el mismo speaker que abrió el HOOK por paridad**.

### 6.0 Formato obligatorio del SALUDO_Y_PRESENTACION

El bloque debe tener **mínimo 3 intervenciones separadas**, en este orden:

1. `{opener}: Soy {opener_name}.`
2. `{otro}: Y yo soy {otro_name}.`
3. `{opener}: [tag] Antes de empezar... {aviso completo}`

**Hard-fail si**:
- Una sola intervención contiene los dos nombres ("Soy Maria. Y yo soy Yago.") — el segundo nombre debe estar en una intervención del otro speaker.
- El aviso lo dice cualquier speaker distinto del opener.

**Prohibido: apellidos**. Los presentadores se llaman **Maria** y **Yago**, sin apellidos. No "Maria Grandury", no "Yago Goyoaga". Hard-fail si aparecen.

### Forma para episodios T (versión advertencia, 12-15s)

> "Antes de empezar, el aviso de siempre: este episodio lo genera un sistema
> automático de inteligencia artificial. Puede contener errores. Si oyes algo
> que no te cuadra, contrástalo."

**Reglas:**

- Obligatorio en todos los episodios T sin excepción. **Hard-fail si falta.**
- Debe contener literalmente las palabras clave **"sistema automatico"** y
  **"puede contener errores"** (hard-fail si faltan).
- **Lo dice el mismo speaker que abrió el HOOK** (hard-fail si lo dice el otro).
- Duración 12-18 segundos.
- Sin variación enfática en T: aquí el aviso advierte, no engancha. Eso es
  trabajo del M.

---

## 7. Reglas de contenido y fuentes

### 7.1 Pre-escritura obligatoria

Antes de escribir el guion, el generador rellena internamente esta tabla a
partir del PDF:

```
- 3 datos numéricos con cifra concreta (porcentajes, $, años)
- 2 casos con nombre propio (empresa, paper, autor)
- 1 frase-fuerza del resumen ejecutivo del PDF
- 2 contraintuitivos del bloque (lo que el oyente NO esperaría)
```

**Regla dura:** al menos uno de cada categoría debe aparecer dentro de los
**primeros 90 segundos hablados** del episodio (HOOK + apertura de
BLOQUE_QUE). El resto, distribuidos en los bloques.

Si el PDF no aporta material para alguna categoría, se loguea en
VERIFICACIONES y se justifica.

### 7.2 Fuentes del generador

**Fuente primaria (obligatoria, hard-fail si no se lee):**

- PDF del tema en `PDFs/temas/M{n}_T{x}_*.pdf`.
- **El generador DEBE leer el PDF como input y los tokens deben quedar
  reflejados en VERIFICACIONES (`tokens > 0`).**
- Cobertura: mínimo 75% de los conceptos clave del PDF deben aparecer en el guion.
- Hard-fail si `tokens=0` en el reporte de Anthropic o si cobertura<75%.

**Fuentes secundarias (siempre disponibles, uso obligatorio cuando aplique):**

1. `PDFs/auxiliares/glosario_unificado.md`
   - Definiciones canónicas de términos técnicos del corpus.
   - Regla dura: cualquier término técnico que aparezca en el guion Y
     esté en el glosario debe respetar la definición canónica.

2. `PDFs/auxiliares/benchmarks_academicos.md`
   - Lista de currículos universitarios (CMU, Stanford, Oxford, UCL,
     King's, Florida, ETH, Sydney) que cubren el tema.
   - Uso opcional: el HOOK puede invocar autoridad académica si encaja
     ("El currículo público del máster de IA de Stanford dedica un
     módulo entero a esto..."). Cero clichés.
   - Máximo 1 mención por episodio.

3. `PDFs/auxiliares/fuentes_directas.md`
   - Lista de papers, documentación oficial y URLs canónicas.
   - Uso para citar de forma específica cuando un dato del PDF principal
     necesita respaldo ("según el paper de OpenAI/Anthropic/Google de
     2026...", o el año real del documento si la publicación es anterior).
   - Máximo 2 menciones por episodio.

**Regla anti-relleno:**

Las fuentes secundarias NO pueden inflar el guion. La duración objetivo
(10 min) no cambia. El uso de fuentes auxiliares sustituye contenido
genérico por contenido específico, no añade volumen.

**Regla de prioridad ante conflicto:**

Si una fuente secundaria contradice al PDF principal, prevalece el PDF
principal. Se loguea en VERIFICACIONES como soft-warn.

### 7.3 Reglas generales de contenido

- Cubrir al menos el **75%** de los conceptos clave del PDF del tema.
- **Cada concepto técnico complejo debe ir seguido de una analogía cotidiana en ≤2 frases**, antes (o como parte de) la traslación corporativa. La audiencia núcleo es técnica, pero la secundaria (CTO/CIO/CEO y oyente curioso) tiene que poder seguir el episodio sin sentirse expulsada por terminología. Es preferible alargar el episodio antes que dejar un concepto sin aterrizar.
- Marcadores aceptables (uso libre, sin léxico obligatorio): "imagina que", "es como cuando", "piensa en", "el equivalente sería", "en tu día a día", "igual que", "lo mismo que pasa cuando".
- Soft-warn si un término técnico denso aparece en BLOQUE_COMO sin ningún marcador de analogía cotidiana en las 6 frases siguientes.
- Si un concepto del PDF es muy visual para audio, justificar su ausencia en
  VERIFICACIONES.

### 7.4 Referencias temporales

Regla operativa para que el corpus envejezca bien:

- **Año por defecto: 2026** (año de producción del podcast). Cuando se hable del estado actual del mercado, de los modelos o de la práctica empresarial, **no se cita año**; se usan formas como "hoy", "actualmente", "en este momento", "ahora mismo".
- **Excepción única — publicaciones/informes/papers/eventos identificables**: ahí sí se conserva el año real ("el paper de Sennrich de 2016", "el estudio de Hugging Face de 2023", "el informe McKinsey State of AI 2025"). El año va siempre acompañado de un autor o publicación con nombre propio.
- **Prohibido**: usar 2024 o 2025 como marcador del presente. Hard-warn si se detecta `\b(2024|2025|dos mil veint(icuatro|icinco))\b` y en las 6 palabras anteriores NO aparece uno de: paper, informe, estudio, reporte, publicación, encuesta, según, lanzamiento, McKinsey, Hugging Face, Anthropic, OpenAI, Google, Meta, Gartner, IBM, IDC, Lucid, Forrester, Stanford.
- **Permitido sin etiqueta**: 2026 (presente), o años pasados narrados como historia ("el primer invierno llegó en los setenta", "los Transformers se publicaron en 2017").

---

## 8. Cierre

### 8.1 CIERRE_CONCEPTOS

- Abre con: `No te puedes ir de este capitulo sin haber entendido estos conceptos`
- **EXACTAMENTE 3 conceptos**, ni 4 ni 5 (hard-fail si hay otra cantidad).
- Cada concepto en una frase, no expandidos.
- Los 3 conceptos se alternan entre Yago y Maria: 1-2-3 → líder-apoyo-líder
  o apoyo-líder-apoyo según paridad.

### 8.2 CIERRE_FINAL

Debe incluir literalmente:

> "Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada. Siguenos
> para nuevos capitulos donde la I.A. crea contenido sobre I.A."

---

## 9. Etiquetas TTS

- Una sola etiqueta por intervención.
- Va al inicio del texto.
- Las etiquetas son instrucciones de tono, no separadores de microfrases.
- Usadas con criterio para reforzar ideas, no para fragmentar la voz.

---

## 9B. Reglas de producción de audio

Estas reglas afectan la calidad del MP3 final. El guion debe cumplirlas
antes de enviarse a síntesis (ElevenLabs eleven_v3 a 1.20× + 1.10× post = **1.32× total**).

### Audio-Regla 1 — Números siempre en palabras
A velocidad 1.32×, cifras como "3.7%" o "$3M" son ininteligibles para el TTS.
```
MAL: "el 3.7% de empresas", "en Q3 2026", "costó $3M"
BIEN: "el tres punto siete por ciento de empresas", "en el tercer trimestre de dos mil veintiséis"
Excepción: años de papers donde el año es parte del nombre ("el informe McKinsey 2024")
```

### Audio-Regla 2 — Longitud óptima de intervención
ElevenLabs sintetiza mejor con intervenciones de 60-120 palabras.
Intervenciones >200 palabras generan artefactos (saltos tonales).
```
Reacción/pregunta: 5-12 palabras (hard-fail si >15)
Intervención de desarrollo: 60-120 palabras (4-6 frases) — zona óptima TTS
Máximo absoluto: 200 palabras por intervención (divide en dos si necesitas más)
```

### Audio-Regla 3 — Tags TTS: guían el estilo de escritura
Las etiquetas [tag] guían el ESTILO DE ESCRITURA, NO los parámetros de ElevenLabs
(style=0.0 hardcodeado). El texto debe ser coherente con la etiqueta:
```
[ironico]: frases con contraste, preguntas retóricas
[tenso]: frases cortas, sin adornos, directas
[reflexivo]: frases más largas con subordinadas, pausas implícitas
[calido]: vocabulario cercano, contracciones, primera persona
```

### Audio-Regla 4 — Tecnicismos acelerados: introducción obligatoria
A 1.32×, palabras técnicas largas pierden claridad sin contexto previo.
```
MAL: "backpropagation es el algoritmo que..."
BIEN: "El algoritmo clave, que llamamos backpropagation, es..."
Aplica a: cualquier tecnicismo >3 sílabas de origen inglés o compuesto.
```

### Audio-Regla 5 — INTRO_SONIDO: documentación, no generación
La línea `[INTRO - SONIDO DE MAQUINAS ARRANCANDO - 8-10 segundos]` es
obligatoria en validación pero NO genera audio. El sonido viene de
`background_bed_path` en la config. No confundir con instrucción generativa.

---

## 10. Configuración (JSON)

<!-- PODCAST_T_SPEC_JSON_START -->
```json
{
  "version": "2026-05-12-v5",
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
    "default_generation_model": "claude-sonnet-4-5",
    "default_concept_model": "claude-haiku-4-5-20251001",
    "temperature": 0.7,
    "max_output_tokens": 5000,
    "stream": true
  },
  "episode_defaults": {
    "duration_minutes": 11,
    "duration_range_minutes": [10, 13],
    "target_audience": "Profesionales tecnicos curiosos sobre como funciona la IA por dentro. CTOs/CIOs/CEOs y profesionales de IT como audiencia secundaria. Toda concepto complejo se aterriza con analogia cotidiana antes de la traslacion tecnica.",
    "tone": "divulgativo tecnico, riguroso pero accesible",
    "hook_style": "menu_3_plantillas",
    "minimum_audio_minutes": 9.5,
    "maximum_audio_minutes": 15.0
  },
  "parity_rules": {
    "applies_to": "tema_number",
    "rule": "T_impar_yago_abre__T_par_maria_abre",
    "opener_does_hook_and_aviso": true,
    "examples": {
      "M1_T1": "Yago abre",
      "M1_T2": "Maria abre",
      "M3_T2": "Maria abre",
      "M7_T1": "Yago abre",
      "M8_T1": "Yago abre",
      "M10_T5": "Yago abre",
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
      "leads_blocks": ["BLOQUE_PANORAMA"],
      "shares_blocks": ["BLOQUE_COMO"],
      "supports_blocks": ["BLOQUE_REALIDAD"],
      "traits": ["grave", "contundente", "tecnico"],
      "allowed_tags": [
        "didactico", "explicativo", "directo", "serio", "firme",
        "contundente", "grave", "tenso", "conversacional", "reflexivo",
        "curioso", "ironico", "esceptico", "natural", "pausado", "calido",
        "claro", "analitica"
      ]
    },
    "MARIA": {
      "display_name": "Maria",
      "spoken_name": "Maria",
      "opens_odd_temas": false,
      "opens_even_temas": true,
      "role": "voz_experta_empresa_y_oyente_exigente",
      "leads_blocks": ["BLOQUE_REALIDAD"],
      "shares_blocks": ["BLOQUE_COMO"],
      "supports_blocks": ["BLOQUE_PANORAMA"],
      "traits": ["clara", "analitica", "incisiva"],
      "allowed_tags": [
        "didactico", "explicativo", "directo", "serio", "firme",
        "contundente", "grave", "tenso", "conversacional", "reflexivo",
        "curioso", "ironico", "esceptico", "natural", "pausado", "calido",
        "claro", "analitica"
      ]
    }
  },
  "script_rules": {
    "required_sections": [
      "HOOK",
      "INTRO_SONIDO",
      "SALUDO_Y_PRESENTACION",
      "BLOQUE_PANORAMA",
      "BLOQUE_COMO",
      "BLOQUE_REALIDAD",
      "CIERRE_CONCEPTOS",
      "CIERRE_FINAL",
      "VERIFICACIONES"
    ],
    "forbidden_sections": [
      "BLOQUE_1", "BLOQUE_2", "BLOQUE_3", "BLOQUE_4",
      "BLOQUE_QUE", "BLOQUE_LIMITES", "BLOQUE_TEMAS_CLAVE", "BLOQUE_DESTACADO",
      "INSERCION_1", "INSERCION_2", "INSERCION_3",
      "INSERCION_EMPRESA",
      "APLICACION_PRACTICA"
    ],
    "max_consecutive_blocks_same_speaker": 2,
    "key_concepts_block_count_exact": 3,
    "minimum_word_count": 1400,
    "maximum_word_count": 1850,
    "minimum_sentences_per_intervention": 4,
    "maximum_sentences_per_intervention": 8,
    "reaction_word_limit": 30,
    "max_reactions_per_block": 3,
    "target_avg_words_per_intervention_min": 50,
    "target_avg_words_per_intervention_max": 110,
    "target_max_words_per_single_intervention": 200,
    "hard_fail_on_digits_in_dialogue": false,
    "minimum_pdf_coverage_percent": 75,
    "leader_share_min_percent": 65,
    "shared_block_balance_range_percent": [40, 60],
    "support_intervention_ratio_max": "1_per_3_leader",
    "leader_opens_block": true,
    "hook_closing_phrase": "Esto es MaquinarIA Pesada. Arrancamos.",
    "intro_comment": "[INTRO - SONIDO DE MAQUINAS ARRANCANDO - 8-10 segundos]",
    "warning_phrase_keywords_required": [
      "sistema automatico",
      "puede contener errores"
    ],
    "warning_must_be_said_by_opener": true,
    "concepts_closing_phrase": "No te puedes ir de este capitulo sin haber entendido estos conceptos",
    "final_closing_phrase": "Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada. Siguenos para nuevos capitulos donde la I.A. crea contenido sobre I.A.",
    "speaker_aliases": {
      "MARIA": ["MARIA", "MARÍA"],
      "IAGO": ["IAGO"]
    },
    "blacklist_validation_interjections": [
      "exactamente",
      "claro que sí",
      "muy bien dicho",
      "tienes toda la razón",
      "exacto",
      "por supuesto",
      "eso es",
      "totalmente"
    ],
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
        "glossary": {
          "path": "PDFs/auxiliares/glosario_unificado.md",
          "required": true,
          "rule": "respect_canonical_definitions"
        },
        "casos_empresariales": {
          "path": "PDFs/auxiliares/casos_empresariales_ia.md",
          "required": true,
          "rule": "use_prioritarily_in_BLOQUE_REALIDAD",
          "note": "Fuente obligatoria para BLOQUE_REALIDAD. Usar antes que inventar datos."
        },
        "benchmarks": {
          "path": "PDFs/auxiliares/benchmarks_academicos.md",
          "required": false,
          "max_uses_per_episode": 1,
          "preferred_location": "HOOK"
        },
        "direct_sources": {
          "path": "PDFs/auxiliares/fuentes_directas.md",
          "required": false,
          "max_uses_per_episode": 2
        }
      },
      "anti_inflation_rule": "auxiliary_sources_replace_not_add",
      "conflict_resolution": {
        "secondary_vs_primary": "primary_wins_softwarn"
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
    "normalization_target_dbfs": -16,
    "true_peak_target_dbtp": -1.5,
    "post_speed_multiplier": 1.10,
    "voices": {
      "IAGO": {
        "voice_id": "CdAqYBLnsNjmTqYgD5Ha",
        "stability": 0.65,
        "similarity_boost": 0.65,
        "style": 0.0,
        "use_speaker_boost": false,
        "speed": 1.20
      },
      "MARIA": {
        "voice_id": "gD1IexrzCvsXPHUuT0s3",
        "stability": 0.68,
        "similarity_boost": 0.55,
        "style": 0.0,
        "use_speaker_boost": false,
        "speed": 1.20
      }
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
    "soft_warn_on_missing_preescritura_evidence": true,
    "soft_warn_on_pingpong_pattern": true,
    "soft_warn_on_secondary_vs_primary_conflict": true,
    "soft_warn_on_unused_benchmark_when_relevant": true,
    "soft_warn_on_temporal_reference_without_publication_context": true,
    "soft_warn_on_missing_everyday_analogy_after_complex_concept": true,
    "hard_fail_on_saludo_collapsed_single_block": true,
    "hard_fail_on_presenter_surname_invented": true,
    "hard_fail_on_shared_block_balance": true,
    "hard_fail_on_missing_cta_in_final": false,
    "soft_warn_on_digit_numbers_in_dialogue": true,
    "soft_warn_on_intervention_over_200_words": true,
    "soft_warn_on_missing_empresa_case_in_realidad": true,
    "leader_share_min_percent_realidad": 60
  },
  "saludo_format": {
    "min_blocks": 3,
    "block_1": "opener_intro_with_own_name",
    "block_2": "other_intro_with_own_name",
    "block_3": "opener_aviso_ia",
    "forbidden_patterns": [
      "soy maria.*y yo soy yago",
      "soy yago.*y yo soy maria"
    ]
  },
  "presenter_names": {
    "allow_only": ["Maria", "Yago"],
    "forbid_surnames": true,
    "forbidden_surname_regex": "\\b(Maria|Yago)\\s+[A-ZÁÉÍÓÚÑ][a-zñáéíóú]+"
  },
  "temporal_references": {
    "default_year": 2026,
    "current_state_uses_no_year": true,
    "publication_context_markers": [
      "paper", "informe", "estudio", "reporte", "publicacion", "encuesta", "segun",
      "lanzamiento", "McKinsey", "Hugging Face", "Anthropic", "OpenAI", "Google",
      "Meta", "Gartner", "IBM", "IDC", "Lucid", "Forrester", "Stanford", "MIT"
    ],
    "forbidden_present_year_patterns": [
      "\\b2024\\b", "\\b2025\\b", "dos mil veinticuatro", "dos mil veinticinco"
    ],
    "context_window_words": 6
  },
  "everyday_analogy_rule": {
    "applies_to_blocks": ["BLOQUE_PANORAMA", "BLOQUE_COMO"],
    "required_per_complex_concept": 1,
    "max_sentences_per_analogy": 2,
    "marker_phrases": [
      "imagina que", "es como cuando", "piensa en", "el equivalente seria",
      "en tu dia a dia", "igual que", "lo mismo que pasa cuando", "como si",
      "es como", "como cuando"
    ]
  },
  "reporting": {
    "require_script_validation": true,
    "require_audio_validation": true,
    "print_anthropic_tokens": true,
    "print_elevenlabs_credits": true,
    "report_sources_used": true,
    "report_parity_check": true,
    "report_leader_share_per_block": true
  }
}
```
<!-- PODCAST_T_SPEC_JSON_END -->
