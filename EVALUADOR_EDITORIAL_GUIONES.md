# EVALUADOR_EDITORIAL_GUIONES.md
**Panel editorial multi-perspectiva sobre guiones de MaquinarIA Pesada**
**Ejecutado desde Claude Code como prompt para Sonnet · Opera sobre `.txt` ya parseables**
Versión: 2026-05-18 (v1)

---

## 0. Qué es este documento

Este evaluador **no valida** el guion contra la spec técnica (eso es trabajo de
`EVALUADOR_GUIONES.md` y del paquete `validators/`). Esto evalúa el guion
**como producto editorial**: ¿funciona como podcast?, ¿encaja con la marca?,
¿lo escucharía la audiencia objetivo?, ¿compite con lo que hay en el sector?

**Orden de uso recomendado:**

```
1. validators/ + podcast_spec.validate_script_text  → ¿el guion es generable
                                                       y locutable sin fallos?
2. EVALUADOR_EDITORIAL_GUIONES.md (este doc)        → ¿el guion es un BUEN
                                                       podcast?
```

Si un guion falla el (1), arréglalo antes de pasarlo por el (2). El panel
editorial no juzga errores técnicos; los da por resueltos.

---

## 1. Visión de producto (input normativo del panel)

Antes de evaluar nada, el panel internaliza esta visión. Es la verdad del
proyecto. Si un guion va contra esto, se penaliza, por bonito que esté escrito.

### 1.1 Marca

- **Posicionamiento:** arquitecto de sistemas, no AI bro.
- **Persona detrás:** técnico hispano (Vallecas), con biografía concreta
  (ingeniería, banca/consultoría, padre, músico). No es influencer ni coach.
- **Tono:** directo, ironía sin abuso, paréntesis aclaratorios, coletillas
  conversacionales españolas ("a ver", "de hecho", "incluso", "y eso que").
- **Referentes positivos:** Lex Fridman (calma técnica), Andrej Karpathy
  (didáctica densa), Veritasium (rigor accesible), Latent Space (profundidad
  conversacional), Dwarkesh Patel (preguntas afiladas).
- **Anti-referentes:** Dot CSV (clickbait visual, superficial), AI bros con
  flechas y emojis, coaches motivacionales de LinkedIn, NotebookLM (validación
  coro entre dos voces sin criterio).

### 1.2 Audiencias por tipo

**M (módulo, 18-22 min) — captación + autoridad**
- Primaria: oyente nuevo curioso técnicamente (puede ser CTO/CIO/CEO o
  ingeniero/a no especializado en IA).
- Secundaria: contactos LinkedIn del autor que descubren el podcast.
- Función: que esa persona escuche M0 y decida que el resto del corpus
  vale la pena. M es la pieza-marca multi-plataforma.

**T (tema, 25-28 min) — formación**
- Primaria: estudiantes del máster que cursan el módulo. Audiencia cautiva
  con expectativa formativa concreta.
- Secundaria: profesional técnico que viene a profundizar un tema.
- Función: dejar al oyente con un mapa funcional del tema + casos reales
  que pueda llevar a su empresa.

**S (short, 60-90s) — descubrimiento + glosario**
- Primaria: usuario de Shorts/Reels/TikTok que tropieza con el vídeo en
  formato vertical mientras hace scroll.
- Secundaria: alguien que busca "qué es <término>" en YouTube.
- Función: que en 75s entienda un término y quiera escuchar el T asociado.

### 1.3 Diferenciadores del producto

1. **El sistema que genera el podcast es contenido del propio podcast**
   (APLICACION_PRACTICA en M). Construcción en público real, no manufacturada.
2. **Aviso de IA narrado explícito** (M/T) en el saludo. Honestidad como rasgo
   de marca, no como descargo legal escondido.
3. **Reparto Yago/Maria con criterio**: explicador técnico + voz escéptica
   experta empresarial. No son dos NotebookLMs validándose. Maria tensa,
   discrepa, pide aterrizar.
4. **Estructura por bloques visibles** con paridad opener — codificado en
   spec, no improvisado.
5. **Aplicación empresarial real en T** (BLOQUE_REALIDAD/CASOS) con
   fuentes reconocidas (Gartner, McKinsey, MIT, Stanford).
