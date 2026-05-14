# Área 11 — Sistemas de Inteligencia Artificial

## ⚠️ ÁREA CRÍTICA — Peso × 2 (igual que Seguridad)
## Aplica RGPD + AI Act UE 2024/1689 + recomendaciones de buenas prácticas

---

## FASE A — DETECCIÓN: ¿Hay IA en el proyecto?

Ejecuta esta fase primero. Si no se detecta ningún sistema de IA, el área puntúa ⚪ (no aplica)
y se documenta "Sin sistemas de IA detectados". No continúes con el resto del análisis.

### A.1 Detección de proveedores de IA por dependencias
```bash
# Buscar SDKs y clientes de IA en package.json
cat package.json 2>/dev/null | python3 -c "
import json,sys
data=json.load(sys.stdin)
all_deps={**data.get('dependencies',{}),**data.get('devDependencies',{})}
ai_providers={
  '@anthropic-ai/sdk': 'Anthropic Claude',
  'anthropic': 'Anthropic Claude',
  'openai': 'OpenAI (GPT)',
  '@openai/openai': 'OpenAI (GPT)',
  'openai-api': 'OpenAI (GPT)',
  '@google-ai/generativelanguage': 'Google Gemini',
  '@google/generative-ai': 'Google Gemini',
  'groq-sdk': 'Groq',
  'mistralai': 'Mistral AI',
  '@mistralai/mistralai': 'Mistral AI',
  'cohere-ai': 'Cohere',
  'cohere': 'Cohere',
  '@aws-sdk/client-bedrock-runtime': 'AWS Bedrock',
  'langchain': 'LangChain (multi-proveedor)',
  '@langchain/core': 'LangChain Core',
  '@langchain/anthropic': 'LangChain + Anthropic',
  '@langchain/openai': 'LangChain + OpenAI',
  'llamaindex': 'LlamaIndex',
  'ai': 'Vercel AI SDK (multi-proveedor)',
  '@ai-sdk/anthropic': 'Vercel AI SDK + Anthropic',
  '@ai-sdk/openai': 'Vercel AI SDK + OpenAI',
  'replicate': 'Replicate',
  'together-ai': 'Together AI',
  'huggingface': 'HuggingFace',
  '@huggingface/inference': 'HuggingFace Inference',
  'ollama': 'Ollama (modelos locales)',
  'transformers': 'Transformers.js (local)',
  '@xenova/transformers': 'Transformers.js (local en browser)',
  'tensorflow': 'TensorFlow.js',
  '@tensorflow/tfjs': 'TensorFlow.js',
  'onnxruntime-node': 'ONNX Runtime (modelos locales)',
  'onnxruntime-web': 'ONNX Runtime Web (modelos locales)',
}
found=[(k,v) for k,v in ai_providers.items() if k in all_deps]
if found:
  print('=== PROVEEDORES DE IA DETECTADOS ===')
  for dep,name in found:
    print(f'  {name} ({dep}: {all_deps[dep]})')
else:
  print('No se detectaron SDKs de IA en package.json')
" 2>/dev/null

# Buscar también en requirements.txt (Python), go.mod, Cargo.toml
grep -i "anthropic\|openai\|gemini\|mistral\|cohere\|huggingface\|langchain\|llama\|groq\|replicate\|bedrock\|tensorflow\|torch\|transformers" \
  requirements.txt requirements-dev.txt pyproject.toml go.mod Cargo.toml 2>/dev/null
```

### A.2 Detección por llamadas a APIs de IA en el código
```bash
# Detectar llamadas a APIs de IA por URL o cliente
grep -rn \
  "anthropic\|claude\|openai\|gpt-\|gemini\|mistral\|groq\|cohere\|replicate\|bedrock\|huggingface\|ollama\|together\.ai\|perplexity" \
  . --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
     --include="*.py" --include="*.go" --include="*.rs" \
  | grep -v node_modules | grep -v dist | grep -v ".test." | grep -v ".spec." \
  | grep -iv "comment\|#.*claude\|\/\/.*claude" \
  | head -40

# Detectar URLs de APIs de IA
grep -rn \
  "api\.anthropic\.com\|api\.openai\.com\|generativelanguage\.googleapis\.com\|api\.mistral\.ai\|api\.groq\.com\|api\.cohere\.ai\|api\.replicate\.com" \
  . --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" \
  | grep -v node_modules | head -20

# Detectar variables de entorno de IA
grep -rn \
  "ANTHROPIC\|OPENAI\|GEMINI\|MISTRAL\|GROQ\|COHERE\|HUGGINGFACE\|HF_TOKEN\|REPLICATE\|BEDROCK\|AI_API" \
  .env.example .env.local .env.development .env.production . \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.env*" \
  2>/dev/null | grep -v node_modules | grep -v "process\.env\." | head -20
```

