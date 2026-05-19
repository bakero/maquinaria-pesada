# Sistema de logs — MaquinarIA Pesada

Toda ejecución de cualquier generador, validador o pipeline de la app deja
traza en una **bitácora diaria centralizada**. Este documento explica el
contrato: dónde se escribe, qué se guarda, cómo se valida, y cómo añadir
logs a un generador nuevo.

> TL;DR — Todo lo que se ejecute en la app debe estar envuelto en
> `with RunLog(...):` y cualquier paso/IA call/retry debe pasar por
> `RunLogger.step|ai_call|retry` para que quede registrado.

---

## 1. Arquitectura

Hay **tres sistemas de logs** complementarios, todos vivos hoy:

| Sistema | Fichero | Qué guarda | Quién lo escribe |
|---------|---------|------------|------------------|
| **Bitácora diaria** | `logs/run/maquinaria_YYYY-MM-DD.log` | Cada ejecución (START/END), pasos, llamadas IA, retries, errores | `daylog.RunLog` + `cockpit.core.log_helpers.RunLogger` |
| **Uso de IA** | `logs/ai_usage.jsonl` | Append-only: por cada llamada Anthropic/OpenAI: tokens in/out, coste estimado, latencia | `cockpit.core.usage_tracker.record()` |
| **Economía** | `logs/economics.json` | Estado mutable: topups, gastos manuales, suscripciones | `cockpit.core.economics.{load,save}()` |

La **bitácora diaria es la fuente de verdad** para "qué ha pasado en la
app". `ai_usage.jsonl` es el detalle financiero/operativo (consumo) y
`economics.json` es el estado contable.

---

## 2. Bitácora diaria (`daylog`)

### 2.1 Ubicación y rotación

- Directorio: `logs/run/` (override con env `DAYLOG_DIR`).
- Un fichero por **día-log**: `maquinaria_YYYY-MM-DD.log`.
- **Frontera a las 05:00 hora local**: una ejecución a las 04:59 cuenta
  para el día anterior; a las 05:00, para el del propio día (`daylog.ROLL_HOUR`).
- Append-only con flush por línea: varios procesos escriben al mismo
  fichero sin coordinarse. Una línea gigante se trunca a 2000 caracteres.

### 2.2 Formato de línea

Texto plano legible, una entrada por línea:

```
2026-05-18T15:30:01 [INFO ] run=a1b2c3 script=generar_guion.py pid=1234 | mensaje k=v k2=v2
```

| Campo | Significado |
|-------|-------------|
| `2026-05-18T15:30:01` | Timestamp local en ISO-8601 (hasta segundos) |
| `[INFO ]` | Nivel (ver tabla siguiente) |
| `run=a1b2c3` | UUID corto (6 chars) de la ejecución; `-` si se escribió fuera de un RunLog |
| `script=...` | Nombre del entrypoint (o módulo) que emitió la línea |
| `pid=1234` | PID del proceso |
| `mensaje k=v` | Cuerpo: texto libre + campos estructurados `k=v` (los valores con espacios van entre comillas) |

### 2.3 Niveles

| Nivel | Cuándo se emite |
|-------|-----------------|
| `START` | `RunLog.__enter__`: marca el inicio de una ejecución, lleva los `params` |
| `END` | `RunLog.__exit__`: cierre con `status=ok|error`, `elapsed_s`, `out_lines`, `err_lines` |
| `INFO` | Paso del pipeline, AI call iniciada, mensaje informativo |
| `WARN` | Reintento (`retry`), aviso recuperable, auto-validate detecta inconsistencias |
| `ERROR` | Fallo capturado o no manejado, AI call que erró |
| `OK` | AI call completada con éxito, paso completado con resultado positivo |
| `OUT` | Línea capturada de `stdout` (espejado de `print()` mientras `RunLog` está activo) |
| `ERR` | Línea capturada de `stderr` |

### 2.4 Auto-validación al cierre

Al salir del context manager, `RunLog.__exit__` invoca a
`cockpit.core.log_validator.validate_after_run(run_id)`. Si detecta
inconsistencias (pasos esperados ausentes, AI calls iniciadas sin OK/ERROR,
etc.), deja líneas extra de `WARN auto-validate: issues` y/o
`INFO auto-validate: warnings` en el mismo día-log. **No bloquea ni rompe
la ejecución**.

Opt-out (tests muy ajustados):

```bash
export DAYLOG_NO_AUTOVALIDATE=1
```

---

## 3. API para los generadores

Hay dos capas:

### 3.1 `daylog.RunLog` — context manager del entrypoint