6. **Glosario unificado** con definiciones canónicas que se reusan
   transversalmente en el corpus.

### 1.4 Anti-patrones a detectar (lista negra editorial)

- **NotebookLM mode:** "Exactamente", "Claro que sí", "Eso es", "Por supuesto"
  como muletillas de validación coro entre los dos speakers.
- **AI bro pomposo:** "En el mundo actual de la IA…", "Sin más preámbulos…",
  "Es importante destacar que…", "Cabe mencionar…".
- **Coach motivacional:** "¡Excelente pregunta!", "Espero que esto te ayude",
  "Tienes toda la razón", "¡Adelante con tu proyecto!".
- **Intriga manufacturada:** "Stay tuned", "lo veremos en próximos episodios",
  cliffhanger artificial sin promesa real.
- **Divulgación amable genérica:** suena igual que cualquier otro podcast de
  IA en español. Sin biografía, sin criterio, sin postura.
- **Tecnicismo sin aterrizaje:** acumula términos en inglés sin traducir ni
  ejemplificar.
- **Caso empresarial inventado o genérico:** "una gran empresa del sector
  financiero implementó IA y mejoró la productividad un 30%". Sin nombre, sin
  fuente, sin verificable.
- **Métrica obsoleta:** datos de 2024 o 2025 presentados como "ahora", sin
  contexto de publicación.

---

## 2. Panel editorial — 5 perspectivas

Cada perspectiva es un "personaje evaluador". El prompt para Sonnet describe
cada uno como un experto con biografía y criterios. La voz importa: un buen
productor no habla como un SEO.

### 2.1 Perspectiva 1 — PRODUCTOR (estructura narrativa, retención)

**Personaje:** Productor con 15 años en podcasting de larga forma. Ha
producido formatos tipo Hard Fork, Practical AI, podcasts técnicos en
español. Sabe dónde aburre la gente. Su pregunta favorita es "¿por qué
debería seguir escuchando esto en el minuto 7?".

**4 ejes (todos los tipos):**

| Eje | Pregunta clave |
|------|----------------|
| `hook` | ¿La apertura para el scroll? ¿Es la versión más agresiva del conflicto? ¿Promete algo concreto en los 30-45s? |
| `pacing` | ¿Hay valle de atención? ¿Alguna sección se hace larga? ¿El reparto Yago/Maria fluye o se atasca en monólogos? |
| `retencion` | ¿Qué razones tiene el oyente para no cerrar en el minuto 3? ¿Hay anclajes (datos, casos, frase-fuerza) repartidos en el cuerpo, no solo al principio? |
| `cierre` | ¿La intervención previa al cierre canónico (CTA M / puente T) suena natural o forzada? La frase canónica final es literal y NO se juzga en este eje (es HARD-FAIL técnico). |

### 2.2 Perspectiva 2 — EDITOR DE MARCA (tono, posicionamiento)

**Personaje:** Editor de marca que conoce a fondo el style_guide de
MaquinarIA Pesada. Sabe distinguir entre Lex Fridman y Dot CSV en 30
segundos. Le obsesiona que el podcast no suene a "uno más de IA en español".

**4 ejes (todos los tipos):**

| Eje | Pregunta clave |
|------|----------------|
| `anti_ai_bro` | ¿Hay clichés, validación coro, "¡excelente pregunta!", emojis verbales, pose pomposa? Lista negra del §1.4. |
| `anti_notebook_lm` | ¿Maria y Yago tienen criterio o se aplauden? ¿Hay discrepancia real o solo turnos? ¿Maria tensa o solo asiente? |
| `posicionamiento` | ¿Suena a "arquitecto de sistemas que construye un podcast con IA" o a "divulgador genérico explicando IA"? |
| `voz_humana` | ¿Hay coletillas, paréntesis aclaratorios, ironía, anclajes de persona real detrás? ¿O suena 100% sintético? |

### 2.3 Perspectiva 3 — OYENTE PROTOTIPO (CTO/CIO/CEO escéptico)

**Personaje:** CTO de empresa española mediana, 42 años, escucha podcasts
en el coche. Le sobran ofertas de podcasts de IA. Cierra el podcast a los
4 minutos si no se justifica su tiempo. Detecta humo a kilómetros.

