# Glosario Unificado — MaquinarIA Pesada

Definiciones canónicas de términos técnicos del corpus del máster.
Cualquier término que aparezca en un guion Y esté aquí debe usar esta definición.

---

## IA / Inteligencia Artificial
Sistema computacional capaz de realizar tareas que típicamente requieren inteligencia humana.
Abreviatura canónica en el podcast: **I.A.** (con puntos).

## LLM (Large Language Model)
Modelo de lenguaje de gran escala entrenado sobre corpus masivos de texto.
Genera texto prediciendo el siguiente token dado un contexto previo.

## Prompt
Instrucción o contexto de entrada que se proporciona a un LLM para guiar su respuesta.
Puede incluir system prompt, contexto, ejemplos y la pregunta del usuario.

## Token
Unidad mínima de procesamiento de un LLM. Aproximadamente 0.75 palabras en inglés,
0.6-0.7 palabras en español. Los LLMs tienen un límite de contexto medido en tokens.

## RAG (Retrieval-Augmented Generation)
Técnica que combina recuperación de documentos relevantes con generación de texto.
El modelo accede a una base de conocimiento externa en el momento de la inferencia.

## Fine-tuning
Proceso de ajuste de los pesos de un modelo preentrenado sobre un conjunto de datos
específico para mejorar su rendimiento en una tarea concreta.

## Embedding
Representación vectorial densa de texto (o cualquier dato) en un espacio de alta dimensión.
Permite medir similitud semántica mediante distancia vectorial.

## Agentic AI / Agente IA
Sistema de IA capaz de planificar y ejecutar secuencias de acciones de manera autónoma
para alcanzar un objetivo, usando herramientas y retroalimentación del entorno.

## Chain-of-Thought (CoT)
Técnica de prompting que instruye al modelo a razonar paso a paso antes de responder.
Mejora la precisión en tareas de razonamiento complejo.

## Temperatura (en LLMs)
Hiperparámetro que controla la aleatoriedad en el muestreo de tokens.
Valores bajos (0.0-0.3): respuestas más deterministas.
Valores altos (0.7-1.0): más variedad y creatividad.

## Context window / Ventana de contexto
Límite máximo de tokens que un LLM puede procesar en una sola inferencia
(entrada + salida combinadas).

## Hallucination / Alucinación
Generación de información factualmente incorrecta pero presentada con confianza
por un LLM. Efecto emergente del entrenamiento por predicción de tokens.

## RLHF (Reinforcement Learning from Human Feedback)
Técnica de alineación que usa feedback humano para entrenar un modelo de recompensa
y ajustar el LLM mediante aprendizaje por refuerzo.

## Vector database / Base de datos vectorial
Sistema de almacenamiento especializado en búsqueda por similaridad de embeddings.
Fundamental para implementaciones RAG.

## Sistema automatico
Término canónico del podcast para referirse al sistema de producción de MaquinarIA Pesada.
Siempre en minúsculas en el texto hablado.

---

*Este glosario se actualiza con cada módulo del máster.
Última actualización: 2026-05-11*
