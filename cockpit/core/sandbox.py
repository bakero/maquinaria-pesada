"""Política de paths permitidos para escrituras propuestas por IA.

REGLA DURA del sistema: Claude (vía la cockpit) solo puede modificar:
  - Contenido generado (Guiones/, episodios/, escaletas/, RRSS/, output/, PDFs/...)
  - Configuración de generación (cockpit/components_map.json, prompts/)
  - Logs de su propio uso (logs/ai_usage.jsonl)

Claude NUNCA debería modificar:
  - Código de la cockpit (cockpit/**/*.py)
  - Pipelines del repo (generar_*.py, validar_*.py, normalizar_*.py, etc.)
  - Workflows CI (.github/)
  - Configuración del proyecto (pyproject.toml, requirements*.txt)
  - Documentación de arquitectura/legal (BIBLIA_SISTEMA.md, PODCAST_*_SPEC.md)

Este módulo no aplica permisos del sistema operativo: define la política y la
expone como `is_write_allowed(path)`. Los puntos de la app que vayan a aplicar
cambios sugeridos por IA deben llamar a esta función antes.
"""
from __future__ import annotations

from pathlib import Path

from . import paths

# Directorios cuyo contenido completo Claude puede escribir/modificar.
ALLOWED_WRITE_DIRS: tuple[str, ...] = (
    "Guiones",
    "episodios",
    "escaletas",
    "RRSS",
    "output",
    "PDFs/auxiliares",
    "PDFs/resumenes",
    "PDFs/temas",
    "prompts",
    "Videos/escenas_biblioteca",
)

# Ficheros concretos editables por Claude (config de generación, mapa).
ALLOWED_WRITE_FILES: tuple[str, ...] = (
    "cockpit/components_map.json",
    "logs/ai_usage.jsonl",
    "logs/economics.json",
)

# Patrones que SIEMPRE están prohibidos (incluso si caen dentro de un dir permitido).
FORBIDDEN_PATTERNS: tuple[str, ...] = (
    ".git",
    ".github",
    ".env",
    ".claude",
    "cockpit/",                # toda la app (excepto los allowlist files arriba)
    "pyproject.toml",
    "requirements",
    "/tests/",
    "_archivo/",
)


def is_write_allowed(target: str | Path) -> tuple[bool, str]:
    """¿Puede Claude escribir/modificar este path?

    Devuelve (allowed, reason). `reason` siempre tiene texto para mostrar al
    usuario aunque allowed sea True.
    """
    p = Path(target)
    try:
        rel = p.resolve().relative_to(paths.repo_root().resolve())
    except ValueError:
        return False, f"Fuera del repo ({p})"

    rel_str = str(rel).replace("\\", "/")

    # Allowlist explícita de ficheros.
    if rel_str in ALLOWED_WRITE_FILES:
        return True, f"Fichero de configuración permitido: {rel_str}"

    # Forbidden patterns ganan sobre cualquier permiso.
    for pat in FORBIDDEN_PATTERNS:
        if pat in rel_str:
            return False, f"Coincide con patrón prohibido «{pat}»"

    # Directorios permitidos.
    for d in ALLOWED_WRITE_DIRS:
        if rel_str == d or rel_str.startswith(d + "/"):
            return True, f"Dentro de directorio permitido: {d}/"

    return False, f"Ruta fuera del sandbox: {rel_str}"


def explain_policy() -> str:
    """Resumen humano de la política para mostrar en UI o pasar al system prompt."""
    return (
        "POLÍTICA DE SANDBOX para escrituras propuestas por IA:\n"
        "PERMITIDO: contenido generado (Guiones, episodios, escaletas, RRSS, "
        "output, PDFs/{auxiliares,resumenes,temas}, Videos/escenas_biblioteca, "
        "prompts) y los ficheros de configuración cockpit/components_map.json, "
        "logs/ai_usage.jsonl, logs/economics.json.\n"
        "PROHIBIDO: cockpit/ (código de la app), pipelines top-level (.py), "
        ".github/, pyproject.toml, requirements*.txt, .env, _archivo/, tests/."
    )


def filter_paths(paths_iter) -> tuple[list[str], list[tuple[str, str]]]:
    """Reparte una lista de paths en (permitidos, rechazados-con-motivo)."""
    ok: list[str] = []
    rejected: list[tuple[str, str]] = []
    for p in paths_iter:
        allowed, reason = is_write_allowed(p)
        if allowed:
            ok.append(str(p))
        else:
            rejected.append((str(p), reason))
    return ok, rejected
