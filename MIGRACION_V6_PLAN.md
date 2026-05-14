# Migración v6 — Plan de batalla

Plan ejecutable para la migración v6 del sistema de generación de episodios de
**MaquinarIA Pesada**. Consolida las 18 decisiones cerradas en la sesión de
diseño y las organiza en 10 fases con 42 pasos para ejecución incremental.

- **Versión del plan:** v6 · 2026-05-14
- **Branch de trabajo:** `feature/v6-migration`
- **Branch de archivo (estado pre-v6 congelado):** `archive/pre-v6-migration`
- **Regla de oro:** una fase = un bloque revisable. No delegar las 10 fases de
  golpe. Cada paso de código pasa `ruff` + `pytest` antes de merge.

---

## 0. Resumen ejecutivo de la migración

El sistema pasa de **2 formatos** (M, T) con specs v5 a **3 formatos** (M, T, S)
con specs v6, arquitectura de validadores/generadores refactorizada
(`base + 3 especialistas`), tests unitarios obligatorios (cobertura ≥85%) y
borrón limpio de los episodios actuales (ninguno publicado).

| Formato | Antes (v5) | Después (v6) |
|---|---|---|
| **M** (Módulo) | 17-19 min · 3 bloques · 2100-2600 palabras | **18-22 min · 4 bloques de contenido · 2700-3300 palabras** |
| **T** (Tema) | 10-13 min · 3 bloques · 1400-1850 palabras | **25-28 min · 6 bloques de contenido · 3700-4500 palabras** |
| **S** (Short) | — no existía — | **60-90s · 4 bloques internos · 157-198 palabras · 1 sola voz** |

---

## 1. Decisiones cerradas (las 18)

### Bloque A — Alineación M/T

**A1. Duraciones invertidas y ampliadas.**
- M: **18-22 min**, 2700-3300 palabras (meta-producto: módulo + aplicación al
  sistema generador; motor de la estrategia LinkedIn).
- T: **25-28 min**, 3700-4500 palabras (contenido puro: tema del máster +
  ejemplos + aplicación empresarial).

**A2. Estructura T = 6 bloques de contenido** (escala por más bloques, no por
bloques más largos):
`PANORAMA + COMO + CASOS + LIMITES + FUENTES` (+ HOOK, INTRO_SONIDO, SALUDO,
CIERRE_CONCEPTOS, CIERRE_FINAL, VERIFICACIONES).
- `BLOQUE_CASOS` (nuevo, reemplaza/expande REALIDAD): 4-5 min, Maria ≥60%,
  casos empresariales con nombre propio.
- `BLOQUE_LIMITES` (recuperado de v1): 3-4 min, Yago ≥55%, "qué NO es / cuándo
  no usarlo".
- `BLOQUE_FUENTES` (nuevo): 2-3 min, las 3 fuentes que más importan del tema.

**A3. Estructura M = 4 bloques de contenido:**
`PANORAMA + DESTACADO + APLICACION_PRACTICA + FUENTES`.
- `BLOQUE_FUENTES` (nuevo): 2-3 min, **3-4 fuentes-marco del módulo entero**
  (Variante A), leídas de `PDFs/auxiliares/fuentes_marco_modulo_M{n}.md`
  (fichero por módulo, obligatorio). Distintas de las fuentes de los T.
- M **no** lleva `BLOQUE_LIMITES` (sigue siendo territorio del T).
- `CIERRE_CONCEPTOS` en M: 3-5 conceptos (T mantiene exactamente 3).

**A4. Invariante de diseño — calidad TTS sintética.** Los episodios se generan
con voces de IA: no valen los parámetros de un podcast humano. Cuadro de
invariantes que **debe ir al spec y al validador** (ver §2).

### Bloque B — Diseño del formato S

**B1. Fuente de S = `glosario_unificado.md` como fuente única.** Cada entrada
del glosario tiene definición canónica + línea `**Fuentes:**` programática.
Sin lectura de PDFs adicionales.

