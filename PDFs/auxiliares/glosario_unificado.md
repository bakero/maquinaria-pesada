# Glosario Unificado — MaquinarIA Pesada

Definiciones canónicas de términos técnicos del corpus del máster.
Cualquier término que aparezca en un guion Y esté aquí debe usar esta definición.

Cada entrada incluye una línea `**Fuentes:**` con los PDFs donde aparece el concepto,
en formato `MX_TY` (módulo X, tema Y) o `MX_RESUMEN` (resumen del módulo X).
Esta línea es de lectura programática: `generar_guion.py` y `validar_episodio.py` la
parsean para alimentar y medir la cobertura de conceptos en los guiones.

---

## Conceptos base

## IA / Inteligencia Artificial
**Fuentes:** base
Sistema computacional capaz de realizar tareas que típicamente requieren inteligencia humana.
Abreviatura canónica en el podcast: **I.A.** (con puntos).

## LLM (Large Language Model)
**Fuentes:** M0_T1, M0_T2, M0_T3, M0_T4, M0_RESUMEN, M5_T2, M5_T3, M5_RESUMEN
**S:** 23
Modelo de lenguaje de gran escala entrenado sobre corpus masivos de texto.
Genera texto prediciendo el siguiente token dado un contexto previo.

## Prompt
**Fuentes:** M6_T1, M6_T2, M6_T3, M6_T4, M6_T5, M6_T6, M6_T7, M6_T8, M6_T9, M6_RESUMEN, M12_T2
**S:** 12
Instrucción o contexto de entrada que se proporciona a un LLM para guiar su respuesta.
Puede incluir system prompt, contexto, ejemplos y la pregunta del usuario.

## Token
**Fuentes:** M1_T10, M5_T2, M5_T3, M5_T5, M5_RESUMEN, M9_T7
**S:** 19
Unidad mínima de procesamiento de un LLM. Aproximadamente 0.75 palabras en inglés,
0.6-0.7 palabras en español. Los LLMs tienen un límite de contexto medido en tokens.

## RAG (Retrieval-Augmented Generation)
**Fuentes:** M0_T1, M0_T2, M0_T4, M0_T5, M1_T7, M1_T11, M1_RESUMEN, M3_RESUMEN, M5_T3, M5_T4, M5_T8, M5_RESUMEN, M7_T1, M7_T2, M7_T3, M7_T4, M7_T5, M7_T6, M7_T7, M7_T8, M7_RESUMEN, M8_T2, M9_T1, M9_T4, M9_T5, M9_T6, M9_T7, M9_RESUMEN, M12_T1, M12_T3, M12_T5, M14_T1, M14_T2, M14_T4, M14_T6
**S:** 1
Técnica que combina recuperación de documentos relevantes con generación de texto.
El modelo accede a una base de conocimiento externa en el momento de la inferencia.

## Fine-tuning
**Fuentes:** M0_T3, M0_RESUMEN, M1_T3, M2_T1, M2_T2, M2_T5, M3_T1, M4_T5, M4_T6, M4_RESUMEN, M5_T2, M5_T3, M5_T4, M5_RESUMEN, M8_T2, M8_T3, M9_T1, M9_T7, M9_T9, M12_T3, M12_T8
**S:** 2
Proceso de ajuste de los pesos de un modelo preentrenado sobre un conjunto de datos
específico para mejorar su rendimiento en una tarea concreta.

## Embedding
**Fuentes:** M0_T2, M1_T8, M1_T9, M2_T1, M2_T6, M2_T7, M2_RESUMEN, M5_T2, M5_T5, M5_RESUMEN, M7_T1, M7_T2, M7_T3, M7_T4, M7_T5, M7_RESUMEN
**S:** 6
Representación vectorial densa de texto (o cualquier dato) en un espacio de alta dimensión.
Permite medir similitud semántica mediante distancia vectorial.

## Agentic AI / Agente IA
**Fuentes:** M0_T1, M0_T2, M0_T6, M0_RESUMEN, M10_T1, M10_T2, M10_T3, M10_T4, M10_T5, M10_T6, M10_T7, M10_T8, M10_T9, M10_T10, M10_RESUMEN, M11_T5, M11_T6, M12_T1, M12_T5, M14_T4, M14_T6, M14_T7, M14_T8
**S:** 5
Sistema de IA capaz de planificar y ejecutar secuencias de acciones de manera autónoma
para alcanzar un objetivo, usando herramientas y retroalimentación del entorno.

## Chain-of-Thought (CoT)
**Fuentes:** M1_T4, M1_T12, M1_RESUMEN, M5_T8, M6_T1, M6_T2, M6_T3, M6_T4, M6_T5, M6_T6, M6_T9, M6_RESUMEN
**S:** 9
Técnica de prompting que instruye al modelo a razonar paso a paso antes de responder.
Mejora la precisión en tareas de razonamiento complejo.

## Temperatura (en LLMs)
**Fuentes:** M1_T6, M1_T8, M1_T11, M5_T6, M5_RESUMEN
**S:** 40
Hiperparámetro que controla la aleatoriedad en el muestreo de tokens.
Valores bajos (0.0-0.3): respuestas más deterministas.
Valores altos (0.7-1.0): más variedad y creatividad.

## Context window / Ventana de contexto
**Fuentes:** M0_T4, M5_T5, M5_RESUMEN, M7_T3
**S:** 24
Límite máximo de tokens que un LLM puede procesar en una sola inferencia
(entrada + salida combinadas).

## Hallucination / Alucinación
**Fuentes:** M0_T1, M0_T2, M0_T4, M0_RESUMEN, M1_T11, M1_RESUMEN, M2_T8, M5_T7, M5_T8, M5_RESUMEN, M6_T9, M12_T1, M13_T3, M13_RESUMEN
**S:** 3
Generación de información factualmente incorrecta pero presentada con confianza
por un LLM. Efecto emergente del entrenamiento por predicción de tokens.

## RLHF (Reinforcement Learning from Human Feedback)
**Fuentes:** M2_T4, M2_T8, M3_T1, M3_RESUMEN, M4_T5, M4_RESUMEN, M5_T3, M5_T8
**S:** 11
Técnica de alineación que usa feedback humano para entrenar un modelo de recompensa
y ajustar el LLM mediante aprendizaje por refuerzo.

## Vector database / Base de datos vectorial
**Fuentes:** M2_T1, M2_T6, M7_T1, M7_T2, M7_T4, M7_T5, M7_T6, M8_T7
**S:** 26
Sistema de almacenamiento especializado en búsqueda por similaridad de embeddings.
Fundamental para implementaciones RAG.

## Sistema automatico
**Fuentes:** M1_T2, M1_T5, M11_T1, M11_T3
**S:** 131
Término canónico del podcast para referirse al sistema de producción de MaquinarIA Pesada.
Siempre en minúsculas en el texto hablado.

---

## Módulo 0 — Introducción Estratégica

## IA Descriptiva y Analítica
**Fuentes:** M0_T1
Primera generación de IA empresarial (años 90–2010): dashboards, reporting y estadística que analiza datos históricos ya ocurridos. Sigue siendo el 80% del valor real en muchas organizaciones.

## IA Predictiva
**Fuentes:** M0_T1, M0_RESUMEN
**S:** 173
Segunda generación de IA empresarial (2010–2020): machine learning clásico aplicado a forecasting, scoring de riesgo y detección de anomalías; aprende patrones históricos para predecir comportamientos futuros.

## IA Generativa
**Fuentes:** M0_T1, M0_T2, M0_RESUMEN
**S:** 110
Paradigma de IA (2020–presente) en el que los modelos aprenden la distribución estadística de los datos y generan nuevo contenido. Su limitación estructural es producir lo estadísticamente probable en lugar de lo verificablemente verdadero.

## IA Estrecha vs IA General (ANI / AGI)
**Fuentes:** M0_RESUMEN
**S:** 227
Toda la IA existente en 2025 es IA Estrecha (ANI): optimizada para tareas específicas sin generalización fuera de su dominio. La IA General (AGI) razonaría sobre cualquier dominio con flexibilidad humana y sigue siendo objeto de debate.

## Modelos frontier
**Fuentes:** M0_T3, M0_RESUMEN
**S:** 192
Modelos de IA con la mayor capacidad disponible en el mercado en cada momento (familias GPT, Claude, Gemini). Su uso implica dependencia del proveedor, precio por token y cesión de datos a su infraestructura.

## Modelos open weights (pesos abiertos)
**Fuentes:** M0_T3, M0_RESUMEN
**S:** 193
Modelos que publican sus parámetros para uso libre y pueden desplegarse en infraestructura propia (Llama, Mistral/Mixtral, Qwen, Falcon). Ofrecen soberanía de datos y menor coste de inferencia a escala a cambio de mayor esfuerzo operativo.

## Self-hosting
**Fuentes:** M0_T3
Estrategia de despliegue en la que la organización ejecuta modelos open weights en su propia infraestructura (vLLM, TGI, TensorRT-LLM). Elimina la dependencia del proveedor y mantiene los datos dentro del perímetro corporativo.

## Estrategia multiproveedores / capa de abstracción
**Fuentes:** M0_T3
Enfoque arquitectónico que abstrae el modelo subyacente (p. ej. con LiteLLM) para cambiar de proveedor con mínimo refactoring. Reduce el vendor lock-in y permite enrutar cada tarea al modelo más adecuado por coste.

## Benchmarks de evaluación de modelos (MMLU, GPQA, SWE-bench)
**Fuentes:** M0_T3, M0_T4
Conjuntos de pruebas estandarizados que miden capacidad de razonamiento general (MMLU, GPQA) o de generación de código (SWE-bench). Miden capacidad general, no rendimiento en un caso de uso concreto.

## Zero data retention
**Fuentes:** M0_T3
Configuración enterprise por la que los datos procesados no se retienen para entrenamiento ni mejora del servicio. Requisito para sectores con obligaciones estrictas de confidencialidad.

## Corte de conocimiento (knowledge cutoff)
**Fuentes:** M0_T4, M1_T11
**S:** 230
Fecha límite de entrenamiento de un LLM más allá de la cual el modelo no tiene información. Hace inadecuados a los LLMs sin acceso a búsqueda para tareas que requieren datos actualizados.

## Fenómeno "lost in the middle"
**Fuentes:** M0_T4, M1_T8, M1_T11
**S:** 222
Degradación de la atención en contextos largos: el modelo presta menos atención a la información ubicada en la parte central del contexto que a la del inicio y el final.

## Tool use (uso de herramientas)
**Fuentes:** M0_T4, M9_T3
**S:** 235
Capacidad de un LLM para invocar herramientas externas (intérprete de código, calculadora, búsqueda web) durante la generación. Compensa las limitaciones aritméticas y de acceso a información actualizada.

## Golden dataset
**Fuentes:** M0_T4, M6_T1, M6_T8, M6_RESUMEN, M7_T1, M7_T2, M7_T6, M7_T7, M8_T1, M8_T2, M8_T8, M8_T9, M8_RESUMEN, M10_T9, M10_T10, M10_RESUMEN, M14_T2
**S:** 4
Conjunto curado de 50–500 casos representativos con output de referencia verificado, usado como test suite para medir y comparar de forma objetiva el rendimiento de un sistema de IA antes de desplegarlo.

## Human-in-the-loop (HITL)
**Fuentes:** M0_T1, M0_T4, M0_T5, M10_T2, M10_T5, M10_T10, M10_RESUMEN, M11_T3, M11_T4, M11_T5, M11_RESUMEN, M12_T2, M12_T5, M14_T2
**S:** 8
Patrón de diseño en el que una persona supervisa, valida o aprueba las salidas del modelo en casos de baja confianza o alto impacto, antes de continuar. Defensa robusta frente a alucinación y prompt injection.

## RPA (Robotic Process Automation)
**Fuentes:** M0_T2, M11_T1, M11_T2, M11_T4, M11_RESUMEN
**S:** 39
Automatización robótica de procesos mediante bots que siguen flujos predefinidos a nivel de interfaz de usuario, sin capacidad de adaptación. A diferencia de la IA agéntica, ejecuta secuencias fijas.

## MLOps (Machine Learning Operations)
**Fuentes:** M0_T6, M0_RESUMEN, M8_T1, M8_RESUMEN
**S:** 50
Conjunto de prácticas y herramientas (versionado de modelos, monitorización continua, CI/CD para IA) que permite mantener sistemas de IA en producción de forma sostenible y escalar de piloto a producción.

## AI Champions
**Fuentes:** M0_T6, M14_T5, M14_T6, M14_RESUMEN
**S:** 43
Empleados de negocio con formación en IA que lideran su adopción en sus equipos y actúan como catalizadores bottom-up. Mecanismo de mayor impacto en la velocidad de adopción con bajo coste.

## Shadow AI
**Fuentes:** M0_T6
Uso de herramientas de IA personales por parte de empleados para trabajo corporativo sin aprobación ni política oficial. Ocurre en más del 90% de las empresas; ignorarlo crea riesgos de seguridad.

## LangChain / LlamaIndex
**Fuentes:** M0_RESUMEN
**S:** 228
Frameworks de desarrollo de aplicaciones de IA que simplifican la construcción de sistemas RAG y agénticos mediante abstracciones reutilizables. Estándares de facto del ecosistema en 2025.

## Modelos de difusión
**Fuentes:** M0_T2, M0_RESUMEN, M4_T4
**S:** 69
Modelos generativos que aprenden la distribución de imágenes añadiendo y eliminando ruido de forma iterativa. Base de DALL-E, Midjourney, Stable Diffusion y Sora; superan a las GANs en calidad y estabilidad.

---

## Módulo 1 — Fundamentos y Razonamiento

## Test de Turing
**Fuentes:** M1_T1
Criterio de inteligencia propuesto por Alan Turing (1950): una máquina lo supera si un evaluador humano no puede distinguirla de otro humano en una conversación textual.

## Inviernos de la IA
**Fuentes:** M1_T1, M1_RESUMEN
**S:** 176
Períodos cíclicos de caída drástica en financiación e interés de la IA, desencadenados cuando las expectativas superaron las capacidades reales (años 70 y finales de los 80).

## Ciclo del hype de Gartner
**Fuentes:** M1_T1
Modelo que describe el patrón recurrente de pico de expectativas sobredimensionadas seguido de decepción y estabilización en cualquier tecnología emergente.

## Paradigma simbólico
**Fuentes:** M1_T1, M1_T2
Enfoque de IA donde el conocimiento se representa explícitamente como símbolos, hechos y reglas lógicas, y un motor de inferencia los combina para derivar conclusiones. Garantiza interpretabilidad total pero es frágil ante la incertidumbre.

## Paradigma conexionista
**Fuentes:** M1_T1, M1_T3
Enfoque de IA donde el conocimiento emerge del ajuste iterativo de millones de parámetros numéricos (pesos de redes neuronales) mediante optimización sobre datos.

## Paradigma estadístico/probabilístico
**Fuentes:** M1_T1, M1_T6
Enfoque de IA que modela el conocimiento como distribuciones de probabilidad sobre variables; los LLMs son su expresión moderna al representar P(token_siguiente | tokens_anteriores).

## Backpropagation
**Fuentes:** M1_T1, M1_T3, M2_T2, M2_RESUMEN, M4_RESUMEN
**S:** 21
Algoritmo que calcula el gradiente de la función de pérdida respecto a cada peso de una red neuronal aplicando la regla de la cadena hacia atrás en una sola pasada. Base de todo el deep learning moderno.

## Sistema experto
**Fuentes:** M1_T1, M1_T2
Programa de IA simbólica compuesto por una base de conocimiento (reglas si-entonces y hechos) y un motor de inferencia que las aplica. MYCIN y R1/XCON son ejemplos históricos; Drools e IBM ODM, sucesores modernos.

