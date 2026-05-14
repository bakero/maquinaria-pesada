"""
Paso 02 - Extraccion de contenido del guion etiquetado y del PDF.

Del guion extrae: secciones, intervenciones, speakers, tonos, texto.
Del PDF extrae: datos estadisticos, conceptos, fechas, cifras.
Combina todo en content_data.json.
"""

import json
import re
from collections import OrderedDict
from pathlib import Path

from .logger import get_logger

SECTION_RE = re.compile(r"^\s*#\s+(.+?)\s*$")
SPEAKER_RE = re.compile(
    r"^\s*(MARIA|MARÍA|IAGO|NARRADOR|NARRADORA)\s*:\s*(.*)$",
    re.IGNORECASE,
)
TONE_RE = re.compile(r"\[\s*([^\]]+?)\s*\]")
SILENCE_RE = re.compile(r"<silence\s*=\s*([\d.]+)\s*s\s*/?>", re.IGNORECASE)

PERCENT_RE = re.compile(r"\b(\d{1,3}(?:[.,]\d+)?)\s*%")
MONEY_RE = re.compile(
    r"(\$|€|USD|EUR)?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*(B|M|K|mil|millones|billones|miles)\b",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"\b(19[5-9]\d|20\d{2})\b")
USERS_RE = re.compile(
    r"(\d{1,3}(?:[.,]\d+)?)\s*(M|B|mil|millones|billones)\s*(usuarios?|users?|empresas?|companies?)",
    re.IGNORECASE,
)

ACRONYM_RE = re.compile(r"\b([A-Z]{2,6}(?:-?[A-Z0-9]{1,4})?)\b")
COMMON_ACRONYMS_KEEP = {
    "IA", "ML", "DL", "LLM", "LLMs", "GPT", "API", "GPU", "CPU", "RAG",
    "MLP", "RNN", "CNN", "AI", "EU", "UE", "RL", "TPU", "SaaS", "B2B",
    "ROI", "KPI", "CEO", "CTO", "CIO", "ETL", "JSON", "SQL", "NLP",
}


def parse_script(script_path: str | Path) -> dict:
    """Parsea el guion etiquetado en secciones e intervenciones."""
    log = get_logger("02_content_extractor")
    script_path = Path(script_path)
    text = script_path.read_text(encoding="utf-8")

    sections = []
    current = None
    line_idx = 0

    for raw_line in text.splitlines():
        line_idx += 1
        line = raw_line.rstrip()
        if not line.strip():
            continue

        m_sec = SECTION_RE.match(line)
        if m_sec:
            if current:
                sections.append(current)
            section_name = m_sec.group(1).strip().upper().replace(" ", "_")
            current = {
                "name":          section_name,
                "raw_title":     m_sec.group(1).strip(),
                "interventions": [],
                "line_start":    line_idx,
            }
            continue

        m_speak = SPEAKER_RE.match(line)
        if m_speak:
            speaker = m_speak.group(1).upper().replace("MARÍA", "MARIA")
            content = m_speak.group(2).strip()
            tones = [t.lower() for t in TONE_RE.findall(content)]
            silences = [float(s) for s in SILENCE_RE.findall(content)]
            clean_text = TONE_RE.sub("", content)
            clean_text = SILENCE_RE.sub("", clean_text).strip()

            if current is None:
                current = {
                    "name":          "INTRO",
                    "raw_title":     "INTRO",
                    "interventions": [],
                    "line_start":    line_idx,
                }

            current["interventions"].append({
                "speaker":  speaker,
                "tones":    tones,
                "silences": silences,
                "text":     clean_text,
                "line":     line_idx,
            })

    if current:
        sections.append(current)

    log.info(f"Guion parseado: {len(sections)} secciones, "
             f"{sum(len(s['interventions']) for s in sections)} intervenciones")
    return {"sections": sections, "raw_text": text}


def extract_pdf_content(pdf_path: str | Path | None) -> dict:
    """Extrae texto del PDF (si existe). Si no, devuelve estructura vacia."""
    log = get_logger("02_content_extractor")
    if not pdf_path or not Path(pdf_path).exists():
        log.info("Sin PDF de contenido, se omite extraccion PDF.")
        return {"text": "", "pages": []}

    try:
        import pdfplumber
    except ImportError:
        log.warning("pdfplumber no esta instalado, omitiendo PDF.")
        return {"text": "", "pages": []}

    pages = []
    full_text_parts = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages):
            try:
                t = page.extract_text() or ""
            except Exception as exc:
                log.warning(f"No se pudo extraer pagina {i + 1}: {exc}")
                t = ""
            pages.append({"page": i + 1, "text": t})
            full_text_parts.append(t)

    log.info(f"PDF extraido: {len(pages)} paginas")
    return {"text": "\n".join(full_text_parts), "pages": pages}