**4 ejes (M y T; en S este personaje no aplica — ver §3):**

| Eje | Pregunta clave |
|------|----------------|
| `densidad_valor` | ¿Cada minuto justifica su existencia? ¿Hay relleno conceptual o introducciones largas? |
| `aplicabilidad` | ¿Se lleva algo accionable o solo conceptos abstractos? ¿Podría aplicar algo de esto el lunes en su empresa? |
| `tolerancia_tecnica` | ¿Se siente expulsado por jerga sin aterrizar? ¿Las analogías cotidianas funcionan o son artificiales? ¿Se expanden las siglas al primer uso (en castellano, en aposición con comas)? |
| `credibilidad` | ¿Lo escucharía un par técnico (su CIO peer) sin sonrojarse? ¿Las fuentes son verificables o genéricas? |

### 2.4 Perspectiva 4 — EXPERTO TÉCNICO DEL SECTOR (rigor)

**Personaje:** Investigador/a senior en IA con doctorado, ha hecho papers
sobre los temas del corpus. Lee directamente los originales (Anthropic,
DeepMind, OpenAI, Google, papers de NeurIPS). Detecta simplificaciones
engañosas al instante.

**4 ejes (todos los tipos):**

| Eje | Pregunta clave |
|------|----------------|
| `precision` | ¿Hay errores conceptuales, simplificaciones engañosas, datos obsoletos, métricas mal interpretadas? |
| `profundidad` | ¿Se queda en superficie o entra al mecanismo? ¿El "cómo funciona" es real o es analogía sin contenido? |
| `casos` | ¿Los ejemplos empresariales son verificables o genéricos? ¿Las cifras tienen fuente y fecha? |
| `cobertura` | ¿Se cubren los conceptos críticos del módulo o se evitan los espinosos? ¿Hay sesgo hacia lo fácil de explicar? |

### 2.5 Perspectiva 5 — SEO/DISTRIBUCIÓN (descubribilidad)

**Personaje:** Director/a de distribución de un podcast network. Le importa
que el episodio funcione en YouTube, Spotify, iVoox, LinkedIn, X, Shorts.
Piensa en "qué fragmento de 60s se hace clip" antes de oír el episodio
entero.

**4 ejes (todos los tipos, con énfasis distinto por tipo):**

| Eje | Pregunta clave |
|------|----------------|
| `hook_como_clip` | ¿Los primeros 60s funcionan recortados como short/clip de LinkedIn? ¿Sin contexto, ¿sigue siendo interesante? |
| `frase_fuerza` | ¿Hay 1-2 frases citables que polaricen o sorprendan? ¿Aptas para post de LinkedIn o thumbnail? |
| `keyword_density` | ¿El término central aparece con la densidad justa para posicionar (sin keyword-stuffing)? ¿El módulo o tema queda inequívocamente marcado? |
| `titulo_preview` | ¿De qué se hablaría en LinkedIn al citar este episodio? ¿Hay un ángulo claro o es genérico? |

---

## 3. Adaptación por tipo

### 3.1 Pesos por perspectiva y tipo

El score global del guion es media ponderada. Los pesos reflejan qué importa
más para cada función del producto.

| Perspectiva | Peso M | Peso T | Peso S |
|-------------|--------|--------|--------|
| Productor | 0.25 | 0.20 | 0.30 |
| Editor de marca | 0.25 | 0.15 | 0.25 |
| Oyente prototipo | 0.10 | 0.25 | 0.00 (N/A) |
| Experto técnico | 0.15 | 0.30 | 0.15 |
| SEO/distribución | 0.25 | 0.10 | 0.30 |
| **Total** | **1.00** | **1.00** | **1.00** |

**Lectura:**
- **M:** equilibrio productor + marca + SEO. Captación pesa.
- **T:** experto técnico + oyente CTO mandan. Es formación, no captación.
- **S:** SEO + productor. La marca importa pero la audiencia es masiva,
  no se filtra por CTOs. Sin oyente CTO (no aplica).

### 3.2 Ejes específicos adicionales por tipo

#### Ejes específicos de M (3 ejes adicionales)

