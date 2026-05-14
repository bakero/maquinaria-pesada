"""Modelo de dominio: módulos y episodios.

Convención de nomenclatura del repo:

  * Módulo principal Mn → episodio tipo «M» (largo, 1 por módulo)
    - guion:    Guiones/Mn_<Slug>.txt
    - pdf:      PDFs/Mn_T_<Slug>.pdf
    - escaleta: escaletas/Mn_*.md
    - audio:    episodios/Mn.mp3
    - log:      episodios/Mn_produccion.log, episodios/Mn_E_*_cmd.log

  * Tema Tk del módulo Mn → episodio tipo «T» (corto)
    - guion:    Guiones/Mn_TX_Tk_<slug>.txt
    - pdf:      PDFs/temas/Mn_TX_<slug>.pdf  (si existe)
    - escaleta: escaletas/Mn_TX_Tk_*.md
    - audio:    episodios/Mn_Tk.mp3
    - log:      episodios/Mn_Tk_produccion.log, episodios/Mn_TX_E_Tk_*_cmd.log

Tres estados de módulo:
  - "listo"        → todos los episodios completos (4 contenidos)
  - "en_curso"     → algún contenido producido pero no todo
  - "sin_empezar"  → ningún contenido producido
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import paths

_T_GUION = re.compile(r"^M(\d+)_TX_T(\d+)_(.+)\.txt$", re.IGNORECASE)
_M_GUION = re.compile(r"^M(\d+)_(?!TX_)(.+)\.txt$", re.IGNORECASE)
_T_AUDIO = re.compile(r"^M(\d+)_T(\d+)\.mp3$", re.IGNORECASE)
_M_AUDIO = re.compile(r"^M(\d+)\.mp3$", re.IGNORECASE)

CONTENT_TYPES = ("pdf", "guion", "escaleta", "audio")
"""Tipos de contenido que un episodio puede tener producidos."""


@dataclass
class Episode:
    id: str                       # "M3" o "M3_T2"
    module: str                   # "M3"
    kind: str                     # "M" (módulo) | "T" (tema)
    number: int | None = None     # k para tipo T
    slug: str = ""                # "Machine_Learning_Clasico" o "modelos_clasicos"
    pdf: Path | None = None
    guion: Path | None = None
    escaleta: Path | None = None
    audio: Path | None = None
    video: Path | None = None
    logs: list[Path] = field(default_factory=list)

    @property
    def label(self) -> str:
        if self.kind == "M":
            return f"{self.module} · {self.slug.replace('_', ' ')}"
        return f"{self.module} · T{self.number} · {self.slug.replace('_', ' ')}"

    def has(self, content: str) -> bool:
        return bool(getattr(self, content, None))

    @property
    def produced(self) -> list[str]:
        return [c for c in CONTENT_TYPES if self.has(c)]

    @property
    def missing(self) -> list[str]:
        return [c for c in CONTENT_TYPES if not self.has(c)]

    @property
    def complete(self) -> bool:
        return not self.missing

    @property
    def progress(self) -> float:
        return len(self.produced) / len(CONTENT_TYPES)


# ---- Helpers ----------------------------------------------------------


def _safe_iter(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return [p for p in directory.iterdir() if p.is_file()]


def _index_guiones() -> tuple[dict[str, tuple[str, Path]], dict[tuple[str, int], tuple[str, Path]]]:
    """Devuelve (m_guiones, t_guiones).

    m_guiones[module] = (slug, path)
    t_guiones[(module, num)] = (slug, path)
    """
    m_out: dict[str, tuple[str, Path]] = {}
    t_out: dict[tuple[str, int], tuple[str, Path]] = {}
    for p in _safe_iter(paths.guiones_dir()):
        if p.suffix.lower() != ".txt":
            continue
        mt = _T_GUION.match(p.name)
        if mt:
            mod = f"M{int(mt.group(1))}"
            num = int(mt.group(2))
            t_out[(mod, num)] = (mt.group(3), p)
            continue
        mm = _M_GUION.match(p.name)
        if mm:
            mod = f"M{int(mm.group(1))}"
            m_out[mod] = (mm.group(2), p)
    return m_out, t_out


def _index_audios() -> tuple[dict[str, Path], dict[tuple[str, int], Path]]:
    m_out: dict[str, Path] = {}
    t_out: dict[tuple[str, int], Path] = {}
    for p in _safe_iter(paths.episodios_dir()):
        if p.suffix.lower() != ".mp3":
            continue
        mt = _T_AUDIO.match(p.name)
        if mt:
            t_out[(f"M{int(mt.group(1))}", int(mt.group(2)))] = p
            continue
        mm = _M_AUDIO.match(p.name)
        if mm:
            m_out[f"M{int(mm.group(1))}"] = p
    return m_out, t_out


def _find_pdf(module: str, kind: str, number: int | None) -> Path | None:
    pdir = paths.pdfs_dir()
    if not pdir.exists():
        return None
    digits = module[1:].lstrip("0") or "0"
    if kind == "M":
        # PDFs/Mn_T_<Slug>.pdf
        for p in pdir.glob("*.pdf"):
            if re.match(rf"^M0*{digits}_T_.+\.pdf$", p.name, re.IGNORECASE):
                return p
        return None
    # T: busca en PDFs/temas/ algo que contenga Mn_TX_T{number} o Tk
    sub = pdir / "temas"
    if sub.exists():
        for p in sub.glob("*.pdf"):
            if re.search(
                rf"\bM0*{digits}_TX_T0*{number}\b", p.name, re.IGNORECASE
            ) or re.search(rf"\bT0*{number}_", p.name, re.IGNORECASE):
                return p
    return None


def _find_escaleta(module: str, kind: str, number: int | None) -> Path | None:
    edir = paths.repo_root() / "escaletas"
    if not edir.exists():
        return None
    digits = module[1:].lstrip("0") or "0"
    if kind == "M":
        # M (largo): primera escaleta del módulo sin _T sufijo
        for p in edir.glob("*.md"):
            if re.match(rf"^M0*{digits}_(?!TX_T).+\.md$", p.name, re.IGNORECASE):
                return p
        # fallback: cualquier escaleta MODxxx con el dígito
        for p in edir.glob("*.md"):
            if re.search(rf"\bMOD0*{digits}\b", p.name, re.IGNORECASE):
                return p
        return None
    for p in edir.glob("*.md"):
        if re.search(rf"\bM0*{digits}_TX_T0*{number}\b", p.name, re.IGNORECASE):
            return p
    return None


def _find_logs(module: str, kind: str, number: int | None) -> list[Path]:
    edir = paths.episodios_dir()
    if not edir.exists():
        return []
    digits = module[1:].lstrip("0") or "0"
    out: list[Path] = []
    if kind == "M":
        pat_prod = re.compile(rf"^M0*{digits}_produccion\.log$", re.IGNORECASE)
        pat_cmd = re.compile(rf"^M0*{digits}_E_.+\.log$", re.IGNORECASE)
        for p in edir.glob("*.log"):
            if pat_prod.match(p.name) or pat_cmd.match(p.name):
                out.append(p)
        return out
    pat_prod = re.compile(rf"^M0*{digits}_T0*{number}_produccion\.log$", re.IGNORECASE)
    pat_cmd = re.compile(rf"^M0*{digits}_TX_E_T0*{number}_.+\.log$", re.IGNORECASE)
    for p in edir.glob("*.log"):
        if pat_prod.match(p.name) or pat_cmd.match(p.name):
            out.append(p)
    return out


def _find_video(module: str, kind: str, number: int | None) -> Path | None:
    vdir = paths.videos_dir()
    if not vdir.exists():
        return None
    digits = module[1:].lstrip("0") or "0"
    suffix = "" if kind == "M" else f"_T0*{number}"
    pat = re.compile(rf"^M0*{digits}{suffix}\..*", re.IGNORECASE) if kind == "M" \
        else re.compile(rf"^M0*{digits}_T0*{number}\..*", re.IGNORECASE)
    for p in vdir.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower() in (".mp4", ".mov", ".mkv") and pat.match(p.name):
            return p
    return None


# ---- API pública ------------------------------------------------------


def scan_all() -> list[Episode]:
    """Escanea el repo y devuelve TODOS los episodios detectados."""
    m_guiones, t_guiones = _index_guiones()
    m_audios, t_audios = _index_audios()

    keys: set[tuple[str, str, int | None]] = set()
    for mod in m_guiones:
        keys.add((mod, "M", None))
    for mod in m_audios:
        keys.add((mod, "M", None))
    for (mod, num) in t_guiones:
        keys.add((mod, "T", num))
    for (mod, num) in t_audios:
        keys.add((mod, "T", num))

    # Garantizar episodio M para cada módulo conocido (M0..M14)
    for mod in paths.MODULES:
        keys.add((mod, "M", None))

    out: list[Episode] = []
    for mod, kind, num in keys:
        if kind == "M":
            slug, gpath = m_guiones.get(mod, ("", None))
            ep = Episode(
                id=mod,
                module=mod,
                kind="M",
                slug=slug,
                guion=gpath,
                audio=m_audios.get(mod),
            )
        else:
            slug, gpath = t_guiones.get((mod, num), ("", None))
            ep = Episode(
                id=f"{mod}_T{num}",
                module=mod,
                kind="T",
                number=num,
                slug=slug,
                guion=gpath,
                audio=t_audios.get((mod, num)),
            )
        ep.pdf = _find_pdf(mod, kind, num)
        ep.escaleta = _find_escaleta(mod, kind, num)
        ep.video = _find_video(mod, kind, num)
        ep.logs = _find_logs(mod, kind, num)
        out.append(ep)

    out.sort(key=lambda e: (_mod_num(e.module), 0 if e.kind == "M" else 1, e.number or 0))
    return out


def _mod_num(module: str) -> int:
    try:
        return int(module[1:])
    except ValueError:
        return 9999


def scan_module(module: str) -> list[Episode]:
    return [e for e in scan_all() if e.module == module]


def get_episode(episode_id: str) -> Episode | None:
    for e in scan_all():
        if e.id == episode_id:
            return e
    return None


def module_status(episodes: list[Episode]) -> tuple[str, float]:
    """Devuelve (estado, ratio_completitud) para una lista de episodios.

    estado ∈ {"listo", "en_curso", "sin_empezar"}.
    ratio = media de progreso de los episodios (0..1).
    """
    if not episodes:
        return ("sin_empezar", 0.0)
    total = sum(e.progress for e in episodes) / len(episodes)
    if all(e.complete for e in episodes):
        return ("listo", 1.0)
    if total <= 0.0:
        return ("sin_empezar", 0.0)
    return ("en_curso", total)


STATUS_BADGE = {
    "listo": "🟢 Listo",
    "en_curso": "🟡 En curso",
    "sin_empezar": "⚪ Sin empezar",
}

CONTENT_ICON = {
    "pdf": "📕",
    "guion": "📝",
    "escaleta": "🗂️",
    "audio": "🎧",
    "video": "🎬",
    "log": "📜",
}