## Motor de inferencia
**Fuentes:** M1_T2
Componente de un sistema experto que evalúa las reglas sobre los hechos disponibles para derivar conclusiones. Opera por encadenamiento hacia adelante (forward chaining) o hacia atrás (backward chaining).

## Lógica de predicados (primer orden)
**Fuentes:** M1_T2
Extensión de la lógica proposicional con variables, cuantificadores y relaciones entre entidades. Lenguaje formal subyacente a los sistemas expertos clásicos.

## Ontología (IA)
**Fuentes:** M1_T2, M1_T7
Especificación formal y explícita de una conceptualización de dominio: qué entidades existen, qué propiedades tienen y qué relaciones las conectan. Estándares de referencia: W3C OWL y RDF/RDFS.

## Grafo de conocimiento (Knowledge Graph)
**Fuentes:** M1_T2, M1_T7
Implementación a gran escala de los principios ontológicos mediante millones de tripletas RDF (sujeto, predicado, objeto). Ejemplos: Knowledge Graph de Google, Wikidata, grafos empresariales de LinkedIn o Amazon.

## SPARQL
**Fuentes:** M1_T7
Lenguaje de consulta estándar W3C para grafos de conocimiento RDF, análogo a SQL. Permite navegar tripletas y recuperar subgrafos mediante patrones sobre sujeto, predicado y objeto.

## GraphRAG
**Fuentes:** M1_T7, M7_T5, M7_T8, M7_RESUMEN
**S:** 49
Variante de RAG (Microsoft, 2024) que usa un grafo de entidades y relaciones como base de recuperación estructurada en lugar de similitud vectorial. Supera al RAG estándar en preguntas sobre relaciones y síntesis global del corpus.

## Descenso de gradiente
**Fuentes:** M1_T3
Algoritmo de optimización que actualiza iterativamente los pesos de una red en la dirección que reduce la función de pérdida. Mecanismo de entrenamiento universal del paradigma conexionista.

## Función de activación (ReLU, GELU, sigmoid, tanh)
**Fuentes:** M1_T3, M2_T2, M2_RESUMEN, M4_T1, M4_T2, M4_RESUMEN
**S:** 17
No-linealidad aplicada en cada neurona tras la suma ponderada de sus entradas. ReLU(x)=max(0,x) mitiga el vanishing gradient; GELU es la más usada en LLMs modernos; sigmoid y tanh saturan en redes profundas. Sin ellas, una red multicapa equivaldría a una capa lineal.

## Transfer learning
**Fuentes:** M1_T3, M4_T5
**S:** 236
Técnica que reutiliza un modelo preentrenado en corpus genéricos y lo adapta a un caso de uso específico con datos reducidos. Permite aprovechar modelos como BERT o ResNet sin un preentrenamiento desde cero.

## Sistema 1 / Sistema 2 (dualidad en IA)
**Fuentes:** M1_T4, M1_T12, M1_RESUMEN
**S:** 123
Marco de Daniel Kahneman aplicado a IA: Sistema 1 es el modo rápido y basado en patrones (LLMs estándar); Sistema 2 es el modo deliberativo y costoso (modelos de razonamiento extendido como o1/o3 o Claude con extended thinking).

## Reasoning tokens (tokens de razonamiento)
**Fuentes:** M1_T4, M1_T12
Tokens internos generados por modelos de razonamiento extendido como espacio de trabajo deliberativo antes de la respuesta visible. Se facturan como output, consumen contexto y permiten explorar y verificar hipótesis.

## Thinking budget
**Fuentes:** M1_T4, M1_T12
Parámetro configurable que establece cuántos tokens de razonamiento interno puede usar el modelo antes de responder. Más presupuesto mejora la calidad en tareas complejas a cambio de mayor latencia y coste.

## IA neuro-simbólica
**Fuentes:** M1_T5, M0_T2
**S:** 232
Arquitectura híbrida que integra componentes neuronales (percepción y patrones en datos no estructurados) con componentes simbólicos (razonamiento lógico auditable). Patrón común: integración secuencial neural→simbólico.

## Lógica difusa (fuzzy logic)
**Fuentes:** M1_T6
Sistema de razonamiento con incertidumbre (Lotfi Zadeh, 1965) que asigna grados de pertenencia continuos [0,1] a conjuntos vagos en lugar de valores booleanos. Usado en controladores industriales e IoT.

## Defuzzificación
**Fuentes:** M1_T6
Última etapa de un controlador difuso: convierte la conclusión difusa en un valor concreto de actuación. Métodos habituales: centroide (media ponderada del área) y máximo.

## Red Bayesiana
**Fuentes:** M1_T6
Grafo dirigido acíclico donde los nodos son variables aleatorias y los arcos representan dependencias condicionales cuantificadas con tablas de probabilidad. Usado para diagnóstico de fallos y evaluación de riesgo.

## Teorema de Bayes
**Fuentes:** M1_T6, M2_T3, M2_RESUMEN
**S:** 75
Regla fundamental del razonamiento probabilístico: P(H|E) = P(E|H)·P(H)/P(E). Actualiza la creencia en una hipótesis dada la evidencia observada. Base de filtros de spam, detección de fraude y clasificadores de riesgo.

## Calibración probabilística
**Fuentes:** M1_T6, M1_RESUMEN, M2_T3, M2_T8
**S:** 44
Propiedad de un modelo cuyas probabilidades predichas reflejan las frecuencias reales de los eventos. Los LLMs actuales están mal calibrados: afirman lo incorrecto con el mismo tono confiado que lo correcto. Se corrige con calibración isotónica o de Platt.

## Representación del conocimiento
**Fuentes:** M1_T7
Disciplina que estudia cómo codificar el conocimiento de un dominio de forma que un sistema de IA pueda razonar sobre él: reglas, ontologías, grafos de conocimiento y embeddings.

## Arquitectura Transformer
**Fuentes:** M0_T2, M0_RESUMEN, M1_T8, M5_T2, M5_T3, M5_RESUMEN
**S:** 16
Arquitectura de red neuronal (2017) basada en self-attention que procesa secuencias completas en paralelo. Base técnica de BERT, GPT y todos los LLMs modernos.

## Positional encoding
**Fuentes:** M1_T8
Señal añadida a los embeddings de tokens para indicar su posición en la secuencia. Sin él, la atención es invariante al orden y el modelo no podría distinguir el sujeto del objeto de una frase.

## Conexión residual (skip connection)
**Fuentes:** M1_T8, M4_T1, M4_T2, M4_RESUMEN
**S:** 45
Suma directa de la entrada de un bloque a su salida. Permite que el gradiente fluya sin degradarse desde capas profundas a superficiales, haciendo entrenables redes de cientos de capas. Introducidas en ResNet (2016).

## Encoder / Decoder (variantes Transformer)
**Fuentes:** M1_T8
El encoder procesa la secuencia bidireccionalmente (BERT, útil para embeddings y clasificación); el decoder aplica atención causal para generación autoregresiva (GPT, Llama); encoder-decoder (T5, BART) combina ambos.

## Mecanismo de atención Query-Key-Value (QKV)
**Fuentes:** M1_T9, M2_T1, M2_RESUMEN
**S:** 68
Operación central del Transformer: proyecta cada token en tres vectores (Q, K, V), calcula scores de relevancia como QKᵀ/√d_k, los normaliza con softmax y pondera los Values. Permite a cada token absorber información contextualizada del resto.

## Multi-head attention
**Fuentes:** M1_T8, M1_T9
Variante de la atención QKV que ejecuta varias instancias en paralelo con proyecciones independientes y concatena sus salidas. Captura simultáneamente relaciones sintácticas, semánticas y de correferencia.

## KV Cache (Key-Value cache)
**Fuentes:** M1_T9, M9_T2, M9_T6
**S:** 223
Almacenamiento de los vectores K y V ya calculados para los tokens previos durante la generación autoregresiva, evitando recalcularlos. Crece linealmente con el contexto y es el principal cuello de botella de memoria en inferencia.

## Flash Attention
**Fuentes:** M1_T9, M4_T4
**S:** 231
Reimplementación del mecanismo de atención que opera en SRAM (memoria rápida de GPU) en bloques, logrando aceleraciones de 2–8× y reduciendo el uso de memoria de O(n²) a O(n) sin cambiar el resultado matemático.

## Byte-Pair Encoding (BPE)
**Fuentes:** M1_T10, M5_T5, M5_RESUMEN
**S:** 60
Algoritmo de tokenización dominante que construye el vocabulario fusionando iterativamente los pares de tokens adyacentes más frecuentes del corpus. Garantiza cobertura total sin tokens desconocidos; estándar en GPT.

## Sesgo de idioma en tokenización
**Fuentes:** M1_T10
Fenómeno por el que tokenizadores entrenados sobre texto en inglés requieren 1,5×–3× más tokens para el mismo contenido en español, árabe o chino, incrementando el coste de API y reduciendo la ventana de contexto efectiva.

## Inconsistencia estocástica
**Fuentes:** M1_T11
Variabilidad en las respuestas de un LLM ante el mismo input, consecuencia del muestreo aleatorio con temperatura > 0. Problemática para auditoría o compliance; se mitiga fijando temperatura a 0.

## Conocimiento paramétrico vs conocimiento en contexto
**Fuentes:** M1_RESUMEN
**S:** 226
El conocimiento paramétrico está codificado en los pesos del modelo (estático, potencialmente desactualizado); el conocimiento en contexto está en el prompt actual (dinámico y verificable). El patrón RAG explota esta distinción.

## Tree of Thoughts (ToT)
**Fuentes:** M1_RESUMEN, M6_T3, M6_RESUMEN
**S:** 77
Técnica de razonamiento (Yao et al., 2023) que extiende Chain-of-Thought generando múltiples cadenas en paralelo, evaluando su promesa y convergiendo en la solución más robusta. Efectivo en planificación y problemas con backtracking.

## ReAct (Reasoning + Acting)
**Fuentes:** M1_RESUMEN, M6_T6, M6_RESUMEN, M10_T1, M10_T2, M10_RESUMEN
**S:** 18
Patrón que entrelaza pasos de razonamiento (Thought), invocación de herramientas externas (Action) y procesamiento de resultados (Observation). Base de la mayoría de sistemas agénticos en producción.

## Self-consistency
**Fuentes:** M1_RESUMEN, M5_T8, M6_T4, M6_RESUMEN
**S:** 25
Técnica que genera N cadenas de razonamiento independientes con temperatura > 0 y selecciona por votación mayoritaria. Mejora la precisión en razonamiento 10–20 puntos sobre CoT estándar sin fine-tuning.

## LLM-as-judge
**Fuentes:** M1_T11, M1_RESUMEN, M2_RESUMEN, M5_T7, M6_T8, M6_RESUMEN, M8_T1, M8_T7, M8_T9, M8_RESUMEN, M10_T9
**S:** 7
Patrón de evaluación automática en el que un LLM (a menudo más capaz o más económico) evalúa la calidad de las respuestas de otro sistema. Requiere calibración contra evaluación humana (correlación objetivo > 0.8).

---

## Módulo 2 — Matemáticas y Fundamentos

## Similitud coseno
**Fuentes:** M2_T1, M2_T7, M2_RESUMEN, M7_T2, M7_T4, M7_RESUMEN
**S:** 32
Métrica que mide el ángulo entre dos vectores mediante cos(θ) = (a·b)/(‖a‖·‖b‖), entre -1 y 1. Operación estándar de búsqueda semántica: ignora la magnitud y captura solo la orientación relativa.

## SVD (Descomposición en Valores Singulares)
**Fuentes:** M2_T1, M2_RESUMEN
**S:** 209
Factorización de cualquier matriz M como U·Σ·Vᵀ. Truncar a los k valores singulares mayores produce la mejor aproximación de rango k; base matemática de LoRA y de la reducción de dimensionalidad.

## PCA (Análisis de Componentes Principales)
**Fuentes:** M2_T1, M2_T6, M2_T7
Caso especial de SVD aplicado a la matriz de covarianza; proyecta los datos sobre las direcciones de máxima varianza para reducir dimensionalidad preservando la mayor parte de la información.

## LoRA (Low-Rank Adaptation)
**Fuentes:** M2_T1, M2_RESUMEN, M4_T6, M4_RESUMEN, M5_T3, M8_T2, M8_T3, M8_RESUMEN
**S:** 10
Técnica de fine-tuning eficiente (Hu et al., 2021) que congela los pesos del modelo y aproxima la actualización como producto de dos matrices de bajo rango (ΔW ≈ A·B). Reduce los parámetros entrenables hasta 128× sin añadir latencia en inferencia.

## QLoRA (Quantized LoRA)
**Fuentes:** M4_T6, M4_RESUMEN, M8_T3, M8_RESUMEN
**S:** 53
Combina LoRA con cuantización del modelo base a NF4 (4-bit), permitiendo fine-tuning de modelos de 70B parámetros en una sola GPU A100 de 80 GB.

## FAISS (Facebook AI Similarity Search)
**Fuentes:** M2_T1, M2_T6, M7_T1, M7_T2
**S:** 130
Librería open source de búsqueda de vecinos aproximados (índices IVF y PQ) que reduce la complejidad de búsqueda con pérdida de recall controlada. Base de ChromaDB y otras herramientas de prototipado.

## HNSW (Hierarchical Navigable Small World Graphs)
**Fuentes:** M2_T1, M2_T7
Algoritmo de búsqueda aproximada de vecinos más cercanos basado en grafos jerárquicos; logra latencias de 1–5 ms con recall del 95–99% en corpus de millones de documentos.

## Adam / AdamW (Adaptive Moment Estimation)
**Fuentes:** M2_T2, M2_T5, M2_RESUMEN, M4_RESUMEN
**S:** 42
Optimizador que mantiene estimaciones del primer y segundo momento de los gradientes para adaptar la tasa de aprendizaje por parámetro. AdamW añade weight decay desacoplado y es el estándar en fine-tuning de LLMs.

## Vanishing gradient (gradiente desvaneciente)
**Fuentes:** M2_T2, M2_RESUMEN, M4_T1, M4_T3, M4_RESUMEN
**S:** 41
Fenómeno en redes profundas donde los gradientes se vuelven exponencialmente pequeños al propagarse hacia atrás a través de activaciones saturadas, impidiendo el aprendizaje en capas iniciales. Se mitiga con residual connections y ReLU/GELU.

## Gradient clipping
**Fuentes:** M2_T2, M2_RESUMEN
**S:** 168
Técnica que limita la norma del vector de gradiente a un valor máximo antes de la actualización de pesos, evitando que spikes ocasionales desestabilicen el entrenamiento.

## Learning rate scheduler (warmup + cosine decay)
**Fuentes:** M2_T2, M2_RESUMEN
**S:** 180
Estrategia que combina un warmup lineal inicial con un decaimiento coseno posterior de la tasa de aprendizaje. Esquema estándar en el entrenamiento y fine-tuning de LLMs.

## ROC-AUC / PR-AUC
**Fuentes:** M2_T3, M2_RESUMEN, M3_T2, M3_T4, M3_RESUMEN
**S:** 38
Métricas que agregan el rendimiento de un clasificador a través de todos los umbrales. ROC-AUC mide la capacidad discriminativa general; PR-AUC (área bajo precision-recall) es preferida en problemas desbalanceados.

## A/B testing (Champion/Challenger)
**Fuentes:** M2_T3, M6_T8, M6_RESUMEN
**S:** 59
Método experimental que divide el tráfico aleatoriamente entre el sistema actual (A) y el nuevo (B) para comparar métricas con significancia estadística. Estándar para demostrar mejora en producción.

## Distributional shift
**Fuentes:** M2_T3
Fenómeno en el que la distribución de los datos en producción difiere de la del entrenamiento, causando degradación silenciosa del rendimiento. Requiere monitorización continua.

## MSE / MAE (Mean Squared Error / Mean Absolute Error)
**Fuentes:** M2_T4, M2_RESUMEN, M3_T4
**S:** 70
Funciones de coste para regresión: MSE penaliza errores grandes cuadráticamente (sensible a outliers, produce la media condicional); MAE trata todos los errores proporcionalmente (más robusto, produce la mediana condicional).