**B2. Selección automática de qué términos son S.** Filtro 100% automático,
sin override manual: una entrada es candidata a S si cumple **al menos uno**:
- aparece en **≥2 módulos distintos** (transversal), o
- tiene **≥4 menciones** totales en el corpus, o
- aparece en algún `_RESUMEN` (concepto-marco del módulo).

**B3. Ordenación automática (orden de publicación).** Score puro, cero
intervención humana:
`score = (transversalidad × 3) + min(densidad, 20) + (5 si aparece en RESUMEN)`.
Desempate: transversalidad > densidad > orden alfabético del nombre canónico.

**B4. Numeración y voz.** Se añade una línea `**S:** N` a cada entrada del
glosario seleccionada, donde **N es el número de orden de publicación**.
- Nomenclatura de archivo: `S{N}_nombre.mp3`.
- Voz por paridad del número S: **impar → Yago, par → Maria**.
- El número S es editable a mano en el glosario para controlar qué se publica
  primero (gancho), pero el **automatismo** lo asigna por defecto según B3.

**B5. Script `seleccionar_y_ordenar_shorts.py`** — idempotente y estable:
- ejecutar dos veces sobre el mismo glosario da el mismo resultado;
- añadir términos nuevos no reordena los existentes (se añaden al final);
- escribe `**S:** N` en el glosario y un reporte `glosario_shorts_ranking.md`.

**B6. Estructura interna de S = 4 bloques** (objetivo 75s):
`HOOK 5-7s + DEFINICIÓN 18-22s + EJEMPLO 28-35s + APLICACIÓN/GANCHO 12-18s`.
- 3 plantillas de HOOK: H1 contradicción / H2 número / H3 pregunta.
- Reglas duras S: voz única (sin diálogo), **cero etiquetas TTS de tono**, no
  URLs ni citas de papers en narración, cierre canónico obligatorio, marca
  "MaquinarIA Pesada" solo en el cierre.
- Cierre canónico literal: `Más sobre [tema] en el episodio T de MaquinarIA Pesada.`
- Aviso de IA: **no narrado**; va en la descripción del vídeo + texto en
  pantalla durante el primer segundo.

**B7. Parámetros TTS de S** (distintos de M/T):
`stability 0.78 · similarity_boost 0.70/0.60 · speed 1.10 · post_speed_multiplier 1.00 · total 1.10×`.
Loudness `-14 LUFS` integrated, `-1 dBTP`.
- **Cambio derivado:** aplicar `-14 LUFS` también a M y T (hoy usan `-16 dBFS`,
  no cumple el estándar Spotify).

**B8. Validaciones de S:** 12 hard-fail + 5 soft-warn + 3 post-TTS + 3 de
archivo = 23 validaciones (detalle en `PODCAST_S_SPEC.md`).

### Bloque C — Arquitectura de validaciones y generadores

**C1. Validadores: base + 3 especialistas.**
`validators/base_validator.py` (reglas comunes) + `m_validator.py` +
`t_validator.py` + `s_validator.py`. Implementación por **composición** (no
herencia): módulos en `validators/shared/`.

**C2. Output estructurado.** Cada validador devuelve `list[ValidationResult]`
con `rule_name`, `severity` (`HARD`|`SOFT`), `passed`, `message`, `context`.

**C3. Eliminar legacy en la migración.** `podcast_spec.py` y
`generar_episodio_v2.py` se eliminan en la propia migración (no se mantiene
modo legacy). Borrón limpio: ningún episodio actual está publicado.

**C4. Generadores: misma arquitectura que validadores.**
`generadores/base_generator.py` + `m_generator.py` + `t_generator.py` +
`s_generator.py` + `generadores/shared/`.

**C5. Modelo LLM por formato.** M y T → `claude-sonnet-4-5`. S →
`claude-haiku-4-5-20251001` (texto corto, plantilla rígida, ~12× más barato).

**C6. Política de retry en hard-fail.** Retry **1 vez con feedback explícito**
al LLM ("el guion anterior falló por X, corrígelo manteniendo Y"). Si falla el
retry, aborta y registra para revisión.

**C7. Tracking de coste obligatorio.** `costes_generacion.log` (CSV):
`timestamp, tipo, episode_id, model, input_tokens, output_tokens, cost_usd, validation_result`.