Cada entrypoint top-level debe envolver su `main()` así:

```python
# generar_guion.py — al final del módulo
if __name__ == "__main__":  # pragma: no cover
    import sys
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="generar_guion.py", params=sys.argv[1:])
    except Exception:
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        sys.exit(main())
```

Esto garantiza:

- Línea `START` con los argumentos.
- Captura automática de `stdout`/`stderr` en `OUT`/`ERR`.
- Línea `END` con `status=ok|error` y `elapsed_s`.
- Auto-validación al cierre.

> El test `tests/test_entrypoints_logged.py` enforcement obliga a que
> **cualquier `.py` con `if __name__ == "__main__"` en el repo (excepto
> ramas excluidas)** importe `daylog` y use `RunLog`. Si añades un nuevo
> entrypoint sin RunLog, los tests fallarán.

### 3.2 `cockpit.core.log_helpers.RunLogger` — logging granular

Dentro de las funciones del generador, usa el helper:

```python
from cockpit.core.log_helpers import get_run_logger

log = get_run_logger("generar_guion")

log.step("extract_concepts", pdf=str(pdf_path))     # INFO con prefijo "paso → "
log.info("conceptos extraídos", count=8)
log.warn("material insuficiente", paragraphs=2)
log.error("validación falló", hard=3)
log.ok("guion guardado", path=str(out))
log.retry(attempt=2, reason="hard_fails", count=4)  # WARN

# Llamada IA (context manager):
with log.ai_call(model="claude-sonnet-4-5",
                 purpose="generate_block",
                 source="generar_guion.py") as call:
    response = client.messages.create(...)
    call.set_tokens(in_=response.usage.input_tokens,
                    out_=response.usage.output_tokens)
    call.set_cost_usd(0.0042)  # opcional
```

Lo que se escribe (resumido):

```
[INFO ] paso → extract_concepts step=extract_concepts pdf=PDFs/RESUMEN_M3.pdf
[INFO ] AI call → generate_block model=claude-sonnet-4-5 purpose=generate_block ...
[OK   ] AI call ok → generate_block model=... ms=4231 tokens_in=1500 tokens_out=800
[WARN ] retry attempt=2 reason=hard_fails count=4
[OK   ] guion guardado path=Guiones/M3.txt tokens_total=2300
```

Sin `RunLog` activo, las líneas se escriben igual con `run=-` (no se pierde
nada; sólo no correlacionan con un run id).

### 3.3 Llamadas IA centralizadas

Para los generadores M y T, **todas** las llamadas pasan por
`guion_common.call_claude`, que ya emite `ai_call` automáticamente. Lo
mismo `cockpit.core.ai_client.improve_with_claude_stream` para la cabina
web, y los dos puntos de `dual_debate.py`.

Si añades una llamada IA nueva, encápsulala en `RunLogger.ai_call` o pásala
por uno de los wrappers existentes para que quede trazada.

---

## 4. Validador (`cockpit.core.log_validator`)

Lee un día-log y, por cada `run_id`, verifica:

- Existe `START` y `END`.
- `status` final es `ok` o `error` (no `None`, no inválido).
- `elapsed_s` ≥ 0.
- No hay AI calls iniciadas sin OK/ERROR.
- (Heurística) los pasos esperados por script aparecen al menos una vez
  (`EXPECTED_STEPS` en `log_validator.py`; falta = warning, no issue).

### 4.1 Uso programático

```python
from cockpit.core import log_validator

# Validar el día-log de hoy
reports = log_validator.validate_day()
for run_id, report in reports.items():
    if not report.ok:
        print(run_id, report.issues)

# Validar un run concreto justo después de cerrar
report = log_validator.validate_after_run(run_log_instance.run_id)
```

### 4.2 Desde la CLI del evaluador

```bash
# Día-log de hoy
python -m evaluador --check-run-log

# Día-log explícito
python -m evaluador --check-run-log 2026-05-18
```

Salida ejemplo:

```
# Validación de día-log · 3 ejecuciones

[OK] run=a1b2c3 script=generar_guion.py status=ok elapsed=42.3s ai=2/2
[OK] run=d4e5f6 script=evaluador status=ok elapsed=1.1s
[ISSUE] run=99aabb script=generar_guion.py status=error elapsed=8.5s ai=1/2(err=1)
   - issue: ejecución terminó en error
   - warn:  pasos esperados ausentes: validate, save
```

Exit code: `0` si todo OK, `1` si algún run tiene issues, `2` si la fecha
es inválida.

### 4.3 Pasos esperados por script

