# Auditoría de system prompts — pre-Fase 3 (v6 → v7)

Taxonomía aplicada a cada regla:

- **A** Negación pura ("NO uses X")
- **B** Meta-regla de proceso ("Antes de escribir, identifica...")
- **C** Verificable programáticamente (ya cubierta por el validator)
- **D** Redundante con el user prompt o con otra regla
- **E** Vaga / estilística
- **Núcleo** Irreducible (frases canónicas literales, contrato de formato)

## `m_generator.SYSTEM_PROMPT` (v6 — 24 reglas + checklist)

| # | Regla (resumen) | Cat. | Acción v7 |
|---|---|---|---|
| 1 | Estructura en orden EXACTO de secciones | Núcleo | Mantener en `<output_contract><structure>` |
| 2 | Word count 2700-3300 (duro 2400-3680) | C + Núcleo | Mantener cifra; eliminar instrucción "si te quedas corto AÑADE" (va a `<remediation>`) |
| 3 | HOOK cierra con frase canónica | Núcleo | A `<canonical_phrases>` |
| 4 | SALUDO 3 intervenciones separadas + aviso IA | Núcleo + C | Mantener; `saludo_format` ya valida |
| 5 | Apertura por paridad | Núcleo | Mantener (parámetro variable, va al user prompt) |
| 6-8 | Speaker balance por bloque (PANORAMA / DESTACADO / APLICACION) | C | Validator-only; en prompt solo el rango target |
| 9 | BLOQUE_FUENTES 3-4 con año | Núcleo + C | Mantener; validator cuenta años |
| 10 | CIERRE_CONCEPTOS 3-5 intervenciones, 1ª combinada | Núcleo | Mantener (es contraintuitivo, hay que decirlo) |
| 11 | CIERRE_FINAL frase literal | Núcleo | A `<canonical_phrases>` |
| 12 | CIERRE_CONCEPTOS abre con frase literal | Núcleo | A `<canonical_phrases>` |
| 13 | BLOQUE_FUENTES 3-4 años distintos (duplica 9) | D | Eliminar (consolidar con 9) |
| 14 | APLICACION_PRACTICA reparto detallado | C + B | Validator-only; el detalle de palabras lo gestiona retry hint |
| 15 | BLOQUE_DESTACADO 40-60% | C | Validator-only |
| 16 | CIERRE_CONCEPTOS 3-5 (duplica 10) | D | Eliminar |
| 17 | Sin interjecciones coro, sin apellidos | C | Validator-only |
| 18 | Tags TTS lista cerrada | Núcleo | A `<tts_tags>` |
| 19 | Reglas TTS críticas (frases ≤32, ping-pong, reacciones ≤15) | C | Validator-only (audio_rules) |
| 20 | Números en palabras | C | Validator-only + post-process num2words |
| 21 | Aplicación NO en HOOK | E | Eliminar (vaga) |
| 22 | HOOK cierre canónico (duplica 3) | D | Eliminar |
| 23 | Aviso IA palabras literales | Núcleo + C | Mantener; ya valida `saludo_format` |
| 24 | PRE-CIERRE checklist 14 puntos | B | A `<process><scratchpad>` (1 sola entrada) |

**Total**: 24 → 11 reglas + 4 secciones canónicas + 1 process. Tokens del system: ~3 500 → objetivo ≤ 2 000.

## `t_generator.SYSTEM_PROMPT` (v6 — 25 reglas)

Patrón equivalente a M. Diferencias:
- BLOQUE_FUENTES exacto 3 (no 3-4)
- CIERRE_CONCEPTOS exacto 3
- Aviso IA 30-50 palabras
- Añade `<patrones_limites>` con la lista semántica obligatoria ("no es", "no debe confundirse", "el error común es", "cuando no")

## `s_generator.SYSTEM_PROMPT` (v6 — 11 reglas)

| # | Regla | Cat. | Acción |
|---|---|---|---|
| 1 | Una voz, sin diálogo | Núcleo | `<output_contract>` |
| 2 | Word count 157-198 | Núcleo + C | Mantener |
| 3 | Estructura interna 4 momentos | E | A `<structure>` simplificado |
| 4 | HOOK 3 plantillas (H1/H2/H3) | Núcleo | `<hook_template>` con anchors |
| 5 | Cierre canónico literal | Núcleo | `<canonical_closing>` |
| 6 | Lista de prohibiciones (tags, URLs, citas, etc.) | A → invertir | Mover a `<prohibitions>` agrupada |
| 7 | MaquinarIA solo en cierre | Núcleo | Mantener |
| 8 | Aviso IA no se narra | Núcleo | Mantener |
| 9 | Una idea técnica | E | Eliminar (vaga) |
| 10 | Frases ≤28 palabras | C | Validator-only |
| 11 | Cuenta antes de devolver | B | A `<process>` |

**Reducción objetivo**: 11 → 4-5 hard rules + 3 anchors. Tokens: ~700 → ≤ 600 (no aplica caching; ya está en Haiku).

## Notas para la implementación

- Los XML tags (`<role>`, `<output_contract>`, etc.) son convención semántica del prompt, no XML estructural que el modelo deba renderear. Claude trata bien los tags como bloques cognitivos.
- Las frases canónicas SE MANTIENEN LITERALES — siguen siendo el principal gancho de validación.
- El `<scratchpad>` interno del Process puede aumentar levemente el output tokens, pero al ser de uso interno se descarta antes del guion.
- Pre-flight del refactor: comparar con [test_specialists.py](../tests/generadores/test_specialists.py) que NO ata el contenido literal del prompt (solo build_user_prompt / build_system_blocks).