**C8. `pronunciation_overrides.json` — generación híbrida.** 1ª versión
automática desde el glosario (entradas con sigla entre paréntesis) + añadidos
manuales obvios (PyTorch, Hugging Face, GPT-4, Claude). Capa pre-TTS.

**C9. Tests unitarios obligatorios, cobertura ≥85%.** Sin tests no hay merge.
- Framework: `pytest` + `pytest-cov` con `--cov-fail-under=85`.
- Mocks obligatorios para Anthropic API y ElevenLabs (tests no llaman APIs
  reales; los de integración van marcados `@pytest.mark.integration`).
- GitHub Actions: workflow que ejecuta tests + cobertura y bloquea merge.
- Tests específicos obligatorios para `seleccionar_y_ordenar_shorts.py`:
  idempotencia, estabilidad, correctitud del filtro, correctitud del score,
  desempate.

### Bloque D — Plan de migración

**D1. Borrón limpio.** Ningún guion/episodio actual está publicado: se borran.
La spec v6 es la única spec; los validadores no necesitan modo legacy.

**D2. Qué se borra / qué se mantiene** (ver tabla §5).

**D3. Backup.** Branch `archive/pre-v6-migration` con el estado actual
congelado **antes** de cualquier borrado. (Ya creado en Fase 0.)

**D4. Orden: migrar primero, borrar después.** Todo el código v6 + tests +
specs se construye y valida (generando 1 episodio de prueba) **antes** de
borrar `episodios/`.

**D5. Re-producción módulo por módulo.** Tras la migración: M0 + sus T como
unidad coherente, después M1 + sus T, etc. Los S se producen en paralelo
(dependen solo del glosario).

---

## 2. Invariante de diseño: calidad TTS sintética

Estos parámetros condicionan toda especificación de bloque/intervención y
**deben estar en el spec y en el validador**. Algunos ya existen (anti-pingpong,
lista negra, longitud mínima); otros son nuevos.

| Parámetro | Regla TTS sintética | Razón |
|---|---|---|
| Longitud intervención máxima | 40-60s seguidos del mismo speaker (≤200 palabras, zona óptima 60-120) | Sin variación natural, el oyente desconecta |
| Muletillas | Cero muletillas no escriptadas | El TTS las pronuncia raras |
| Frases cortas seguidas | Máximo 2-3 frases <12 palabras seguidas del mismo speaker | Suenan robóticas (ping-pong mecánico) |
| Frases largas | Máximo 28-32 palabras por frase | Sin respiración natural, se atropellan |
| Densidad conceptual | 1 concepto técnico nuevo cada 30-40s, máx. 2 tecnicismos seguidos sin aterrizaje | Sin glosa natural el oyente se pierde |
| Cambio de speaker | Pausa 400-600ms obligatoria | Sin pausa suena cortado |
| Pausa intra-bloque | Cada 60-90s, pausa 300-500ms explícita (SSML) | Sin SSML el audio se atropella |
| Variación entonativa | Limitada → se compensa con cambio de speaker (M/T) o con plantilla visual + captions + música (S) | El TTS plano cansa rápido |

**Pausas SSML explícitas que faltan en el sistema actual (añadir en v6):**
- Entre bloques: 800-1200ms
- Entre subtemas dentro de bloque: 400-600ms
- Al final del HOOK: 600ms
- Antes y después del aviso de IA: 400ms

---

## 3. Cuadro consolidado de reglas

### A. Reglas vigentes sin cambios (aplican a M, T y S salvo nota)

- **A.1** Lista negra de 8 interjecciones (anti-NotebookLM). Hard-fail.
- **A.2** Aviso de generación por IA en SALUDO_Y_PRESENTACION (M y T; en S va
  en descripción + texto en pantalla, no narrado). Palabras clave obligatorias
  "sistema automatico" + "puede contener errores". Hard-fail si falta.
- **A.3** Apertura por paridad: M por nº de módulo, T por nº de tema, S por nº
  de orden de publicación.