### A.3 Detección de modelos locales o embebidos
```bash
# Detectar modelos locales (ONNX, GGUF, PyTorch, etc.)
find . -name "*.onnx" -o -name "*.gguf" -o -name "*.pt" -o -name "*.pth" \
  -o -name "*.bin" -o -name "*.safetensors" \
  | grep -v node_modules | head -10

# Detectar Transformers.js o WebNN (IA en el browser)
grep -rn "@xenova/transformers\|transformers\.js\|WebNN\|navigator\.ml\|MLGraphBuilder" \
  src/ --include="*.ts" --include="*.tsx" --include="*.js" 2>/dev/null | head -10

# Detectar Ollama (modelos locales vía servidor)
grep -rn "ollama\|localhost:11434\|127\.0\.0\.1:11434" \
  . --include="*.ts" --include="*.js" --include="*.env*" | grep -v node_modules | head -10
```

**SI NO SE DETECTA NADA:** Documentar como "Sin sistemas de IA detectados" y finalizar área 11.
**SI SE DETECTA ALGO:** Continuar con Fases B, C, D, E, F.

---

## FASE B — INVENTARIO: ¿Qué sistemas de IA hay y cómo están integrados?

### B.1 Localización: ¿dónde vive el código de IA?
```bash
# Encontrar todos los archivos que hacen llamadas a IA
grep -rln \
  "anthropic\|Anthropic\|openai\|OpenAI\|createClient\|generateText\|streamText\|chat\.completions\|messages\.create\|generateContent" \
  . --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" \
  | grep -v node_modules | grep -v dist | sort

# Clasificar si el código de IA está en frontend, backend o ambos
echo "=== ARCHIVOS DE IA EN FRONTEND ==="
grep -rln "anthropic\|openai\|ai-sdk\|generateText\|streamText" \
  src/components/ src/app/ src/pages/ src/hooks/ 2>/dev/null | head -20

echo "=== ARCHIVOS DE IA EN BACKEND/API ==="
grep -rln "anthropic\|openai\|ai-sdk\|generateText\|streamText" \
  src/api/ api/ server/ backend/ app/api/ pages/api/ src/server/ 2>/dev/null | head -20

# Detectar si la API key se usa directamente en frontend (CRÍTICO)
grep -rn "ANTHROPIC_API_KEY\|OPENAI_API_KEY\|AI_API_KEY" \
  src/components/ src/app/ src/pages/ src/hooks/ \
  --include="*.tsx" --include="*.ts" --include="*.jsx" --include="*.js" 2>/dev/null | head -10
```

### B.2 Arquitectura: ¿cómo está integrada la IA?
```bash
# Detectar si hay una capa de abstracción (servicio, hook, helper)
find . -path "*/services/*ai*" -o -path "*/lib/*ai*" -o -path "*/utils/*ai*" \
  -o -name "*ai*.ts" -o -name "*ai*.js" -o -name "*llm*.ts" -o -name "*claude*.ts" \
  -o -name "*openai*.ts" -o -name "*prompt*.ts" \
  | grep -v node_modules | grep -v dist | grep -v ".test." | head -20

# Detectar si hay gestión de prompts centralizada
find . -name "*prompt*" -o -name "*template*" \
  | grep -v node_modules | grep -v dist | grep -v ".test." \
  | xargs grep -l "anthropic\|openai\|claude\|gpt" 2>/dev/null | head -10

# Detectar si hay API propia que hace de proxy hacia la IA
grep -rln "messages\.create\|chat\.completions\.create\|generateText" \
  pages/api/ app/api/ api/ src/api/ server/ \
  --include="*.ts" --include="*.js" 2>/dev/null | head -10

# Detectar uso de streaming
grep -rn "stream\|StreamingTextResponse\|streamText\|createStreamableValue\|ReadableStream\|EventSource" \
  . --include="*.ts" --include="*.tsx" --include="*.js" \
  | grep -v node_modules | grep -i "ai\|anthropic\|openai\|claude\|gpt" | head -15
```

