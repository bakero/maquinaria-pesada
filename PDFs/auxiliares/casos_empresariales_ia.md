# Casos Empresariales IA — Fuente Auxiliar para BLOQUE_REALIDAD

Fuente verificada de casos reales, estadísticas y marcos regulatorios de IA empresarial.
Uso obligatorio en BLOQUE_REALIDAD de episodios T-type y BLOQUE_DESTACADO de episodios M-type.

**INSTRUCCIÓN PARA EL LLM**: Usa PRIORITARIAMENTE los casos y datos de este documento.
Si necesitas datos fuera de este documento, usa formulaciones como
"según estudios recientes de Gartner o McKinsey" sin inventar cifras exactas.

---

## MARCOS REGULATORIOS VERIFICADOS

### AI Act (Unión Europea)
- **2025 (vigente)**: Prohibiciones de prácticas de IA inaceptables + obligación de alfabetización
  en IA para todos los empleados que trabajen con sistemas de IA.
- **Agosto 2025**: GPAI rules (reglas para modelos de IA de propósito general, incluye GPT-4, Claude,
  Gemini). Aplica a proveedores con más de diez mil millones de parámetros.
- **2 de agosto de 2026**: Grueso del AI Act en vigor. Sistemas de IA de alto riesgo (RRHH,
  crédito, sanidad, infraestructura crítica) sujetos a evaluación de conformidad obligatoria.
- **Agosto 2027**: Artículo seis punto uno — sistemas de IA integrados en productos regulados
  (maquinaria, dispositivos médicos, vehículos).
- **Impacto empresarial**: Multas de hasta treinta millones de euros o el seis por ciento de la
  facturación global anual, lo que sea mayor.

### NIST AI Risk Management Framework (NIST AI RMF)
- **Publicación**: NIST.AI.100-1 (enero 2023), NIST.AI.100-2e2025 (actualización 2025).
- **Cuatro funciones**: GOVERN (gobernanza organizativa), MAP (identificación de riesgos),
  MEASURE (evaluación y métricas), MANAGE (tratamiento y respuesta).
- **Adopción**: Marco voluntario, de facto estándar en empresas Fortune 500 que operan en EEUU.
- **Compatibilidad**: Diseñado para complementar ISO 42001 y el AI Act europeo.

### ISO 42001 — AIMS (AI Management System)
- **Publicado**: Diciembre 2023. Primera norma ISO específica para sistemas de gestión de IA.
- **Equivalente ISO**: Para IA lo que ISO 27001 es para seguridad de la información.
- **Certificación**: Las organizaciones pueden obtener certificación de terceros.
- **Alcance**: Aplica a cualquier organización que desarrolle, provea o use sistemas de IA.

### OWASP Top 10 for LLMs (2025)
- **LLM01**: Prompt Injection — manipulación de instrucciones al modelo.
- **LLM02**: Insecure Output Handling — outputs del LLM sin sanitizar usados directamente.
- **LLM03**: Training Data Poisoning — contaminación de datos de entrenamiento.
- **LLM04**: Model Denial of Service — saturación del modelo para interrumpir servicio.
- **LLM06**: Sensitive Information Disclosure — filtración de datos confidenciales en outputs.
- **Uso**: Referencia estándar de facto para auditorías de seguridad de aplicaciones LLM.

---

## CASOS REALES VERIFICADOS

### Harvey AI — Sector Legal
- **Empresa**: Harvey AI, startup fundada en 2022, especializada en IA para bufetes.
- **Tecnología base**: LLM con fine-tuning sobre corpus jurídico; integración con bases de datos
  legales (Westlaw, LexisNexis).
- **Adopción**: Más del noventa y siete por ciento de los grandes bufetes de EEUU en lista de espera
  durante dos mil veintitrés.
- **Caso de uso**: Redacción de contratos, due diligence, investigación jurídica, análisis
  de precedentes.
- **Resultado**: Reducción de entre treinta y setenta por ciento del tiempo en tareas de
  revisión documental según testimonios de usuarios piloto.

### Morgan Stanley — Sector Financiero / RAG
- **Empresa**: Morgan Stanley, banco de inversión con más de doscientos años de historia.
- **Sistema**: RAG (Retrieval-Augmented Generation) para asesores financieros.
- **Escala**: Base de conocimiento con más de cien mil documentos internos (informes de análisis,
  presentaciones de producto, políticas de compliance).