## Cross-Entropy Loss
**Fuentes:** M2_T4, M2_T8, M2_RESUMEN
**S:** 103
Función de coste estándar para clasificación y preentrenamiento de LLMs. Penaliza fuertemente las predicciones confiadas incorrectas; minimizarla sobre el siguiente token es el objetivo del preentrenamiento.

## Focal Loss
**Fuentes:** M2_T4, M2_RESUMEN
**S:** 165
Modificación de la cross-entropy (Lin et al., 2017) que reduce el peso de los ejemplos fáciles mediante un factor (1−p)^γ, enfocando el aprendizaje en los casos difíciles. Útil con desbalance extremo de clases.

## KL Divergence (Divergencia de Kullback-Leibler)
**Fuentes:** M2_T4, M2_T8, M2_RESUMEN
**S:** 112
Medida asimétrica de la diferencia entre dos distribuciones: D_KL(P‖Q) = Σ p_i·log(p_i/q_i) ≥ 0. Aparece en el entrenamiento de VAEs y en RLHF como regularización para que el modelo alineado no se desvíe del base.

## Dilema bias-varianza
**Fuentes:** M2_T5, M2_RESUMEN, M3_T5, M3_RESUMEN
**S:** 46
Descomposición del error de generalización: Error = Bias² + Varianza + Ruido irreducible. El bias alto produce underfitting; la varianza alta, overfitting. Reducir uno tiende a aumentar el otro.

## Dropout
**Fuentes:** M2_T5, M2_RESUMEN, M4_T1, M4_RESUMEN
**S:** 47
Técnica de regularización (Srivastava et al., 2014) que desactiva aleatoriamente una fracción p de neuronas en cada forward pass durante el entrenamiento, forzando representaciones redundantes y robustas.

## Early stopping
**Fuentes:** M2_T5, M2_RESUMEN
**S:** 155
Técnica de regularización que detiene el entrenamiento cuando la pérdida de validación deja de mejorar durante un número predefinido de épocas (paciencia). Primera salvaguarda recomendada contra el overfitting.

## Regularización L1 / L2 (Lasso / Ridge / Weight Decay)
**Fuentes:** M2_T5, M2_RESUMEN, M3_T5, M3_RESUMEN
**S:** 55
Técnicas que añaden un término de penalización sobre el tamaño de los pesos. L1 (Lasso) produce soluciones sparse con selección automática de features; L2 (Ridge) distribuye la penalización; L2 se denomina weight decay en LLMs.

## TF-IDF (Term Frequency-Inverse Document Frequency)
**Fuentes:** M2_T6, M5_T1, M5_RESUMEN
**S:** 76
Representación clásica sparse de texto que pondera cada término por su frecuencia en el documento dividida por su frecuencia en el corpus. Estándar pre-Transformer para clasificación y recuperación; no capta sinónimos.

## Word2Vec / GloVe
**Fuentes:** M2_T6, M2_T7
Modelos que aprenden embeddings densos estáticos a partir de co-ocurrencia distribucional de palabras. Permiten aritmética semántica (rey − hombre + mujer ≈ reina) pero no capturan polisemia.

## Embeddings contextuales
**Fuentes:** M2_T6, M2_RESUMEN
**S:** 157
Representaciones en las que el vector de cada token depende de todo el contexto de la frase (vía atención), superando la limitación de los embeddings estáticos de Word2Vec. Base de los Sentence Transformers.

## MTEB (Massive Text Embedding Benchmark)
**Fuentes:** M2_T6, M7_T2
**S:** 233
Benchmark estándar que evalúa modelos de embedding en tareas de recuperación, clasificación y similitud semántica en múltiples idiomas y dominios. Referencia para elegir el modelo de embedding adecuado.

## CLIP (Contrastive Language-Image Pre-Training)
**Fuentes:** M2_T7
Modelo de OpenAI (2021) que entrena conjuntamente un encoder de texto y uno de imagen mediante aprendizaje contrastivo en un espacio semántico compartido. Permite búsqueda de imágenes por texto y clasificación zero-shot.

## UMAP / t-SNE
**Fuentes:** M2_T6, M2_T7
Algoritmos de reducción de dimensionalidad no lineal que proyectan embeddings a 2D para visualización. Deben usarse para exploración cualitativa, no para conclusiones cuantitativas sobre distancias.

## Entropía de Shannon
**Fuentes:** M2_T8, M2_RESUMEN
**S:** 158
Medida de incertidumbre de una distribución de probabilidad: H(P) = −Σ p_i·log₂(p_i) en bits. En LLMs mide cuántas opciones plausibles tiene el modelo en cada paso; la temperatura modifica directamente esta entropía.

## Perplejidad (Perplexity)
**Fuentes:** M2_T8, M2_RESUMEN
**S:** 200
Métrica para evaluar modelos de lenguaje, la exponencial de la cross-entropy: PPL = e^H. Mide el número efectivo de opciones equivalentes en cada paso; los LLMs modernos en inglés alcanzan valores de 3–7.

## Información mutua
**Fuentes:** M2_T8
Medida de la dependencia entre dos variables aleatorias: I(X;Y) = H(X) + H(Y) − H(X,Y). Más potente que la correlación lineal para relaciones no lineales; se usa para selección de características.

## Scaling Laws (leyes de escalado)
**Fuentes:** M2_RESUMEN
**S:** 229
Relaciones empíricas de ley de potencia (Kaplan et al., 2020) que describen cómo mejora el rendimiento de los LLMs al aumentar tamaño del modelo, datos y cómputo. Justificación teórica para invertir en modelos más grandes.

---

## Módulo 3 — Machine Learning Clásico

## Aprendizaje supervisado
**Fuentes:** M3_T1, M3_RESUMEN
**S:** 139
Paradigma de ML en el que el modelo aprende de pares (input, etiqueta correcta) para predecir clasificaciones o valores de regresión. Cubre el 80% de los casos de uso empresarial: churn, fraude, scoring, forecasting.

## Aprendizaje no supervisado
**Fuentes:** M3_T1, M3_RESUMEN
**S:** 137
Paradigma en el que el modelo recibe inputs sin etiquetas y descubre estructura intrínseca: clustering, reducción de dimensionalidad, detección de anomalías. La validez de los resultados requiere juicio de dominio.

## Aprendizaje por refuerzo (RL)
**Fuentes:** M3_T1, M3_RESUMEN
**S:** 138
Paradigma en el que un agente aprende una política de decisión maximizando la recompensa acumulada tras interactuar con un entorno. Se formaliza como MDP; base técnica del RLHF.

## Aprendizaje semi-supervisado
**Fuentes:** M3_T1
Técnica que combina un pequeño conjunto de datos etiquetados con un gran conjunto no etiquetado, produciendo mejores resultados que el supervisado puro cuando las etiquetas escasean.

## Self-supervised learning (aprendizaje auto-supervisado)
**Fuentes:** M3_T1
Variante en la que el modelo genera sus propias señales de supervisión a partir de los datos (por ejemplo, predecir el siguiente token). Es el paradigma del preentrenamiento de LLMs.

## Proceso de Decisión de Markov (MDP)
**Fuentes:** M3_T1
Formalización matemática del aprendizaje por refuerzo: espacio de estados, espacio de acciones, función de transición y función de recompensa. El agente aprende la política que maximiza la recompensa acumulada.

## Reward hacking
**Fuentes:** M3_T1
Fenómeno en RL en el que el agente maximiza técnicamente la función de recompensa mediante comportamientos no previstos que no cumplen el objetivo real. Consecuencia de una función de recompensa mal especificada.

## Regresión logística
**Fuentes:** M3_T2, M3_RESUMEN
**S:** 204
Modelo de clasificación binaria que aplica la función sigmoide sobre una combinación lineal de las variables de entrada. Sus coeficientes son auditables: estándar para sectores regulados bajo GDPR y AI Act.

## Random Forest
**Fuentes:** M3_T2, M3_T5, M3_RESUMEN
**S:** 119
Método ensemble que entrena muchos árboles de decisión independientes sobre muestras aleatorias y combina sus predicciones por votación o promedio. Reduce la varianza sin aumentar el bias; robusto con pocos ajustes.

## Gradient Boosting / XGBoost / LightGBM
**Fuentes:** M3_T2, M3_T5, M3_RESUMEN
**S:** 108
Familia de métodos ensemble que construye árboles secuencialmente, cada uno ajustado a los residuos del ensemble anterior. Estado del arte en ML tabular.

## SVM — Support Vector Machine
**Fuentes:** M3_T2, M3_RESUMEN
**S:** 210
Algoritmo de clasificación que encuentra el hiperplano de máximo margen entre clases. Útil con datos de alta dimensionalidad y conjuntos de entrenamiento pequeños.

## Kernel trick
**Fuentes:** M3_T2, M3_RESUMEN
**S:** 178
Técnica matemática que permite a las SVM separar clases no linealmente separables proyectándolas implícitamente a espacios de alta dimensión mediante funciones kernel (RBF, polinomial), sin calcular las coordenadas.

## SHAP (SHapley Additive exPlanations)
**Fuentes:** M3_T2, M3_T3, M3_T7, M3_RESUMEN, M13_T8, M13_RESUMEN
**S:** 31
Método de interpretabilidad post-hoc basado en los Shapley values de la teoría de juegos. Calcula la contribución de cada variable a la predicción de forma matemáticamente consistente. Estándar de facto en producción.

## LIME (Local Interpretable Model-agnostic Explanations)
**Fuentes:** M3_T7, M13_T8, M13_RESUMEN
**S:** 66
Método de interpretabilidad post-hoc que genera una explicación local perturbando el input y ajustando un modelo lineal simple sobre las predicciones. Más inestable que SHAP; aplicable a cualquier modelo de caja negra.

## Feature engineering
**Fuentes:** M3_T3, M3_RESUMEN
**S:** 163
Proceso de transformar datos brutos en representaciones que los modelos aprenden mejor: normalización, encoding de categóricas, features temporales, ratios de dominio. Frecuentemente determina más el rendimiento que el algoritmo.

## Feature leakage (fuga de datos)
**Fuentes:** M3_T3, M3_T6
Error crítico que ocurre cuando el modelo usa durante el entrenamiento información que no estaría disponible en el momento real de la predicción. Produce métricas artificialmente buenas que no se replican en producción.

## One-hot encoding
**Fuentes:** M3_T3
Codificación de variables categóricas que convierte una variable con N categorías en N variables binarias. Simple y sin ambigüedad de orden, pero genera matrices dispersas con vocabularios grandes.

## Target encoding
**Fuentes:** M3_T3
Encoding que reemplaza cada categoría por la media del target en esa categoría. Muy informativo pero propenso a leakage si se calcula sobre todo el dataset; CatBoost implementa una versión robusta con permutación ordenada.

## Maldición de la dimensionalidad
**Fuentes:** M3_T3
Fenómeno por el que añadir muchas variables de baja información degrada el rendimiento al dispersar los datos en un espacio de alta dimensión donde las distancias pierden significado.

## Matriz de confusión
**Fuentes:** M3_T4
Tabla que organiza las predicciones de un clasificador binario en verdaderos/falsos positivos y negativos (TP, FP, TN, FN). Toda métrica de clasificación se deriva de estas cuatro cantidades.

## Underfitting
**Fuentes:** M3_T5, M3_RESUMEN
**S:** 217
Situación de alto bias en la que el modelo es demasiado simple: métricas malas en entrenamiento y validación, con diferencia pequeña entre ambas. Solución: aumentar complejidad o reducir la regularización.

## Overfitting (sobreajuste)
**Fuentes:** M3_T5, M3_RESUMEN
**S:** 196
Situación de alta varianza en la que el modelo memoriza el ruido del entrenamiento: métricas excelentes en entrenamiento y peores en validación. Solución: regularización, más datos, menos complejidad o ensembles.

## Curvas de aprendizaje
**Fuentes:** M3_T5
Representación gráfica del error de entrenamiento y validación en función del tamaño de los datos o de la complejidad del modelo. Herramienta de diagnóstico para distinguir bias alto de varianza alta.

## Validación cruzada k-fold
**Fuentes:** M3_T6, M3_RESUMEN
**S:** 218
Técnica que divide los datos en K partes y entrena K modelos, usando cada fold como validación una vez. Produce estimaciones del rendimiento más robustas que un único split, con media y desviación explícitas.

## Time Series Cross-Validation (walk-forward)
**Fuentes:** M3_T6
Variante de validación cruzada para series temporales que respeta el orden cronológico: siempre entrena sobre el pasado y evalúa sobre el futuro inmediato, evitando el leakage temporal.

## GAM (Generalized Additive Models)
**Fuentes:** M3_T7
Modelos intrínsecamente interpretables que modelan el efecto de cada variable con una función no lineal independiente y visualizable. Mayor capacidad expresiva que la regresión lineal manteniendo la trazabilidad.

## EDA (Exploratory Data Analysis)
**Fuentes:** M3_T3, M3_RESUMEN
**S:** 156
Etapa inicial de un proyecto de ML: visualizar distribuciones, identificar nulos y outliers, calcular correlaciones con el target y analizar relaciones bivariadas. Guía el diseño de features y la detección de problemas.

---

## Módulo 4 — Deep Learning

## Capa densa (fully connected)
**Fuentes:** M4_T1, M4_RESUMEN
**S:** 145
Unidad básica de una red neuronal profunda que conecta cada neurona de entrada con cada neurona de salida mediante pesos aprendibles: salida = activación(W·entrada + b).

## GELU / SiLU
**Fuentes:** M4_T1
Funciones de activación suaves (diferenciables en todo punto) usadas en arquitecturas modernas: GELU en GPT-2, SiLU en Llama. Mejoran la estabilidad del entrenamiento respecto a ReLU.

## Batch Normalization
**Fuentes:** M4_T1, M4_T2, M4_RESUMEN
**S:** 96
Técnica de normalización que fuerza las activaciones de cada capa a media 0 y varianza 1 sobre el batch actual; permite tasas de aprendizaje más altas y actúa como regularizador implícito.

## Layer Normalization
**Fuentes:** M4_T1, M4_RESUMEN
**S:** 179
Variante de la normalización que opera sobre las características de cada ejemplo individual en lugar del batch. Estándar en Transformers por su mejor comportamiento con secuencias de longitud variable.

## RMSNorm
**Fuentes:** M4_T1
Variante eficiente de LayerNorm usada en Llama que normaliza solo por la raíz de la media de los cuadrados sin centrar la media, reduciendo el coste computacional.

## CNN (Convolutional Neural Network)
**Fuentes:** M1_T3, M4_T2, M4_RESUMEN
**S:** 61
Red neuronal especializada en datos con estructura espacial que aplica filtros convolucionales aprendidos detectando características jerárquicamente (bordes → formas → objetos), con compartición de pesos e invarianza a la traslación.

## Feature map
**Fuentes:** M4_T2
Salida de aplicar un filtro convolucional sobre una imagen; indica la presencia e intensidad del patrón detectado por ese filtro en cada posición espacial.

## Pooling (Max pooling / Global Average Pooling)
**Fuentes:** M4_T2
Operación que reduce la dimensión espacial de los feature maps; max pooling toma el valor máximo de cada región y GAP colapsa toda la dimensión espacial a un valor por canal.

## ResNet
**Fuentes:** M4_T1, M4_T2, M4_T5
Arquitectura CNN de 2016 con conexiones residuales que permite entrenar redes de 50–152+ capas. Base de innumerables sistemas de visión en producción.

## EfficientNet
**Fuentes:** M4_T1, M4_T2
Familia de CNNs (2019) que escala de forma óptima y simultánea profundidad, anchura y resolución de la red. Mejor equilibrio rendimiento/eficiencia en clasificación de imágenes.

