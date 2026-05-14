"""
Buscador de medios (imagenes, GIFs, memes) para conceptos del master.

Fuentes:
  - Wikipedia ES + EN (imagen principal del articulo + thumbnails)        -> sin API key
  - Wikimedia Commons (busqueda libre)                                    -> sin API key
  - Tenor v2 (Google) para GIFs/memes                                     -> requiere TENOR_API_KEY
  - DuckDuckGo Images (scraping liviano)                                  -> sin API key, fallback

Persiste todo en `Videos/escenas_biblioteca/media/<slug_concepto>/` con
sus metadatos en `_media_index.json` (mapa concepto -> lista de medios).
"""

import json
import os
import re
import time
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

from .logger import get_logger


def _slugify(s: str) -> str:
    s = s.lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")[:60]


_STOPWORDS = {
    "the", "of", "in", "on", "and", "or", "a", "an", "to", "for",
    "with", "by", "from", "as", "is", "are", "be", "this", "that",
    "el", "la", "los", "las", "de", "del", "y", "o", "un", "una",
    "en", "para", "por", "con", "se", "que", "es", "ser", "al",
    "ai", "ia",
}


def _meaningful_words(term: str) -> set[str]:
    """Tokens significativos del termino (sin stopwords)."""
    norm = "".join(c for c in unicodedata.normalize("NFD", term.lower())
                    if unicodedata.category(c) != "Mn")
    tokens = re.findall(r"[a-z0-9]{3,}", norm)
    return {t for t in tokens if t not in _STOPWORDS}


def _title_matches_term(title: str, term: str, min_overlap: int = 1) -> bool:
    """¿El titulo del articulo tiene relacion con el termino buscado?

    Para descartar resultados Wikipedia irrelevantes (ej. busqueda
    'Golden dataset' devolviendo 'Staphylococcus aureus' por la palabra
    'dataset' en el cuerpo del articulo).
    """
    term_words = _meaningful_words(term)
    if not term_words:
        return True
    title_words = _meaningful_words(title)
    if not title_words:
        return False
    overlap = term_words & title_words
    return len(overlap) >= min_overlap


