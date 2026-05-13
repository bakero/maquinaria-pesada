# Podcast M Spec — MaquinarIA Pesada

Especificación normativa para generar guiones y audio de **episodios M (Módulos)**:
los 14 episodios de resumen de módulo que cierran cada bloque de Ts.

Reemplaza al spec genérico anterior **solo para episodios M**. Los episodios T
(temas individuales) tienen su propio spec en `PODCAST_T_SPEC.md`.

Versión: 2026-05-12 (v5 — BLOQUE_DESTACADO reemplaza TEMAS_CLAVE, BLOQUE_LIMITES eliminado, word count 2100-2600, APLICACION_PRACTICA tipo B, audio rules)
Tipo: M
Duración objetivo: 17-19 minutos (rango 16-19 min)

---

## 1. Filosofía del episodio M

Un episodio M es **el ancla de cada módulo**: pieza más larga de carácter
promocional/marketing que cubre los 2-3 conceptos más impactantes del módulo
y los conecta con el sistema real que genera el podcast. Sirve a:

- Captación de oyentes nuevos (pieza-marca multi-plataforma).
- Construcción de autoridad técnica concreta a través de la propia obra.
- Diferenciación del corpus respecto al panorama saturado de podcasts IA.
- **Publicación**: 2 semanas después de desbloquear los T del mismo módulo.

**La diferencia clave con un T:**

Un M no es un T más largo. Es estructuralmente distinto. Un T forma sobre
un tema. Un M selecciona los 2-3 conceptos más impactantes del módulo y los
conecta con el sistema real. El bloque APLICACION_PRACTICA es el que carga
el peso de la marca y de la diferenciación — en versión high-level (tipo B),
sin detalles técnicos de implementación.

**CTA obligatoria en CIERRE_FINAL**: mencionar que los episodios T del módulo
están disponibles en plataformas. Integrar de forma natural, no como anuncio.

---

## 2. Principios duros

- Priorizar claridad antes que estilo.
- Mantener tono divulgativo-técnico, riguroso y accesible.
- Episodios de **16 a 20 min**, objetivo práctico **17-19 min**. Se prefiere extender duración antes que dejar conceptos sin aterrizar.
- Empezar siempre con hook que cumpla una de las 3 plantillas (§5).
- **Apertura por paridad del número de MÓDULO:** impares Yago, pares Maria.
  M0 → Maria, M1 → Yago, M2 → Maria, M3 → Yago, etc.
- **Quien abre el episodio también dice el aviso de IA y abre el HOOK.**
- Usar "Yago" dentro del texto hablado, nunca "Iago".
- Aviso de IA dentro del SALUDO_Y_PRESENTACION en versión enganche (§6).
- Bloque **APLICACION_PRACTICA obligatorio y único** (§8). Es el bloque
  distintivo del formato M.
- APLICACION_PRACTICA se construye consultando los 4 documentos vivos del
  proyecto (BIBLIA_SISTEMA, PRIMERPODCAST, VIDEOPODCAST, PODCAST) — ver §8.4.
- **3 a 5 conceptos** en CIERRE_CONCEPTOS según riqueza del módulo (rango fijo).
- Verificaciones reales del guion al final del archivo generado.
- Validación real del audio y reporte de créditos en el log.

---

## 3. Estructura obligatoria del guion

```
1.  # HOOK
2.  # INTRO_SONIDO
3.  # SALUDO_Y_PRESENTACION
4.  # BLOQUE_PANORAMA
5.  # BLOQUE_DESTACADO
6.  # APLICACION_PRACTICA
7.  # CIERRE_CONCEPTOS
8.  # CIERRE_FINAL  (con CTA a episodios T)
9.  # VERIFICACIONES
```

**Función de cada bloque:**

- **BLOQUE_PANORAMA** (~3-4 min): qué cubre el módulo, por qué importa, qué
  preguntas responde. Apertura del módulo entero. Lidera Yago (≥65%).
