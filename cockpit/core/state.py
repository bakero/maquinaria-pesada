"""Inventory scan: per-module presence of PDF / Guion / Audio / Video / Log.

Pure stdlib, no dependency on the live repo's `estado_proyecto.py`. The cockpit
must work even when REPO_ROOT does not yet expose its scripts as importable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import paths

# Filename heuristics. Conservative — match anything containing the module token.
_MODULE_TOKEN = re.compile(r"\bM(\d{1,2})\b", re.IGNORECASE)


def _has_module(name: str, module: str) -> bool:
    """Match module token strictly, avoiding M1 ⊂ M10 collisions.

    Accepts: M3, M03, MOD003, mod3, _M3_, M3.txt, M3-T-...
    Rejects: M30 when module=M3, RESUMEN_M10_* when module=M1.
    """
    n = name.upper()
    digits = module[1:].lstrip("0") or "0"
    pattern = rf"(?:^|[^A-Z0-9])M(?:OD)?0*{digits}(?=[^0-9]|$)"
    return bool(re.search(pattern, n))


def _list(directory: Path, suffixes: tuple[str, ...]) -> list[Path]:
    if not directory.exists():
        return []
    return [p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in suffixes]


def _filter(items: list[Path], module: str) -> list[Path]:
    return [p for p in items if _has_module(p.name, module)]


@dataclass
class ModuleStatus:
    module: str
    pdf: list[Path] = field(default_factory=list)
    guion: list[Path] = field(default_factory=list)
    audio: list[Path] = field(default_factory=list)
    video: list[Path] = field(default_factory=list)
    log: list[Path] = field(default_factory=list)

    @property
    def pdf_ok(self) -> bool:
        return bool(self.pdf)

    @property
    def guion_ok(self) -> bool:
        return bool(self.guion)

    @property
    def audio_ok(self) -> bool:
        return bool(self.audio)

    @property
    def video_ok(self) -> bool:
        return bool(self.video)

    @property
    def log_ok(self) -> bool:
        return bool(self.log)

    @property
    def complete(self) -> bool:
        return self.pdf_ok and self.guion_ok and self.audio_ok and self.video_ok


def scan() -> list[ModuleStatus]:
    pdfs = _list(paths.pdfs_dir(), (".pdf",))
    guiones = _list(paths.guiones_dir(), (".txt",))
    audios = _list(paths.episodios_dir(), (".mp3",))
    videos = _list(paths.videos_dir(), (".mp4", ".mov", ".mkv"))
    logs = _list(paths.episodios_dir(), (".log",))

    out: list[ModuleStatus] = []
    for m in paths.MODULES:
        out.append(
            ModuleStatus(
                module=m,
                pdf=_filter(pdfs, m),
                guion=_filter(guiones, m),
                audio=_filter(audios, m),
                video=_filter(videos, m),
                log=_filter(logs, m),
            )
        )
    return out


def pendientes(states: list[ModuleStatus]) -> list[ModuleStatus]:
    return [s for s in states if not s.complete]