class MediaFinder:
    """
    Busca y descarga medios para conceptos del master.

    Uso:
        f = MediaFinder(library_base="Videos/escenas_biblioteca/media")
        f.search_and_download("Transformers", search_terms=["Transformer (modelo de IA)"],
                              max_results=3)
    """

    def __init__(self, library_base: str | Path,
                 user_agent: str = "MaquinarIaPesada/1.0 (research)"):
        self.base = Path(library_base)
        self.base.mkdir(parents=True, exist_ok=True)
        self.index_path = self.base / "_media_index.json"
        self._index = self._load_index()
        self.user_agent = user_agent
        self.tenor_key = os.getenv("TENOR_API_KEY")
        self.log = get_logger("media_finder")
        self._sess = None

    @property
    def http(self):
        if self._sess is None:
            import requests
            s = requests.Session()
            s.headers["User-Agent"] = self.user_agent
            self._sess = s
        return self._sess

    # ─── catalogo ───────────────────────────────────────────────────

    def _load_index(self) -> dict:
        if self.index_path.exists():
            try:
                return json.loads(self.index_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"version": "1.0", "media_by_concept": {}}

    def _save_index(self) -> None:
        self.index_path.write_text(
            json.dumps(self._index, indent=2, ensure_ascii=False),
            encoding="utf-8")

    def has(self, slug: str) -> bool:
        items = self._index["media_by_concept"].get(slug, [])
        return any(Path(i["path"]).exists() for i in items)

    # ─── Wikipedia / Wikimedia ─────────────────────────────────────

    def _wikipedia_search(self, term: str, lang: str = "es",
                          max_results: int = 3) -> list[dict]:
        """
        Devuelve lista de {title, url, thumbnail, license_hint}.

        Estrategia:
          1) Buscar el termino para encontrar el articulo mas relevante.
          2) Pedir pageimages + thumbs.
        """
        try:
            # 1) busqueda simple
            r = self.http.get(
                f"https://{lang}.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "format": "json",
                    "list":   "search",
                    "srsearch": term,
                    "srlimit": 1,
                },
                timeout=15,
            )
            r.raise_for_status()
            search = r.json().get("query", {}).get("search", [])
            if not search:
                return []
            page_title = search[0]["title"]

            # 2) traer imagen principal
            r2 = self.http.get(
                f"https://{lang}.wikipedia.org/w/api.php",
                params={
                    "action":      "query",
                    "format":      "json",
                    "prop":        "pageimages|info|images",
                    "pithumbsize": 800,
                    "titles":      page_title,
                    "inprop":      "url",
                },
                timeout=15,
            )
            r2.raise_for_status()
            data = r2.json()
            pages = data.get("query", {}).get("pages", {})
            results = []
            for _, page in pages.items():
                title = page.get("title", page_title)
                # Filtrar resultados claramente irrelevantes
                if not _title_matches_term(title, term):
                    self.log.debug(f"  wikipedia({lang}) descartado por irrelevante: '{title}' vs '{term}'")
                    continue
                if "thumbnail" in page and page["thumbnail"].get("source"):
                    results.append({
                        "title":     title,
                        "url":       page["thumbnail"]["source"],
                        "page_url":  page.get("fullurl"),
                        "source":    f"wikipedia.{lang}",
                        "license_hint": "Wikipedia / probablemente CC-BY-SA o dominio publico",
                    })
            return results[:max_results]
        except Exception as exc:
            self.log.debug(f"  wikipedia({lang}) fallo: {exc}")
            return []

    def _wikimedia_commons_search(self, term: str, max_results: int = 3) -> list[dict]:
        """Busqueda en Wikimedia Commons via API."""
        try:
            r = self.http.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action":     "query",
                    "format":     "json",
                    "generator":  "search",
                    "gsrsearch":  f"{term} filetype:bitmap|drawing",
                    "gsrlimit":   max_results,
                    "prop":       "imageinfo",
                    "iiprop":     "url|extmetadata",
                    "iiurlwidth": 800,
                },
                timeout=15,
            )
            r.raise_for_status()
            pages = r.json().get("query", {}).get("pages", {})
            out = []
            for _, p in pages.items():
                title = p.get("title", "")
                if not _title_matches_term(title, term):
                    continue
                ii = (p.get("imageinfo") or [{}])[0]
                if ii.get("thumburl") or ii.get("url"):
                    out.append({
                        "title":  title,
                        "url":    ii.get("thumburl") or ii.get("url"),
                        "page_url": ii.get("descriptionurl"),
                        "source": "wikimedia.commons",
                        "license_hint": (ii.get("extmetadata", {})
                                          .get("LicenseShortName", {})
                                          .get("value", "ver pagina")),
                    })
            return out[:max_results]
        except Exception as exc:
            self.log.debug(f"  commons fallo: {exc}")
            return []

    # ─── Tenor (GIFs) ──────────────────────────────────────────────

    def _tenor_search(self, term: str, max_results: int = 3) -> list[dict]:
        if not self.tenor_key:
            return []
        try:
            r = self.http.get(
                "https://tenor.googleapis.com/v2/search",
                params={
                    "q":       term,
                    "key":     self.tenor_key,
                    "limit":   max_results,
                    "media_filter": "gif",
                    "client_key": "maquinaria_pesada",
                    "locale":  "es_ES",
                },
                timeout=15,
            )
            r.raise_for_status()
            results = r.json().get("results", [])
            out = []
            for it in results:
                gif = (it.get("media_formats", {}).get("gif")
                       or it.get("media_formats", {}).get("mediumgif"))
                if not gif:
                    continue
                out.append({
                    "title":    it.get("content_description") or it.get("title", ""),
                    "url":      gif.get("url"),
                    "page_url": it.get("itemurl"),
                    "source":   "tenor",
                    "license_hint": "Tenor (Google) - revisa terminos",
                    "is_gif":   True,
                })
            return out
        except Exception as exc:
            self.log.debug(f"  tenor fallo: {exc}")
            return []

    # ─── descarga ──────────────────────────────────────────────────

    def _download(self, url: str, dest: Path) -> bool:
        try:
            with self.http.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                dest.parent.mkdir(parents=True, exist_ok=True)
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1 << 14):
                        if chunk:
                            f.write(chunk)
            return True
        except Exception as exc:
            self.log.debug(f"  download fallo: {exc}")
            return False

    # ─── flujo de alto nivel ───────────────────────────────────────

    def search_and_download(self, concept_name: str,
                             search_terms: list[str] | None = None,
                             max_per_source: int = 2,
                             want_gif: bool = True,
                             skip_existing: bool = True) -> list[dict]:
        """
        Busca medios para un concepto en todas las fuentes habilitadas y
        descarga los mejores.
        """
        slug = _slugify(concept_name)
        if skip_existing and self.has(slug):
            self.log.info(f"  [{slug}] ya tiene medios, skip")
            return self._index["media_by_concept"].get(slug, [])

        terms = search_terms or [concept_name]
        all_candidates: list[dict] = []

        for term in terms:
            # Wikipedia EN primero (mas cobertura para terminos tecnicos)
            all_candidates.extend(self._wikipedia_search(term, "en", max_per_source))
            if len(all_candidates) < max_per_source:
                all_candidates.extend(self._wikipedia_search(term, "es", max_per_source))
            all_candidates.extend(self._wikimedia_commons_search(term, max_per_source))
            if want_gif:
                all_candidates.extend(self._tenor_search(term, max_per_source))
            if len(all_candidates) >= max_per_source * 3:
                break

        # Deduplicar por URL
        seen = set()
        unique = []
        for c in all_candidates:
            if c["url"] in seen:
                continue
            seen.add(c["url"])
            unique.append(c)

        if not unique:
            self.log.info(f"  [{slug}] sin resultados")
            return []

        # Descargar
        target_dir = self.base / slug
        target_dir.mkdir(parents=True, exist_ok=True)
        downloaded = []
        for i, cand in enumerate(unique[:max_per_source * 2]):
            ext = Path(urlparse(cand["url"]).path).suffix.lower() or ".jpg"
            if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"):
                ext = ".gif" if cand.get("is_gif") else ".jpg"
            stem = _slugify(cand.get("title") or cand["source"])[:40] or f"img_{i}"
            dest = target_dir / f"{stem}{ext}"
            if dest.exists():
                continue
            if self._download(cand["url"], dest):
                downloaded.append({
                    **cand,
                    "path":  str(dest),
                    "size":  dest.stat().st_size,
                })

        if downloaded:
            self._index["media_by_concept"][slug] = downloaded
            self._save_index()
            self.log.info(f"  [{slug}] {len(downloaded)} medios descargados")
        return downloaded


