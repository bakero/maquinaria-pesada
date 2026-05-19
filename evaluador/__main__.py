"""Entry point para `python -m evaluador`.

Envuelve la ejecución en `daylog.RunLog` igual que cualquier otro entrypoint
top-level, para que las llamadas via `-m` queden correlacionadas con un
`run_id` en el día-log.
"""

import sys

from .cli import main

try:
    from daylog import RunLog as _RunLog
    _run_ctx = _RunLog(script="evaluador/cli.py", params=sys.argv[1:])
except Exception:  # noqa: BLE001
    from contextlib import nullcontext as _nullcontext
    _run_ctx = _nullcontext()

with _run_ctx:
    raise SystemExit(main())
