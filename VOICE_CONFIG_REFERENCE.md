# MaquinarIa Pesada — Referencia de configuración de voces
## Versión validada: EP001_v4 (generación aprobada)

---

## 1. Modelo y voces

| Parámetro | Valor |
|---|---|
| Modelo ElevenLabs | `eleven_v3` |
| IAGO — nombre | Tony |
| IAGO — voice_id | `851ejYcv2BoNPjrkw93G` |
| MARÍA — nombre | voz española v4 |
| MARÍA — voice_id | `gJlzF5JxsCvM5hQAoRyD` |
| Output format | `mp3_44100_128` |
| Bitrate montaje | `192k` |

---

## 2. VoiceSettings exactos

### IAGO (Tony)
```python
stability         = 0.50
similarity_boost  = 0.65
style             = 0.00
use_speaker_boost = False
speed             = 1.15
```

### MARÍA (voz española v4)
```python
stability         = 0.70
similarity_boost  = 0.55
style             = 0.00
use_speaker_boost = False
speed             = 1.25
```

> **Por qué estos valores:**
> - `stability` más alta en María (0.70 vs 0.50) estabiliza el acento español que tiende a variar
> - `similarity_boost` más baja en María (0.55) da algo más de expresividad natural
> - `style = 0.00` en ambos — con eleven_v3 las etiquetas del guión ya controlan el estilo; activarlo duplica la variabilidad y rompe la coherencia entre episodios
> - `use_speaker_boost = False` — no disponible en v3, dejarlo False evita errores silenciosos
> - Velocidad: Iago 1.15 / María 1.25 — equilibrada subjetivamente, María necesita +0.10 por su patrón de habla más pausado

---

## 3. Silencios de montaje

```python
SILENCIO_INICIO_MS           = 2000   # 2s de silencio al arrancar el episodio
SILENCIO_MISMO_SPEAKER_MS    = 250    # 0.25s entre intervenciones del mismo presentador
SILENCIO_DISTINTO_SPEAKER_MS = 500    # 0.50s al cambiar de presentador
```

---

## 4. Normalización de audio

```python
# Aproximación a -16 LUFS (estándar podcast)
episodio = episodio.normalize()
episodio = episodio.apply_gain(-16 - episodio.dBFS)
```

---

## 5. Mezcla de música de fondo

```python
musica_loop = musica_loop.fade_in(3000).fade_out(5000)  # fade in 3s, fade out 5s
musica_loop = musica_loop - 20                           # -20 dB bajo las voces
episodio    = episodio.overlay(musica_loop)
```

La música se genera con el siguiente prompt via ElevenLabs sound-generation:
```
"Lo-fi instrumental background music for a technology podcast.
Slow repetitive beats, no vocals, no dominant melody, ambient electronic,
deep focus mood, seamlessly loopable, subtle and unobtrusive"
duration_seconds: 30
prompt_influence: 0.3
```

---

## 6. Etiquetas validadas del guión

Las etiquetas van dentro del texto del bloque y ElevenLabs eleven_v3 las interpreta como instrucciones de dirección. Son parte del texto enviado a la API.

| Etiqueta | Uso correcto |
|---|---|
| `[serio]` | Afirmaciones con peso, datos duros |
| `[tenso]` | Urgencia, riesgo, momentos críticos |
| `[grave]` | Cierres de sección, máximo impacto dramático |
| `[conversacional]` | Diálogo natural entre presentadores |
| `[natural]` | Intervenciones sin carga emocional especial |
| `[directo]` | Listas de conceptos, bullet points hablados |
| `[firme]` | Convicción sin gritar, asertivo |
| `[contundente]` | Golpes dramáticos puntuales |
| `[didáctico]` | Explicaciones técnicas, enseñanza |
| `[explicativo]` | Desarrollo de conceptos, más extenso |
| `[reflexivo]` | Preguntas retóricas, transiciones |
| `[irónico]` | Comentarios con distancia crítica |
| `[curioso]` | Preguntas genuinas, apertura |
| `[pausado]` | Frases cortas que necesitan espacio |
| `[cálido]` | Cierres, despedidas |
| `[escéptico]` | Reacciones de duda |

**Regla de uso:** una sola etiqueta por bloque, al inicio del texto, antes de la primera palabra.