def find_statistics(text: str) -> list:
    """Detecta porcentajes, dinero, usuarios, anios..."""
    stats = []

    for m in PERCENT_RE.finditer(text):
        stats.append({"type": "percent", "value": m.group(0).strip(),
                      "raw": m.group(0), "pos": m.start()})

    for m in MONEY_RE.finditer(text):
        stats.append({"type": "money", "value": m.group(0).strip(),
                      "raw": m.group(0), "pos": m.start()})

    for m in USERS_RE.finditer(text):
        stats.append({"type": "users", "value": m.group(0).strip(),
                      "raw": m.group(0), "pos": m.start()})

    seen_years = set()
    for m in YEAR_RE.finditer(text):
        y = m.group(1)
        if y in seen_years:
            continue
        seen_years.add(y)
        stats.append({"type": "year", "value": y,
                      "raw": m.group(0), "pos": m.start()})

    # Deduplicar conservando orden
    dedup = OrderedDict()
    for s in stats:
        key = (s["type"], s["value"].lower())
        if key not in dedup:
            dedup[key] = s
    return list(dedup.values())


def extract_acronyms(text: str) -> list:
    found = OrderedDict()
    for m in ACRONYM_RE.finditer(text):
        token = m.group(1)
        if token in COMMON_ACRONYMS_KEEP or len(token) <= 4:
            found[token] = True
    return list(found.keys())[:40]


def build_keywords(script_data: dict, pdf_data: dict, stats: list) -> list:
    """
    Construye lista de keywords para resaltar en subtitulos.
    Incluye: cifras, acronimos, conceptos repetidos.
    """
    keywords = set()

    for s in stats:
        keywords.add(s["value"])

    text_combined = script_data.get("raw_text", "") + "\n" + pdf_data.get("text", "")
    keywords.update(extract_acronyms(text_combined))

    # Conceptos comunes en MaquinarIA
    domain_terms = [
        "inteligencia artificial", "machine learning", "deep learning",
        "redes neuronales", "transformers", "fine-tuning", "RAG",
        "agentes", "embedding", "alineamiento", "alucinacion", "alucinaciones",
        "GPT", "Claude", "Gemini", "OpenAI", "Anthropic", "Google",
        "EU AI Act", "regulacion", "compliance", "GDPR",
        "automatizacion", "productividad",
    ]
    text_lower = text_combined.lower()
    for term in domain_terms:
        if term.lower() in text_lower:
            keywords.add(term)

    return sorted(keywords, key=lambda x: (-len(x), x.lower()))


def extract_content(script_path: str | Path,
                    pdf_path: str | Path | None,
                    output_folder: str | Path,
                    force: bool = False) -> dict:
    """
    Funcion publica del paso 02.
    Genera content_data.json con secciones, datos, conceptos y keywords.
    """
    log = get_logger("02_content_extractor")
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    cache = output_folder / "content_data.json"

    if cache.exists() and not force:
        log.info(f"content_data cacheado: {cache.name}")
        return json.loads(cache.read_text(encoding="utf-8"))

    script_data = parse_script(script_path)
    pdf_data = extract_pdf_content(pdf_path)

    combined_text = script_data["raw_text"] + "\n" + pdf_data["text"]
    stats = find_statistics(combined_text)
    keywords = build_keywords(script_data, pdf_data, stats)

    speakers = sorted({
        i["speaker"]
        for s in script_data["sections"]
        for i in s["interventions"]
    })

    tone_map = {}
    for s in script_data["sections"]:
        tones = []
        for i in s["interventions"]:
            tones.extend(i["tones"])
        tone_map[s["name"]] = list(set(tones))

    output = {
        "sections":   script_data["sections"],
        "statistics": stats,
        "concepts":   extract_acronyms(combined_text),
        "keywords":   keywords,
        "speakers":   speakers,
        "tone_map":   tone_map,
        "pdf_pages":  len(pdf_data.get("pages", [])),
        "pdf_text":   pdf_data.get("text", ""),
    }

    cache.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"content_data generado: {len(stats)} stats, {len(keywords)} keywords")
    return output


if __name__ == "__main__":
    # Bitácora diaria centralizada (logs/run/). Localiza daylog.py subiendo
    # directorios; si fallara, el script sigue con un nullcontext de respaldo.
    import sys as _sys
    from pathlib import Path as _Path
    for _p in _Path(__file__).resolve().parents:
        if (_p / "daylog.py").exists():
            if str(_p) not in _sys.path:
                _sys.path.insert(0, str(_p))
            break
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script=_Path(__file__).name, params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("script")
        parser.add_argument("--pdf", default=None)
        parser.add_argument("--out", default="./outputs")
        parser.add_argument("--force", action="store_true")
        args = parser.parse_args()
        extract_content(args.script, args.pdf, args.out, args.force)