- **BLOQUE_DESTACADO** (~4-5 min): los **2-3 conceptos más impactantes** del módulo.
  No exhaustivo. Criterios de selección en orden:
  1. El más contraintuitivo (lo que la mayoría no sabe)
  2. El más relevante para profesionales no técnicos (CTOs, CEOs)
  3. El que mejor conecta con la APLICACION_PRACTICA
  Compartido 40-60% entre ambos speakers.
- **APLICACION_PRACTICA** (~3-4 min): el sistema que genera el podcast como
  caso de uso real del módulo — en formato high-level (tipo B). Ver §8.
- **CIERRE_CONCEPTOS**: 3-5 conceptos canónicos.
- **CIERRE_FINAL**: cierre canónico + CTA natural a episodios T del módulo.

**BLOQUE_LIMITES eliminado del M-type.** El M no cubre límites técnicos del
módulo; eso es territorio del T. El M conecta conceptos con el sistema real.

---

## 4. Roles de los presentadores (líder por bloque)

Idéntico al spec T en filosofía, ajustado al formato M.

### 4.1 Asignación de líder por bloque

| Bloque | Líder | Apoyo | Lógica |
|---|---|---|---|
| HOOK | Por paridad del nº de MÓDULO | El otro | M impares Yago, M pares Maria |
| SALUDO_Y_PRESENTACION | Quien abre | El otro | Aviso de IA enganche dicho por quien abre |
| **BLOQUE_PANORAMA** | **Yago** | Maria | Mapa del módulo entero: territorio explicador |
| **BLOQUE_DESTACADO** | **Compartido por concepto** | — | Líder rota por concepto, 40-60% global, ver §4.2 |
| **APLICACION_PRACTICA** | **Maria abre, Yago detalla** | — | Reparto explícito en 3 momentos, ver §8 |
| CIERRE_CONCEPTOS | Por paridad | El otro | 3-5 conceptos alternando |
| CIERRE_FINAL | Por paridad | El otro | Cita canónica + CTA a episodios T |

### 4.2 Cómo funciona "compartido por concepto" en BLOQUE_DESTACADO

El M cubre solo 2-3 conceptos (los más impactantes, no todos). El generador
asigna líder por concepto alternando. Ejemplo con 2 conceptos: Yago - Maria.
Con 3 conceptos: Yago - Maria - Yago.

Regla: el líder del concepto da la explicación principal (4-8 frases). El
otro hace 1-2 intervenciones de pregunta o matiz por concepto.
**Reparto global de BLOQUE_DESTACADO debe quedar entre 40% y 60% para cada speaker.**

### 4.3 Perfiles de los presentadores

- **Yago = explicador técnico.** Profundidad, terminología precisa, mecanismo.
  Lleva BLOQUE_PANORAMA y el detalle high-level (momento 2) de APLICACION_PRACTICA.
- **Maria = oyente exigente + conductora de marca.** Cuestiona, tensa, pide
  aterrizar. Abre y cierra APLICACION_PRACTICA (momentos 1 y 3).
  **No es asistente.** No valida, no aplaude, no asiente.

### 4.4 Lista negra de interjecciones (anti-NotebookLM)

**Prohibido en todos los episodios M (hard-fail si aparece):**

- "Exactamente"
- "Claro que sí"
- "Muy bien dicho"
- "Tienes toda la razón"
- "Exacto"
- "Por supuesto"
- "Eso es"
- "Totalmente"

### 4.5 Reglas de longitud y reparto

- Intervenciones de desarrollo: **mínimo 4 frases** en bloques centrales.
- En APLICACION_PRACTICA se permiten intervenciones largas (hasta 10 frases)
  cuando el caso lo requiera. Es donde el M respira más.
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

Idéntico al spec T. Plantillas A (dato), B (pregunta-incómoda), C (caso).