### B.3 Tipos de sistemas de IA detectados
```bash
# Chatbot / asistente conversacional
grep -rn "messages.*role\|role.*user\|role.*assistant\|conversationHistory\|chatHistory\|thread" \
  . --include="*.ts" --include="*.tsx" --include="*.js" \
  | grep -v node_modules | head -10

# Generación de texto / completions
grep -rn "completion\|generate\|prompt\|system_prompt\|systemPrompt\|user_message" \
  . --include="*.ts" --include="*.js" | grep -v node_modules | head -10

# Análisis / clasificación de datos de usuario
grep -rn "analyze\|classify\|evaluate\|score\|rank\|recommend\|interpret" \
  . --include="*.ts" --include="*.js" | grep -v node_modules \
  | grep -i "ai\|claude\|openai\|model\|llm" | head -10

# RAG (Retrieval Augmented Generation)
grep -rn "embedding\|vector\|similarity\|pgvector\|pinecone\|weaviate\|chroma\|qdrant\|faiss\|retriev" \
  . --include="*.ts" --include="*.js" | grep -v node_modules | head -10

# Generación de imágenes
grep -rn "dall-e\|dall_e\|stable-diffusion\|imagen\|midjourney\|generateImage\|image_generation" \
  . --include="*.ts" --include="*.js" | grep -v node_modules | head -5

# Transcripción / voz
grep -rn "whisper\|transcrib\|speech-to-text\|text-to-speech\|tts\|stt\|elevenlabs" \
  . --include="*.ts" --include="*.js" | grep -v node_modules | head -5

# Agentes / herramientas
grep -rn "tool_use\|function_call\|tools:\|tool_choice\|agent\|useTools\|runAgent" \
  . --include="*.ts" --include="*.js" | grep -v node_modules | head -10
```

---

## FASE C — FLUJO DE DATOS: ¿Qué datos viajan a la IA y cómo?

### C.1 ¿Qué datos se envían a la IA?
```bash
# Examinar los prompts construidos en el código
grep -rn -A 10 "messages:\|prompt:\|content:\|system:" \
  . --include="*.ts" --include="*.tsx" --include="*.js" \
  | grep -v node_modules | grep -B2 -A8 "user\|assistant\|system" | head -80

# Detectar si se incluyen datos de usuario en los prompts
grep -rn "user\.\|userData\|userProfile\|req\.body\|req\.user\|session\.user\|currentUser" \
  . --include="*.ts" --include="*.js" \
  | grep -v node_modules \
  | grep -i "prompt\|message\|content\|send\|claude\|openai\|ai" | head -20

# Detectar si se incluyen datos sensibles en prompts
grep -rn -i "email\|phone\|name\|address\|dni\|passport\|health\|medical\|salary\|payment\|card\|iban\|password" \
  . --include="*.ts" --include="*.tsx" --include="*.js" \
  | grep -v node_modules \
  | grep -i "prompt\|message\|content\|claude\|openai\|llm" | head -20
```

### C.2 ¿Cómo viajan los datos? (frontend directo vs proxy)
```bash
# CASO 1: Llamada directa desde frontend (RIESGO CRÍTICO — API key expuesta)
grep -rn "new Anthropic\|new OpenAI\|createClient" \
  src/components/ src/app/ src/pages/ src/hooks/ \
  --include="*.tsx" --include="*.ts" --include="*.jsx" 2>/dev/null | head -10

# CASO 2: Llamada a ruta API propia (patrón correcto)
grep -rn "fetch.*\/api\/\|axios.*\/api\/" \
  src/components/ src/app/ src/pages/ src/hooks/ \
  --include="*.tsx" --include="*.ts" 2>/dev/null \
  | grep -i "ai\|chat\|generate\|prompt\|claude\|gpt" | head -10

# CASO 3: Server Action de Next.js (correcto)
grep -rn "'use server'\|\"use server\"" \
  . --include="*.ts" --include="*.tsx" 2>/dev/null \
  | grep -v node_modules | head -10

# Verificar que la API key NO está en variables de entorno públicas (VITE_, NEXT_PUBLIC_)
grep -rn "NEXT_PUBLIC_ANTHROPIC\|NEXT_PUBLIC_OPENAI\|VITE_ANTHROPIC\|VITE_OPENAI\|VITE_AI" \
  .env* --include=".env*" . --include="*.ts" --include="*.tsx" 2>/dev/null | head -10
```