| Eje | Perspectiva responsable | Pregunta clave |
|-----|------------------------|----------------|
| `m_aplicacion_practica_resonancia` | Editor de marca | ¿APLICACION_PRACTICA conecta el sistema generador con el módulo de forma resonante? ¿O suena pegada y promocional? |
| `m_aviso_ia_engancha` | Productor | ¿La versión enganche del aviso IA (M-specific) funciona como gancho o suena rutinaria? |
| `m_cta_T_natural` | SEO/distribución | ¿La CTA hacia los T del módulo en CIERRE_FINAL suena natural o como anuncio? |

#### Ejes específicos de T (3 ejes adicionales)

| Eje | Perspectiva responsable | Pregunta clave |
|-----|------------------------|----------------|
| `t_bloque_casos_verificable` | Experto técnico | ¿BLOQUE_CASOS contiene casos con nombre propio + fuente + resultado concreto? ¿O son genéricos ("una gran empresa")? |
| `t_bloque_limites_honesto` | Experto técnico | ¿BLOQUE_LIMITES reconoce de verdad los límites o los maquilla? |
| `t_maria_voz_experta` | Editor de marca | ¿Maria en BLOQUE_CASOS es realmente voz experta empresarial o solo presenta datos sin postura? |

#### Ejes específicos de S (3 ejes adicionales)

| Eje | Perspectiva responsable | Pregunta clave |
|-----|------------------------|----------------|
| `s_hook_template_funciona` | Productor | ¿El hook encaja en H1/H2/H3 y funciona? ¿O es genérico ("Hoy hablamos de...")? |
| `s_cierre_canonico_resuena` | SEO/distribución | ¿El cierre canónico hacia el T del tema suena como CTA real o como muletilla? |
| `s_termino_unico_claro` | Experto técnico | ¿El short define UN solo concepto claramente o intenta cubrir varios? |

### 3.3 Total de ejes por tipo

| Tipo | Ejes generales | Ejes específicos | Total |
|------|----------------|------------------|-------|
| M | 20 | 3 | 23 |
| T | 20 (con oyente CTO) | 3 | 23 |
| S | 16 (sin oyente CTO) | 3 | 19 |

---

## 4. Score por perspectiva y veredicto final

### 4.1 Cómo se construye el score por perspectiva

Cada perspectiva da:
- **Score global 1-10** de su voz (media implícita de sus 4 ejes, ponderada
  por el peso editorial que la propia perspectiva ponga; no se exige cálculo
  matemático visible — el LLM justifica el global con 1 línea).
- **1 línea de rationale** del score global.
- **3-5 issues priorizados** accionables. Cada issue es:
  ```
  [Severidad] · Eje · "frase concreta del problema" → "propuesta de cambio"
  ```
  Severidad: `critico` · `relevante` · `menor`.

### 4.2 Score global del guion

Media ponderada de los 5 scores de perspectiva (pesos del §3.1). Resultado:
1 número 1-10 con 1 decimal.

### 4.3 Veredicto en 3 niveles

```
PUBLICAR ✅       si score global ≥ 7.5 Y ningún issue crítico en ninguna perspectiva
REVISAR  🟡       si 6.0 ≤ score < 7.5  O  hay 1-2 issues críticos
BLOQUEAR 🔴       si score < 6.0  O  hay ≥3 issues críticos  O  ≥1 issue crítico en marca
```

**Asimetría intencional (confirmada por desempate editorial 2026-05-19):**
un issue crítico en la perspectiva **Editor de marca** basta para bloquear,
aunque el resto puntúe alto. La marca es la columna del producto; un
episodio brillante técnicamente pero que suena a AI bro **no se publica**.

### 4.4 Razones para subir de nivel

Tras el veredicto, el panel emite:

```
Para subir REVISAR → PUBLICAR, cambia:
  1. [crítico · hook]    "Este hook empieza con 'Hoy hablamos de…'"
                         → "Sustituir por hook-dato con la cifra de adopción
                            que aparece en el minuto 3"
  2. [relevante · pacing] "Pacing BLOQUE_DESTACADO se hace largo en 5-6 min"
                         → "Romper segundo concepto en dos sub-bloques
                            con pregunta de Maria intercalada"
```

Si el veredicto es BLOQUEAR, las razones explican qué hay que arreglar para
pasar a REVISAR (un paso, no dos).

---

## 5. Benchmark vs referentes del sector