**Diferencia operativa con T:** en M, el hook puede tirar fuerte de la
estadística-marco del módulo entero (ej: "el 88% usa IA, solo el 33% la
escala") porque el episodio cubre más territorio.

**Reglas duras del hook:**

- 30-45 segundos hablados.
- Cierra exactamente con: `Esto es MaquinarIA Pesada. Arrancamos.`
- **Apertura por paridad del número de MÓDULO: M pares Maria abre, M impares Yago abre.**
  Lista explícita: M0→Maria, M1→Yago, M2→Maria, M3→Yago, M4→Maria, M5→Yago,
  M6→Maria, M7→Yago, M8→Maria, M9→Yago, M10→Maria, M11→Yago, M12→Maria,
  M13→Yago, M14→Maria.

---

## 6. Aviso de generación por IA — versión enganche

**Dentro de SALUDO_Y_PRESENTACION**, justo después de la presentación. Lo
dice **el mismo speaker que abrió el HOOK por paridad del módulo**.

### 6.0 Formato obligatorio del SALUDO_Y_PRESENTACION

El bloque debe tener **mínimo 3 intervenciones separadas**, en este orden:

1. `{opener}: [tag] Bienvenidos/Hola/etc. + Soy {opener_name}.`
2. `{otro}: [tag] Y yo soy {otro_name}.`
3. `{opener}: [tag] Antes de empezar, lo de siempre... {aviso completo}`

**Hard-fail si**:
- Una sola intervención contiene los dos nombres ("Soy Maria. Y yo soy Yago.") — el segundo nombre debe estar en una intervención del otro speaker.
- El aviso lo dice cualquier speaker distinto del opener.

**Prohibido: apellidos**. Los presentadores se llaman **Maria** y **Yago**, sin apellidos. No se inventan "Maria Grandury", "Yago Goyoaga" ni ningún apellido. Hard-fail si aparecen palabras tras "Maria" o "Yago" que parezcan apellido (regex de fail: `\b(Maria|Yago)\s+[A-ZÁÉÍÓÚÑ][a-zñáéíóú]+\b`).

### Forma para episodios M (versión enganche, 18-25s)

> "Antes de empezar, lo de siempre: este episodio lo genera un sistema
> automático de inteligencia artificial. Puede contener errores. Si oyes algo
> que no te cuadra, contrástalo. El sistema que produce este podcast también
> es contenido del podcast — al final del episodio veremos cómo se aplica lo
> de hoy a ese sistema."

**Reglas:**

- Obligatorio en todos los episodios M sin excepción. **Hard-fail si falta.**
- Debe contener literalmente las palabras clave **"sistema automatico"** y
  **"puede contener errores"** (hard-fail si faltan).
- **Lo dice el mismo speaker que abrió el HOOK** (hard-fail si lo dice el otro).
- Debe contener una frase que conecte el aviso con APLICACION_PRACTICA.
  Lista de frases-marca aceptables (soft-check, el generador puede variar):
  - "el sistema que produce este podcast también es contenido del podcast"
  - "ese sistema también forma parte de lo que escuchas"
  - "veremos cómo se aplica lo de hoy a ese sistema al final"
  - "el sistema que está generando este episodio aparecerá al final"
- Duración 18-25 segundos.

---

## 7. Reglas de contenido y fuentes

### 7.1 Pre-escritura obligatoria

Antes de escribir el guion, el generador rellena internamente esta tabla a
partir del PDF RESUMEN del módulo + de los 4 documentos vivos del proyecto:

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
```

**Regla dura:** al menos uno del PDF debe aparecer dentro de los **primeros
90 segundos hablados**. La aplicación práctica del sistema **NO debe
aparecer en el HOOK** (hard-fail si aparece).

### 7.2 Fuentes del generador

**Fuente primaria (obligatoria, hard-fail si no se lee):**

- PDF RESUMEN del módulo en `PDFs/resumenes/RESUMEN_M{n}_*.pdf`.
- **El generador DEBE leer el PDF como input y los tokens deben quedar
  reflejados en VERIFICACIONES (`tokens > 0`).**
- Cobertura: mínimo 75% de los conceptos clave del PDF.
- Hard-fail si `tokens=0` o cobertura<75%.

**Fuente primaria para APLICACION_PRACTICA — los 4 documentos vivos:**

| Documento | Tipo | Prioridad por módulo |
|---|---|---|
| `BIBLIA_SISTEMA.md` | Referencia técnica estática | M1, M5, M6, M7, M9, M10 |
| `PRIMERPODCAST.md` | Diario producción audio | M5, M6, M8, M11, M12 |
| `VIDEOPODCAST.md` | Diario producción video | M2, M4, M8, M9, M10 |
| `PODCAST.md` | Diario operativo unificado con marcas DECISIÓN/CAMBIO/INCIDENCIA/PRODUCCIÓN/REGLA | Todos, especialmente M8, M12, M13 |

**Regla de extracción por módulo:**

Para cada M{n}, el generador hace una pasada de extracción sobre los 4
documentos buscando entradas que mencionen explícitamente:

1. Conceptos del PDF RESUMEN del módulo (búsqueda por términos clave).
2. Tecnologías o patrones del módulo (ej. "RAG", "prompt", "agente", "Kling",
   "scipy", "validador", "fsync", "JWT").
3. Decisiones marcadas como `[DECISIÓN]`, `[CAMBIO]`, `[INCIDENCIA]`,
   `[REGLA]` (en `PODCAST.md`) que tocan los conceptos del módulo.

El generador construye internamente la "ficha de aplicación" del módulo y la
guarda en `episodios/temp/aplicacion_extraida_M{n}.md` para trazabilidad.

**Fallback si no hay material suficiente:**

Si el generador no encuentra: 1 problema concreto + 1 decisión técnica +
1 cifra verificable, entonces:

1. **Hard-fail.** NO genera el episodio.
2. Pide intervención humana: enriquecer los documentos vivos con material
   relevante para ese módulo, O proveer override manual en
   `PDFs/aplicacion_practica/M{n}.md`.

**Override manual opcional:**

Si existe `PDFs/aplicacion_practica/M{n}.md`, el generador lo usa como
fuente prioritaria para APLICACION_PRACTICA y los 4 documentos vivos solo
como complemento.

**Fuentes secundarias (siempre disponibles, uso obligatorio cuando aplique):**

1. `PDFs/auxiliares/glosario_unificado.md`
   - Definiciones canónicas de términos técnicos del corpus.
   - Hard-fail si no existe el archivo.

2. `PDFs/auxiliares/benchmarks_academicos.md`
   - Lista de currículos universitarios.
   - Uso opcional: máximo 1 mención por episodio.

3. `PDFs/auxiliares/fuentes_directas.md`
   - Lista de papers, documentación oficial.
   - Máximo 3 menciones por episodio.

**Fuentes secundarias adicionales para M (consulta opcional):**

4. PDFs de los temas T del módulo, en `PDFs/temas/M{n}_T*.pdf`.

**Regla anti-relleno:**

Las fuentes secundarias NO pueden inflar el guion.

**Regla de prioridad ante conflicto:**

- Si una fuente secundaria contradice al PDF RESUMEN, prevalece el RESUMEN
  (soft-warn).
- Si los documentos vivos contradicen al PDF RESUMEN en APLICACION_PRACTICA,
  prevalecen los documentos vivos (soft-warn).

### 7.3 Reglas generales de contenido

- Cubrir al menos el **75%** de los conceptos clave del PDF RESUMEN.
- **Cada concepto técnico complejo debe ir seguido de una analogía cotidiana en ≤2 frases**, antes de la traslación corporativa. La audiencia núcleo es técnica, pero la secundaria (CTO/CIO/CEO y oyente curioso) tiene que poder seguir el episodio sin sentirse expulsada. Es preferible alargar el episodio antes que dejar un concepto sin aterrizar.
- Marcadores aceptables para introducir el ejemplo cotidiano (uso libre, sin léxico obligatorio): "imagina que", "es como cuando", "piensa en", "el equivalente sería", "en tu día a día", "igual que", "lo mismo que pasa cuando".
- Soft-warn si un concepto del PDF aparece en BLOQUE_TEMAS_CLAVE sin ningún marcador de analogía cotidiana en las 6 frases siguientes.

### 7.4 Referencias temporales

Regla operativa para que el corpus envejezca bien:

- **Año por defecto: 2026** (año de producción del podcast). Cuando se hable del estado actual del mercado, de los modelos, del ecosistema o de la práctica empresarial, **no se cita año**; se usan formas como "hoy", "actualmente", "en este momento", "ahora mismo".
- **Excepción única — publicaciones/informes/papers/eventos identificables**: ahí sí se conserva el año real ("el paper de Sennrich de 2016", "el informe McKinsey State of AI de 2025", "la encuesta IBM AI in Action 2024", "el lanzamiento de GPT-4 en 2023"). El año va siempre acompañado de un autor o publicación con nombre propio.
- **Prohibido**: usar 2024 o 2025 como marcador del presente (ej. "en 2025 las empresas..."). Hard-warn si se detecta `\b(2024|2025|dos mil veint(icuatro|icinco))\b` y en las 6 palabras anteriores NO aparece uno de: paper, informe, estudio, reporte, publicación, encuesta, según, lanzamiento, McKinsey, Hugging Face, Anthropic, OpenAI, Google, Meta, Gartner, IBM, IDC, Lucid, Forrester, Stanford.
- **Permitido sin etiqueta**: 2026 (presente), o años pasados narrados como historia ("el primer invierno llegó en los setenta", "los Transformers se publicaron en 2017").

---

## 8. APLICACION_PRACTICA: el bloque distintivo del M

### 8.1 Función

Conectar el módulo entero con un caso de uso real verificable: el sistema
que genera el podcast. NO es BLOQUE_META. NO es promoción. ES aplicación
didáctica del concepto a un sistema real que el oyente puede inspeccionar.

### 8.2 Estructura interna obligatoria — 3 momentos

**Momento 1 — Maria plantea (~45-60s).**

Maria abre conectando el módulo con el sistema. Plantea la pregunta
operativa concreta del módulo aplicada al sistema real.

Patrón de apertura: "Ahora veamos cómo todo esto se aplica en un sistema
real. Concretamente, en el sistema que está generando este podcast.
Concretamente: ¿[pregunta operativa del módulo]?"

Ejemplo en M6 (Prompts):
> "Si todo esto del prompting es disciplina y no truco, ¿cómo se aplica
> cuando tienes que generar 100 episodios de podcast con calidad consistente?"

**Momento 2 — Yago detalla en formato high-level (tipo B) (~2-2.5 min).**

Yago conecta los conceptos del módulo con el sistema de forma conceptual,
NO técnica. El patrón es: "esto que acabas de aprender es exactamente lo que
hace posible que [X del sistema]". No citar componentes técnicos del pipeline,
no dar detalles de implementación. Debe sonar como revelación natural, no como
anuncio técnico ni clase de arquitectura.

**Ejemplos del tono correcto (tipo B):**
- "Lo que acabas de entender sobre RAG es exactamente lo que permite que
  los guiones del podcast tengan contexto del módulo completo sin que el
  LLM lo haya memorizado."
- "El ajuste fino que describimos antes es el proceso que diferencia que
  el sistema genere un guion técnico creíble y no texto genérico de IA."

**Lo que NO se hace en Momento 2:**
- No describir el pipeline paso a paso.
- No citar nombres de archivos, funciones o parámetros.
- No detallar costes, tokens ni métricas técnicas específicas.

**Esto se redacta a partir de las extracciones de los 4 documentos vivos
del proyecto o, si existe, del archivo de override manual, pero siempre
en nivel conceptual.**

**Momento 3 — Cierre conjunto (~30-45s).**

Maria pregunta o señala el aprendizaje. Yago lo aterriza. Frase final que
conecta de vuelta con el módulo entero.

### 8.3 Reglas específicas del bloque

- Duración 3-4 min total (180-240s).
- Reparto de palabras: **Maria 30-40%, Yago 60-70%**.
- El contenido técnico de Yago debe basarse en hechos verificables extraídos
  de los 4 documentos vivos del proyecto, o del archivo de override manual.
- **No inventar.** Si los documentos no aportan material suficiente, el
  generador hace hard-fail.
- El bloque debe conectar al menos 2 conceptos del módulo con el caso del
  sistema. Si solo conecta 1, soft-warn.

### 8.4 Material fuente: extracción automática + override opcional

**Modo automático (por defecto):**

El generador construye internamente una "ficha de aplicación" extrayendo
de los 4 documentos vivos según las reglas del §7.2. La ficha tiene esta
estructura:

```markdown
# Ficha de aplicación del módulo M{n}: {nombre}

## Pregunta operativa
{Pregunta que conecta el módulo con un problema real del sistema}

## Problema concreto encontrado
{Descripción técnica extraída de los docs, 50-100 palabras}

## Decisión tomada
{Qué se hizo y por qué, 80-150 palabras, citando fuente}

## Cifras / verificables
- {dato 1 con fuente: doc + sección}
- {dato 2}
- {dato 3}

## Conexión con conceptos del módulo
- Concepto 1: {cómo se aplicó}
- Concepto 2: {cómo se aplicó}

## Fuentes consultadas
- {doc1.md§sección}
- {doc2.md§sección}
```

La ficha se guarda en `episodios/temp/aplicacion_extraida_M{n}.md` para
trazabilidad y debugging.

**Modo override manual (opcional):**

Si existe `PDFs/aplicacion_practica/M{n}.md`, el generador lo usa como
fuente prioritaria. La estructura del override es la misma de la ficha
automática.

---

## 9. Cierre

### 9.1 CIERRE_CONCEPTOS

- Abre con: `No te puedes ir de este capitulo sin haber entendido estos conceptos`
- **3 a 5 conceptos** según riqueza del módulo (hard-fail si <3 o >5).
- Cada concepto en una frase, no expandidos.
- Al menos uno debe conectarse con APLICACION_PRACTICA.

### 9.2 CIERRE_FINAL

Debe incluir literalmente:

> "Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada. Siguenos
> para nuevos capitulos donde la I.A. crea contenido sobre I.A."

**CTA obligatoria (WARN si falta, no hard-fail):**

El speaker de cierre debe mencionar de forma natural que los episodios del
módulo están disponibles. Fórmula aceptable (el generador puede adaptar):

> "...y si quieres profundizar en cualquiera de estos conceptos, los episodios
> del módulo ya están disponibles en nuestras plataformas habituales."

La CTA debe sonar como continuación natural del cierre, nunca como anuncio.
`enforce_fixed_phrases()` NO gestiona la CTA (demasiado variable para hardcode).
Validación: regex flexible `episodio[s]?.{0,30}(módulo|disponible|plataforma|escucha)`.

---

## 10. Etiquetas TTS

- Una sola etiqueta por intervención.
- Va al inicio del texto.
- Las etiquetas son instrucciones de tono, no separadores de microfrases.

---

## 10B. Reglas de producción de audio

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
Excepción M: APLICACION_PRACTICA puede tener hasta 250 palabras en Momento 2
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

## 11. Configuración (JSON)

<!-- PODCAST_M_SPEC_JSON_START -->
```json
{
  "version": "2026-05-12-v5",
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
    "max_output_tokens": 8000,
    "stream": true
  },
  "episode_defaults": {
    "duration_minutes": 18,
    "duration_range_minutes": [16, 20],
    "target_audience": "Profesionales tecnicos curiosos sobre como funciona la IA por dentro. CTOs/CIOs/CEOs y profesionales de IT como audiencia secundaria. Pieza ancla del modulo. Toda concepto complejo se aterriza con analogia cotidiana antes de la traslacion tecnica/corporativa.",
    "tone": "divulgativo tecnico, riguroso pero accesible, con momento de ingenieria-real en APLICACION_PRACTICA",
    "hook_style": "menu_3_plantillas",
    "minimum_audio_minutes": 15.5,
    "maximum_audio_minutes": 20.0
  },
  "parity_rules": {
    "applies_to": "module_number",
    "rule": "M_par_maria_abre__M_impar_yago_abre",
    "opener_does_hook_and_aviso": true,
    "explicit_table": {
      "M0": "Maria",
      "M1": "Yago",
      "M2": "Maria",
      "M3": "Yago",
      "M4": "Maria",
      "M5": "Yago",
      "M6": "Maria",
      "M7": "Yago",
      "M8": "Maria",
      "M9": "Yago",
      "M10": "Maria",
      "M11": "Yago",
      "M12": "Maria",
      "M13": "Yago",
      "M14": "Maria"
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
      "shares_blocks": ["BLOQUE_DESTACADO"],
      "supports_blocks": [],
      "aplicacion_role": "detalla_highlevel_momento_2_tipo_B",
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
      "opens_odd_modules": false,
      "opens_even_modules": true,
      "role": "oyente_exigente_y_conductora_marca",
      "leads_blocks": [],
      "shares_blocks": ["BLOQUE_DESTACADO"],
      "supports_blocks": ["BLOQUE_PANORAMA"],
      "aplicacion_role": "abre_y_cierra_momentos_1_y_3",
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
      "BLOQUE_DESTACADO",
      "APLICACION_PRACTICA",
      "CIERRE_CONCEPTOS",
      "CIERRE_FINAL",
      "VERIFICACIONES"
    ],
    "forbidden_sections": [
      "BLOQUE_1", "BLOQUE_2", "BLOQUE_3", "BLOQUE_4",
      "BLOQUE_QUE", "BLOQUE_COMO", "BLOQUE_LIMITES",
      "BLOQUE_TEMAS_CLAVE", "BLOQUE_REALIDAD",
      "INSERCION_1", "INSERCION_2", "INSERCION_3",
      "INSERCION_EMPRESA"
    ],
    "max_consecutive_blocks_same_speaker": 2,
    "key_concepts_block_count_min": 3,
    "key_concepts_block_count_max": 5,
    "minimum_word_count": 2100,
    "maximum_word_count": 2600,
    "minimum_sentences_per_intervention": 4,
    "maximum_sentences_per_intervention": 10,
    "reaction_word_limit": 30,
    "max_reactions_per_block": 3,
    "target_avg_words_per_intervention_min": 55,
    "target_avg_words_per_intervention_max": 120,
    "target_max_words_per_single_intervention": 200,
    "hard_fail_on_digits_in_dialogue": false,
    "hard_fail_on_missing_cta_in_final": false,
    "minimum_pdf_coverage_percent": 75,
    "leader_share_min_percent": 65,
    "shared_block_balance_range_percent": [40, 60],
    "support_intervention_ratio_max": "1_per_3_leader",
    "leader_opens_block": true,
    "aplicacion_practica": {
      "duration_seconds_min": 180,
      "duration_seconds_max": 240,
      "maria_share_percent_range": [30, 40],
      "yago_share_percent_range": [60, 70],
      "must_connect_concepts_min": 2,
      "no_invention_allowed": true,
      "extraction_mode": "automatic_from_live_docs_with_optional_override",
      "min_facts_required": {
        "problema_concreto": 1,
        "decision_tecnica": 1,
        "cifra_verificable": 1
      }
    },
    "hook_closing_phrase": "Esto es MaquinarIA Pesada. Arrancamos.",
    "intro_comment": "[INTRO - SONIDO DE MAQUINAS ARRANCANDO - 8-10 segundos]",
    "warning_phrase_keywords_required": [
      "sistema automatico",
      "puede contener errores"
    ],
    "warning_must_be_said_by_opener": true,
    "warning_phrase_keywords_softcheck": [
      "sistema que produce",
      "parte del podcast",
      "veremos como se aplica"
    ],
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
    "hook_templates": ["dato", "pregunta_incomoda", "caso"],
    "preescritura_required": {
      "datos_numericos_min": 4,
      "casos_nombre_propio_min": 3,
      "frase_fuerza_min": 1,
      "contraintuitivos_min": 3,
      "aplicacion_problema_min": 1,
      "aplicacion_decision_min": 1,
      "aplicacion_cifra_min": 1,
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
          {
            "name": "BIBLIA_SISTEMA",
            "path": "BIBLIA_SISTEMA.md",
            "type": "static_reference",
            "priority_modules": ["M1", "M5", "M6", "M7", "M9", "M10"]
          },
          {
            "name": "PRIMERPODCAST",
            "path": "PRIMERPODCAST.md",
            "type": "production_diary_audio",
            "priority_modules": ["M5", "M6", "M8", "M11", "M12"]
          },
          {
            "name": "VIDEOPODCAST",
            "path": "VIDEOPODCAST.md",
            "type": "production_diary_video",
            "priority_modules": ["M2", "M4", "M8", "M9", "M10"]
          },
          {
            "name": "PODCAST",
            "path": "PODCAST.md",
            "type": "operational_diary_unified",
            "structured_markers": ["DECISIÓN", "CAMBIO", "INCIDENCIA", "PRODUCCIÓN", "REGLA"],
            "priority_modules": ["M8", "M12", "M13"]
          }
        ],
        "extraction_strategy": "search_by_module_concepts_and_keywords",
        "extraction_artifact_path": "episodios/temp/aplicacion_extraida_M{n}.md",
        "fallback_on_insufficient_material": "hard_fail_request_human_input",
        "manual_override": {
          "path_pattern": "PDFs/aplicacion_practica/M{n}.md",
          "priority": "overrides_automatic_extraction"
        }
      },
      "secondary": {
        "glossary": {
          "path": "PDFs/auxiliares/glosario_unificado.md",
          "required": true
        },
        "benchmarks": {
          "path": "PDFs/auxiliares/benchmarks_academicos.md",
          "required": false,
          "max_uses_per_episode": 1
        },
        "direct_sources": {
          "path": "PDFs/auxiliares/fuentes_directas.md",
          "required": false,
          "max_uses_per_episode": 3
        },
        "temas_modulo": {
          "path_pattern": "PDFs/temas/M{n}_T*.pdf",
          "required": false
        }
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
    "hard_fail_on_concepts_count_out_of_range": true,
    "hard_fail_on_missing_resumen_source": true,
    "hard_fail_on_zero_input_tokens": true,
    "hard_fail_on_pdf_coverage_below_75": true,
    "hard_fail_on_missing_glossary": true,
    "hard_fail_on_aplicacion_in_hook": true,
    "hard_fail_on_insufficient_aplicacion_material": true,
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
    "hard_fail_on_saludo_collapsed_single_block": true,
    "hard_fail_on_presenter_surname_invented": true,
    "hard_fail_on_shared_block_balance": true
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
    "applies_to_blocks": ["BLOQUE_DESTACADO", "BLOQUE_PANORAMA"],
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
    "report_leader_share_per_block": true,
    "save_aplicacion_extraction_artifact": true
  }
}
```
<!-- PODCAST_M_SPEC_JSON_END -->