### C.3 ¿Se guardan los datos que van y vienen de la IA?
```bash
# Detectar si se guardan conversaciones o prompts en BBDD
grep -rn "insert\|upsert\|save\|store\|create" \
  . --include="*.ts" --include="*.js" \
  | grep -v node_modules \
  | grep -i "message\|conversation\|prompt\|response\|completion\|history" | head -20

# Detectar tablas relacionadas con IA en migraciones
grep -rn "conversation\|message\|chat_history\|prompt\|ai_response\|llm_log\|ai_log" \
  supabase/migrations/ --include="*.sql" 2>/dev/null | head -20

# Detectar si se loguean los prompts/respuestas (riesgo de PII en logs)
grep -rn "console\.log\|logger\.\|log\." \
  . --include="*.ts" --include="*.js" | grep -v node_modules \
  | grep -i "prompt\|message\|response\|content\|completion" | head -20

# Detectar si hay retención de datos configurada
grep -rn "retention\|ttl\|expires\|delete.*old\|cleanup\|purge" \
  . --include="*.ts" --include="*.js" --include="*.sql" \
  | grep -v node_modules | grep -i "message\|conversation\|log\|ai" | head -10
```

### C.4 ¿Hay context window o historial de conversación?
```bash
# Detectar gestión de historial de conversación
grep -rn "conversationHistory\|chatHistory\|messages\[\]\|history\[\]\|thread_id\|session_id" \
  . --include="*.ts" --include="*.tsx" --include="*.js" \
  | grep -v node_modules | head -15

# Detectar límites de contexto o truncado
grep -rn "maxTokens\|max_tokens\|context_length\|truncate\|slice.*messages\|messages\.slice" \
  . --include="*.ts" --include="*.js" | grep -v node_modules | head -10
```

---

## FASE D — CALIDAD DE LA INTEGRACIÓN: ¿Cómo está construida?

### D.1 Gestión de errores de la IA
```bash
# Detectar manejo de errores en llamadas a IA
grep -rn -A5 "messages\.create\|generateText\|chat\.completions\|streamText" \
  . --include="*.ts" --include="*.js" | grep -v node_modules \
  | grep -E "catch|try|error|Error|APIError|RateLimitError|timeout" | head -20

# Detectar reintentos (retry logic)
grep -rn "retry\|backoff\|maxRetries\|max_retries\|attempt\|AbortSignal" \
  . --include="*.ts" --include="*.js" | grep -v node_modules | head -10

# Detectar timeouts configurados
grep -rn "timeout\|AbortController\|signal\|maxDuration" \
  . --include="*.ts" --include="*.js" | grep -v node_modules \
  | grep -i "ai\|fetch\|anthropic\|openai" | head -10

# Detectar fallbacks cuando la IA falla
grep -rn "fallback\|default.*response\|error.*response\|catch.*return" \
  . --include="*.ts" --include="*.js" | grep -v node_modules \
  | grep -i "ai\|prompt\|generate\|claude\|openai" | head -10
```

### D.2 Gestión de costes y rate limiting
```bash
# Detectar configuración de max_tokens
grep -rn "max_tokens\|maxTokens\|max_output_tokens" \
  . --include="*.ts" --include="*.js" | grep -v node_modules | head -10

# Detectar rate limiting propio
grep -rn "rateLimit\|rate_limit\|rateLimiter\|upstash\|redis.*limit\|limit.*request" \
  . --include="*.ts" --include="*.js" | grep -v node_modules | head -10

# Detectar control de uso por usuario
grep -rn "usage\|quota\|credits\|tokens_used\|requests_count" \
  . --include="*.ts" --include="*.js" --include="*.sql" \
  | grep -v node_modules | head -10
```

### D.3 Calidad de los prompts
```bash
# Examinar system prompts (instrucciones al modelo)
grep -rn -A 20 "role.*system\|system:\|systemPrompt\|system_prompt" \
  . --include="*.ts" --include="*.js" \
  | grep -v node_modules | head -60

# Detectar si los prompts están centralizados o dispersos
find . -name "*prompt*" -o -name "*template*" \
  | grep -v node_modules | grep -v dist | grep -v ".test." | head -20

grep -rn "prompt\s*=\s*\`\|prompt\s*=\s*\"" \
  . --include="*.ts" --include="*.tsx" --include="*.js" \
  | grep -v node_modules | wc -l

# Detectar inyección de prompts (prompt injection risk)
grep -rn "req\.body\|req\.params\|searchParams\|formData\|input\." \
  . --include="*.ts" --include="*.js" | grep -v node_modules \
  | grep -i "prompt\|message\|content\|user.*said\|user.*input" | head -15
```