**Formato correcto:**
```
IAGO: [serio] Te voy a contar algo que nadie te dice...
MARÍA: [didáctico] Lo primero: un modelo de inteligencia artificial no ve palabras...
```

**Formato incorrecto (nunca hacer):**
```
IAGO: [serio] texto [tenso] más texto    ← dos etiquetas en un bloque
IAGO: texto [serio]                       ← etiqueta al final
IAGO: [serio][pausado] texto             ← etiquetas encadenadas
```

---

## 7. Estructura del guión

```
PRESENTADOR: [etiqueta] texto del bloque completo
```

- `IAGO:` → Tony
- `MARÍA:` → voz española v4
- Líneas con `#` → comentarios, ignorados por el parser
- Líneas vacías → ignoradas
- Líneas entre corchetes sin presentador (ej: `[INSERTAR AQUÍ: intro.wav]`) → ignoradas
- **Un bloque = un turno de habla completo**. No partir una idea en dos bloques del mismo speaker consecutivos.
- Alternar speakers regularmente. Bloques del mismo speaker seguidos se ven raros en audio.

---

## 8. Longitud de bloques recomendada

| Tipo | Caracteres aprox. | Notas |
|---|---|---|
| Mínimo | 80–120 chars | Menos suena entrecortado |
| Normal | 150–300 chars | Rango óptimo |
| Máximo | 400–500 chars | ElevenLabs puede variar el tono en bloques muy largos |

EP001 tiene 113 bloques, ~168 chars de media. Ese tamaño produce la consistencia de tono más estable.

---

## 9. Lo que NO cambiar entre episodios

Para que las voces suenen idénticas episodio a episodio:

1. **No cambiar voice_id** — aunque el nombre de la voz siga siendo el mismo en ElevenLabs, si actualizan el modelo de la voz el ID puede apuntar a una versión diferente. Usar siempre los IDs hardcodeados de arriba.
2. **No cambiar el modelo** — `eleven_v3` es el validado. `eleven_multilingual_v2` suena diferente y no interpreta las etiquetas igual.
3. **No cambiar speed** — diferencias de ±0.05 en speed son perceptibles en escucha comparada.
4. **No cambiar stability** — subir stability en Iago por encima de 0.60 lo hace monótono. Bajar la de María por debajo de 0.60 introduce variabilidad de acento.
5. **No mezclar etiquetas** — una por bloque, al inicio.
6. **No regenerar bloques ya aprobados** — si el episodio sonó bien, conservar los MP3 en `output/temp/`. Regenerar consume créditos y puede producir una toma ligeramente distinta.

---

## 10. Checklist antes de cada generación

- [ ] `ELEVENLABS_API_KEY` configurada en el entorno
- [ ] Créditos suficientes (~170 chars × nº bloques, estimar 19.000–20.000 por episodio de 18 min)
- [ ] ffmpeg oficial instalado (WinGet, Gyan.FFmpeg) — NO usar el de CapCut (no tiene encoder MP3)
- [ ] Guión en UTF-8 sin BOM
- [ ] Voice IDs correctos en el script (no actualizar sin validar)
- [ ] `style = 0.00` en ambas voces
- [ ] `use_speaker_boost = False` en ambas voces
- [ ] Probar bloque 1 con `--solo-bloque 1` antes del episodio completo si hay dudas

---

## 11. Comando de producción estándar

```bash
# Episodio completo
python generar_episodio_v2.py --guion EPxxx_guion_etiquetas.txt --ep EPxxx

# Con música de fondo (genera nueva música, consume créditos)
python generar_episodio_v2.py --guion EPxxx_guion_etiquetas.txt --ep EPxxx --generar-musica

# Remontar sin regenerar (usa archivos en output/temp/)
python generar_episodio_v2.py --guion EPxxx_guion_etiquetas.txt --ep EPxxx --solo-montar

# Regenerar solo una voz (ej: si María falló a medias)
python generar_episodio_v2.py --guion EPxxx_guion_etiquetas.txt --ep EPxxx --solo-speaker MARÍA

# Probar un bloque antes de gastar créditos
python generar_episodio_v2.py --guion EPxxx_guion_etiquetas.txt --ep EPxxx --solo-bloque 1
```