## YOLO (You Only Look Once)
**Fuentes:** M4_T2
Arquitectura CNN de detección de objetos en tiempo real que detecta y clasifica múltiples objetos en una sola pasada. Usada en seguridad perimetral, conteo de personas y análisis de tráfico.

## Data augmentation
**Fuentes:** M4_T2, M4_RESUMEN
**S:** 150
Técnica para reducir el sobreajuste en visión que genera variaciones aleatorias de las imágenes de entrenamiento (rotaciones, recortes, cambios de color), multiplicando el tamaño efectivo del dataset.

## RNN (Recurrent Neural Network)
**Fuentes:** M1_T3, M4_T3, M4_RESUMEN
**S:** 73
Red neuronal que procesa secuencias un elemento a la vez manteniendo un estado oculto que actúa como memoria acumulada de los pasos anteriores.

## LSTM (Long Short-Term Memory)
**Fuentes:** M1_T3, M4_T3, M4_RESUMEN
**S:** 67
Variante de RNN (Hochreiter y Schmidhuber, 1997) con tres compuertas y un estado de celda, que resuelve el gradiente desvaneciente y captura dependencias de cientos de pasos.

## GRU (Gated Recurrent Unit)
**Fuentes:** M4_T3, M4_RESUMEN
**S:** 169
Versión simplificada de LSTM con dos compuertas y sin estado de celda separado; rendimiento similar con menor coste computacional.

## State Space Models / Mamba (SSM)
**Fuentes:** M4_T3, M4_T4
Familia de arquitecturas (Gu y Dao, 2024) que generaliza las RNNs con un selective state space; procesa secuencias en tiempo lineal O(n) frente al O(n²) de los Transformers, igualando su calidad en secuencias largas.

## Vision Transformer (ViT)
**Fuentes:** M4_T4
Arquitectura que divide la imagen en patches de 16×16 píxeles, trata cada patch como un token y aplica self-attention global. Supera a las CNNs con suficiente preentrenamiento, pero con datos limitados las CNNs mantienen ventaja.

## MoE (Mixture of Experts)
**Fuentes:** M4_T4
Arquitectura donde la capa feed-forward de cada bloque Transformer se reemplaza por múltiples sub-redes especializadas y una gating network activa dinámicamente 2–4 por token, aumentando la capacidad sin escalar el coste de inferencia.

## Cuantización de modelos
**Fuentes:** M4_T4, M4_T8, M9_T7, M9_T8, M9_RESUMEN
**S:** 33
Técnica que representa los pesos del modelo con menor precisión numérica (FP32→FP16→INT8→INT4/NF4), reduciendo la VRAM necesaria 2–8× con pérdida de calidad inferior al 5%. Formatos: GGUF, GPTQ. Base del Edge AI.

## Feature extraction (Transfer Learning)
**Fuentes:** M4_T5
Estrategia de transfer learning en la que los pesos del modelo preentrenado se congelan por completo y solo se entrena la nueva cabeza. Adecuada con menos de 1.000 ejemplos por clase.

## Differential learning rate
**Fuentes:** M4_T5
Técnica de fine-tuning que asigna tasas de aprendizaje distintas por grupos de capas: muy pequeña para el backbone preentrenado y mayor para la nueva cabeza, evitando destruir representaciones preaprendidas.

## Catastrophic forgetting
**Fuentes:** M4_T5, M4_T6, M5_T3, M8_T2, M8_T3
**S:** 58
Fenómeno por el que el fine-tuning degrada capacidades del modelo en dominios no representados en los datos de adaptación. Se mitiga con tasas de aprendizaje bajas, LoRA, data mixing y pocas épocas.

## PEFT (Parameter-Efficient Fine-Tuning)
**Fuentes:** M4_T6, M4_RESUMEN, M8_T3
**S:** 72
Familia de técnicas que adaptan un modelo preentrenado entrenando solo una pequeña fracción de sus parámetros (~0,1–1%), manteniendo los pesos originales congelados para reducir memoria, coste y riesgo de sobreajuste.

## Instruction tuning (SFT)
**Fuentes:** M4_T6, M4_RESUMEN, M5_T3
**S:** 65
Fine-tuning supervisado sobre pares (instrucción, respuesta ideal) que convierte un modelo base en un asistente que sigue instrucciones. Suelen bastar 500–2.000 pares de alta calidad del dominio.

## DPO (Direct Preference Optimization)
**Fuentes:** M4_RESUMEN, M5_T3
**S:** 79
Alternativa más simple al RLHF que logra alineamiento con preferencias humanas sin un modelo de recompensa separado ni el algoritmo PPO. Adoptada por modelos como Claude y Llama 3.

## Data parallelism / Model parallelism
**Fuentes:** M4_T7
Estrategias de entrenamiento distribuido: data parallelism replica el modelo en cada GPU y divide el batch; model parallelism divide el modelo entre GPUs cuando no cabe en una sola.

## ZeRO (Zero Redundancy Optimizer)
**Fuentes:** M4_T7
Optimización de Microsoft DeepSpeed que elimina la redundancia en el almacenamiento distribuido de parámetros, gradientes y estados del optimizador, haciendo factible entrenar modelos de cientos de miles de millones de parámetros.

## Mixed precision training (BF16/FP16)
**Fuentes:** M4_T7
Entrenamiento que usa BF16 o FP16 en los forward/backward passes para reducir memoria y acelerar los Tensor Cores, manteniendo los pesos maestros en FP32. BF16 es preferido en A100/H100.

## Gradient checkpointing
**Fuentes:** M4_T7
Técnica que guarda solo algunas activaciones intermedias durante el forward pass y recalcula el resto en el backward, reduciendo la VRAM 4–8× a cambio de ~33% más de tiempo de entrenamiento.

## Gradient accumulation
**Fuentes:** M4_T7
Técnica que acumula gradientes de N pasos antes de actualizar los pesos, simulando un batch size N veces mayor sin coste adicional de cómputo. Permite batch sizes grandes con VRAM limitada.

## Tensor Cores
**Fuentes:** M4_T8
Unidades de procesamiento de NVIDIA especializadas en operaciones Matrix Multiply-Accumulate, introducidas en Volta (V100, 2017). La H100 las lleva a su 4ª generación con soporte FP8/BF16/TF32.

## CUDA
**Fuentes:** M4_T8
Entorno de programación paralela de NVIDIA que permite a PyTorch, TensorFlow y JAX ejecutarse en GPUs. Su ecosistema maduro (cuBLAS, cuDNN, NCCL, TensorRT) es la ventaja competitiva estructural de NVIDIA.

## VRAM
**Fuentes:** M4_T4, M4_T7, M4_T8
Memoria de vídeo de la GPU, recurso limitante en deep learning. Un modelo de N parámetros en FP16 necesita 2·N bytes; para entrenamiento se multiplica por 3–4 para incluir gradientes y estados del optimizador.

---

## Módulo 5 — NLP y LLMs

## NER (Named Entity Recognition)
**Fuentes:** M5_T1, M5_T2, M5_RESUMEN
**S:** 116
Tarea de extracción de información que identifica y clasifica entidades en texto (personas, organizaciones, fechas, importes). Base de los sistemas de procesamiento automático de contratos, facturas y expedientes.

## BERT (Bidirectional Encoder Representations from Transformers)
**Fuentes:** M1_T8, M2_T6, M2_RESUMEN, M5_T1, M5_T2, M5_T3, M5_RESUMEN
**S:** 13
Modelo Transformer encoder bidireccional (Google, 2018) preentrenado con Masked Language Modeling. Cada token atiende a todos los demás; estándar para clasificación, NER y embeddings de alta calidad.

## GPT (Generative Pre-trained Transformer)
**Fuentes:** M5_T2, M5_T3, M5_T4, M5_RESUMEN
**S:** 84
Modelo Transformer decoder autoregresivo (OpenAI, 2018) preentrenado con language modeling causal: predice el siguiente token dado el contexto anterior. Arquitectura dominante en generación de texto y razonamiento.

## MLM (Masked Language Modeling)
**Fuentes:** M5_T2, M5_T3
Objetivo de preentrenamiento de BERT: el 15% de los tokens se enmascaran aleatoriamente y el modelo debe predecirlos usando el contexto bidireccional completo.

## In-Context Learning (ICL)
**Fuentes:** M5_T4, M5_RESUMEN
**S:** 174
Capacidad emergente de los LLMs para adaptarse a nuevas tareas a partir de ejemplos incluidos en el prompt, sin actualizar los parámetros. La calidad y diversidad de los ejemplos importa más que la cantidad.

## Zero-shot prompting
**Fuentes:** M5_T4, M5_RESUMEN
**S:** 221
Modalidad de ICL en la que el modelo recibe solo la descripción de la tarea sin ejemplos. Funciona bien para conocimiento general; puede fallar en tareas de dominio específico o formatos inusuales.

## Few-shot prompting
**Fuentes:** M5_T4, M5_RESUMEN, M6_T1, M6_RESUMEN
**S:** 48
Modalidad de ICL en la que se incluyen 3–10 pares (input, output correcto) antes del caso a resolver. Especialmente efectivo cuando el formato de output es inusual o las categorías son ambiguas.

## Varianza de orden (order sensitivity en ICL)
**Fuentes:** M5_T4
Efecto por el que el orden de los ejemplos few-shot en el prompt afecta al rendimiento, especialmente en modelos pequeños. Se recomienda evaluar con múltiples órdenes y reportar media y desviación.

## WordPiece
**Fuentes:** M5_T5
Variante de tokenización usada en BERT que elige las fusiones maximizando la probabilidad del corpus bajo un modelo de unigramas. Marca las subcontinuaciones con el prefijo "##".

## SentencePiece
**Fuentes:** M5_T5
Framework de tokenización (Google) que opera directamente sobre la secuencia de caracteres Unicode sin pre-tokenización por espacios. Adecuado para idiomas sin separación explícita de palabras; usado en Llama 2.

## Tokens especiales (special tokens / chat template)
**Fuentes:** M5_T5
Tokens de formato que estructuran la entrada de los modelos instruct (`<|system|>`, `[INST]`, `<|im_start|>`). Usar el template incorrecto al cambiar de modelo produce degradaciones silenciosas de rendimiento.

## Greedy decoding
**Fuentes:** M5_T6
Mecanismo de decodificación que selecciona en cada paso el token de mayor probabilidad. Completamente determinista, equivale a temperatura 0; ideal para extracción de datos estructurados o código.

## Top-p sampling (nucleus sampling)
**Fuentes:** M5_T6
Estrategia de muestreo que considera solo el conjunto mínimo de tokens cuya probabilidad acumulada supera un umbral p (típicamente 0.9). Se combina con temperatura para controlar la creatividad sin permitir tokens muy improbables.

## Structured outputs / Constrained decoding
**Fuentes:** M5_T6
Modalidad de generación en la que la decodificación se restringe para garantizar un output JSON válido conforme a un schema. Obligatorio en pipelines de producción donde el output se parsea programáticamente.

## Beam search
**Fuentes:** M5_T6
Algoritmo de decodificación que mantiene los k caminos más prometedores en cada paso y devuelve el de mayor probabilidad conjunta. Más costoso que greedy o sampling; usado históricamente en traducción y resumen.

## MMLU (Massive Multitask Language Understanding)
**Fuentes:** M5_T7, M5_RESUMEN
**S:** 190
Benchmark de conocimiento académico con 14.042 preguntas de múltiple opción en 57 materias. Estándar de referencia hasta saturarse en 2024, lo que motivó benchmarks más difíciles como MMLU-Pro y GPQA.

## BLEU / ROUGE
**Fuentes:** M5_T7
Métricas automáticas de evaluación de texto generado basadas en solapamiento de n-gramas: BLEU mide precisión y ROUGE mide recall. No capturan equivalencia semántica ni corrección factual.

## BERTScore
**Fuentes:** M5_T7
Métrica que calcula la similitud coseno entre los embeddings de BERT del texto generado y la referencia, capturando similitud semántica. Mayor correlación con el juicio humano que BLEU/ROUGE, pero no evalúa corrección factual.

## Sycophancy (sobreconformidad)
**Fuentes:** M5_T8
Tendencia de los LLMs a generar respuestas que se alinean con las expectativas implícitas del usuario, incluso cuando son incorrectas. Causa estructural de alucinaciones, originada en el proceso de RLHF.

## Faithfulness (fidelidad al contexto)
**Fuentes:** M5_T8, M7_T7, M7_RESUMEN
**S:** 64
Métrica que evalúa qué fracción de las afirmaciones del output de un sistema RAG están respaldadas por los documentos recuperados. Métrica de alucinación específica para RAG, implementada en frameworks como RAGAS.

## Modelos multilingües (mBERT, XLM-R)
**Fuentes:** M5_T1, M5_T5
Modelos preentrenados sobre corpus en múltiples idiomas simultáneamente, que producen representaciones transferibles entre lenguas. Alternativa a modelos monolingües especializados como BETO (español).

---

## Módulo 6 — Ingeniería de Prompts

## System Prompt
**Fuentes:** M6_T1, M6_RESUMEN
**S:** 212
Instrucción que se proporciona al modelo antes de cualquier interacción del usuario y que define rol, contexto, restricciones y formato de respuesta. Actúa como el "ADN" del sistema y produce comportamientos consistentes.

## Zero-shot CoT
**Fuentes:** M6_T2, M6_RESUMEN
**S:** 220
Variante de Chain-of-Thought que induce el razonamiento paso a paso añadiendo solo una instrucción como "Vamos a razonar paso a paso", sin ejemplos. Primer paso recomendado antes de técnicas más complejas.

## Few-shot CoT
**Fuentes:** M6_T2, M6_RESUMEN
**S:** 164
Variante de Chain-of-Thought en la que se proporcionan 3–8 ejemplos que incluyen la cadena de razonamiento intermedio completa. Mejor que zero-shot CoT en tareas con estructura de razonamiento muy específica.

## Beam Search (en ToT)
**Fuentes:** M6_T3
Estrategia de búsqueda aplicada al Tree of Thoughts que mantiene solo los B mejores pensamientos en cada nivel del árbol para controlar el coste computacional.

## BFS / DFS (Breadth-First / Depth-First Search)
**Fuentes:** M6_T3
Algoritmos de búsqueda usados en Tree of Thoughts para decidir el orden de expansión de los nodos del árbol de razonamiento. BFS prioriza cobertura completa; DFS profundiza con posibilidad de backtracking.

## Universal Self-Consistency
**Fuentes:** M6_T4
Extensión de self-consistency para tareas de generación libre sin conteo de mayoría simple: se generan N respuestas y un LLM evaluador selecciona o sintetiza la más representativa del consenso.

## Least-to-Most Prompting
**Fuentes:** M6_T5, M6_RESUMEN
**S:** 181
Técnica (Zhou et al., 2022) que descompone un problema complejo en subproblemas ordenados de menor a mayor dificultad, resolviendo cada uno con los resultados anteriores como contexto acumulado.

## Prompt Chaining
**Fuentes:** M6_T5, M6_RESUMEN
**S:** 203
Cadena de prompts especializados donde el output de cada uno es el input del siguiente, permitiendo auditar cada etapa, reintentar solo la fallida y usar modelos distintos en cada paso.

## MapReduce (patrón para LLMs)
**Fuentes:** M6_T5
Patrón de descomposición para procesar volúmenes que exceden la ventana de contexto: la fase Map aplica el mismo prompt en paralelo a cada elemento; la fase Reduce sintetiza los resultados parciales.

## Auto-refinamiento
**Fuentes:** M6_T2, M6_T6, M6_RESUMEN
**S:** 94
Técnica (Madaan et al., 2023) en la que el modelo critica y mejora su propio output en un ciclo: generar borrador → generar retroalimentación estructurada → refinar. Se repite 1–3 veces.