### D.4 Supervisión humana de outputs de IA
```bash
# Detectar si el output de IA se muestra directo o pasa por validación
grep -rn "validate\|sanitize\|filter\|moderate\|review\|approve\|human" \
  . --include="*.ts" --include="*.tsx" --include="*.js" \
  | grep -v node_modules \
  | grep -i "ai\|response\|output\|result\|generate\|completion" | head -15

# Detectar moderación de contenido
grep -rn "moderat\|content.filter\|safe\|harmful\|toxicity" \
  . --include="*.ts" --include="*.js" | grep -v node_modules | head -10

# Detectar si el usuario puede dar feedback o corregir la IA
grep -rn "feedback\|thumbs\|like\|dislike\|rating\|correction\|report\|flag" \
  src/ --include="*.tsx" --include="*.ts" 2>/dev/null | head -10
```

---

## FASE E — IMPLICACIONES LEGALES

### E.1 AI Act — Clasificación de riesgo

Evalúa y documenta:

**¿La IA toma o influye en decisiones sobre personas?**
- Si genera recomendaciones personalizadas → puede ser sistema de riesgo limitado
- Si clasifica, puntúa o perfila usuarios → puede ser sistema de alto riesgo (Anexo III)
- Si toma decisiones automatizadas sin revisión humana → posible prohibición o alto riesgo

**Clasificación según AI Act (aplicar la más restrictiva detectada):**

| Tipo de uso detectado | Clasificación AI Act | Obligaciones |
|-----------------------|---------------------|-------------|
| Chatbot / asistente informativo | Riesgo mínimo | Transparencia: informar que es IA |
| Recomendaciones personalizadas sin consecuencias graves | Riesgo limitado | Transparencia + supervisión humana recomendada |
| Clasificación o scoring de usuarios | Posible alto riesgo (Anexo III) | Evaluación de conformidad, transparencia, supervisión humana, registro |
| Decisiones sobre acceso, crédito, empleo, salud | Alto riesgo (Anexo III) | Evaluación de conformidad obligatoria, auditoría, explicabilidad |
| Manipulación subliminal, vigilancia masiva | Prohibido | No desplegar bajo ningún concepto |

**Calendario AI Act:**
- Feb 2025: Prohibiciones en vigor
- Ago 2025: GPAI (modelos como Claude, GPT) — obligaciones de transparencia en vigor
- Ago 2026: Alto riesgo — obligaciones completas en vigor

**Verificar en código:**
```bash
# ¿Se informa al usuario que está interactuando con IA?
grep -rn "IA\|inteligencia artificial\|AI\|powered by\|generated by\|asistente\|bot" \
  src/ --include="*.tsx" --include="*.ts" 2>/dev/null | grep -iv "comment\|test" | head -15

# ¿Existe mecanismo de supervisión humana?
grep -rn "human.*review\|revisión\|supervisión\|override\|aprobar\|rechazar\|feedback" \
  src/ --include="*.tsx" --include="*.ts" 2>/dev/null | head -10

# ¿Los outputs de IA están marcados como tal?
grep -rn "generado por IA\|AI generated\|IA generated\|powered by AI\|asistido por IA" \
  src/ --include="*.tsx" --include="*.ts" 2>/dev/null | head -5
```

### E.2 RGPD — Datos personales procesados por la IA

```bash
# Verificar qué datos de usuario se incluyen en los prompts
# (Combinar con hallazgos de C.1 y C.2)

# ¿La política de privacidad menciona el uso de IA?
grep -rn "inteligencia artificial\|IA\|AI\|procesamiento automatizado\|decisiones automatizadas" \
  . --include="*.md" --include="*.txt" --include="*.html" \
  | grep -i "privacidad\|privacy\|términos\|terms\|legal" | head -10

# ¿Existe base legal para el tratamiento de datos con IA?
# (Verificar en docs/legal/ si existe)
cat docs/legal/data-processing-register.md 2>/dev/null | grep -i "ia\|ai\|automatiz"

# ¿El proveedor de IA tiene DPA (Data Processing Agreement)?
# Anthropic: https://www.anthropic.com/legal/data-processing-addendum
# OpenAI: https://openai.com/policies/data-processing-addendum
grep -rn "DPA\|data processing agreement\|encargado.*tratamiento\|processor agreement" \
  docs/ . --include="*.md" 2>/dev/null | head -5
```