El panel sitúa cada guion en un mapa de referentes. Esto **no sustituye** al
score; lo enriquece y lo hace comparable culturalmente.

### 5.1 Mapa de referentes

| Cluster | Score implícito | Referentes | Características |
|---------|----------------|------------|-----------------|
| **Top tier** | 9-10 | Lex Fridman AI, Latent Space, Dwarkesh Patel | Profundidad técnica real, criterio editorial fuerte, voz humana, fuentes primarias |
| **Sólido sectorial** | 7-8 | Practical AI, Hard Fork, El Robot de Platón, Nate Gentile | Buena producción, ángulo claro, criterio, accesible sin ser superficial |
| **Estándar IA** | 5-6 | La mayoría de podcasts IA en español, AI in Business | Útil pero genérico, sin diferenciación clara, tono divulgativo amable |
| **Bajo** | 3-4 | Dot CSV (con permiso), divulgación tipo YouTube IA en español promedio | Clickbait visual, superficial, AI-bro mood |
| **Crítico** | 1-2 | Podcasts coach-mode, contenido auto-generado sin criterio | NotebookLM puro, sin postura, sin voz |

### 5.2 Output de benchmark

Por cada guion, el panel emite **una frase** del tipo:

> "Este guion está en el clúster Sólido sectorial (7.2), cerca de Practical AI
> en estructura pero por debajo en profundidad técnica. Le falta el rasgo
> Karpathy de entrar al mecanismo en lugar de quedarse en el qué."

Esta frase aparece en el reporte después del score global y antes de los
issues priorizados por perspectiva.

### 5.3 Detección de derivas (solo modo `--corpus`)

En modo lote, el panel además identifica:
- **Inconsistencia de marca:** ¿hay guiones que suenan distintos entre sí?
- **Deriva de profundidad:** ¿se simplifica más el corpus a medida que avanza?
- **Saturación de ejemplos:** ¿se repite el caso JPMorgan en 4 episodios?
- **Reparto Yago/Maria:** ¿Maria gana o pierde peso a lo largo del corpus?

---

## 6. Prompts del panel

### 6.1 Prompt maestro (modo por-guion, default)

```
Sos un panel editorial de 5 voces que evalúa guiones del podcast
MaquinarIA Pesada. El podcast es un proyecto de "arquitecto de sistemas
que construye un podcast de IA con IA". Audiencia técnica hispana. Tono
directo, anti-AI-bro, anti-NotebookLM. Referentes positivos: Lex Fridman,
Karpathy, Veritasium, Latent Space, Dwarkesh Patel. Anti-referentes: Dot CSV,
coaches LinkedIn, podcasts de IA en español genéricos.

INPUT que vas a recibir:
1. Tipo de guion: M | T | S
2. Spec correspondiente (PODCAST_{tipo}_SPEC.md) — para entender el formato
3. Contenido del guion .txt
4. Visión de producto (la del §1 de EVALUADOR_EDITORIAL_GUIONES.md)
5. Ejes adaptados al tipo (la matriz del §3 de este mismo doc)

INSTRUCCIONES:
1. Lee el guion como si lo fueras a escuchar en el coche, no como un
   linter. Tu trabajo es decir si funciona como podcast.
2. Adopta sucesivamente cada una de las 5 perspectivas (Productor,
   Editor de marca, Oyente prototipo, Experto técnico, SEO/distribución).
   Para cada una:
   - Da un score 1-10 con UNA línea de justificación.
   - Identifica 3-5 issues priorizados. Cada issue:
     [crítico|relevante|menor] · eje · "frase del problema" → "propuesta"
   - Las propuestas tienen que ser concretas (qué cambiar, no "mejorar el hook").
3. Aplica los ejes específicos del tipo (§3.2):
   - M: m_aplicacion_practica_resonancia, m_aviso_ia_engancha, m_cta_T_natural
   - T: t_bloque_casos_verificable, t_bloque_limites_honesto, t_maria_voz_experta
   - S: s_hook_template_funciona, s_cierre_canonico_resuena, s_termino_unico_claro
4. Calcula el score global ponderado según los pesos del §3.1.
5. Sitúa el guion en el mapa de referentes (§5.1) con UNA frase comparativa.
6. Emite veredicto: PUBLICAR ✅ · REVISAR 🟡 · BLOQUEAR 🔴 (criterios §4.3).
7. Si el veredicto es REVISAR o BLOQUEAR, lista las 2-3 cosas concretas
   que hay que cambiar para subir UN nivel.

NO HAGAS:
- Ni "¡excelente guion!" ni "tiene mucho potencial". Sé directo.
- No restaures el guion completo en tu output.
- No valides reglas técnicas (eso lo hace el otro evaluador).
- No inventes datos de mercado para justificar tus scores.
- No sugieras añadir emojis ni cambios contra el style_guide.
- NO juzgues la frase canónica del cierre (es literal e intocable, HARD-FAIL técnico).

FORMATO DE OUTPUT: estrictamente el template del §6.3 de este doc.
```

