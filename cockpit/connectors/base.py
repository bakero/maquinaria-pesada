"""Connector base classes + registry.

Three categories share a tiny interface so the dashboard can render them
uniformly. New connectors register themselves at import time via @register.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Category = Literal["service", "pipeline", "source"]


@dataclass
class Status:
    ok: bool
    detail: str = ""


@dataclass
class Field_:
    """Form field for a pipeline flag."""
    flag: str                      # e.g. "--pdf"
    label: str                     # human label
    kind: str = "str"              # str | int | bool | path | select
    required: bool = False
    default: Any = None
    help: str = ""
    options: list[str] = field(default_factory=list)  # for kind=="select"
    placeholder: str = ""


class Connector:
    id: str = ""
    category: Category = "service"
    label: str = ""
    icon: str = ""
    description: str = ""

    def status(self) -> Status:
        return Status(ok=True)

    def describe(self) -> dict[str, Any]:
        """Serialización para la API JSON del cockpit web."""
        s = self.status()
        return {
            "id":          self.id,
            "category":    self.category,
            "label":       self.label,
            "description": self.description,
            "status":      {"ok": s.ok, "detail": s.detail},
        }


class ServiceConnector(Connector):
    category: Category = "service"
    env_keys: tuple[str, ...] = ()

    def status(self) -> Status:
        import os

        from cockpit.core import paths

        env: dict = {}
        if paths.env_file().exists():
            try:
                from dotenv import dotenv_values
                env = dotenv_values(paths.env_file()) or {}
            except ImportError:
                env = {}
        merged = {**env, **os.environ}
        missing = [k for k in self.env_keys if not merged.get(k)]
        if missing:
            return Status(ok=False, detail=f"faltan en .env: {', '.join(missing)}")
        return Status(ok=True, detail="credenciales presentes" if self.env_keys else "OK")

    def describe(self) -> dict[str, Any]:
        d = super().describe()
        d["env_keys"] = list(self.env_keys)
        return d


class PipelineConnector(Connector):
    category: Category = "pipeline"
    script: str = ""              # e.g. "generar_guion.py"
    fields: list[Field_] = []

    def status(self) -> Status:
        from cockpit.core import paths
        sp = paths.repo_root() / self.script
        return Status(ok=sp.exists(), detail=str(sp) if not sp.exists() else "")

    def build_command(self, values: dict[str, Any]) -> str:
        from cockpit.core import prompt_builder
        flags = [(f.flag, values.get(f.flag)) for f in self.fields]
        return prompt_builder.build(
            script=self.script,
            flags=flags,
            cwd=prompt_builder.default_cwd(),
            header=f"Codex prompt — {self.label}",
        )

    def _flag_pairs(self, values: dict[str, Any]) -> list[tuple[str, Any]]:
        return [(f.flag, values.get(f.flag)) for f in self.fields]

    def stream(self, values: dict[str, Any]):
        """Yields líneas de stdout y un RunResult final."""
        from cockpit.core import runner
        yield from runner.stream_pipeline(self.script, self._flag_pairs(values))

    def preview(self, values: dict[str, Any]) -> str:
        from cockpit.core import runner
        return runner.preview_command(self.script, self._flag_pairs(values))

    def describe(self) -> dict[str, Any]:
        d = super().describe()
        d["script"] = self.script
        d["fields"] = [
            {"flag": f.flag, "label": f.label, "kind": f.kind,
             "required": f.required, "default": f.default,
             "help": f.help, "options": f.options, "placeholder": f.placeholder}
            for f in self.fields
        ]
        return d


class SourceConnector(Connector):
    category: Category = "source"
    suffixes: tuple[str, ...] = ()

    def list_items(self) -> list[Path]:
        return []

    def describe(self) -> dict[str, Any]:
        d = super().describe()
        items = self.list_items()
        d["count"] = len(items)
        d["sample"] = items[0].name if items else None
        d["suffixes"] = list(self.suffixes)
        return d


# ---- Registry ----------------------------------------------------------

REGISTRY: dict[str, Connector] = {}


def register(cls: type[Connector]) -> type[Connector]:
    inst = cls()
    if not inst.id:
        raise ValueError(f"Connector {cls.__name__} missing id")
    if inst.id in REGISTRY:
        raise ValueError(f"Connector id {inst.id!r} already registered")
    REGISTRY[inst.id] = inst
    return cls


def by_category(cat: Category) -> list[Connector]:
    return [c for c in REGISTRY.values() if c.category == cat]


def get(connector_id: str) -> Connector:
    return REGISTRY[connector_id]