## Reflexion
**Fuentes:** M6_T6, M10_T2, M10_T3, M10_RESUMEN
**S:** 54
Extensión de ReAct (Shinn et al., 2023) que añade memoria episódica: el agente genera reflexiones verbales sobre lo aprendido en cada intento y las incluye en el contexto de los siguientes para evitar repetir errores.

## Function Calling / Tool calling
**Fuentes:** M6_T6, M9_T3, M10_T1, M10_T5, M10_RESUMEN
**S:** 22
Mecanismo de las APIs de LLM por el que el modelo genera un bloque JSON estructurado con el nombre de una función externa y sus argumentos; el cliente la ejecuta y devuelve el resultado al modelo. Base de los sistemas agénticos.

## Prompt Injection
**Fuentes:** M6_T7, M6_RESUMEN, M9_T4, M12_T1, M12_T2, M12_T4, M12_RESUMEN
**S:** 15
Ataque en el que texto malicioso en el input del usuario o en datos externos intenta hacer que el LLM ignore las instrucciones del system prompt y ejecute acciones no autorizadas. Vulnerabilidad #1 del OWASP LLM Top 10 (LLM01:2025).

## Inyección Indirecta
**Fuentes:** M6_T7, M6_RESUMEN, M12_T2, M12_T5, M12_RESUMEN
**S:** 34
Variante de prompt injection en la que las instrucciones maliciosas provienen de datos externos procesados por el agente (documentos, páginas web, emails, resultados RAG). Especialmente peligrosa en sistemas agénticos.

## Prompt Leaking / System Prompt Leakage
**Fuentes:** M6_T7, M6_RESUMEN, M12_T1, M12_T2
**S:** 52
Ataque que intenta hacer que el modelo revele el contenido confidencial del system prompt, directa o indirectamente. Vulnerabilidad LLM07; la defensa es no almacenar información sensible en el prompt.

## OWASP Top 10 para LLMs (2025)
**Fuentes:** M6_T7, M6_RESUMEN, M12_T1, M12_RESUMEN
**S:** 51
Lista estándar de las diez vulnerabilidades críticas de aplicaciones LLM, publicada por OWASP en 2023 y revisada en 2025. Establece la defensa en capas como enfoque correcto.

## Defensa en capas (LLM)
**Fuentes:** M6_T7, M6_RESUMEN
**S:** 151
Estrategia de seguridad que combina múltiples controles independientes: separación de roles API, etiquetado XML del contenido externo, filtrado de input, mínimo privilegio para herramientas y logging de acciones.

## DSPy
**Fuentes:** M6_T8, M6_RESUMEN
**S:** 154
Framework de Stanford que automatiza la optimización de prompts: el desarrollador especifica el programa de prompts y DSPy optimiza iterativamente cada componente para maximizar una métrica de evaluación.

## TextGrad
**Fuentes:** M6_T8
Herramienta de optimización de prompts que usa retroalimentación textual del LLM como señal de gradiente para actualizar el prompt, por analogía con backpropagation.

## RAGAS
**Fuentes:** M6_T9, M7_T1, M7_T6, M7_T7, M7_RESUMEN
**S:** 36
Framework estándar de evaluación automática de sistemas RAG (EACL 2024) que calcula con un LLM cuatro métricas — Faithfulness, Answer Relevancy, Context Recall y Context Precision — sin anotaciones humanas extensas.

## Grounding explícito
**Fuentes:** M6_T9
Técnica de prompting anti-alucinación que instruye al modelo a basar su respuesta exclusivamente en los documentos de contexto, declarando explícitamente cuando la información no se encuentra en ellos.

## Separación hechos/inferencias/opiniones
**Fuentes:** M6_T9
Técnica de prompting que instruye al modelo a etiquetar cada afirmación con su nivel de certeza — [HECHO], [INFERENCIA] u [OPINIÓN] — haciendo transparente el grado de verificabilidad de la respuesta.

## XML tags en prompts
**Fuentes:** M6_T1, M6_T2, M6_T7
Uso de etiquetas XML como delimitadores estructurales dentro del prompt para separar instrucciones, contexto, datos del usuario y razonamiento. Recomendado por Anthropic y mecanismo de defensa ante prompt injection.

## Red Team Dataset
**Fuentes:** M6_T7, M8_T9, M12_T8, M12_T9
**S:** 78
Conjunto de 20–50 prompts de inyección representativos, incluyendo variantes conocidas de ataques, usado para evaluar la robustez de un sistema LLM. Se ejecuta en CI/CD y se amplía conforme se descubren nuevos ataques.

---

## Módulo 7 — Sistemas RAG

## Chunking (fixed-size)
**Fuentes:** M7_T1, M7_T3, M7_RESUMEN
**S:** 99
División de documentos en fragmentos de N tokens con un solapamiento de M tokens entre chunks consecutivos. La estrategia más simple, aunque los cortes arbitrarios pueden romper el significado.

## Semantic chunking
**Fuentes:** M7_T2, M7_T3, M7_T4, M7_RESUMEN
**S:** 90
Estrategia de chunking que identifica fronteras naturales del texto (párrafos, headings, cambios de tema por similitud de embeddings) para dividir el documento en fragmentos semánticamente coherentes.

## Parent-child chunking
**Fuentes:** M7_T3, M7_RESUMEN
**S:** 197
Estrategia que mantiene dos niveles de chunks: hijos pequeños (200–500 tokens) para búsqueda precisa y padres mayores (500–2000 tokens) que se insertan en el prompt como contexto completo cuando se recupera un hijo.

## Long RAG
**Fuentes:** M7_T3
Variante de RAG que procesa chunks grandes (secciones o documentos enteros) aprovechando ventanas de contexto de 128K+ tokens; recupera 2–5 secciones grandes en lugar de muchos chunks pequeños.

## Pipeline de ingesta
**Fuentes:** M7_T1, M7_T5, M7_RESUMEN
**S:** 117
Proceso offline que toma documentos fuente y los prepara para indexación: extracción de texto, limpieza, chunking, enriquecimiento de metadatos, generación de embeddings e inserción en la base vectorial. Debe ser idempotente.

## Pipeline de consulta
**Fuentes:** M7_T5
Proceso online en tiempo real que cubre, por cada consulta: autenticación, query transformation opcional, embedding, recuperación híbrida, reranking, construcción del prompt, llamada al LLM y post-procesamiento con citas.

## BM25 (Best Match 25)
**Fuentes:** M7_T2, M7_T4, M7_RESUMEN
**S:** 97
Algoritmo clásico de recuperación de información que puntúa documentos por frecuencia de los términos de la consulta normalizada por longitud e inversa de frecuencia en el corpus. Búsqueda dispersa de referencia.

## Búsqueda híbrida
**Fuentes:** M7_T2, M7_T4, M7_T5, M7_RESUMEN
**S:** 83
Combinación de búsqueda densa (vectorial) y dispersa (BM25) ejecutadas en paralelo y cuyos resultados se fusionan. Demostrada superior a cualquier método individual (estudio BlendedRAG de IBM, 2024).

## RRF (Reciprocal Rank Fusion)
**Fuentes:** M7_T2, M7_T4
Algoritmo de fusión de rankings para búsqueda híbrida que asigna puntuaciones según la posición relativa de cada resultado en cada lista. Robusto sin calibrar pesos; el método más usado en producción.

## Reranking / Cross-encoder
**Fuentes:** M7_T4, M7_T5, M7_T8, M7_RESUMEN
**S:** 88
Técnica que aplica un modelo cross-encoder (evalúa el par consulta+documento conjuntamente) sobre los top-K candidatos del retrieval inicial para reordenarlos. Añade 10–30% de precisión con 50–100 ms de latencia.

## HyDE (Hypothetical Document Embeddings)
**Fuentes:** M7_T4, M7_RESUMEN
**S:** 172
Técnica de query transformation que genera un documento hipotético que respondería la consulta y usa su embedding para buscar. Mitiga el desajuste semántico entre la consulta corta del usuario y los fragmentos.

## Query transformation
**Fuentes:** M7_T4, M7_T5
Familia de transformaciones aplicadas a la consulta antes del retrieval: query expansion, query rewriting, HyDE y multi-query. Mejora la recuperación en consultas ambiguas o mal formuladas.

## Answer Relevancy
**Fuentes:** M7_T7, M7_RESUMEN
**S:** 135
Métrica RAGAS que mide si la respuesta generada responde efectivamente la pregunta del usuario, calculada por similitud coseno entre la pregunta original y las que el LLM inferiría a partir de la respuesta.

## Context Recall
**Fuentes:** M7_T4, M7_T7, M7_RESUMEN
**S:** 102
Métrica RAGAS que mide qué fracción de la respuesta de referencia puede atribuirse al contexto recuperado. Un score bajo indica que el retrieval no recupera toda la información necesaria.

## Context Precision
**Fuentes:** M7_T4, M7_T7, M7_RESUMEN
**S:** 101
Métrica RAGAS que mide qué fracción de los documentos recuperados son realmente relevantes para la pregunta. Un score bajo indica que el retriever introduce ruido en el contexto.

## Adaptive RAG
**Fuentes:** M7_T5, M7_RESUMEN
**S:** 132
Patrón (Jeong et al., 2024) que clasifica cada consulta por complejidad y decide la estrategia de recuperación óptima: sin recuperación, recuperación simple o recuperación multi-hop.

## CRAG (Corrective RAG)
**Fuentes:** M7_T5
Arquitectura RAG (Chen et al., 2024) que añade un evaluador de relevancia que clasifica los documentos recuperados en Correct, Incorrect o Ambiguous, y activa una búsqueda adicional cuando son insuficientes.

## Agentic RAG
**Fuentes:** M7_T5, M7_T8
Patrón que trata la recuperación como una acción de agente: el sistema realiza múltiples recuperaciones secuenciales (multi-hop), usando la información de cada una para formular la consulta siguiente.

## Local search / Global search (GraphRAG)
**Fuentes:** M7_T8
Dos modos de consulta en GraphRAG: local search navega entidades cercanas para respuestas precisas; global search recorre las comunidades temáticas del grafo para preguntas de panorama general.

## Algoritmo Leiden
**Fuentes:** M7_T8
Algoritmo de detección de comunidades en grafos usado por GraphRAG para agrupar entidades relacionadas en comunidades temáticas, sobre las que se generan descripciones resumen para la global search.

## RAPTOR
**Fuentes:** M7_T8
Técnica (Sarthi et al., 2024) que construye un árbol de resúmenes jerárquicos del corpus agrupando chunks similares y generando resúmenes recursivos; recupera tanto detalles específicos como síntesis de alto nivel.

## Multimodal RAG
**Fuentes:** M7_T8
Extensión del pipeline RAG que incluye el procesamiento de imágenes, gráficos y tablas además del texto; las imágenes se describen con modelos de visión-lenguaje y las tablas se convierten a markdown/JSON.

## Sistema de citas y trazabilidad
**Fuentes:** M7_T1, M7_T5, M7_T6
Componente obligatorio en RAG de producción que asocia cada afirmación de la respuesta con su documento fuente, sección y fragmento exacto. Permite verificar la corrección y facilita auditorías.

## Gap prototipo-producción (RAG)
**Fuentes:** M7_T1, M7_T5
Diferencia entre un RAG que funciona en un notebook y uno listo para producción. En producción se requiere gestión del corpus, pipelines separados de ingesta y consulta, multi-tenancy, control de acceso y evaluación continua.

---

## Módulo 8 — Ingeniería y LLMOps

## LLMOps (Large Language Model Operations)
**Fuentes:** M8_T1, M8_RESUMEN
**S:** 183
Conjunto de prácticas, herramientas y procesos que hacen que los sistemas LLM funcionen de forma fiable, escalable y mejorable en producción. Especialización de MLOps adaptada a los modelos de lenguaje.

## SLO (Service Level Objective)
**Fuentes:** M8_T1, M8_T7
Compromisos de calidad del sistema que definen qué es un servicio aceptable; para un LLM típico: latencia P99 < 3s, disponibilidad > 99.5%, tasa de errores < 0.1% y faithfulness > 0.85.

## Canary deployment
**Fuentes:** M8_T1, M8_T9, M8_RESUMEN
**S:** 98
Estrategia de despliegue gradual en la que el nuevo sistema recibe inicialmente un 5–10% del tráfico real mientras se monitoriza su calidad frente al sistema actual, antes de escalar al 100%.

## Shadow mode
**Fuentes:** M8_T1, M8_T9, M11_T5
**S:** 224
Modo de despliegue en el que el nuevo sistema procesa las mismas consultas que producción pero sin devolver respuestas al usuario, permitiendo medir calidad sin riesgo para el usuario final.

## Tracing distribuido
**Fuentes:** M8_T1, M8_T7, M8_RESUMEN
**S:** 127
Técnica de observabilidad que captura cada paso del pipeline LLM (retrieval, prompt, llamada, post-procesamiento) como un "span" con tiempos y contenidos, permitiendo reproducir y diagnosticar cualquier interacción.

## Drift detection
**Fuentes:** M8_T1, M8_T7
Monitorización de si la distribución de los inputs del sistema cambia respecto al baseline, usando técnicas como embedding drift, topic drift y performance drift para detectar degradaciones antes de que se quejen los usuarios.

## SFTTrainer (Supervised Fine-Tuning Trainer)
**Fuentes:** M8_T3
Componente de la librería TRL de Hugging Face que gestiona el entrenamiento supervisado de LLMs con datasets de instrucciones, formateando los ejemplos y gestionando el ciclo de entrenamiento con QLoRA.

## Test-Time Compute (TTC) / Inference-time scaling
**Fuentes:** M8_T4, M8_RESUMEN
**S:** 214
Paradigma que invierte más cómputo en el tiempo de inferencia (en lugar de en el entrenamiento) para mejorar la calidad en tareas difíciles. Implementado nativamente en modelos como o1/o3 y Claude con extended thinking.

## Extended thinking
**Fuentes:** M8_T4, M8_RESUMEN
**S:** 162
Capacidad de modelos de razonamiento para generar un proceso de pensamiento interno extenso antes de la respuesta final, explorando múltiples caminos y autocorrigiéndose. Controlado mediante un presupuesto de tokens de razonamiento.

## Best-of-N (BoN) sampling
**Fuentes:** M8_T4
Técnica de test-time compute que genera N respuestas independientes en paralelo y selecciona la mejor según un verifier. Puede alcanzar el rendimiento de modelos más grandes a menor coste.

## Process Reward Model (PRM)
**Fuentes:** M8_T4
Modelo entrenado para evaluar la calidad del razonamiento en cada paso intermedio de una cadena (no solo al final), usado en técnicas de búsqueda en árbol para guiar la exploración de cadenas de razonamiento.

## Routing dinámico
**Fuentes:** M8_T4, M8_T5, M8_RESUMEN, M9_T7
**S:** 56
Estrategia que clasifica automáticamente cada consulta según su dificultad y la envía al modelo más económico capaz de resolverla correctamente. Puede reducir el coste total un 40–60% manteniendo la calidad.

## Prefix caching
**Fuentes:** M8_T5, M8_T6, M8_RESUMEN, M9_T6, M9_T7, M9_RESUMEN
**S:** 30
Mecanismo por el que el inicio del prompt (system prompt) se cachea entre consultas, reduciendo su coste al 50% o más y el TTFT un 50–90%. Ahorra el 30–40% del coste de tokens de entrada en sistemas con system prompts largos.

## Streaming / TTFT (Time To First Token)
**Fuentes:** M8_T5, M9_T6, M9_RESUMEN
**S:** 74
TTFT mide el tiempo desde que el usuario envía la consulta hasta el primer token de la respuesta; indicador más crítico para la experiencia conversacional (objetivo P99 < 2s). El streaming devuelve tokens a medida que se generan.

## vLLM
**Fuentes:** M8_T6, M8_RESUMEN, M9_T1, M9_T2, M9_T5, M9_T6, M9_T7, M9_T9, M9_RESUMEN
**S:** 20
Framework de inferencia LLM (UC Berkeley) que implementa PagedAttention y continuous batching, logrando hasta 24× mayor throughput que TGI bajo alta concurrencia. Estándar de facto en 2025, compatible con la API de OpenAI.

