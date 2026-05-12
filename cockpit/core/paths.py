"""Central path resolution.

REPO_ROOT default points to the live repo at C:/Users/Asus/maquinaria_pesada.
Override via env var REPO_ROOT to run the cockpit against a different checkout.
"""
from __future__ import annotations

import os
from pathlib import Path

DEFAULT_REPO_ROOT = Path(r"C:\Users\Asus\maquinaria_pesada")


def repo_root() -> Path:
    return Path(os.environ.get("REPO_ROOT", DEFAULT_REPO_ROOT)).resolve()


def p(*parts: str) -> Path:
    return repo_root().joinpath(*parts)


def pdfs_dir() -> Path:
    return p("PDFs")


def guiones_dir() -> Path:
    return p("Guiones")


def episodios_dir() -> Path:
    return p("episodios")


def videos_dir() -> Path:
    return p("Videos")


def logos_dir() -> Path:
    return p("Logos")


def musica_dir() -> Path:
    return p("Música")


def intro_dir() -> Path:
    return p("intro")


def output_dir() -> Path:
    return p("output")


def env_file() -> Path:
    return p(".env")


def logs_dir() -> Path:
    return p("logs")


def ai_usage_log() -> Path:
    return logs_dir() / "ai_usage.jsonl"


def master_spec_md() -> Path:
    return p("PODCAST_MASTER_SPEC.md")


MODULES: list[str] = [f"M{i}" for i in range(15)]