**Verificaciones RGPD para IA — documentar en informe:**

1. ¿Los datos personales que se envían a la IA tienen base legal identificada?
2. ¿El proveedor de IA (Anthropic, OpenAI, etc.) actúa como encargado del tratamiento con DPA firmado?
3. ¿Los datos se transfieren fuera de la UE? (Muchos proveedores de IA tienen servidores en EE.UU.)
4. ¿Los usuarios son informados de que sus datos son procesados por IA?
5. ¿Existe mecanismo para excluir datos de usuarios menores de 16 años?
6. ¿Los datos enviados a la IA están en el RAT (Registro de Actividades de Tratamiento)?
7. ¿El proveedor de IA entrena sus modelos con los datos enviados? (Verificar términos de servicio)

```bash
# Detectar si hay menores en el sistema
grep -rn "age\|edad\|birth\|fecha.*nacimiento\|minor\|menor\|parental\|consent" \
  . --include="*.ts" --include="*.tsx" --include="*.js" --include="*.sql" \
  | grep -v node_modules | head -10
```

### E.3 Transferencia internacional de datos (Schrems II / Cláusulas Contractuales Tipo)

Documenta para cada proveedor detectado:

| Proveedor | Sede | Servidores | Mecanismo de transferencia | DPA disponible |
|-----------|------|------------|---------------------------|----------------|
| Anthropic | EE.UU. | EE.UU. / AWS | SCCs + EU Data Privacy Framework | Sí |
| OpenAI | EE.UU. | EE.UU. / Azure | SCCs + EU Data Privacy Framework | Sí |
| Google Gemini | EE.UU. | Global | SCCs + EU Data Privacy Framework | Sí |
| Mistral AI | Francia (UE) | UE | No requiere SCCs | Sí |
| Groq | EE.UU. | EE.UU. | SCCs | Sí |

**Verificar si la empresa tiene los mecanismos de transferencia documentados:**
```bash
cat docs/legal/data-processing-register.md 2>/dev/null | grep -i "transfer\|sccs\|cláusula\|adecuación"
cat docs/legal/*.md 2>/dev/null | grep -i "anthropic\|openai\|gemini\|mistral\|groq"
```

---

## FASE F — GENERACIÓN DEL INFORME DEL ÁREA 11

### Estructura del informe `docs/evaluations/<EVAL_ID>/11-ai-systems.md`:

```markdown
# Área 11 — Sistemas de Inteligencia Artificial   <semáforo>

**Puntuación:** X/10  |  **Anterior:** X/10  |  **Tendencia:** ↑↓→

## Resumen ejecutivo
<Descripción de qué sistemas de IA se han encontrado y diagnóstico general>

## Sistemas de IA detectados

| Sistema | Proveedor | Versión/Modelo | Tipo de integración | Localización en código |
|---------|-----------|----------------|--------------------|-----------------------|
| ...     | ...       | ...            | ...                | ...                   |

## Arquitectura de integración
<Diagrama textual del flujo de datos: Usuario → Frontend → [API propia?] → IA → respuesta>

## Tipos de uso de IA identificados
- [ ] Chatbot / asistente conversacional
- [ ] Generación de texto
- [ ] Análisis de datos de usuario
- [ ] Recomendaciones personalizadas
- [ ] Clasificación / scoring
- [ ] RAG (búsqueda en documentos)
- [ ] Generación de imágenes
- [ ] Transcripción de voz
- [ ] Agentes con herramientas
- [ ] Modelos locales / embebidos

## Flujo de datos hacia la IA

### Datos que se envían
<Describir qué información va al modelo>

### Datos potencialmente sensibles
<Listar campos que podrían ser PII según RGPD>

### Ruta de los datos
<Frontend directo / API proxy / Server Action / Backend>

### Almacenamiento de conversaciones
<Se guardan / No se guardan / Parcialmente>

## Hallazgos técnicos

### 🔴 Críticos
...

### 🟡 Mejorables
...

### 🟢 Correctos
...

## Evaluación legal

### AI Act — Clasificación
**Clasificación detectada:** <Mínimo / Limitado / Alto riesgo / Prohibido>
**Justificación:** <por qué se clasifica así>
**Obligaciones aplicables:**
- ...

### RGPD — Cumplimiento
| Requisito | Estado | Acción necesaria |
|-----------|--------|-----------------|
| Base legal para IA identificada | 🔴/🟡/🟢 | ... |
| DPA con proveedor de IA | 🔴/🟡/🟢 | ... |
| Transferencia internacional documentada | 🔴/🟡/🟢 | ... |
| Usuarios informados del uso de IA | 🔴/🟡/🟢 | ... |
| IA en el RAT | 🔴/🟡/🟢 | ... |
| Proveedor no entrena con datos | 🔴/🟡/🟢 | ... |

### Transparencia hacia el usuario
| Requisito | Estado |
|-----------|--------|
| Se informa que la respuesta es de IA | 🔴/🟡/🟢 |
| Existe mecanismo de supervisión humana | 🔴/🟡/🟢 |
| Usuario puede rechazar/corregir output de IA | 🔴/🟡/🟢 |
| Output marcado como generado por IA | 🔴/🟡/🟢 |

## Recomendaciones priorizadas

### Prioridad 1 — Acción inmediata
...
→ Plan Maestro: <PR o "Sin PR asignado — considerar añadir">

### Prioridad 2 — Antes de salir de Bloque 1
...

### Prioridad 3 — Bloque 2
...
```

