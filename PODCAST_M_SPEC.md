# Podcast M Spec — MaquinarIA Pesada

Especificación normativa para generar guiones y audio de **episodios M (Módulos)**:
los 14 episodios de resumen de módulo que cierran cada bloque de Ts.

Reemplaza al spec genérico anterior **solo para episodios M**. Los episodios T
(temas individuales) tienen su propio spec en `PODCAST_T_SPEC.md`.

Versión: 2026-05-10 (v3 — incorpora correcciones de la revisión de los 7 episodios T piloto + extracción automática desde documentos vivos)
Tipo: M
Duración objetivo: 15-17 minutos (rango 14-18 min)

---

## 1. Filosofía del episodio M

Un episodio M es **el ancla de cada módulo**: pieza más larga que cubre el
módulo entero a vista de pájaro y aterriza con un ejemplo verificable
único: el sistema que está generando el podcast. Sirve a:

- Conversión de oyente curioso a oyente fiel (es la pieza-marca).
- Construcción de autoridad técnica concreta a través de la propia obra.
- Diferenciación del corpus respecto al panorama saturado de podcasts IA.

**La diferencia clave con un T:**

Un M no es un T más largo. Es estructuralmente distinto. Un T explica un
tema. Un M explica un módulo + lo aplica al sistema real. El bloque
APLICACION_PRACTICA es el que carga el peso de la marca y de la
diferenciación.

---

## 2. Principios duros

