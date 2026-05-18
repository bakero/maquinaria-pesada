# Output_v6_aprobados — 30 episodios

Generados con el pipeline v6 + optimizaciones v7 (prompt caching TTL 1h,
retries reducidos, patch retry con Haiku, retry hints granulares,
catálogo empresas ampliado +60%).

## Inventario

- **M (6/6)**: M0, M1, M2, M3, M4, M5
- **T (13/13)**: M0_T1, M0_T2, M0_T3, M10_T1, M10_T5, M1_T1, M1_T2, M1_T3,
  M2_T1, M2_T2, M3_T1, M4_T1, M5_T1
- **S (11/11)**: S1_RAG, S2_Fine_tuning, S3_Agentic_AI, S3_Embedding,
  S4_Agentic_AI, S4_Hallucination, S5_Chain_of_Thought, S5_Golden_dataset,
  S6_Hallucination, S7_RLHF, S8_Golden_dataset

## Aceptados manualmente (3 episodios, hard fail editorialmente irrelevante)

Estos 3 episodios el validator marcó como bloqueados por reglas demasiado
estrictas. Tras inspección editorial, son **perfectamente locutables** y se
aceptaron sin regenerar:

| Episodio | Regla que falla | Distancia al límite | Razón de aceptación |
|---|---|---|---|
| **M/M3** | `m_leader_destacado` | Yago 66% — 1pp del techo 65% | Diferencia de 1 punto, imperceptible al oído |
| **T/M10_T5** | `audio_rule_reaction_length` | Una reacción >22 palabras | Pregunta con contexto narrativo válido |
| **T/M1_T2** | `audio_rule_reaction_length` | Una reacción >22 palabras | Idem |

Si quieres re-validarlos en el futuro, suben de `revisar` a `aprobados` con
una micro-tolerancia adicional (ej. `reaction_word_limit` a 25, o
`LEADER_SHARE_DESTACADO_BAND` a (0.34, 0.66)).

## Resumen de coste

Sesión completa para llegar a 30/30: **~$7.18 / €6.60** de los **€14** de
crédito Anthropic. Quedan **~€7.40** disponibles.

## Reproducir

```bash
python scripts/smoke_test_v7.py --run --plan produccion --budget-usd 14
```

(Tras los ajustes acumulados en M/T/S prompts y validators, una nueva tanda
debería arrojar tasas similares — ~85-95% al primer pase y 100% tras
1 round de regeneración selectiva.)