- **Función**: Los asesores hacen preguntas en lenguaje natural y el sistema recupera los documentos
  relevantes y genera un resumen contextualizado.
- **Resultado**: Reducción del tiempo de búsqueda de información de horas a minutos.
- **Socio tecnológico**: OpenAI (GPT-4).
- **Fuente**: Presentación pública de Morgan Stanley en OpenAI DevDay 2023.

### JPMorgan COIN — Sector Bancario / ML Clásico
- **Empresa**: JPMorgan Chase, el mayor banco de EEUU por activos.
- **Sistema**: COIN (Contract Intelligence), basado en ML clásico (NLP, clasificadores).
- **Función**: Analiza contratos legales de préstamos comerciales y extrae cláusulas clave.
- **Resultado documentado**: Trescientas sesenta mil horas de trabajo de abogados y analistas
  ahorradas al año. Antes era un proceso manual que llevaba trescientas sesenta mil horas
  anuales; ahora tarda segundos.
- **Relevancia pedagógica**: Caso canónico de ML clásico con ROI cuantificado y verificable.

### IBM Watson Health — Caso de Fracaso Documentado
- **Empresa**: IBM Watson Health, división de IA para oncología.
- **Promesa inicial**: Diagnosticar y recomendar tratamientos de cáncer mejor que oncólogos.
- **Resultado real**: MD Anderson Cancer Center canceló el proyecto en dos mil diecisiete tras
  invertir sesenta y dos millones de dólares. Memorial Sloan Kettering también redujo uso.
- **Causa raíz documentada**: El sistema fue entrenado con datos sintéticos y casos
  hipotéticos, no con pacientes reales. Las recomendaciones eran inconsistentes con
  protocolos médicos reales.
- **Lección**: Las expectativas sobre IA deben calibrarse con la calidad de los datos de
  entrenamiento. El hype no garantiza el rendimiento.
- **Fuente**: Reportaje de STAT News (2017) + declaraciones públicas de IBM.

### Lemonade — Sector Seguros
- **Empresa**: Lemonade, aseguradora digital fundada en 2015.
- **Sistema**: IA para procesamiento automatizado de siniestros (claims).
- **Resultado**: Tiempo de resolución de siniestros de tres segundos en casos simples.
  El récord documentado: un siniestro aprobado y pagado en dos segundos.
- **Modelo**: La IA analiza el vídeo de declaración del cliente, cruza con la póliza,
  aplica reglas de fraude y, si todo es consistente, ejecuta el pago directamente.
- **Fuente**: Blog técnico de Lemonade y múltiples entrevistas públicas de sus fundadores.

### Nordea — Banca Nórdica / Automatización
- **Empresa**: Nordea, el mayor banco de los países nórdicos.
- **Iniciativa**: Automatización de procesos bancarios con IA y RPA (Robotic Process Automation).
- **Escala**: Más de doscientos procesos automatizados internos.
- **Resultado**: Reducción de costes operativos y reasignación de empleados de tareas
  repetitivas a tareas de mayor valor.
- **Relevancia**: Ejemplo de automatización bancaria a gran escala en Europa.

### Zara (Inditex) — Retail / Supply Chain
- **Empresa**: Zara, marca de Inditex, mayor retailer de moda del mundo.
- **Sistema**: IA para forecasting de demanda y optimización de cadena de suministro.
- **Función**: Predice qué productos, tallas y colores tendrán mayor demanda por tienda
  y región, optimizando fabricación y distribución.
- **Resultado**: Ciclo de diseño-producción-distribución de dos semanas (vs. seis meses
  de la industria tradicional). Tasa de descuento sobre stock final inferior al quince
  por ciento (vs. treinta a cuarenta por ciento del sector).
- **Nota**: Inditex no publica datos desagregados; cifras de sector son de analistas
  de moda y reportajes de Harvard Business Review.

### Lenovo — Hardware / Análisis TCO On-Prem vs Cloud
- **Empresa**: Lenovo, fabricante de hardware con amplio portfolio de servidores para IA.
- **Estudio**: Análisis de Coste Total de Propiedad (TCO) para cargas de trabajo de IA.
- **Conclusión**: Para cargas de trabajo de IA sostenidas (uso regular, no esporádico),
  la infraestructura on-premise resulta más económica que el cloud en un horizonte de
  tres a cinco años.
