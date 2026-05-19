# Runbook — Pipeline v7 con €14 de budget

## El plan acordado

1. **Smoke test x 3 iteraciones** (mismo plan repetido 3 veces) → valida que v7 no rompe nada **Y** mide el ahorro real del caching.
2. **Si OK** → **Producción**: 6 M + 11 T + 8 S = **25 episodios**, todos guardados en `Output_v6/`.

Todo bajo budget cap (`--budget-usd 14`): el script aborta automáticamente si se acerca al límite.

## Coste estimado total: ~$2.85 de $15.20 (~22% del crédito)

| Fase | Eps | Coste estimado | Acumulado |
|------|-----|----------------|-----------|
| Smoke iter 1 (cold) | 11 | $0.50 | $0.50 |
| Smoke iter 2 (warm) | 11 | $0.25 | $0.75 |
| Smoke iter 3 (warm) | 11 | $0.25 | $1.00 |
| Producción | 25 | $1.85 | $2.85 |

Deja **~$12 / €11 de margen** para repetir, regenerar episodios fallidos, o continuar producción.

## Episodios del plan

### Smoke (2 M + 4 T + 5 S, x3 iter)
```
M:  M0  M3
T:  M0_T1  M0_T2  M10_T1  M10_T5
S:  RAG  Fine-tuning  Agentic AI  Hallucination  Golden dataset
```

### Producción (6 M + 11 T + 8 S)
```
M:  M0  M1  M2  M3  M4  M5

T:  M0_T1  M0_T2  M0_T3
    M1_T1  M1_T2  M1_T3
    M2_T1  M2_T2
    M3_T1
    M4_T1
    M5_T1

S:  RAG (S1)  Fine-tuning (S2)  Embedding (S3)  Agentic AI (S4)
    Chain-of-Thought (S5)  Hallucination (S6)  RLHF (S7)  Golden dataset (S8)
```

## Comandos paso a paso

### 0) Pre-flight (sin gastar API)

```bash
# Valida entorno + PDFs + glosario + estimación de coste
python scripts/smoke_test_v7.py --check --plan smoke --iteraciones 3 --budget-usd 14
python scripts/smoke_test_v7.py --check --plan produccion --budget-usd 14
```

Si reporta "Falta ANTHROPIC_API_KEY", añádela al `.env` de la raíz o exporta:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### 1) Smoke x3 iteraciones (~$1.00)

```bash
python scripts/smoke_test_v7.py --run --plan smoke --iteraciones 3 --budget-usd 14
```

**Qué mirar en el reporte `docs/smoke_v7_iter3_*.md`:**

- **Tabla "Evolución por iteración"**: cache hit % debe subir de ~0% (iter 1) a ≥70% (iter 2-3). Coste medio debe bajar ≥40% entre iter 1 y iter 3.
- **Pass-first rate**: si ≥60% el sistema está sano. Si <40% revisar `top_hard` para ver qué regla regresiona.
- **Cualquier episodio "BLOQUEADO"**: indica que tras 3 retries no pasó validación. Si pasan varios, posible regresión de prompts v7.

**Criterio de continuación a producción:**

✅ Continúa si en la iter 3 ves:
- cache_hit_rate_global ≥ 70%
- pass_first_rate ≥ 50%
- coste medio iter 3 ≤ 60% del coste medio iter 1
- ningún tipo (M/T/S) con bloqueo total

❌ Para y revisa si:
- pass_first_rate < 30% en algún tipo → probable regresión de prompts v7
- cache_hit_rate < 30% en iter 2-3 → el cache no se está aplicando (revisar logs de WARNING)

### 2) Producción (~$1.85)

```bash
python scripts/smoke_test_v7.py --run --plan produccion --budget-usd 14
```

Los 25 guiones se guardan en:
```
Output_v6/M/M0.txt   M1.txt   M2.txt   M3.txt   M4.txt   M5.txt
Output_v6/T/M0_T1.txt   M0_T2.txt   M0_T3.txt   M1_T1.txt  ...
Output_v6/S/S1_RAG.txt   S2_Fine_tuning.txt   ...
```

Si el budget se acerca al límite (~$14), el script aborta y deja un reporte parcial.

### 3) Regenerar episodios bloqueados (opcional)

Si algún episodio queda bloqueado, lo puedes regenerar individualmente:

```bash
# Solo M (si fue M1 el problema):
python scripts/smoke_test_v7.py --run --plan produccion --solo M --budget-usd 14
```

(O editar `PROD_M`/`PROD_T`/`PROD_S` en `scripts/smoke_test_v7.py` para correr solo los que faltan.)

## Qué generan los runs

Por cada `--run`:

| Artefacto | Ruta |
|-----------|------|
| Guiones finales | `Output_v6/<M\|T\|S>/<episode_id>[_iterN].txt` |
| Reporte humano | `docs/<plan>_v7_iter<N>_<timestamp>.md` |
| Datos crudos | `docs/<plan>_v7_iter<N>_<timestamp>.json` |
| CSV de costes acumulados | `costes_generacion.log` (raíz, formato v2) |
| Trace daylog | `logs/run/<id>/` |
| Cache pre_writing | `episodios/cache/pre_writing/<hash>.json` |

## Salvaguardas anti-gasto

El script aborta si:

1. **Pre-flight detecta `ANTHROPIC_API_KEY` ausente** → no llega a hacer ninguna llamada.
2. **Estimación previa al run supera `--budget-usd`** → para antes de empezar.
3. **Coste acumulado supera `--budget-usd`** durante la ejecución → corta el bucle y deja reporte parcial.

`--budget-usd 14` es el valor por defecto efectivo; ajústalo a un valor menor si quieres ser aún más conservador (ej. `--budget-usd 5` para limitarte a un cuarto del crédito).

## Si algo va mal: rollback rápido

**Si TODOS los M o T quedan bloqueados** (regresión de prompts v7):

```python
# En generadores/t_generator.py — usar la versión v6 conservada:
SYSTEM_PROMPT = SYSTEM_PROMPT_V6_LEGACY
```

Para M y S, hacer revert al commit anterior al refactor v7:
```bash
git log --oneline generadores/m_generator.py | head
git checkout <commit_pre_v7> -- generadores/m_generator.py generadores/s_generator.py
```

El resto del sistema (caching, retries, patch retry) sigue funcionando con prompts v6.

## Después de los runs

- Revisa los guiones en `Output_v6/` (calidad cualitativa).
- Compara `Output_v6/M/M0.txt` (iter 1, smoke) con `Output_v6/M/M0_iter2.txt` y `_iter3.txt` → mide consistencia entre runs del mismo episodio con cache caliente.
- El JSON del último run sirve de input para `scripts/ab_test_prompts.py` si más adelante quieres comparar v6 vs v7 con eval humana.