### 6.2 Prompt modo corpus (`--corpus`)

```
Acabás de leer N guiones (M/T/S mezclados) del podcast MaquinarIA Pesada.
Además de la evaluación individual de cada uno (que ya hiciste o que vas a
hacer en este mismo prompt si N es manejable), responde estas 4 preguntas
sobre el corpus como conjunto:

1. RANKING — ordená los guiones del mismo tipo por score global descendente.
   Identificá los 3 mejores y los 3 peores de cada tipo.
2. CONSISTENCIA DE MARCA — ¿suenan todos a la misma marca? Si hay derivas
   (M0-M3 vs M8-M14, por ejemplo), señalalas con guiones concretos.
3. DERIVAS DE PROFUNDIDAD — ¿se simplifica el corpus a lo largo del tiempo?
   ¿Hay temas críticos del máster que se cubren con menos rigor que otros?
4. SATURACIÓN — ¿qué casos empresariales se repiten? ¿Hay ejemplos
   sobreusados (JPMorgan, OpenAI, etc.)? ¿Se diversifica el catálogo?

OUTPUT: sección "AUDITORÍA DE CORPUS" añadida al final del informe, antes
del cierre.
```

### 6.3 Template de output por guion

```markdown
## {filename} · {tipo}

**Score global:** {X.X}/10 · **Veredicto:** {PUBLICAR ✅ | REVISAR 🟡 | BLOQUEAR 🔴}
**Cluster:** {Top tier | Sólido sectorial | Estándar IA | Bajo | Crítico} — {frase comparativa con referente concreto}

### Panel

**Productor — {score}/10.** {1 línea rationale}
- [{sev}] {eje} · "{problema}" → "{propuesta}"
- [...]

**Editor de marca — {score}/10.** {1 línea}
- [...]

**Oyente prototipo — {score}/10.** {1 línea}     ← omitir esta sección si tipo == S
- [...]

**Experto técnico — {score}/10.** {1 línea}
- [...]

**SEO/distribución — {score}/10.** {1 línea}
- [...]

### Ejes específicos del tipo

- **{eje específico 1}:** {1-2 frases}
- **{eje específico 2}:** {1-2 frases}
- **{eje específico 3}:** {1-2 frases}

### Para subir de nivel

Para pasar de **{veredicto actual}** a **{siguiente nivel}**, cambia:
1. {acción concreta} — impacto en eje {eje}
2. {acción concreta} — impacto en eje {eje}
3. (opcional) {acción concreta}
```

---

## 7. CLI esperada

```bash
# Evaluar un guion concreto (modo por-guion)
python evaluador_editorial.py --file Guiones/M3.txt

# Evaluar todo un directorio en modo por-guion (ejecuta 1 prompt por fichero)
python evaluador_editorial.py --dir Guiones/

# Modo corpus (1 prompt sobre todo el directorio + auditoría global)
python evaluador_editorial.py --dir Guiones/ --corpus

# Solo un tipo
python evaluador_editorial.py --dir Guiones/ --only-kind M

# Filtrar por perspectiva
python evaluador_editorial.py --file Guiones/M3.txt --perspective brand

# Output a markdown
python evaluador_editorial.py --dir Guiones/ --md docs/editorial/{timestamp}.md

# Output a JSON
python evaluador_editorial.py --dir Guiones/ --json logs/editorial.json

# Pasar veredicto a exit code
python evaluador_editorial.py --dir Guiones/ --strict
# exit 0 = todo PUBLICAR · exit 1 = al menos un REVISAR · exit 2 = al menos un BLOQUEAR
```