## PagedAttention
**Fuentes:** M8_T6, M9_T6, M9_RESUMEN
**S:** 71
Implementación del mecanismo de atención de vLLM que gestiona el KV cache como memoria virtual paginada en lugar de un buffer contiguo, eliminando la fragmentación y permitiendo empaquetar más secuencias concurrentes.

## Continuous batching
**Fuentes:** M8_T6, M9_T5, M9_RESUMEN
**S:** 62
Técnica que incorpora nuevas solicitudes al batch en curso tan pronto como hay capacidad, en lugar de esperar a que todas las secuencias terminen. Mantiene la GPU ocupada y mejora el throughput 2–5×.

## TGI (Text Generation Inference)
**Fuentes:** M8_T6, M8_RESUMEN
**S:** 215
Framework de inferencia LLM de Hugging Face enfocado en producción empresarial, con telemetría OpenTelemetry y métricas Prometheus integradas, prefix caching optimizado para contextos muy largos y mayor estabilidad en concurrencia media.

## Speculative decoding
**Fuentes:** M8_T6, M9_T6
**S:** 234
Técnica de aceleración que usa un modelo draft pequeño para generar un borrador de K tokens que el modelo principal verifica en paralelo. Puede reducir la latencia 2–3× en modelos grandes con bajo batch size.

## ADR (Architecture Decision Record)
**Fuentes:** M8_T2
Documento que registra una decisión de diseño con el problema que resuelve, las opciones evaluadas, los datos de evaluación de cada una (métricas, coste, latencia) y la decisión tomada con sus criterios.

## MLflow Model Registry
**Fuentes:** M8_T8, M8_RESUMEN
**S:** 189
Componente de MLflow que almacena modelos entrenados y versiones de adaptadores LoRA con sus metadatos, y gestiona el ciclo de vida del modelo (staging, producción, archivado), integrándose con pipelines CI/CD.

## DVC (Data Version Control)
**Fuentes:** M8_RESUMEN, M12_T3, M12_T8
**S:** 63
Estándar de versionado de datasets y modelos que hace commit de referencias a archivos grandes en Git mientras los almacena en S3/GCS. Permite detectar cuándo se introdujeron datos maliciosos en un pipeline de fine-tuning.

## Reproducibilidad hermética
**Fuentes:** M8_T8
Requisito de que todos los componentes de un experimento LLM estén fijados a versiones exactas: modelo, prompt (hash de commit), golden dataset, seed de muestreo y versiones de librerías. Sin esto, dos ejecuciones pueden diferir.

## Feature flags
**Fuentes:** M8_T9
Mecanismo que permite activar o desactivar funcionalidades (versión del modelo, del prompt, RAG habilitado) sin desplegar nuevo código, implementando canary deployments a nivel lógico y revirtiendo cambios en segundos.

## Red Teaming de IA
**Fuentes:** M8_T9, M8_RESUMEN, M12_T8, M12_T9, M12_RESUMEN
**S:** 37
Práctica de simular ataques adversariales sobre un sistema de IA para identificar vulnerabilidades antes de que atacantes reales las exploten. En IA cubre jailbreaks, prompt injection, data poisoning y sesgos.

---

## Módulo 9 — Infraestructura y Despliegue

## TCO (Total Cost of Ownership)
**Fuentes:** M9_T1, M9_T7, M9_RESUMEN, M14_T3
**S:** 57
Métrica que cuantifica el coste real de poseer y operar un sistema de IA a lo largo de su ciclo de vida: hardware, personal, electricidad, cooling, licencias de API, mantenimiento y actualizaciones.

## CAPEX / OPEX
**Fuentes:** M9_T1, M9_T7
CAPEX es la inversión inicial en hardware propio (un servidor 8× H100 cuesta 250.000–400.000 USD); OPEX son los costes operativos recurrentes (electricidad, cooling, personal), 20–35% del CAPEX anual en on-premise.

## Estrategia híbrida (cloud + on-premise)
**Fuentes:** M9_T1, M9_RESUMEN
**S:** 160
Modelo adoptado por el 68% de las empresas con IA en producción que combina carga base en infraestructura propia (workloads predecibles) con burst en cloud para picos de demanda y experimentación.

## Break-even cloud vs on-premise
**Fuentes:** M9_T1, M9_T7
Punto en que el TCO de on-premise iguala al del cloud; se alcanza con utilización sostenida > 70–80% y horizonte de amortización de 3+ años, considerando todos los costes ocultos.

## Prefill / Decode
**Fuentes:** M9_T6, M9_RESUMEN
**S:** 202
Dos fases de la inferencia LLM: prefill procesa el prompt completo generando el KV cache (compute-bound); decode genera tokens uno a uno leyendo el KV cache (memory-bandwidth-bound).

## Semantic Caching
**Fuentes:** M9_T5, M9_T7
Técnica que almacena respuestas a consultas previas y las reutiliza cuando llega una consulta semánticamente similar (detectada por similitud coseno de embeddings), reduciendo las llamadas al modelo un 30–60%.

## KEDA (Kubernetes Event-Driven Autoscaler)
**Fuentes:** M9_T2, M9_T5, M9_RESUMEN
**S:** 111
Componente de Kubernetes que escala pods de inferencia LLM según métricas personalizadas (longitud de cola, throughput de tokens, utilización de GPU). Soporta scale-to-zero y scale-up hasta N réplicas.

## Warm Pool
**Fuentes:** M9_T2, M9_T5, M9_RESUMEN
**S:** 129
Conjunto de pods de inferencia pre-calentados (con el modelo ya cargado en VRAM) que se mantienen activos para eliminar los cold starts de 1–5 minutos. Garantiza disponibilidad inmediata ante picos de demanda.

## Arquitectura disaggregada (prefill-decode separation)
**Fuentes:** M9_T2
Patrón de despliegue que separa el procesamiento del prompt (prefill) y la generación de tokens (decode) en pods de GPU distintos y especializados; reduce la latencia por token un 40% respecto a una arquitectura monolítica.

## API Gateway
**Fuentes:** M9_T2, M9_T3, M9_T4, M9_RESUMEN
**S:** 81
Punto único de entrada al sistema LLM que centraliza autenticación, autorización, rate limiting, routing, logging y gestión de versiones. Herramientas: Kong, NGINX, AWS API Gateway.

## Estándar API OpenAI (chat completions)
**Fuentes:** M9_T3, M9_RESUMEN
**S:** 161
Formato de facto para APIs de LLM en 2025: endpoint `/v1/chat/completions` con array de mensajes por roles. Implementado por vLLM, TGI y Ollama, permite intercambiar el backend cambiando solo la base URL.

## MCP (Model Context Protocol)
**Fuentes:** M9_T3, M10_T5, M10_T7, M10_T8, M10_RESUMEN, M11_T2, M11_RESUMEN
**S:** 14
Protocolo estándar publicado por Anthropic en noviembre de 2024 para la comunicación entre agentes y herramientas/sistemas externos. Reduce el problema N×M de integraciones a N+M; adoptado por OpenAI, Google, Microsoft y AWS.

## Rate Limiting (RPM / TPM)
**Fuentes:** M9_T3, M9_T4, M9_RESUMEN
**S:** 120
Control que limita el número de peticiones por minuto (RPM) y tokens por minuto (TPM) por cliente. Protege el sistema de abuso; devuelve HTTP 429 con Retry-After cuando se exceden los límites.

## Guardrails
**Fuentes:** M9_T4, M9_RESUMEN
**S:** 170
Filtros de validación aplicados al input y al output para detectar prompt injection, contenido dañino, PII o respuestas fuera de formato. Herramientas: Guardrails AI, NeMo Guardrails, LlamaGuard.

## Enmascarado de PII
**Fuentes:** M9_T4
Técnica que detecta y sustituye datos de identificación personal con pseudónimos antes de enviarlos al LLM, y revierte la sustitución en la respuesta. Garantiza que el modelo nunca procesa datos personales reales.

## RBAC (Role-Based Access Control)
**Fuentes:** M9_T4
Modelo de autorización que asigna permisos según el rol del usuario o servicio. En sistemas LLM multi-tenant controla el acceso al modelo, a los documentos RAG y a las herramientas según el nivel del cliente.

## Audit Logging
**Fuentes:** M9_T4
Registro inmutable de todas las interacciones con el sistema LLM (timestamp, usuario, modelo, tokens, respuesta, resultado de guardrails). Requisito legal en sectores regulados con retención de 1–7 años.

## IaC — Infraestructura como Código
**Fuentes:** M9_T9
Práctica de aprovisionar y gestionar infraestructura cloud mediante código versionado en Git, garantizando reproducibilidad, trazabilidad y automatización. Herramientas: Terraform, Helm, Docker.

## Terraform
**Fuentes:** M9_T9
Herramienta de IaC de HashiCorp que define infraestructura cloud en HCL. Flujo: `terraform plan` → `terraform apply` → `terraform destroy`; estado almacenado en un backend remoto.

## GitOps / ArgoCD
**Fuentes:** M9_T9
Práctica que usa Git como fuente única de verdad del estado del sistema; ArgoCD sincroniza automáticamente el cluster Kubernetes con el repositorio, eliminando despliegues manuales y garantizando trazabilidad.

## Edge AI
**Fuentes:** M9_T8
Paradigma de despliegue que ejecuta modelos de IA directamente en el dispositivo del usuario o en servidores edge cercanos, sin depender de la nube. Indicado cuando la latencia, la privacidad o la conectividad lo exigen.

## llama.cpp
**Fuentes:** M9_T8
Framework de inferencia en C++ para LLMs en hardware de consumo y edge; soporta cuantización GGUF, ejecución en CPU pura y backends GPU. Análogo a vLLM pero orientado a dispositivos sin GPU de datacenter.

## ONNX Runtime
**Fuentes:** M9_T8
Runtime de inferencia de Microsoft que ejecuta modelos en formato ONNX en múltiples backends (CPU, GPU, NPU). Con cuantización INT8 produce modelos 4× más pequeños y 2–4× más rápidos en CPU.

---

## Módulo 10 — Sistemas de Agentes

## Ciclo perceive-reason-act
**Fuentes:** M10_T1, M10_RESUMEN
**S:** 146
Patrón fundamental de operación de un agente LLM: percibir el objetivo/estado del entorno, razonar sobre la acción adecuada, ejecutarla mediante una herramienta, observar el resultado y repetir hasta completar el objetivo.

## Plan-and-Execute
**Fuentes:** M10_T2, M10_T3, M10_RESUMEN
**S:** 118
Patrón arquitectónico en el que el agente genera primero un plan completo de pasos antes de ejecutar ninguno, delegando la ejecución a un executor. Mayor coherencia global y auditabilidad, menos adaptable que ReAct.

## Estado del agente
**Fuentes:** M10_T2, M10_T7
Estructura de datos (TypedDict en LangGraph) que representa todo lo que el agente conoce del progreso de la tarea y fluye entre los nodos del grafo: objetivo, historial de mensajes, acciones, observaciones y metadatos.

## Memoria de trabajo (Working memory)
**Fuentes:** M10_T1, M10_T4, M10_RESUMEN
**S:** 114
Tipo de memoria agéntica que corresponde a la ventana de contexto actual del LLM: objetivo, historial de la sesión activa y resultados de herramientas. La más rápida de acceder pero limitada en capacidad.

## Memoria episódica (Episodic memory)
**Fuentes:** M10_T1, M10_T4, M10_RESUMEN
**S:** 115
Tipo de memoria agéntica que almacena el historial de interacciones de sesiones pasadas en una base con búsqueda semántica. Permite recuperar episodios relevantes sin que el usuario repita el contexto.

## Memoria semántica (Semantic memory)
**Fuentes:** M10_T4, M10_RESUMEN
**S:** 187
Tipo de memoria agéntica que almacena conocimiento general del dominio: paramétrica (en los pesos vía fine-tuning) o no paramétrica (externa, recuperada con RAG). La no paramétrica es más fácil de actualizar y auditar.

## Memoria procedimental (Procedural memory)
**Fuentes:** M10_T4, M10_RESUMEN
**S:** 186
Tipo de memoria agéntica que almacena procedimientos, estrategias y heurísticas aprendidas de la experiencia. Se implementa como prompts de sistema, ejemplos few-shot derivados de éxitos pasados o herramientas especializadas.

## mem0
**Fuentes:** M10_T2, M10_T4
Framework open source para memoria persistente a largo plazo en agentes LLM; provee una API para añadir y recuperar memorias por búsqueda semántica con aislamiento por user_id.

## Zep
**Fuentes:** M10_T2, M10_T4
Sistema de gestión de memoria long-term para agentes y sistemas conversacionales; almacena el historial completo de interacciones de cada usuario y lo recupera antes de cada interacción para personalizar respuestas.

## Parallel tool calling
**Fuentes:** M10_T5
Capacidad de los modelos modernos de invocar múltiples herramientas simultáneamente en un solo turno cuando sus llamadas son independientes, reduciendo la latencia total del agente.

## Tool hallucination
**Fuentes:** M10_T5
Error agéntico en el que el modelo invoca una herramienta con argumentos incorrectos, llama a una inexistente o inventa resultados sin ejecutarla. Se mitiga con schemas JSON estrictos, validación y logging de auditoría.

## Sandbox de ejecución de código
**Fuentes:** M10_T5, M10_RESUMEN
**S:** 206
Entorno aislado que contiene la ejecución de código generado por el LLM para evitar acceso a archivos, red no autorizada o consumo excesivo de recursos. Opciones: contenedores Docker efímeros, microVMs, E2B, Modal.

## Subagent decomposition
**Fuentes:** M10_T3, M10_T6, M10_RESUMEN
**S:** 124
Técnica de planificación jerárquica en la que el agente orquestador descompone un objetivo complejo en subobjetivos independientes y los delega a sub-agentes especializados que trabajan en paralelo.

## Planificación adaptativa
**Fuentes:** M10_T3
Tipo de planificación agéntica que re-evalúa el plan completo después de cada paso y lo ajusta si los resultados son inesperados. Es lo que distingue a los agentes de los pipelines predefinidos.

## Consistency checking
**Fuentes:** M10_T3
Técnica de verificación periódica en la que el agente evalúa, tras cada acción, si el resultado lo acerca al objetivo y si el plan sigue siendo válido. Detecta deriva del objetivo y permite corrección de rumbo.

## Orquestador-Trabajador (patrón Supervisor)
**Fuentes:** M10_T6, M10_RESUMEN
**S:** 195
Patrón de orquestación multi-agente en el que un orquestador descompone el objetivo complejo en subtareas y las delega a agentes trabajadores especializados; luego integra los resultados. El patrón más común en producción.

## Handoffs
**Fuentes:** M10_T6, M10_RESUMEN
**S:** 171
Transferencias estructuradas de control de un agente a otro en sistemas multi-agente, incluyendo el estado relevante y el contexto del objetivo. Abstracción central del OpenAI Agents SDK.

## Cascade failure (fallo en cascada)
**Fuentes:** M10_T6
Patrón de fallo en pipelines multi-agente donde el error de un agente intermedio se propaga y corrompe los outputs de los posteriores. Se mitiga con verificación entre pasos, reintentos con backoff y fallback handlers.

## A2A (Agent-to-Agent)
**Fuentes:** M10_T7, M10_T8, M10_RESUMEN
**S:** 91
Protocolo publicado por Google en abril de 2025 que estandariza la comunicación entre agentes de diferentes frameworks. Complementa a MCP permitiendo que un agente LangGraph delegue subtareas a uno de CrewAI.

## MCP Gateway
**Fuentes:** M10_T8
Componente de infraestructura que centraliza autenticación, rate limiting, logging de auditoría y control de acceso para sistemas con múltiples servidores MCP en producción. Opciones: Bifrost, AWS API Management, Kong.