- **Punto de inflexión**: Si el uso supera aproximadamente el cuarenta por ciento de
  utilización sostenida, on-prem supera en rentabilidad a cloud.
- **Fuente**: LenovoPress LP2225, edición 2025. URL verificable: lenovopress.lenovo.com/lp2225

### Mata vs. Avianca — Caso Legal / Alucinación
- **Caso**: Mata v. Avianca Inc., Tribunal de Distrito Sur de Nueva York, 2023.
- **Hechos**: El abogado Roberto Mata presentó un escrito legal con citas a seis casos
  jurisprudenciales generados por ChatGPT. Ninguno de los seis casos existía.
- **Consecuencia**: El juez Kevin Castel multó al abogado y su firma con cinco mil dólares.
  Resolución pública de cinco de junio de dos mil veintitrés.
- **Lección canónica**: Las alucinaciones de LLMs en contextos legales, médicos o
  financieros tienen consecuencias reales y documentadas.
- **Relevancia**: Caso de referencia en cursos de derecho y ética de IA en todo el mundo.

---

## ESTADÍSTICAS DE ADOPCIÓN — FUENTES VERIFICABLES

### AWS Path-to-Value Framework (2024-2025)
- Marco de Amazon Web Services para priorizar casos de uso de IA en empresas.
- Criterios: impacto en negocio (alto/bajo) vs. viabilidad técnica (alta/baja).
- Recomendación: comenzar por casos de alto impacto y alta viabilidad (cuadrante "quick wins").
- Uso en consultoría: referencia estándar en proyectos de adopción de IA empresarial.

### Moveworks Enterprise Change Management (2024-2025)
- Plataforma de IA para empleados; publicó estudio sobre adopción de IA en empresas.
- Hallazgo principal: la resistencia organizativa al cambio es la barrera número uno para la
  adopción de IA, por encima de los obstáculos técnicos.
- Dato verificable: más del setenta por ciento de los proyectos de IA empresarial fallan en
  la fase de adopción por usuarios, no en la fase técnica.

### AI Incident Database — Incidente cite/473
- Base de datos pública de incidentes de IA (aiincidentdatabase.com).
- Incidente 473: consecuencias operativas documentadas por un vector de ataque sobre
  sistema de IA en producción.
- Relevancia: fuente académica y periodística verificable sobre fallos reales de IA.

---

## REFERENCIAS ACADÉMICAS VERIFICADAS

### Papers Fundacionales
- **Attention Is All You Need** (Vaswani et al., 2017) — arXiv:1706.03762.
  Paper que introduce la arquitectura Transformer. Base de todos los LLMs modernos.

- **BERT: Pre-training of Deep Bidirectional Transformers** (Devlin et al., 2018) — arXiv:1810.04805.
  Modelo que estableció el paradigma de pre-entrenamiento + fine-tuning en NLP.

- **RoBERTa: A Robustly Optimized BERT Pretraining Approach** (Liu et al., 2019) — arXiv:2106.09685.

- **Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks** (Lewis et al., 2020)
  — arXiv:2005.11401. Paper original de RAG.

### Benchmarks Verificables
- **SWE-bench**: Benchmark para evaluar la capacidad de LLMs de resolver issues reales de GitHub.
  URL: swebench.com
- **AgentBench**: Benchmark para agentes de IA en tareas del mundo real (webshop, bases de datos,
  sistemas operativos). arXiv:2308.03688.

---

## INSTITUCIONES PARA REFERENCIAS SIN CIFRA EXACTA

Cuando no tengas una cifra exacta verificada, puedes usar las siguientes formulaciones:
- "según el último informe de Gartner sobre adopción de IA..."
- "de acuerdo con datos de McKinsey Global Institute..."
- "según el Stanford Human-Centered AI Institute (HAI)..."
- "el World Economic Forum señala que..."
- "informes recientes de IDC apuntan a que..."
- "investigadores del MIT han documentado que..."
- "según Forrester Research..."
- "el IBM Institute for Business Value publica anualmente que..."

**REGLA**: Nunca inventes cifras concretas (porcentajes, millones de dólares, fechas exactas)
asociadas a estas instituciones. Solo usa la formulación vaga si no tienes el dato verificado
en este documento.

---

*Última actualización: 2026-05-12. Fuente base: PDFs/auxiliares/Contenidos master y fuentes.pdf*
*Uso: fuente auxiliar obligatoria en generar_guion_t.py para BLOQUE_REALIDAD*
