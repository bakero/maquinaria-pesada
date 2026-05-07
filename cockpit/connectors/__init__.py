"""Auto-import all connector modules so they self-register.

Add a new connector = drop a file in services/, pipelines/, or sources/.
No edits needed here.
"""
from __future__ import annotations

import importlib
import pkgutil

from .base import (  # re-export
    REGISTRY,
    Category,
    Connector,
    Field_,
    PipelineConnector,
    ServiceConnector,
    SourceConnector,
    Status,
    by_category,
    get,
    register,
)


def _autoload() -> None:
    for sub in ("services", "pipelines", "sources"):
        pkg_name = f"{__name__}.{sub}"
        try:
            pkg = importlib.import_module(pkg_name)
        except ModuleNotFoundError:
            continue
        for m in pkgutil.iter_modules(pkg.__path__):
            importlib.import_module(f"{pkg_name}.{m.name}")


_autoload()

__all__ = [
    "REGISTRY",
    "Category",
    "Connector",
    "Field_",
    "PipelineConnector",
    "ServiceConnector",
    "SourceConnector",
    "Status",
    "by_category",
    "get",
    "register",
]