- **A.4** SALUDO_Y_PRESENTACION en mínimo 3 intervenciones (M y T).
- **A.5** Prohibición de apellidos inventados (regex). Hard-fail.
- **A.6** Frases de cierre canónicas (HOOK, CIERRE_CONCEPTOS, CIERRE_FINAL en
  M/T; cierre propio en S).
- **A.7** Audio-Reglas 1-5 (números en palabras, longitud TTS-óptima, tags como
  guía de estilo, tecnicismos acelerados, INTRO_SONIDO documental).
- **A.8** Etiquetas TTS: una por intervención, al inicio, lista cerrada
  (prohibidas en S).
- **A.9** Tecnicismos: aterrizar en la misma intervención.
- **A.10** Referencias temporales: prohibido 2024/2025 como presente sin
  etiqueta de publicación. Hard-warn.
- **A.11** Cobertura de fuente ≥75% (M y T; S no aplica, fuente es el glosario).
- **A.12** Pre-escritura obligatoria (M y T; S no, el glosario ya es la
  pre-escritura).
- **A.13** Anti-pingpong: apoyo máximo 1 cada 3 intervenciones del líder.
  Soft-warn.
- **A.14** Validación de audio post-generación (bloques completos, MP3 abrible,
  duración fuera de rango = soft-warn).
- **A.15** Parámetros TTS ElevenLabs (eleven_v3; M/T speed 1.20 +
  post_speed_multiplier 1.10 = 1.32×; S según B7).

### B. Reglas que cambian con v6

- **B.1** Word count: M 2700-3300, T 3700-4500, S 157-198.
- **B.2** Bloques de contenido: M 4, T 6, S 4 internos.
- **B.3** Duración interna de cada bloque recalculada (ver specs).
- **B.4** `CIERRE_CONCEPTOS`: M 3-5, T exactamente 3, S no tiene.
- **B.5** Aviso de IA: M enganche 18-25s, T advertencia 12-18s, S no narrado.
- **B.6** HOOK: M/T 30-60s, S 5-7s.

### C. Reglas/decisiones nuevas que faltan y hay que añadir

- **C.1** Spec completa de S (`PODCAST_S_SPEC.md`).
- **C.2** Pausas SSML explícitas (ver §2).
- **C.3** `pronunciation_overrides.json` (anglicismos) — capa pre-TTS.
- **C.4** Conversión de números >100 a palabras (`num2words`).
- **C.5** Loudness normalization a -14 LUFS (M, T y S).
- **C.6** Bloques nuevos de T: CASOS, LIMITES, FUENTES (función, líder,
  palabras min/max, validador propio).
- **C.7** Estructura de M con BLOQUE_FUENTES + fichero `fuentes_marco_modulo_M{n}.md`.
- **C.8** Validador unificado: base + 3 especialistas por composición.

### D. Decisiones operativas vigentes

- **D.1** Todo cambio en generación → check correspondiente en validación.
  Ampliado en v6: todo cambio en `validators/` o `generadores/` → tests
  unitarios obligatorios antes de merge.
- **D.2** Sesión en feature branch, consolidar en master cuando funciona.
- **D.3** Separación hard/soft en validación de guion.
- **D.4** `HARD_KEYWORDS` para abortar generación — ajustar al nuevo número de
  bloques de cada formato.

---

## 4. Arquitectura de ficheros objetivo