## LangGraph
**Fuentes:** M10_T2, M10_T6, M10_T7, M10_RESUMEN, M11_T3
**S:** 35
Framework de agentes (equipo de LangChain) que implementa workflows agénticos como grafos dirigidos con aristas condicionales, checkpointing de estado persistente nativo, soporte de HITL y gestión de múltiples hilos.

## CrewAI
**Fuentes:** M10_T7, M10_RESUMEN
**S:** 148
Framework de agentes que organiza los sistemas multi-agente mediante una metáfora de equipo (role, goal, backstory). El más fácil para prototipado rápido, con patrones de orquestación avanzada limitados.

## AutoGen (AG2)
**Fuentes:** M10_T6, M10_T7, M10_RESUMEN
**S:** 95
Framework de Microsoft que modela la colaboración multi-agente como conversaciones en un GroupChat donde un selector determina qué agente habla. Adecuado para debate y refinamiento iterativo de alta calidad.

## Google ADK (Agent Development Kit)
**Fuentes:** M10_T7
Framework de agentes de Google (abril 2025) que organiza los agentes en un árbol jerárquico con soporte nativo del protocolo A2A para interoperabilidad entre frameworks.

## GAIA (benchmark)
**Fuentes:** M10_T9, M10_RESUMEN
**S:** 167
Benchmark de referencia para evaluar agentes en tareas del mundo real que requieren razonamiento, uso de herramientas y múltiples pasos. 466 preguntas a tres niveles de dificultad.

## SWE-bench
**Fuentes:** M10_T9, M10_RESUMEN
**S:** 211
Benchmark de agentes de coding que mide la capacidad de resolver issues reales de repositorios Python en GitHub. Los mejores agentes resuelven el 38–50% de los issues en 2025.

## OSWorld (benchmark)
**Fuentes:** M10_T1, M10_T3, M10_T9
Benchmark de tareas en sistemas operativos reales donde los mejores modelos alcanzan ~42,9% de completación frente al 72,36% humano; la brecha se atribuye a limitaciones de planificación de los agentes actuales.

## Trajectories-based evaluation
**Fuentes:** M10_T9, M10_RESUMEN
**S:** 216
Método de evaluación de agentes que examina la secuencia completa de acciones (trayectoria) y no solo el output final: si cada acción fue apropiada, si las herramientas se usaron bien y si el agente recuperó de los errores.

## Regla 80/20 para agentes en producción
**Fuentes:** M10_T10
Principio operativo: el agente automatiza de forma autónoma el 80% de casos estándar mientras el 20% complejo o de alto impacto se escala al humano. Optimiza el ROI sin comprometer la seguridad en decisiones críticas.

## Mínimo privilegio en herramientas
**Fuentes:** M10_T1, M10_T5, M10_T8, M10_RESUMEN, M12_T1, M12_T5
**S:** 28
Principio de seguridad agéntica según el cual cada agente debe tener acceso exclusivamente a las herramientas y servidores MCP estrictamente necesarios para su función. Reduce el radio de impacto de fallos o ataques.

---

## Módulo 11 — Automatización

## Hiperautomatización
**Fuentes:** M11_T1, M11_T4, M11_RESUMEN
**S:** 109
Convergencia de RPA, IA, ML y process mining para automatizar flujos de trabajo completos de extremo a extremo, incluyendo pasos que antes requerían juicio humano. La IA gestiona comprensión y decisión; el RPA ejecuta.

## Automatización inteligente
**Fuentes:** M11_T1, M11_T4, M11_T6, M11_RESUMEN
**S:** 82
Paradigma que añade al RPA clásico tres capacidades: comprensión del lenguaje natural, toma de decisiones contextual ante ambigüedad y adaptación a nuevos patrones. Permite automatizar procesos variables y no estructurados.

## CoE de automatización (Center of Excellence)
**Fuentes:** M11_T1
Estructura organizativa que centraliza la gobernanza, metodología, selección de casos, estándares técnicos y gestión del cambio de las iniciativas de automatización. Habilitador organizativo del éxito a escala.

## Process mining
**Fuentes:** M11_T1, M11_T4
Técnica analítica que extrae conocimiento sobre procesos reales a partir de logs de sistemas, identificando cuellos de botella y oportunidades de automatización. Componente clave de la hiperautomatización.

## iPaaS (Integration Platform as a Service)
**Fuentes:** M11_T2, M11_RESUMEN
**S:** 177
Middleware cloud que conecta múltiples sistemas empresariales a través de una plataforma centralizada de integración; gestiona transformación de datos, logging, reintentos y resiliencia.

## Arquitectura event-driven
**Fuentes:** M11_T2
Patrón de integración que conecta sistemas de IA a eventos empresariales en tiempo real mediante message brokers (Kafka, RabbitMQ, AWS SNS/SQS), desacoplando productores de datos de consumidores.

## MCP server (Model Context Protocol server)
**Fuentes:** M11_T2, M11_RESUMEN
**S:** 185
Servidor que expone operaciones de un sistema empresarial (CRM, ERP, base de datos) como herramientas invocables por agentes de IA. Simplifica la integración reduciendo el tiempo de días a horas.

## OAuth 2.0 con mínimo privilegio
**Fuentes:** M11_T2
Protocolo de autorización para integraciones de IA con sistemas empresariales bajo el principio de mínimo privilegio: el agente recibe solo los scopes estrictamente necesarios, reduciendo la superficie de ataque.

## Circuit breaker
**Fuentes:** M11_T2
Patrón de resiliencia que detecta cuando una dependencia externa está caída y devuelve respuestas de fallback en lugar de esperar timeouts, evitando que el fallo de un sistema colapse a todos los agentes que dependen de él.

## Workflow inteligente
**Fuentes:** M11_T3, M11_RESUMEN
**S:** 219
Proceso de negocio que combina nodos de automatización determinista con nodos de IA (clasificación, extracción, generación) orquestados con lógica de bifurcación y puntos de supervisión humana.

## Patrón de clasificación y routing
**Fuentes:** M11_T3, M11_RESUMEN
**S:** 198
Diseño de workflow en el que un LLM clasifica el input entrante (emails, tickets, formularios) según tipo, urgencia y departamento, y lo enruta al sub-workflow especializado. El patrón más común para automatizar el triage.

## Patrón de extracción y enriquecimiento
**Fuentes:** M11_T3, M11_RESUMEN
**S:** 199
Diseño de workflow en el que un LLM extrae campos estructurados de inputs no estructurados (PDF, email, formulario) y los enriquece con sistemas externos antes de decidir. Núcleo de la automatización de documentos.

## Touchless processing rate
**Fuentes:** M11_T4, M11_T7, M11_RESUMEN
**S:** 126
Métrica principal de los sistemas IA+RPA: porcentaje de casos procesados de principio a fin sin intervención humana. El objetivo para procesos maduros es 80–90%.

## Taxonomía de excepciones
**Fuentes:** M11_T4
Clasificación estructurada de los casos que un bot RPA no puede procesar, organizada según quién puede resolverlos: el LLM autónomamente, el LLM con información adicional, o escalada obligatoria a humano.

## Orquestador de hiperautomatización
**Fuentes:** M11_T4
Plataforma (UiPath Orchestrator, Automation Anywhere Control Room, Blue Prism Hub) que coordina de forma unificada bots RPA y agentes de IA en workflows de proceso completo.

## Autonomía graduada
**Fuentes:** M11_T5, M11_RESUMEN
**S:** 141
Marco de cinco niveles (de asistencia a autonomía completa con gobernanza) que describe el espectro de control humano sobre un sistema de IA. La progresión entre niveles debe ser gradual y basada en evidencia de desempeño real.

## Umbral de confianza para escalada dinámica
**Fuentes:** M11_T5
Parámetro ajustable que determina a partir de qué nivel de confianza interna el sistema escala automáticamente un caso a revisión humana. Se estima con self-consistency, score de clasificador de incertidumbre o heurísticas.

## KYC/AML (Know Your Customer / Anti-Money Laundering)
**Fuentes:** M11_T6
Procesos regulatorios de verificación de identidad y prevención de blanqueo de capitales en el sector financiero. Caso de uso líder de automatización inteligente.

## COIN (Contract Intelligence) — JPMorgan
**Fuentes:** M11_T6, M11_RESUMEN
**S:** 147
Sistema de IA de JPMorgan Chase que analiza automáticamente acuerdos comerciales mediante NLP; procesa 12.000 contratos en segundos, sustituyendo 360.000 horas de trabajo de abogados al año.

## Baseline de medición
**Fuentes:** M11_T7, M11_RESUMEN
**S:** 143
Estado documentado del proceso antes de implementar la automatización: número de FTEs, tiempo de ciclo, tasa de error, volumen y coste. Requisito previo para calcular el impacto real de la automatización.

## ROI compuesto de automatización
**Fuentes:** M11_T1, M11_T4, M11_T7, M11_RESUMEN
**S:** 89
Fórmula ROI = (Beneficios Netos Anuales / Inversión Total) × 100 que integra el valor financiero directo, operativo y estratégico. El ROI típico es 150–250% en el primer año con payback de 6–18 meses.

## Exception rate
**Fuentes:** M11_T4, M11_T7
Porcentaje de casos de un proceso automatizado que no pueden procesarse automáticamente y requieren intervención humana. Métrica complementaria al touchless processing rate; su evolución determina la madurez del sistema.

---

## Módulo 12 — Seguridad IA

## ASR (Attack Success Rate)
**Fuentes:** M12_T1, M12_T2, M12_T4, M12_T9
**S:** 237
Métrica que expresa el porcentaje de ataques adversariales que logran eludir las defensas del sistema. Valores documentados: roleplay injection 89,6%, logic traps 81,4%, encoding tricks 76,2%.

## Jailbreak
**Fuentes:** M12_T1, M12_T4, M12_T9, M12_RESUMEN
**S:** 86
Subconjunto de prompt injection orientado a eludir los guardrails de seguridad y alineación del modelo para obtener outputs que está entrenado para rechazar (contenido dañino, información restringida).

## Roleplay Injection
**Fuentes:** M12_T2, M12_T4, M12_RESUMEN
**S:** 122
Técnica de jailbreak que instruye al modelo a actuar como un personaje ficticio sin restricciones, desplazando sus políticas de seguridad al contexto del personaje. La técnica con mayor ASR documentado (89,6%).

## Multi-turn Jailbreaking
**Fuentes:** M12_T4, M12_T7
Ataque de erosión gradual que construye el jailbreak a lo largo de múltiples turnos de conversación, escalando hacia contenido prohibido en pasos pequeños que individualmente parecen inocuos.

## Encoding Tricks
**Fuentes:** M12_T1, M12_T2, M12_T4
Técnica que usa transformaciones de texto (Base64, ROT13, homoglifos, caracteres zero-width Unicode) para eludir filtros basados en palabras clave. ASR documentado del 76,2%.

## Data Poisoning
**Fuentes:** M12_T1, M12_T3, M12_RESUMEN
**S:** 105
Ataque que introduce datos maliciosos en el conjunto de entrenamiento o fine-tuning para contaminar el modelo de forma permanente. El fine-tuning es especialmente vulnerable: el 1% de los datos puede bastar.

## Backdoor Attack (trigger oculto)
**Fuentes:** M12_T3, M12_RESUMEN
**S:** 142
Variante de data poisoning que introduce un patrón de activación específico en los pesos; el modelo se comporta con normalidad ante inputs estándar pero cambia su comportamiento al recibir el trigger.

## Supply Chain de modelos (LLM03)
**Fuentes:** M12_T1, M12_T3, M12_RESUMEN
**S:** 125
Vulnerabilidad derivada de depender de modelos base, datasets o librerías de terceros comprometidos. Repositorios públicos como Hugging Face son un vector de ataque (malware en formato pickle, typosquatting).

## Formato Safetensors
**Fuentes:** M12_T3, M12_RESUMEN
**S:** 166
Formato de serialización de modelos que no permite la ejecución de código arbitrario durante la carga, a diferencia del formato pickle. Mitigación recomendada frente al riesgo de supply chain.

## ModelScan (ProtectAI)
**Fuentes:** M12_T3, M12_T8
Herramienta open source que escanea archivos de modelos (pickle, H5, safetensors) para detectar código malicioso embebido y patrones de serialización usados como vectores de ataque.

## Excessive Agency (LLM06)
**Fuentes:** M12_T1, M12_T5, M12_RESUMEN
**S:** 106
Vulnerabilidad en la que un agente LLM dispone de más permisos o herramientas de los necesarios, de modo que una prompt injection exitosa puede desencadenar acciones irreversibles de alto impacto.

## Memory Poisoning
**Fuentes:** M12_T5, M12_RESUMEN
**S:** 188
Ataque específico de sistemas agénticos con memoria persistente que introduce información falsa en la memoria del agente (incluidas bases vectoriales) para influir en sus decisiones futuras o escalar privilegios.

## SSRF via agente (Server-Side Request Forgery)
**Fuentes:** M12_T5, M12_RESUMEN
**S:** 208
Ataque que explota la herramienta de fetch de URL de un agente, instruyéndola vía prompt injection para acceder a servicios internos protegidos usando el agente como proxy involuntario.

## Regla Meta / "Agents Rule of Two"
**Fuentes:** M12_T2, M12_T5, M12_RESUMEN
**S:** 121
Principio de Meta (octubre 2025): los controles de seguridad deben implementarse en la capa de ejecución fuera del LLM, ya que cualquier seguridad implementada solo en el prompt puede eludirse con prompt injection.

## LlamaGuard (Meta)
**Fuentes:** M12_T4, M12_T6, M12_RESUMEN
**S:** 113
Modelo de lenguaje fine-tuneado por Meta para clasificar si el input del usuario o el output del modelo viola políticas de uso seguro. Opera localmente y devuelve una clasificación con la categoría de violación.

## Arquitectura Sandwich de validación
**Fuentes:** M12_T6, M12_RESUMEN
**S:** 140
Patrón de despliegue que sitúa un clasificador de seguridad (típicamente LlamaGuard) tanto antes del LLM (filtrado de input) como después (filtrado de output), dando cobertura bidireccional.

## Guardrails AI
**Fuentes:** M12_T6
Framework que permite definir validaciones programáticas (content, structural, semantic) sobre los outputs del LLM. Cuando la validación falla puede reintentar la llamada o devolver un fallback predefinido.

## Unbounded Consumption / DoS por tokens (LLM10)
**Fuentes:** M12_T1, M12_T7
Vulnerabilidad en la que la ausencia de rate limiting por TPM permite ataques de denegación de servicio por agotamiento de recursos o cost amplification, generando costes desorbitados en pocas horas.

## Golden Dataset Adversarial
**Fuentes:** M12_T8, M12_T9
Conjunto de prompts adversariales que el sistema debe rechazar definitivamente, construido a partir del red teaming inicial y actualizado con nuevos ataques. Se ejecuta en CI/CD como test suite de seguridad mínima.

## Garak (NVIDIA)
**Fuentes:** M12_T1, M12_T4, M12_T8, M12_T9, M12_RESUMEN
**S:** 80
Escáner de vulnerabilidades LLM open source con plugins para docenas de categorías de ataques (jailbreaks, prompt injection, PII leakage) y cobertura del OWASP Top 10. Integrable en pipelines CI/CD.

## Secure AI DLC (Secure AI Development Lifecycle)
**Fuentes:** M12_T8, M12_RESUMEN
**S:** 207
Marco que integra la seguridad en cada fase del ciclo de desarrollo de sistemas de IA: diseño (threat modeling con STRIDE), desarrollo (prompts como código, DVC, ModelScan) y testing (SAST, red teaming, golden dataset en CI/CD).

## STRIDE aplicado a IA
**Fuentes:** M12_T8
Modelo de threat modeling (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) adaptado a sistemas de IA para mapear los vectores de ataque por componente.

