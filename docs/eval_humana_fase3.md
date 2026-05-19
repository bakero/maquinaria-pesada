# Eval humana — Refactor de system prompts (Fase 3, v6 → v7)

## Procedimiento

1. Ejecutar `python scripts/ab_test_prompts.py` con al menos 7 episodios de cada formato (7 M + 7 T + 6 S). Genera 1 reporte MD + 1 JSON con los guiones crudos.
2. Reservar 30-45 min de evaluador para una pasada ciega: cada episodio se puntúa de 0 a 100 en 4 ejes (sin saber si es v6 o v7).
3. Mezclar v6 y v7 en orden aleatorio para evitar sesgo de orden.

## Ejes de puntuación (0-100 cada uno)

- **Naturalidad del diálogo** (0 = leído / artificial; 100 = conversación real entre dos profesionales).
- **Densidad informativa** (0 = redundante / vacío; 100 = cada minuto aporta dato o concepto nuevo).
- **Engagement** (0 = se desconecta a los 30s; 100 = HOOK arrastra + cierre satisface).
- **Coherencia estructural** (0 = saltos lógicos / contradicciones; 100 = construcción limpia bloque a bloque).

Media = promedio aritmético de los 4 ejes.

## Threshold de merge

- **Merge directo** si v7 ≥ v6.
- **Merge condicional** si v7 ∈ [v6 - 8, v6) y el ahorro de tokens del system es ≥ 40% (v7 actual: ≈ 1450 tok vs v6 ≈ 3500 → −58% ✔).
- **Revertir** si v7 < v6 - 8.

## Resultados (a rellenar tras el A/B test)

### Episodios evaluados

| Run | Tipo | Branch | Episodio | Naturalidad | Densidad | Engagement | Coherencia | Media |
|-----|------|--------|----------|-------------|----------|------------|------------|-------|
| 1   | M    |        | M0       |             |          |            |            |       |
| 2   | M    |        | M1       |             |          |            |            |       |
| ... |      |        |          |             |          |            |            |       |

### Agregado por rama

| Métrica | v6 (control) | v7 (refactor) | Δ |
|---|---|---|---|
| Naturalidad | | | |
| Densidad | | | |
| Engagement | | | |
| Coherencia | | | |
| **Media global** | | | |

### Decisión

- [ ] Merge directo
- [ ] Merge condicional (ahorro tokens compensa)
- [ ] Revertir y rediseñar

## Notas cualitativas

(Anotar patrones observados: tipos de regresión / mejora, sesgos, surpresas.)