def find_media_for_concepts(concepts_index_path: str | Path,
                             library_base: str | Path,
                             min_apariciones: int = 2,
                             top_n: int | None = None,
                             want_gif: bool = True,
                             delay_seconds: float = 0.6) -> dict:
    """
    Funcion de alto nivel: lee el catalogo de conceptos y descarga medios
    para los que aparecen en >=min_apariciones modulos (los mas reutilizables).
    """
    log = get_logger("media_finder")
    catalog = json.loads(Path(concepts_index_path).read_text(encoding="utf-8"))
    by_concept = catalog.get("by_concept", {})

    # Ranking por apariciones
    ranking = []
    for slug, refs in by_concept.items():
        modulos = sorted({r.get("modulo") for r in refs if r.get("modulo")})
        if len(modulos) < min_apariciones:
            continue
        first = refs[0]
        ranking.append({
            "slug":         slug,
            "name":         first.get("name") or slug,
            "definicion":   first.get("definicion", ""),
            "modulos":      modulos,
            "apariciones":  len(refs),
        })
    ranking.sort(key=lambda x: -x["apariciones"])
    if top_n:
        ranking = ranking[:top_n]

    log.info(f"Buscando medios para {len(ranking)} conceptos "
             f"(min_apariciones={min_apariciones}, top_n={top_n}).")

    finder = MediaFinder(library_base)
    stats = {"processed": 0, "with_media": 0, "skipped": 0}
    for i, c in enumerate(ranking, 1):
        log.info(f"  [{i:03d}/{len(ranking)}] {c['name']}  ({c['apariciones']}x)")
        try:
            results = finder.search_and_download(
                concept_name=c["name"],
                search_terms=[c["name"], c.get("definicion", "")[:60]],
                max_per_source=2,
                want_gif=want_gif,
            )
            stats["processed"] += 1
            if results:
                stats["with_media"] += 1
            time.sleep(delay_seconds)
        except KeyboardInterrupt:
            log.warning("  interrumpido por usuario")
            break
        except Exception as exc:
            log.error(f"  error con {c['name']}: {exc}")
    log.info(f"Hecho. {stats}")
    return stats