`EXPECTED_STEPS` (`cockpit/core/log_validator.py`) define la lista mínima
de pasos por entrypoint:

| Script | Pasos esperados |
|--------|-----------------|
| `generar_guion.py`, `generar_guion_t.py` | `load_spec`, `extract_concepts`, `generate`, `validate`, `save` |
| `generar_episodio_v2.py` | `load_script`, `audio`, `render` |
| `validar_episodio.py` | `load_script`, `validate` |
| `produce_pending.py` | `scan_pending`, `produce` |
| `lanzar_produccion.py` | `plan`, `produce` |
| `entrenar_v6.py` | `iterate` |
| `dual_debate.py` | `debate` |
| `evaluador/cli.py` | `discover`, `evaluate` |
| `maquinaria_pesada_pipeline/run_pipeline.py` | `plan`, `execute` |

Si añades un generador, actualiza esta tabla y `EXPECTED_STEPS`.

---

## 5. `logs/ai_usage.jsonl`

Append-only de eventos de uso de IA. Cada línea es un JSON con:

```json
{
  "timestamp": "2026-05-18T15:30:01+02:00",
  "kind": "generation",
  "provider": "anthropic",
  "model": "claude-sonnet-4-5",
  "source": "generar_guion.py",
  "input_tokens": 1500,
  "output_tokens": 800,
  "cost_usd": 0.0123,
  "latency_ms": 4231,
  "ok": true,
  "error": null
}
```

Se escribe automáticamente desde:

- `cockpit.core.ai_client.improve_with_claude*` (cabina web).
- `guion_common.call_claude` (vía `cockpit.core.usage_tracker.track_anthropic`).
- `dual_debate.py` (vía `track_openai`).

Las consultas se hacen con `usage_tracker.load_events()`.

---

## 6. Rotación, retención y privacidad

- **Rotación**: 1 fichero por día-log. No hay rotación interna por tamaño.
- **Retención**: no se borra automáticamente. Si quieres limitar tamaño,
  ejecuta una limpieza periódica (`find logs/run -mtime +60 -delete`).
- **Privacidad**: las líneas son texto plano. **No metas claves, tokens de
  API, ni datos personales en `log.info(...)`**: los campos `k=v` se
  serializan tal cual. El cuerpo se trunca a 2000 caracteres por línea.

---

## 7. Cómo añadir logs a un generador nuevo

1. **Engancha a `RunLog`** al final del módulo (ver §3.1). El test
   `tests/test_entrypoints_logged.py` te avisará si lo olvidas.
2. **Importa el helper** dentro de `main()`:
   ```python
   from cockpit.core.log_helpers import get_run_logger
   log = get_run_logger("mi_generador")
   ```
3. **Marca cada paso mayor** con `log.step("nombre_corto")`.
4. **Envuelve cada llamada IA** en `with log.ai_call(...) as call:` y
   anota tokens con `call.set_tokens(in_=..., out_=...)`. Si la llamada
   ya pasa por `guion_common.call_claude` o `ai_client.improve_with_claude_stream`,
   no necesitas hacer nada extra.
5. **Marca retries** con `log.retry(attempt=N, reason="...")`.
6. **Cierra el flujo** con `log.ok("guion guardado", path=...)` (o
   `log.error(...)` si falla).
7. **Añade el script y sus pasos esperados** a `EXPECTED_STEPS` en
   `cockpit/core/log_validator.py` para que la auto-validación lo cubra.
8. **Comprueba**: ejecuta tu generador, busca el run en
   `logs/run/maquinaria_YYYY-MM-DD.log`, y corre
   `python -m evaluador --check-run-log` para verificar que no quedan
   issues.

---

## 8. Tests del sistema

| Test | Verifica |
|------|----------|
| `tests/test_daylog.py` | Contrato de `RunLog` (START/END, captura stdout, SystemExit) |
| `tests/test_log_helpers.py` | `RunLogger`: emit por nivel, step, retry, ai_call OK/ERROR, correlación run= |
| `tests/test_log_validator.py` | Parser de líneas, validate_run, validate_day, EXPECTED_STEPS, auto-validate |
| `tests/test_logging_integration.py` | Corrida simulada con AI mockeada: el día-log queda completo y pasa el validador |
| `tests/test_entrypoints_logged.py` | Enforcement: todo `__main__` está hookeado a RunLog |

Para correr solo los del sistema de logs:

```bash
pytest tests/test_daylog.py tests/test_log_helpers.py \
       tests/test_log_validator.py tests/test_logging_integration.py \
       tests/test_entrypoints_logged.py -v
```