## MITRE ATLAS
**Fuentes:** M12_T1
Marco de conocimiento sobre tácticas y técnicas de adversarios que atacan sistemas de machine learning, equivalente al MITRE ATT&CK pero específico para IA.

---

## Módulo 13 — Gobernanza y Ética

## EU AI Act (Reglamento de Inteligencia Artificial de la UE)
**Fuentes:** M0_T1, M0_RESUMEN, M13_T1, M13_T2, M13_T9, M13_RESUMEN
**S:** 27
Primera regulación integral de IA del mundo, en vigor desde agosto 2024. Adopta un enfoque basado en riesgo con cuatro categorías (inaceptable, alto, limitado, mínimo) y sanciones de hasta 35 M€ o el 7% de la facturación global.

## GPAI — General Purpose AI (IA de Propósito General)
**Fuentes:** M13_T1, M13_T9
Modelos de IA de propósito general (GPT-4o, Claude) con obligaciones específicas desde agosto 2025: documentación técnica, cumplimiento de copyright y transparencia. Los modelos con más de 10²⁵ FLOPS se consideran de riesgo sistémico.

## Conformity Assessment (Evaluación de Conformidad)
**Fuentes:** M13_T1, M13_T2, M13_RESUMEN
**S:** 100
Proceso que certifica que un sistema de alto riesgo cumple los requisitos del Capítulo III del AI Act. Puede ser auto-evaluada o realizada por un Notified Body, y culmina en el marcado CE.

## Notified Body (Organismo Notificado)
**Fuentes:** M13_T2
Organismo de evaluación de conformidad acreditado por los Estados Miembro de la UE, con autoridad para emitir certificados de conformidad bajo el AI Act para sistemas que son componentes de seguridad de productos regulados.

## Marcado CE
**Fuentes:** M13_T1, M13_T2
Marca que certifica que un sistema de IA de alto riesgo ha superado la conformity assessment y cumple los requisitos del AI Act. Requisito previo para comercializar el sistema en el mercado europeo.

## NIST AI RMF (AI Risk Management Framework)
**Fuentes:** M12_T7, M12_T8, M12_T9, M13_T3, M13_T9, M13_RESUMEN
**S:** 29
Framework voluntario del NIST (enero 2023) para gestionar riesgos de sistemas de IA a lo largo de su ciclo de vida, estructurado en cuatro funciones: Govern, Map, Measure y Manage. Estándar de facto más influyente a nivel mundial.

## NIST-AI-600-1 (Perfil GenAI del AI RMF)
**Fuentes:** M13_T3, M13_RESUMEN
**S:** 194
Perfil del AI RMF (julio 2024) específico para IA generativa; identifica 12 riesgos particulares de los LLMs, incluyendo alucinaciones, privacidad de datos, sesgo sistémico y derechos de autor.

## ISO/IEC 42001 — AIMS (Artificial Intelligence Management System)
**Fuentes:** M13_T3, M13_T4, M13_T9, M13_RESUMEN
**S:** 85
Primer estándar internacional certificable para sistemas de gestión de IA (diciembre 2023). Sigue la estructura de alto nivel de ISO con 10 cláusulas y un Anexo A de controles; certificable cada 3 años.

## Anexo III (AI Act) — Sistemas de Alto Riesgo
**Fuentes:** M13_T1, M13_T2
Lista taxativa del AI Act que define los dominios donde un sistema de IA se clasifica como de alto riesgo: biometría, infraestructura crítica, educación, empleo, servicios esenciales, aplicación de ley, migración y justicia.

## RGPD / GDPR (Reglamento General de Protección de Datos)
**Fuentes:** M13_T5, M13_T8, M13_T9
Marco europeo de protección de datos personales que interactúa con el AI Act. El Art. 22 establece el derecho a no estar sujeto a decisiones exclusivamente automatizadas; el Art. 10 exige base legal para usar datos en entrenamiento.

## DPIA (Data Protection Impact Assessment)
**Fuentes:** M13_T5, M13_T9
Evaluación de impacto sobre la privacidad obligatoria para sistemas de IA que procesan datos sensibles o toman decisiones automatizadas con impacto significativo. Requerida por el RGPD.

## Linaje de datos
**Fuentes:** M13_T5, M13_RESUMEN
**S:** 182
Documentación completa del ciclo de vida de los datos de un sistema de IA: origen, transformaciones, versión del dataset y responsable de validación. Imprescindible para cumplir el Art. 10 del AI Act.

## Data Card / Model Card
**Fuentes:** M13_T5, M13_T7, M13_RESUMEN
**S:** 104
Formatos estándar de documentación de datasets (Data Cards) y modelos (Model Cards) que recogen composición, proceso de recolección, limitaciones, usos recomendados y consideraciones éticas. Formato de referencia en auditorías.

## Privacy by Design
**Fuentes:** M13_T5
Principio que exige integrar la protección de la privacidad en el diseño del sistema de IA desde el principio: minimización de datos, anonimización/pseudonimización antes del entrenamiento y privacidad diferencial.

## Fairness / Equidad algorítmica
**Fuentes:** M13_T6, M13_T7, M13_RESUMEN
**S:** 107
Propiedad de un sistema de IA que garantiza que sus decisiones no discriminan sistemáticamente a grupos por características protegidas. Se operacionaliza con métricas cuantitativas; su elección es una decisión ética.

## Demographic Parity (Paridad Demográfica)
**Fuentes:** M13_T7, M13_RESUMEN
**S:** 152
Métrica de fairness que exige que la tasa de resultados positivos del modelo sea igual para todos los grupos demográficos. Matemáticamente incompatible con Predictive Parity cuando las tasas de base difieren.

## Equalized Odds (Igualdad de Probabilidades)
**Fuentes:** M13_T7, M13_RESUMEN
**S:** 159
Métrica de fairness que exige que las tasas de verdaderos positivos y falsos positivos sean iguales para todos los grupos demográficos. Especialmente relevante en crédito, justicia y empleo.

## Disparate Impact
**Fuentes:** M13_T7, M13_RESUMEN
**S:** 153
Métrica de fairness que mide el ratio de tasas de resultados positivos entre el grupo desfavorecido y el favorecido. En la jurisprudencia laboral de EE.UU., el umbral de 0,8 (regla de los 4/5) indica discriminación.

## Teorema de imposibilidad de fairness (Kleinberg et al.)
**Fuentes:** M13_T7, M13_RESUMEN
**S:** 213
Resultado matemático que demuestra que Demographic Parity, Predictive Parity y Equalized Odds son mutuamente incompatibles cuando los grupos tienen tasas de base distintas. La elección de la métrica es una decisión de valores.

## Mechanistic Interpretability (Interpretabilidad mecanicista)
**Fuentes:** M13_T8
Campo emergente que identifica los circuitos neuronales internos responsables de comportamientos específicos en LLMs. Impulsado por Anthropic y OpenAI; actualmente en fase de investigación.

## DORA (Digital Operational Resilience Act)
**Fuentes:** M13_T9
Regulación europea para el sector financiero (en vigor desde 2025) que incluye requisitos específicos para sistemas de IA en la gestión del riesgo operacional. Se superpone al EU AI Act.

## Executive Order 14110 (EE.UU.)
**Fuentes:** M13_T3, M13_T9
Orden ejecutiva de EE.UU. sobre IA segura y confiable que obliga a los proveedores de modelos frontier a entregar resultados de red teaming al gobierno federal. Convierte el NIST AI RMF en de facto obligatorio para proveedores del gobierno.

## Responsible Scaling Policy (RSP)
**Fuentes:** M13_T6
Política pública de Anthropic que establece niveles de seguridad de IA (ASL-1 a ASL-4) con umbrales de capacidad por encima de los cuales un modelo no puede desplegarse hasta que las salvaguardas sean suficientes.

## AIIA (AI Impact Assessment / Evaluación de Impacto Ético)
**Fuentes:** M13_T6, M13_T9
Proceso de evaluación sistemática de los impactos potenciales de un sistema de IA sobre derechos fundamentales, bienestar y equidad antes del despliegue. Más amplio que la DPIA; requerido en la ISO 42001.

## Ethics by Design
**Fuentes:** M13_T6
Enfoque metodológico que integra la evaluación ética en el proceso de desarrollo de sistemas de IA desde el inicio del diseño, en lugar de añadirla como validación al final.

## GRC (Governance, Risk, Compliance)
**Fuentes:** M13_T3, M13_T9
Plataformas integradas de gestión de gobernanza, riesgo y cumplimiento que en 2025 incorporan módulos específicos para el AI Act e ISO 42001 (OneTrust, Vanta, Drata). Mapean controles una vez para satisfacer múltiples frameworks.

## Brussels Effect
**Fuentes:** M13_RESUMEN
**S:** 225
Fenómeno por el que la regulación europea de IA se convierte en estándar global de facto, ya que empresas de EE.UU. y Asia adoptan el estándar europeo para sus operaciones globales, como ocurrió con el GDPR.

---

## Módulo 14 — Estrategia de Empresa

## Matriz de oportunidades de IA
**Fuentes:** M14_T1, M14_RESUMEN
**S:** 184
Herramienta de priorización que evalúa cada caso de uso en dos dimensiones — impacto de negocio y viabilidad técnica/organizativa — clasificando los candidatos en Quick Wins, Strategic Bets, iniciativas incrementales y descartables.

## Quick Wins
**Fuentes:** M14_T1, M14_T4, M14_T8, M14_RESUMEN
**S:** 87
Casos de uso de alto impacto y alta viabilidad que se priorizan en el Horizonte 1 del roadmap para demostrar valor rápido, generar momentum organizativo y financiar las iniciativas siguientes.

## AI Opportunity Workshop
**Fuentes:** M14_T1, M14_RESUMEN
**S:** 134
Taller estructurado de 1–2 días con líderes funcionales que mapea los 20–30 procesos de mayor coste, tiempo de ciclo o tasa de error y evalúa cuáles son candidatos a IA. El método más efectivo de identificación de oportunidades.

## Pilot purgatory
**Fuentes:** M14_T1
Situación en la que una organización acumula pilotos y experimentos de IA sin escalarlos a producción, desperdiciando capital político y financiero sin generar impacto medible.

## Cuatro fuentes de valor de la IA
**Fuentes:** M14_T1, M14_RESUMEN
**S:** 149
Marco que clasifica el valor generado por iniciativas de IA en cuatro dimensiones: reducción de costes operativos, aumento de ingresos, mejora de la experiencia y gestión del riesgo. Los casos multidimensionales son los más estratégicos.

## Flujo to-be
**Fuentes:** M14_T2
Diagrama del proceso mejorado con la IA integrada que define qué acciones realizará el humano, cuáles la IA y cómo interactuarán, determinando las capacidades técnicas necesarias antes de seleccionar la arquitectura.

## Design sprint de IA
**Fuentes:** M14_T2
Metodología de 5 días adaptada a proyectos de IA (Entender, Divergir, Decidir, Prototipar, Validar) que produce una especificación detallada del caso de uso validada con usuarios reales en una semana.

## Business case de IA
**Fuentes:** M14_T3, M14_RESUMEN
**S:** 144
Documento de cinco secciones (contexto/problema, solución propuesta, análisis financiero, plan de implementación y riesgos) que justifica la inversión en IA ante la dirección. Incluye obligatoriamente el análisis de sensibilidad.

## Payback period
**Fuentes:** M14_T3
Tiempo necesario para que los beneficios acumulados de una iniciativa de IA igualen la inversión total realizada. Una de las métricas financieras clave del business case junto al ROI anualizado.

## Análisis de sensibilidad
**Fuentes:** M14_T3, M14_RESUMEN
**S:** 136
Componente del business case que evalúa el ROI bajo tres escenarios (optimista, base, pesimista) para demostrar que la iniciativa es rentable incluso si los beneficios son un 20–40% menores de lo proyectado.

## Roadmap de IA (tres horizontes)
**Fuentes:** M14_T4, M14_RESUMEN
**S:** 205
Plan estratégico a 12–36 meses que organiza las iniciativas de IA en tres horizontes: H1 Quick Wins (0–12 meses), H2 transformación de procesos core (12–24 meses) y H3 iniciativas estratégicas transformacionales (24–36 meses).

## AI Maturity Assessment
**Fuentes:** M14_T4
Evaluación de la madurez de la organización en cinco dimensiones (alineación estratégica, datos y gobernanza, tecnología, talento y cultura, ejecución y métricas) según el modelo MIT CISR.

## Iniciativas de habilitación
**Fuentes:** M14_T4, M14_RESUMEN
**S:** 175
Proyectos del roadmap que no generan ROI directo pero son prerrequisito para las iniciativas de negocio: modernización de la arquitectura de datos, plataforma ML/LLM, equipo de IA, framework de gobernanza y AI literacy.

## AI Steering Committee
**Fuentes:** M14_T4
Órgano de gobierno mensual del roadmap de IA, presidido por el AI Strategy Lead, que revisa el progreso de las iniciativas, resuelve bloqueos y toma decisiones de reasignación de recursos.

## AI literacy
**Fuentes:** M14_T5, M14_T6, M14_RESUMEN
**S:** 92
Conocimiento básico que toda la organización necesita para operar en un entorno con IA: qué puede y qué no puede hacer la IA, cómo funciona y qué riesgos presenta. El AI Act (artículo 4) lo exige como obligación legal.

## Upskilling / Reskilling de IA
**Fuentes:** M14_T5, M14_T6, M14_RESUMEN
**S:** 128
Proceso continuo de desarrollo de capacidades en IA que opera en tres niveles progresivos (AI literacy, AI adoption, AI domain transformation). El reskilling del personal existente es la palanca más económica y sostenible.

## AI Governance Committee (AGC)
**Fuentes:** M14_T7, M14_RESUMEN
**S:** 133
Órgano cross-funcional (tecnología, legal, compliance, negocio, riesgo, RRHH) responsable de aprobar la política de IA, revisar sistemas de alto riesgo antes del despliegue y supervisar el cumplimiento del AI Act.

## AI Registry
**Fuentes:** M14_T7, M14_T8, M14_RESUMEN
**S:** 93
Inventario centralizado de todos los sistemas de IA de la organización con su estado de gobernanza, propietarios y clasificación de riesgo. Componente mínimo obligatorio de cualquier framework de gobernanza en 2025.

## AI incident management
**Fuentes:** M14_T7
Proceso estructurado para detectar, clasificar por severidad, escalar, investigar, remediar y comunicar al regulador los incidentes producidos por sistemas de IA. El AI Act impone obligaciones de notificación para sistemas de alto riesgo.

## Modelo de madurez de IA empresarial (cinco niveles)
**Fuentes:** M14_T8, M14_RESUMEN
**S:** 191
Escala que describe la evolución de la adopción de IA: Exploración, Adopción inicial, Escalado, Transformación y Reinvención (nuevos modelos de negocio habilitados por IA).

## Portfolio de IA 70-20-10
**Fuentes:** M14_T8, M14_RESUMEN
**S:** 201
Marco de asignación de recursos: 70% en explotación (Quick Wins, retorno predecible), 20% en transformación (rediseño de procesos core) y 10% en exploración (IA agéntica, modelos emergentes).

## Internet de los agentes
**Fuentes:** M14_T8
Visión prospectiva del ecosistema emergente donde miles de agentes de IA especializados colaboran de forma autónoma mediante protocolos de interoperabilidad (MCP, A2A) para ejecutar tareas empresariales complejas.

## Customer Data Platform (CDP)
**Fuentes:** M14_T4
Plataforma que unifica datos de comportamiento del cliente de múltiples fuentes en un perfil único. Prerrequisito habilitador para iniciativas de personalización a escala con IA.

---

*Este glosario se construye a partir de los PDFs de `PDFs/temas/` (formato MX_TY)
y `PDFs/resumenes/` (formato MX_RESUMEN).
Última actualización: 2026-05-14.*
