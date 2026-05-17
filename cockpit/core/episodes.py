"""Modelo de dominio: módulos y episodios.

Convención de nomenclatura del repo:

  * Módulo principal Mn → episodio tipo «M» (largo, 1 por módulo)
    - guion:    Guiones/Mn_<Slug>.txt
    - pdf:      PDFs/Mn_T_<Slug>.pdf
    - escaleta: escaletas/Mn_*.md
    - audio:    episodios/Mn.mp3
    - log:      episodios/Mn_produccion.log, episodios/Mn_E_*_cmd.log

  * Tema Tk del módulo Mn → episodio tipo «T» (corto)
    - guion:    Guiones/Mn_Tk_<slug>.txt  (legacy: Guiones/Mn_TX_Tk_<slug>.txt)
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

# Naming actual: Mn_Tk_slug. Legacy aún soportado: Mn_TX_Tk_slug ("TX_" opcional).
_T_GUION = re.compile(r"^M(\d+)_(?:TX_)?T(\d+)_(.+)\.txt$", re.IGNORECASE)
_M_GUION = re.compile(r"^M(\d+)_(?!TX_)(?!T\d+_)(.+)\.txt$", re.IGNORECASE)
_T_AUDIO = re.compile(r"^M(\d+)_T(\d+)\.mp3$", re.IGNORECASE)
_M_AUDIO = re.compile(r"^M(\d+)\.mp3$", re.IGNORECASE)

CONTENT_TYPES = ("pdf", "guion", "escaleta", "audio")
"""Tipos de contenido que cuentan para "complete".  El vídeo se considera
un slot extra (no obligatorio) y se contabiliza aparte en el frontend."""

# Metadatos estáticos por módulo (nombre + descripción corta) extraídos del
# currículum real del Master IA (ver PDFs/auxiliares/master IA.pdf y los
# PDFs maestros de módulo en PDFs/Mn_T_*.pdf).  Los porcentajes y estados
# se calculan dinámicamente escaneando los episodios reales del repo.
MODULES_META: list[dict[str, str]] = [
    # 'short' ≤ 50 caracteres: cabe en las cards del master sin truncar.
    {"id": "M0",  "name": "Introducción Estratégica",
     "short": "Qué es la IA, tipos, capacidades, adopción"},
    {"id": "M1",  "name": "Fundamentos y Razonamiento",
     "short": "Paradigmas, atención, razonamiento, tokens"},
    {"id": "M2",  "name": "Matemáticas para IA",
     "short": "Álgebra, cálculo, probabilidad, embeddings"},
    {"id": "M3",  "name": "Machine Learning Clásico",
     "short": "Aprendizaje, modelos, features, evaluación"},
    {"id": "M4",  "name": "Deep Learning",
     "short": "Redes profundas, CNN, RNN, transfer learning"},
    {"id": "M5",  "name": "NLP y LLMs",
     "short": "PLN, BERT vs GPT, in-context, alucinaciones"},
    {"id": "M6",  "name": "Ingeniería de Prompts",
     "short": "CoT, ToT, ReAct, evaluación de prompts"},
    {"id": "M7",  "name": "Sistemas RAG",
     "short": "Embeddings, vector DB, búsqueda híbrida"},
    {"id": "M8",  "name": "Ingeniería LLMOps",
     "short": "Fine-tuning, PEFT/LoRA, CI/CD para IA"},
    {"id": "M9",  "name": "Infraestructura y Despliegue",
     "short": "Cloud, APIs, escalabilidad, edge AI, IaC"},
    {"id": "M10", "name": "Sistemas de Agentes",
     "short": "Planificación, memoria, tool use, MCP/A2A"},
    {"id": "M11", "name": "Automatización con IA",
     "short": "RPA inteligente, workflows, autónomos"},
    {"id": "M12", "name": "Seguridad de IA",
     "short": "OWASP, prompt injection, jailbreak, red team"},
    {"id": "M13", "name": "Gobernanza y Ética",
     "short": "EU AI Act, NIST RMF, ISO 42001, fairness"},
    {"id": "M14", "name": "Estrategia para Empresa",
     "short": "Oportunidades, ROI, roadmap, gestión cambio"},
]


def modules_meta() -> list[dict[str, str]]:
    """Copia de los metadatos estáticos por módulo (id, name, short)."""
    return [dict(m) for m in MODULES_META]


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


# Patrón: PDFs/temas/Mn_Tk_<slug>.pdf  (acepta también Mn_TX_Tk_<slug>.pdf)
_T_PDF_NAME = re.compile(r"^M(\d+)_(?:TX_)?T(\d+)_(.+)\.pdf$", re.IGNORECASE)


def _index_pdfs_temas() -> dict[tuple[str, int], tuple[str, Path]]:
    """Escanea PDFs/temas/ y devuelve (module, num) → (slug, path).

    Permite descubrir todos los temas planeados aunque aún no tengan guion
    ni audio — el PDF es el "blueprint" del tema.
    """
    out: dict[tuple[str, int], tuple[str, Path]] = {}
    sub = paths.pdfs_dir() / "temas"
    if not sub.exists():
        return out
    for p in sub.iterdir():
        if not p.is_file() or p.suffix.lower() != ".pdf":
            continue
        m = _T_PDF_NAME.match(p.name)
        if not m:
            continue
        mod = f"M{int(m.group(1))}"
        num = int(m.group(2))
        # Si hay duplicados, conservamos el primero ordenado por nombre.
        out.setdefault((mod, num), (m.group(3), p))
    return out


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
    # T: busca en PDFs/temas/ algo como M{n}_T{k}_<slug>.pdf (o legacy
    # M{n}_TX_T{k}_…). Usamos (?<![A-Za-z0-9]) en vez de \b porque '_'
    # es word-char en regex y rompe la transición.
    sub = pdir / "temas"
    if sub.exists():
        for p in sub.glob("*.pdf"):
            if re.search(
                rf"(?<![A-Za-z0-9])M0*{digits}_(?:TX_)?T0*{number}(?![A-Za-z0-9])",
                p.name, re.IGNORECASE,
            ):
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
            if re.search(
                rf"(?<![A-Za-z0-9])MOD0*{digits}(?![A-Za-z0-9])",
                p.name, re.IGNORECASE,
            ):
                return p
        return None
    for p in edir.glob("*.md"):
        if re.search(
            rf"(?<![A-Za-z0-9])M0*{digits}_(?:TX_)?T0*{number}(?![A-Za-z0-9])",
            p.name, re.IGNORECASE,
        ):
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
    """Escanea el repo y devuelve TODOS los episodios detectados.

    Fuentes de descubrimiento:
      * `Guiones/` para guiones (.txt) — M y T
      * `episodios/` para audios (.mp3) — M y T
      * `PDFs/temas/` para PDFs de tema — descubre temas planeados aunque
        aún no tengan guion ni audio
      * `paths.MODULES` (M0..M14) garantiza que todo módulo aparezca
    """
    m_guiones, t_guiones = _index_guiones()
    m_audios, t_audios = _index_audios()
    pdfs_t = _index_pdfs_temas()

    keys: set[tuple[str, str, int | None]] = set()
    for mod in m_guiones:
        keys.add((mod, "M", None))
    for mod in m_audios:
        keys.add((mod, "M", None))
    for (mod, num) in t_guiones:
        keys.add((mod, "T", num))
    for (mod, num) in t_audios:
        keys.add((mod, "T", num))
    # Temas descubiertos vía PDF (planeados aunque sin guion/audio aún)
    for (mod, num) in pdfs_t:
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
            # Si el tema solo vive en PDFs/temas/ (sin guion), tomamos el
            # slug humano del nombre del PDF.
            if not slug:
                pdf_slug, _ = pdfs_t.get((mod, num), ("", None))
                slug = pdf_slug
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
