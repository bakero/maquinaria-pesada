"""Shorts (episodios S) — píldoras de glosario de 60–90 s.

Tipo de episodio independiente de los módulos M y los temas T. Cada Short
es UN término técnico ("RAG", "Fine-tuning", "Hallucination" …) con su
propio guion (~180 palabras), audio (60–90 s) y vídeo vertical.

A diferencia de M y T:
  - No hay PDF fuente (la fuente es el propio prompt + spec).
  - No hay escaleta (formato muy corto).
  - No tienen `module` padre — viven en una sección propia "Shorts".

Los términos los gestiona `entrenar_v6.py:S_TERMS`. Si quieres añadir más
Shorts, edítalo allí y este módulo los recogerá automáticamente.

Layout de archivos en el repo:
  - Guion:  Guiones/round{R}/iter_{I}/S{N}_v6.md          (versionado)
            Guiones/S{N}_<slug>.md / .txt                  (canónico)
  - Audio:  episodios/S{N}_<slug>.mp3   o   episodios/S{N}.mp3
  - Vídeo:  Videos/S{N}_<slug>.mp4
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from cockpit.core import paths


def _import_terms() -> list[tuple[str, str]]:
    """Devuelve los pares (id, term) desde entrenar_v6.py si existe, o un
    fallback con S1–S5 hardcoded si el archivo no se puede importar."""
    try:
        # entrenar_v6.py es script de nivel raíz, no paquete — lectura manual.
        text = (paths.repo_root() / "entrenar_v6.py").read_text(encoding="utf-8")
    except OSError:
        return _FALLBACK_TERMS
    out: list[tuple[str, str]] = []
    in_block = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("S_TERMS"):
            in_block = True
            continue
        if not in_block:
            continue
        if s.startswith("]"):
            break
        # Líneas tipo:  ("S1", "RAG"),
        if s.startswith("("):
            try:
                inside = s.rstrip(",").strip("()")
                a, b = (p.strip().strip('"').strip("'") for p in inside.split(","))
                if a and b:
                    out.append((a, b))
            except ValueError:
                continue
    return out or _FALLBACK_TERMS


_FALLBACK_TERMS: list[tuple[str, str]] = [
    ("S1", "RAG"),
    ("S2", "Fine-tuning"),
    ("S3", "Hallucination"),
    ("S4", "Embedding"),
    ("S5", "Prompt"),
]


def short_terms() -> list[tuple[str, str]]:
    """Lista (id, term) de los Shorts conocidos. Se lee en cada llamada para
    reflejar cambios en entrenar_v6.py sin reiniciar el servidor."""
    return _import_terms()


@dataclass
class Short:
    """Drop-in compatible con cockpit.core.episodes.Episode para que las
    helpers de web_server (load_slot_meta, _state_for_episode) lo acepten sin
    duplicación. Los Shorts no tienen PDF ni escaleta — esos atributos
    quedan None y aparecerán como state="empty" en la UI."""

    id: str
    term: str
    # Drop-in con Episode:
    module: str = ""              # los Shorts no pertenecen a ningún módulo
    kind: str = "S"
    number: int | None = None
    pdf: Path | None = None
    escaleta: Path | None = None
    guion: Path | None = None
    audio: Path | None = None
    video: Path | None = None
    logs: list[Path] = field(default_factory=list)

    @property
    def slug(self) -> str:
        return self.term.lower().replace(" ", "_").replace("-", "_")

    @property
    def label(self) -> str:
        return f"{self.id} · {self.term}"

    def has(self, content: str) -> bool:
        return bool(getattr(self, content, None))

    @property
    def produced(self) -> list[str]:
        return [c for c in ("guion", "audio", "video") if self.has(c)]

    @property
    def progress(self) -> float:
        return len(self.produced) / 3


def _find_guion(sid: str) -> Path | None:
    """Resuelve el guion del Short. Prioriza el canónico (Guiones/S{N}_*.md
    o .txt) y, si no, el último versionado en round*/iter_*/S{N}_v6.md."""
    root = paths.guiones_dir()
    if not root.exists():
        return None
    canon = list(root.glob(f"{sid}_*.md")) + list(root.glob(f"{sid}_*.txt")) \
        + list(root.glob(f"{sid}.md")) + list(root.glob(f"{sid}.txt"))
    if canon:
        return max(canon, key=lambda p: p.stat().st_mtime)
    versioned = list(root.glob(f"round*/iter_*/{sid}_v6.md"))
    if versioned:
        return max(versioned, key=lambda p: p.stat().st_mtime)
    return None


def _find_audio(sid: str) -> Path | None:
    eps = paths.episodios_dir()
    if not eps.exists():
        return None
    for p in eps.glob(f"{sid}_*.mp3"):
        return p
    direct = eps / f"{sid}.mp3"
    return direct if direct.exists() else None


def _find_video(sid: str) -> Path | None:
    root = paths.repo_root() / "Videos"
    if not root.exists():
        return None
    for p in root.glob(f"{sid}_*.mp4"):
        return p
    return None


def list_shorts() -> list[Short]:
    """Devuelve todos los Shorts conocidos con su estado actual en disco."""
    out: list[Short] = []
    for sid, term in short_terms():
        out.append(Short(
            id=sid, term=term,
            guion=_find_guion(sid),
            audio=_find_audio(sid),
            video=_find_video(sid),
        ))
    return out


def get_short(sid: str) -> Short | None:
    for sh in list_shorts():
        if sh.id == sid:
            return sh
    return None
