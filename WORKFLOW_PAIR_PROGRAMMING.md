# Workflow: Claude (Director) + Codex (Ejecutor)
## MaquinarIa Pesada — Automatización del Máster

---

## Roles

**Claude Code (Director)**
- Diseña la arquitectura
- Escribe las especificaciones de cada tarea
- Revisa el código generado
- Decide qué construir y en qué orden

**OpenAI Codex CLI (Ejecutor)**
- Implementa el código según la spec
- Ejecuta comandos de terminal
- Lee/edita archivos
- Reporta resultados a Claude

---

## Protocolo de comunicación

### Formato de tarea para Codex
```
TAREA: [nombre corto]
CONTEXTO: [qué existe ya, qué archivos relevantes]
OBJETIVO: [qué debe producir exactamente]
RESTRICCIONES: [qué no tocar, límites]
ENTREGABLE: [archivo/función/output esperado]
```

### Ciclo de trabajo
1. Claude define la tarea en formato estándar
2. Codex ejecuta: `codex "TAREA: ..."`
3. Codex entrega resultado
4. Claude revisa y aprueba o da feedback
5. Repetir

---

## Cómo invocar Codex desde terminal

```bash
# Modo interactivo (Codex puede ejecutar comandos)
OPENAI_API_KEY=<tu_key> codex

# Tarea directa en modo full-auto
OPENAI_API_KEY=<tu_key> codex --approval-mode full-auto "descripción de la tarea"

# Con contexto de archivo
OPENAI_API_KEY=<tu_key> codex --approval-mode full-auto -c generar_episodio_v2.py "descripción"
```

---

## Pipeline del Máster — Tareas pendientes

### Fase 1: Motor TTS híbrido (PRIORIDAD ALTA)
- [ ] Integrar Kokoro en `generar_episodio_v2.py` como `--motor kokoro`
- [ ] Flag `--motor elevenlabs|kokoro|auto` (auto = Kokoro por defecto, ElevenLabs para bloques marcados)
- [ ] Marcar bloques en guión con `[ELEVEN]` para forzar ElevenLabs en pasajes clave

### Fase 2: Generador de guiones
- [ ] Script `generar_guion.py` que llama a Claude API con el prompt del Constructor v1.0
- [ ] Input: tema + duración deseada → Output: EPxxx_guion_etiquetas.txt
- [ ] Numeración automática de episodios

### Fase 3: Pipeline completo
- [ ] Script `producir_episodio.py` que orquesta: generar_guion → generar_audio → montar
- [ ] Batch production: lista de temas → N episodios sin intervención
- [ ] Dashboard de créditos: cuántos ElevenLabs quedan, coste estimado por episodio

### Fase 4: Distribución
- [ ] Upload automático a RSS/hosting
- [ ] Generación de show notes en Markdown

---

## Variables de entorno necesarias

```bash
ELEVENLABS_API_KEY=...   # Ya configurado
OPENAI_API_KEY=...       # Necesario para Codex + generador de guiones
ANTHROPIC_API_KEY=...    # Para llamadas Claude API desde scripts
```

---

## Directorio del proyecto

```
maquinaria_pesada/
├── generar_episodio_v2.py      # Motor principal (ElevenLabs)
├── EP001_guion_etiquetas_v3.txt
├── kokoro-v1.0.onnx            # Modelo TTS local
├── voices-v1.0.bin             # Voces Kokoro
├── output/
│   ├── EP001_MaquinarIaPesada_v4.mp3
│   ├── background_music_raw.mp3
│   └── temp/                   # 113 bloques individuales
├── WORKFLOW_PAIR_PROGRAMMING.md  ← este archivo
└── INSTRUCCIONES.txt
```