Modelo: **`claude-sonnet-4-6`** (default, según CLAUDE.md). Coste estimado
~$0.034 por guion en modo por-guion; ~$0.55 para corpus completo de 41 guiones.

---

## 8. Cómo se invoca desde Claude Code

```
Lee EVALUADOR_EDITORIAL_GUIONES.md de principio a fin. Lee también
PODCAST_M_SPEC.md, PODCAST_T_SPEC.md, PODCAST_S_SPEC.md y la sección §13
de PODCAST_MASTER_SPEC.md (reglas editoriales) para tener internalizada la
visión de producto.

Para cada fichero .txt en Guiones/:
1. Detecta el tipo por filename.
2. Carga el spec correspondiente.
3. Ejecuta el prompt maestro del §6.1 con el guion y el spec en contexto.
4. Devuelve el output con el template del §6.3.
5. Acumula los outputs.

Al final, si pasé --corpus, ejecuta también el prompt del §6.2 sobre el
conjunto y añade la sección AUDITORÍA DE CORPUS.

NO valides reglas técnicas — para eso uso validators/ y validar_episodio.py.
NO modifiques los guiones.
NO inventes datos.
NO juzgues la frase canónica del cierre.
Sé directo, sin "¡excelente!" ni "mucho potencial".
```

---

## 9. Lo que el evaluador NO hace (límites explícitos)

- **No reescribe guiones.** Solo evalúa y propone cambios. La reescritura es
  decisión humana (o de otro pipeline distinto).
- **No valida reglas técnicas.** Eso es trabajo de `validators/` + `podcast_spec.validate_script_text`.
- **No juzga la frase canónica del cierre.** Es literal e intocable. El eje
  `cierre` solo evalúa cómo se integra la intervención previa (CTA M /
  puente T) con esa frase canónica.
- **No mide audio.** Es evaluación textual del guion; el audio se valida
  con `validar_episodio.py`.
- **No predice métricas reales** de audiencia.
- **No reemplaza el juicio editorial humano final.** Es panel asesor, no
  comité de aprobación.

---

## 10. Roadmap de uso

1. **Primera pasada (modo `--corpus` sobre los 41 guiones del corpus v7):**
   sirve como auditoría inicial. Coste: ~$0.55.
2. **Filtrado por veredicto:** los BLOQUEAR son los que se tocan primero.
3. **Iteración por guion (modo default):** cuando se reescribe un guion, se
   re-evalúa solo a ese. Coste por iteración: ~$0.034.
4. **Auditoría trimestral (modo `--corpus`):** cada vez que se suman 5-10
   guiones nuevos, una pasada de corpus completa para detectar derivas
   de marca o profundidad.

---

## 11. Decisiones de integración (desempates 2026-05-19)

Cuando este evaluador se integró con el sistema técnico existente surgieron
4 conflictos. Decisiones registradas:

| # | Conflicto | Decisión |
|---|---|---|
| 1 | Cierre canónico literal vs naturalidad editorial | Mantener literal (HARD-FAIL técnico). El eje `cierre` juzga solo la integración con la intervención previa. |
| 2 | Pronunciación vs expansión de siglas | Mantener overrides + AÑADIR regla nueva: expansión castellana al primer uso, en aposición con comas. HARD-FAIL técnico. |
| 3 | Blacklists nuevas | Promover a HARD-FAIL técnico (extender `validators/shared/blacklist.py`). Listas extensibles. |
| 4 | Asimetría del veredicto | 1 issue crítico en MARCA = BLOQUEAR aunque el resto puntúe ≥9. |
| 5 | Formato expansión siglas | Aposición con comas: `"los LLM, modelos de lenguaje grandes, son..."` |
| 6 | Fuente de la expansión castellana | Campo `**ES:**` en cada entrada del glosario unificado. |
| 7 | Modelo del panel | `claude-sonnet-4-6`. |
| 8 | Match de las nuevas blacklists | Al inicio de intervención O en intervenciones cortas (≤6 palabras) cuando la frase prohibida es ≤2 palabras; en frases ≥3 palabras basta con match de inicio. |

---

*Fin del documento.*