---

## CRITERIOS DE PUNTUACIÓN DEL ÁREA 11

| Puntuación | Criterio |
|------------|---------|
| 9-10 🟢 | API key solo en backend, proxy propio, sin PII en prompts, sin datos sensibles sin base legal, DPA firmado, transparencia al usuario, supervisión humana, sin API key expuesta, prompts centralizados, errores manejados, rate limiting |
| 7-8 🟢 | Arquitectura correcta pero algún gap menor (prompts dispersos, sin rate limiting, feedback no implementado) |
| 4-6 🟡 | API key solo en backend pero sin proxy claro, algunos datos de usuario en prompts sin verificar base legal, sin transparencia completa, sin supervisión humana |
| 2-3 🔴 | PII en prompts sin base legal, sin DPA, sin informar al usuario, sin supervisión humana, sin gestión de errores |
| 0-1 🔴 | API key expuesta en frontend, datos sensibles en prompts, datos de menores, sin ninguna medida legal ni técnica |

**Penalizaciones automáticas (reducen puntuación en 3 puntos):**
- API key de IA expuesta en frontend o variables NEXT_PUBLIC_ / VITE_
- Datos sensibles (salud, financieros, menores) enviados a IA sin base legal verificada
- Sin informar al usuario que está interactuando con IA (obligatorio AI Act desde ago 2025)

---

## MÉTRICAS A REGISTRAR EN evaluation-data.json

```json
"ai_systems": {
  "detected": true,
  "providers": [],
  "model_names": [],
  "integration_type": "frontend_direct|api_proxy|server_action|backend_only",
  "api_key_exposed_in_frontend": false,
  "data_sent_to_ai": {
    "user_data_included": false,
    "pii_detected_in_prompts": false,
    "sensitive_data_types": [],
    "conversations_stored": false,
    "logs_contain_prompts": false,
    "retention_policy_defined": false
  },
  "architecture": {
    "has_ai_service_layer": false,
    "prompts_centralized": false,
    "has_error_handling": false,
    "has_retry_logic": false,
    "has_timeout_config": false,
    "has_rate_limiting": false,
    "has_fallback": false,
    "uses_streaming": false,
    "has_conversation_history": false
  },
  "user_interaction": {
    "user_sees_ai_output": true,
    "ai_output_labeled": false,
    "human_oversight_mechanism": false,
    "user_can_reject_ai": false,
    "content_moderation": false,
    "user_feedback_mechanism": false
  },
  "legal": {
    "ai_act_classification": "unknown|minimal|limited|high_risk|prohibited",
    "legal_basis_identified": false,
    "dpa_with_provider": false,
    "international_transfer_documented": false,
    "users_informed_of_ai": false,
    "ai_in_rat": false,
    "provider_trains_on_data": "unknown|yes|no",
    "minors_data_risk": false
  }
}
```