```
maquinaria_pesada/
├── PODCAST_M_SPEC.md          (v6 — actualizado)
├── PODCAST_T_SPEC.md          (v6 — actualizado)
├── PODCAST_S_SPEC.md          (NUEVO)
├── MIGRACION_V6_PLAN.md       (este documento)
│
├── validators/                (NUEVO)
│   ├── __init__.py
│   ├── base_validator.py
│   ├── m_validator.py
│   ├── t_validator.py
│   ├── s_validator.py
│   └── shared/
│       ├── blacklist.py
│       ├── audio_rules.py
│       ├── parity.py
│       ├── canonical_phrases.py
│       └── tts_validator.py
│
├── generadores/               (NUEVO)
│   ├── __init__.py
│   ├── base_generator.py
│   ├── m_generator.py
│   ├── t_generator.py
│   ├── s_generator.py
│   └── shared/
│       ├── anthropic_client.py
│       ├── pdf_reader.py
│       ├── pre_writing.py
│       ├── fuentes_loader.py
│       ├── ficha_aplicacion.py
│       ├── pronunciation_overrides.py
│       └── num2words_es.py
│
├── scripts/
│   └── seleccionar_y_ordenar_shorts.py   (NUEVO)
│
├── tests/
│   ├── conftest.py
│   ├── fixtures/{m,t,s,shared}/
│   ├── validators/
│   ├── generators/
│   ├── integration/
│   └── scripts/
│
├── PDFs/auxiliares/
│   ├── glosario_unificado.md             (+ línea **S:** N por entrada)
│   ├── glosario_shorts_ranking.md         (NUEVO — generado)
│   └── fuentes_marco_modulo_M{n}.md       (NUEVO — uno por módulo)
│
├── pronunciation_overrides.json           (NUEVO)
├── costes_generacion.log                  (NUEVO — generado)
│
├── podcast_spec.py            (ELIMINAR en migración)
└── generar_episodio_v2.py     (ELIMINAR en migración — montar_audio se
                                reimplementa en la fase de audio del nuevo
                                pipeline, incl. la optimización de RAM y el
                                soporte de -14 LUFS / SSML)
```

---

## 5. Borrado: qué se borra y qué se mantiene

| Artefacto | Acción | Justificación |
|---|---|---|
| `episodios/M{n}_*.mp3` | **Borrar** | Audios obsoletos |
| `Guiones/M{n}_*.md` (y `.txt`) | **Borrar** | Guiones con spec antigua |
| `episodios/temp/aplicacion_extraida_M{n}.md` | **Borrar** | Fichas obsoletas |
| `episodios/*_cmd.log`, `produccion_runs.log` | **Borrar / archivar** | Logs obsoletos |
| `Videos/M{n}_*.mp4` | **Borrar** si hay | Videopodcast obsoleto |
| `PDFs/resumenes/`, `PDFs/temas/` | **Mantener** | Inputs del máster |
| `PDFs/auxiliares/glosario_unificado.md` | **Mantener + actualizar** con `**S:** N` |
| `PDFs/aplicacion_practica/M{n}.md` | **Mantener** si existen | Overrides manuales |
| `PDFs/auxiliares/fuentes_marco_modulo_M{n}.md` | **Crear** | Inputs nuevos requeridos |
| `BIBLIA_SISTEMA.md`, `PRIMERPODCAST.md`, `VIDEOPODCAST.md`, `PODCAST.md` | **Mantener** | Documentos vivos |
| `PODCAST_*_SPEC.md` | **Mantener y actualizar a v6** | Documentación normativa |
| `podcast_spec.py`, `generar_episodio_v2.py`, `validar_episodio.py` | **Mantener hasta la migración**, luego reemplazar | Se sustituyen durante la migración |

Backup previo: `archive/pre-v6-migration` (rama de archivo).

---

## 6. Plan de fases (10 fases, 42 pasos)

Cada paso de código es un commit. Cada commit pasa `ruff` + `pytest` antes de
merge. **No avanzar de fase sin revisión.**

### Fase 0 — Preparación (sin código nuevo)
1. Crear branch `feature/v6-migration` desde master. ✅
2. Crear branch `archive/pre-v6-migration` con el estado actual congelado. ✅
3. Actualizar `PODCAST_M_SPEC.md` a v6.
4. Actualizar `PODCAST_T_SPEC.md` a v6.
5. Crear `PODCAST_S_SPEC.md` desde cero.
6. Crear entrada de sesión en `PODCAST.md` documentando la migración v6.

### Fase 1 — Infraestructura compartida de validadores
7. Crear estructura `validators/shared/` con módulos e interfaces vacías.
8. Implementar `validators/shared/blacklist.py` + tests.
9. Implementar `validators/shared/audio_rules.py` + tests (5 reglas audio).
10. Implementar `validators/shared/parity.py` + tests.
11. Implementar `validators/shared/canonical_phrases.py` + tests.
12. Implementar `validators/shared/tts_validator.py` + tests.

