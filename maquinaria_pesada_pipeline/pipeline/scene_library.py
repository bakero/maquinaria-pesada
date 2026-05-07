"""
Biblioteca de escenas reutilizables.

Estructura en disco:
  Videos/escenas_biblioteca/
    _concepts_index.json    <- catalogo de conceptos del master (extractor)
    _scenes_index.json      <- catalogo de escenas generadas (este modulo)
    conceptos/              <- MP4 por concepto (Luma)
    transiciones/
    b_roll/
    cierres/

El _scenes_index.json mapea slug -> ruta + metadata. El scene_builder y
el video_compositor pueden buscar aqui antes de generar de cero.
"""

import hashlib
import json
import re
import shutil
import subprocess
import time
import unicodedata
from pathlib import Path

from .logger import get_logger


CATEGORIES = ["conceptos", "transiciones", "b_roll", "cierres", "stickers_anim"]


def _slugify(text: str) -> str:
    """convierte texto en slug filename-safe."""
    text = text.lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text)
                    if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:80]


def _ffprobe_duration(path: Path) -> float:
    if shutil.which("ffprobe") is None:
        return 0.0
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of",
            "default=noprint_wrappers=1:nokey=1", str(path),
        ], text=True).strip()
        return float(out)
    except Exception:
        return 0.0


class SceneLibrary:
    """API para crear, buscar y catalogar escenas reutilizables."""

    def __init__(self, base_folder: str | Path):
        self.base = Path(base_folder)
        self.base.mkdir(parents=True, exist_ok=True)
        for cat in CATEGORIES:
            (self.base / cat).mkdir(parents=True, exist_ok=True)
        self.index_path = self.base / "_scenes_index.json"
        self._index = self._load_index()
        self.log = get_logger("scene_library")

    # ── catalogo ────────────────────────────────────────────────────

    def _load_index(self) -> dict:
        if self.index_path.exists():
            try:
                return json.loads(self.index_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"version": "1.0", "scenes": {}}

    def _save_index(self) -> None:
        self.index_path.write_text(
            json.dumps(self._index, indent=2, ensure_ascii=False),
            encoding="utf-8")

    # ── busqueda ────────────────────────────────────────────────────

    def find(self, slug: str) -> dict | None:
        return self._index["scenes"].get(slug)

    def find_by_tag(self, tag: str) -> list[dict]:
        out = []
        tag_l = tag.lower()
        for slug, scene in self._index["scenes"].items():
            tags = [t.lower() for t in scene.get("tags", [])]
            if tag_l in tags:
                out.append({**scene, "slug": slug})
        return out

    def all_concepts(self) -> list[str]:
        return [s for s, sc in self._index["scenes"].items()
                if sc.get("category") == "conceptos"]

    # ── registro ────────────────────────────────────────────────────

    def register(self, slug: str, path: str | Path,
                 category: str = "conceptos",
                 prompt: str = "",
                 description: str = "",
                 tags: list[str] | None = None,
                 modulo: str | None = None,
                 source: str = "manual") -> dict:
        if category not in CATEGORIES:
            raise ValueError(f"Categoria invalida: {category}")
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(path)
        # Mover a la carpeta de biblioteca si no esta ya alli
        target_dir = self.base / category
        target = target_dir / f"{_slugify(slug)}{path.suffix}"
        if path.resolve() != target.resolve():
            shutil.copy2(path, target)
        scene = {
            "slug":        _slugify(slug),
            "category":    category,
            "path":        str(target),
            "duration":    _ffprobe_duration(target),
            "prompt":      prompt,
            "description": description,
            "tags":        tags or [],
            "modulo":      modulo,
            "source":      source,
            "created":     time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._index["scenes"][scene["slug"]] = scene
        self._save_index()
        self.log.info(f"  registrada escena: {scene['slug']} -> {target}")
        return scene

    # ── utilidades ──────────────────────────────────────────────────

    def stats(self) -> dict:
        by_cat = {}
        for sc in self._index["scenes"].values():
            by_cat[sc["category"]] = by_cat.get(sc["category"], 0) + 1
        return {"total": len(self._index["scenes"]), "by_category": by_cat}

    def repeated_concepts(self, concepts_index_path: str | Path,
                           min_apariciones: int = 2) -> list[dict]:
        """
        Lee `_concepts_index.json` (del concept_extractor) y devuelve los
        conceptos que aparecen en >=N modulos diferentes, ordenados por
        cantidad de apariciones. Util para priorizar generacion con Luma.
        """
        idx_path = Path(concepts_index_path)
        if not idx_path.exists():
            return []
        catalog = json.loads(idx_path.read_text(encoding="utf-8"))
        result = []
        for slug, refs in catalog.get("by_concept", {}).items():
            modulos = sorted({r.get("modulo") for r in refs if r.get("modulo")})
            if len(modulos) >= min_apariciones:
                first = refs[0]
                result.append({
                    "slug":        slug,
                    "name":        first.get("name"),
                    "luma_prompt": first.get("luma_prompt"),
                    "visual_idea": first.get("visual_idea"),
                    "definicion":  first.get("definicion"),
                    "modulos":     modulos,
                    "apariciones": len(refs),
                    "in_library":  slug in self._index["scenes"],
                })
        result.sort(key=lambda x: -x["apariciones"])
        return result