- Priorizar claridad antes que estilo.
- Mantener tono divulgativo-técnico, riguroso y accesible.
- Episodios de **14 a 18 min**, objetivo práctico **15-17 min**.
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
5.  # BLOQUE_TEMAS_CLAVE
6.  # BLOQUE_LIMITES
7.  # APLICACION_PRACTICA
8.  # CIERRE_CONCEPTOS
9.  # CIERRE_FINAL
10. # VERIFICACIONES
```

**Función de cada bloque:**

- **BLOQUE_PANORAMA** (~3-4 min): qué cubre el módulo, por qué importa, qué
  preguntas responde. Apertura del módulo entero.
- **BLOQUE_TEMAS_CLAVE** (~4-5 min): los 3-5 conceptos núcleo del módulo,
  cómo se relacionan entre sí. Es el cuerpo conceptual.
- **BLOQUE_LIMITES** (~2-3 min): qué falla, qué no funciona, los
  contraintuitivos del módulo entero.
- **APLICACION_PRACTICA** (~3-4 min): el sistema que genera el podcast como
  caso de uso real del módulo. Detalle en §8.
- **CIERRE_CONCEPTOS + CIERRE_FINAL**: cierre canónico.

---

## 4. Roles de los presentadores (líder por bloque)

Idéntico al spec T en filosofía, ajustado al formato M.

### 4.1 Asignación de líder por bloque

| Bloque | Líder | Apoyo | Lógica |
|---|---|---|---|
| HOOK | Por paridad del nº de MÓDULO | El otro | M impares Yago, M pares Maria |
| SALUDO_Y_PRESENTACION | Quien abre | El otro | Aviso de IA enganche dicho por quien abre |
| **BLOQUE_PANORAMA** | **Yago** | Maria | Mapa del módulo entero: territorio explicador |
| **BLOQUE_TEMAS_CLAVE** | **Compartido por concepto** | — | Líder rota por concepto, ver §4.2 |
| **BLOQUE_LIMITES** | **Maria** | Yago | Contraintuitivos del módulo: territorio escéptica |
| **APLICACION_PRACTICA** | **Maria abre, Yago detalla** | — | Reparto explícito en 3 momentos, ver §8 |
| CIERRE_CONCEPTOS | Por paridad | El otro | 3-5 conceptos alternando |
| CIERRE_FINAL | Por paridad | El otro | Cita canónica |

### 4.2 Cómo funciona "compartido por concepto" en BLOQUE_TEMAS_CLAVE

Si el módulo cubre 4 conceptos núcleo, el generador asigna líder por concepto
alternando para que no se acumulen 3 seguidos del mismo. Ejemplo en M con
4 conceptos: Yago - Maria - Yago - Maria.

Regla: el líder del concepto da la explicación principal (4-8 frases). El
otro hace 1-2 intervenciones de pregunta o matiz por concepto.
**Reparto global de BLOQUE_TEMAS_CLAVE debe quedar entre 40% y 60% para cada speaker.**

### 4.3 Perfiles de los presentadores

- **Yago = explicador técnico.** Profundidad, terminología precisa, mecanismo.
  Lleva BLOQUE_PANORAMA y la parte técnica (momento 2) de APLICACION_PRACTICA.
- **Maria = oyente exigente.** Cuestiona, tensa, pide aterrizar. Lleva
  BLOQUE_LIMITES y la apertura/cierre (momentos 1 y 3) de APLICACION_PRACTICA.
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
  - BLOQUE_LIMITES: Maria ≥65%.
  - BLOQUE_TEMAS_CLAVE compartido: 40-60% globalmente.
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
- Conceptos complejos con ejemplo cotidiano + traslación corporativa.

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

**Momento 2 — Yago detalla (~2-2.5 min).**

Yago describe el mecanismo técnico real. Cómo el sistema lo resolvió. Qué
decisión concreta se tomó. Cifras si las hay. **Esto se redacta a partir de
las extracciones de los 4 documentos vivos del proyecto o, si existe, del
archivo de override manual.**

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

---

## 10. Etiquetas TTS

- Una sola etiqueta por intervención.
- Va al inicio del texto.
- Las etiquetas son instrucciones de tono, no separadores de microfrases.

---

## 11. Configuración (JSON)

<!-- PODCAST_M_SPEC_JSON_START -->
```json
{
  "version": "2026-05-10-v3",
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
    "duration_minutes": 16,
    "duration_range_minutes": [14, 18],
    "target_audience": "Profesionales tecnicos curiosos sobre como funciona la IA por dentro. CTOs/CIOs/CEOs y profesionales de IT como audiencia secundaria. Pieza ancla del modulo.",
    "tone": "divulgativo tecnico, riguroso pero accesible, con momento de ingenieria-real en APLICACION_PRACTICA",
    "hook_style": "menu_3_plantillas",
    "minimum_audio_minutes": 13.5,
    "maximum_audio_minutes": 18.5
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
      "shares_blocks": ["BLOQUE_TEMAS_CLAVE"],
      "supports_blocks": ["BLOQUE_LIMITES"],
      "aplicacion_role": "detalla_tecnico_momento_2",
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
      "role": "oyente_exigente",
      "leads_blocks": ["BLOQUE_LIMITES"],
      "shares_blocks": ["BLOQUE_TEMAS_CLAVE"],
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
      "BLOQUE_TEMAS_CLAVE",
      "BLOQUE_LIMITES",
      "APLICACION_PRACTICA",
      "CIERRE_CONCEPTOS",
      "CIERRE_FINAL",
      "VERIFICACIONES"
    ],
    "forbidden_sections": [
      "BLOQUE_1", "BLOQUE_2", "BLOQUE_3", "BLOQUE_4",
      "BLOQUE_QUE", "BLOQUE_COMO",
      "INSERCION_1", "INSERCION_2", "INSERCION_3",
      "INSERCION_EMPRESA"
    ],
    "max_consecutive_blocks_same_speaker": 2,
    "key_concepts_block_count_min": 3,
    "key_concepts_block_count_max": 5,
    "minimum_word_count": 2200,
    "maximum_word_count": 2800,
    "minimum_sentences_per_intervention": 4,
    "maximum_sentences_per_intervention": 10,
    "reaction_word_limit": 12,
    "max_reactions_per_block": 3,
    "target_avg_words_per_intervention_min": 55,
    "target_avg_words_per_intervention_max": 100,
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
    "soft_warn_on_module_with_low_live_docs_coverage": true
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