### Fase 2 — Validador base
13. Implementar `validators/base_validator.py` (composición de `shared/`) + tests.

### Fase 3 — Validadores específicos
14. Implementar `validators/m_validator.py` + tests (incl. BLOQUE_FUENTES).
15. Implementar `validators/t_validator.py` + tests (incl. CASOS, LIMITES, FUENTES).
16. Implementar `validators/s_validator.py` + tests (23 validaciones).

### Fase 4 — Infraestructura de generadores
17. Crear estructura `generadores/shared/`.
18. Implementar `generadores/shared/anthropic_client.py` + tests con mocks.
19. Implementar `generadores/shared/pdf_reader.py` + tests.
20. Implementar `generadores/shared/pre_writing.py` + tests.
21. Implementar `generadores/shared/fuentes_loader.py` + tests.
22. Implementar `generadores/shared/ficha_aplicacion.py` + tests (solo M).
23. Implementar `generadores/shared/pronunciation_overrides.py` + JSON inicial
    (híbrido: automático desde glosario + añadidos manuales).
24. Implementar `generadores/shared/num2words_es.py` + tests.

### Fase 5 — Generador base
25. Implementar `generadores/base_generator.py` + tests (incl. inserción de
    pausas SSML y, en la fase de audio, montaje con la optimización de RAM
    heredada de `montar_audio` + normalización -14 LUFS).

### Fase 6 — Generadores específicos
26. Implementar `generadores/m_generator.py` + tests + 1 episodio real (M0).
27. Implementar `generadores/t_generator.py` + tests + 1 episodio real (M0_T1).
28. Implementar `generadores/s_generator.py` + tests + 3 Shorts reales (S1-S3).

### Fase 7 — Selector/ordenador de Shorts
29. Implementar `scripts/seleccionar_y_ordenar_shorts.py` + 5 tests críticos
    (idempotencia, estabilidad, filtro, score, desempate).
30. Ejecutar el script sobre `glosario_unificado.md` real. Verificar
    `glosario_shorts_ranking.md`.

### Fase 8 — Integración con código existente
31. Refactorizar `validar_episodio.py` para usar los nuevos validadores.
32. Refactorizar `lanzar_produccion.py` para soportar tipo M/T/S.
33. Refactorizar el cockpit (`cockpit/`, `web_server.py`, `vite_app/`) para
    mostrar M/T/S separados.
34. Eliminar `podcast_spec.py` legacy.
35. Eliminar `generar_episodio_v2.py` legacy (reemplazado por la cadena
    `m_generator` + fase de audio del `base_generator`).

### Fase 9 — CI/CD
36. Ampliar `.github/workflows/` con job de tests + cobertura ≥85% que bloquea
    merge.
37. (Opcional, recomendado) job de lint.

### Fase 10 — Borrado y producción inicial
38. Borrar artefactos según la tabla §5.
39. Producir M0 + los T del M0 con el nuevo pipeline (módulo 0 completo).
40. Validar audio, descripciones, captions. Iterar si hay problemas.
41. Producir batch inicial S1-S10.
42. Merge `feature/v6-migration` → master.

---

## 7. Notas para quien ejecute la migración

- Leer **siempre** los specs actuales antes de tocar nada. v6 respeta lo que ya
  funciona; solo cambia lo necesario.
- Pasar el plan **fase por fase**, no de golpe. Empezar por la Fase 0 (ya hecha
  salvo pasos 3-6 si quedaran pendientes) y validar antes de seguir.
- Si aparece una decisión no documentada aquí ni en los specs, **parar y
  preguntar**. No improvisar.
- Regla del proyecto vigente y ampliada: todo cambio en generación o validación
  → tests antes de merge; mantener `ruff` + `pytest` verdes (lo aplica el hook).
- El glosario (`PDFs/auxiliares/glosario_unificado.md`) es input crítico de la
  Fase 1 (validador de S) y la Fase 7 (selector). Debe estar presente.
