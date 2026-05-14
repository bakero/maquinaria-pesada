"""Enforcement: todo entry point ejecutable de la app pasa por daylog.

Cualquier fichero `.py` con un bloque `if __name__ == "__main__"` debe enganchar
su ejecución a la bitácora central (`daylog.RunLog`). Este test falla si se
añade un nuevo entry point sin enganchar, de modo que "todo el código ejecutable
trazado" se mantiene en el tiempo sin depender de la memoria de nadie.
"""
from __future__ import annotations

from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]

# Árboles que no son código ejecutable de la app.
_EXCLUDED_DIRS = {
    "_archivo", ".claude", ".git", "tests", "node_modules",
    "vite_app", "web", "build", "dist", "__pycache__",
}
# daylog.py ES el sistema de logs: su `__main__` es el visor, no se auto-engancha.
_EXCLUDED_FILES = {"daylog.py"}

_MAIN_GUARDS = ('if __name__ == "__main__"', "if __name__ == '__main__'")


def _executable_entrypoints() -> list[Path]:
    found: list[Path] = []
    for path in _REPO.rglob("*.py"):
        rel = path.relative_to(_REPO)
        if any(part in _EXCLUDED_DIRS for part in rel.parts):
            continue
        if path.name in _EXCLUDED_FILES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(guard in text for guard in _MAIN_GUARDS):
            found.append(path)
    return found


def test_there_are_entrypoints_to_check():
    """Salvaguarda: si esto falla, el escaneo dejó de encontrar entry points."""
    assert _executable_entrypoints(), "no se encontró ningún entry point ejecutable"


@pytest.mark.parametrize(
    "path",
    _executable_entrypoints(),
    ids=lambda p: str(p.relative_to(_REPO)),
)
def test_entrypoint_is_hooked_to_daylog(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    assert "daylog" in text and "RunLog" in text, (
        f"{path.relative_to(_REPO)} tiene un bloque `__main__` pero no engancha "
        f"la ejecución a daylog.RunLog. Envuelve el cuerpo del bloque con "
        f"`with RunLog(...):` (ver cualquier pipeline ya migrado)."
    )
