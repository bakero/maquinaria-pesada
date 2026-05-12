"""
Extractor de conceptos del temario del master.

Procesa todos los PDFs en una carpeta y genera un catalogo unificado de
conceptos clave por modulo y tema, listo para alimentar:
  - El scene_builder (sabe que conceptos pueden aparecer en cada episodio).
  - La biblioteca de escenas (genera escenas Luma reutilizables por concepto).

Uso programatico:
    from pipeline.concept_extractor import extract_all_concepts
    extract_all_concepts(
        pdfs_folder="C:/Users/Asus/maquinaria_pesada/PDFs",
        output_path="C:/Users/Asus/maquinaria_pesada/Videos/escenas_biblioteca/_concepts_index.json",
    )

Uso CLI:
    python -m pipeline.concept_extractor --pdfs <folder> --out <json>
"""

import json
import os
import re
import sys
import time
from pathlib import Path

from .logger import get_logger


SYSTEM_PROMPT = """Eres un extractor de conceptos didacticos para un master de IA.
Recibes el texto de un PDF de un tema concreto del master y devuelves los
conceptos clave en formato JSON.

Reglas:
1. 6 a 12 conceptos por tema.
2. Cada concepto debe ser FUNDAMENTAL (no detalles secundarios).
3. La definicion DEBE ser una sola frase clara, sin jerga innecesaria.
4. Los sinonimos deben ser variantes naturales que un presentador de podcast
   podria usar (ej. "I.A.", "inteligencia artificial", "AI").
5. La sugerencia visual debe ser CONCRETA y filmable (ej. "una neurona
   activandose con lineas de luz", no "concepto abstracto").
6. Asocia cada concepto a su modulo y tema con los identificadores que te
   proporcione el usuario.

Formato de salida (SOLO JSON, sin markdown):
{
  "concepts": [
    {
      "name": "Transformers",
      "slug": "transformers",
      "definicion": "Arquitectura neuronal que procesa secuencias en paralelo gracias a la atencion.",
      "sinonimos": ["transformadores", "arquitectura de atencion"],
      "tags": ["arquitectura", "deep_learning", "atencion"],
      "visual_idea": "Capas neuronales con flechas que conectan palabras distantes en un texto",
      "luma_prompt": "Cinematic shot of glowing neural network nodes connected by lines of light, parallel processing, dark blue background with yellow accents",
      "importance": "alta"
    }
  ]
}
"""


def _read_pdf(pdf_path: Path) -> str:
    """Extrae texto plano del PDF (max 25000 chars)."""
    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError("pdfplumber no esta instalado")
    parts = []
    total = 0
    with pdfplumber.open(str(pdf_path)) as pdf:
        for p in pdf.pages:
            try:
                t = p.extract_text() or ""
            except Exception:
                t = ""
            if not t:
                continue
            parts.append(t)
            total += len(t)
            if total > 25000:
                break
    return "\n".join(parts)


def _parse_module_topic(filename: str) -> tuple[str, str]:
    """
    Reconoce patrones tipo:
      M0_T1_que_es_ia_hoy.pdf      -> ('M0', 'T1_que_es_ia_hoy')
      M10_T7_frameworks.pdf        -> ('M10', 'T7_frameworks')
      RESUMEN_M0_Introduccion.pdf  -> ('M0', 'RESUMEN_Introduccion')
      M5_T_NLP_LLMs.txt            -> ('M5', 'T_NLP_LLMs')
    """
    stem = Path(filename).stem
    # Caso resumen
    m = re.match(r"^RESUMEN_(M\d+)_(.+)$", stem, re.IGNORECASE)
    if m:
        return (m.group(1).upper(), "RESUMEN_" + m.group(2))
    m = re.match(r"^(M\d+)_(.+)$", stem)
    if m:
        return (m.group(1).upper(), m.group(2))
    return ("M??", stem)


def _ask_claude_for_concepts(pdf_text: str, modulo: str, tema: str,
                              model: str = "claude-haiku-4-5") -> dict:
    """Pide a Claude el JSON de conceptos."""
    log = get_logger("concept_extractor")
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY no definida")
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("Paquete 'anthropic' no instalado")

    client = anthropic.Anthropic()
    user_msg = (
        f"MODULO: {modulo}\n"
        f"TEMA: {tema}\n\n"
        f"TEXTO DEL PDF:\n{pdf_text[:24000]}\n\n"
        "Devuelve EXCLUSIVAMENTE el JSON con los conceptos."
    )

    import time as _t
    _t0 = _t.monotonic()
    msg = client.messages.create(
        model=model,
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    try:
        from cockpit.core.usage_tracker import track_anthropic
        track_anthropic(msg, model=model, source="pipeline.concept_extractor",
                        kind="generation", latency_ms=int((_t.monotonic() - _t0) * 1000))
    except ImportError:
        pass
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        log.warning(f"  JSON invalido del LLM ({modulo} {tema}): {exc}")
        return {"concepts": []}
    if not isinstance(data, dict) or "concepts" not in data:
        return {"concepts": []}
    # Anyadir modulo/tema a cada concepto
    for c in data["concepts"]:
        c.setdefault("modulo", modulo)
        c.setdefault("tema", tema)
    log.debug(f"  {len(data['concepts'])} conceptos extraidos")
    return data


def extract_all_concepts(pdfs_folder: str | Path,
                         output_path: str | Path,
                         model: str = "claude-haiku-4-5",
                         skip_existing: bool = True,
                         delay_seconds: float = 0.3) -> dict:
    """
    Procesa todos los PDFs de la carpeta y genera el catalogo unificado.

    Si `skip_existing=True` y `output_path` ya existe, no procesa de nuevo
    los PDFs cuyas (modulo, tema) ya estan en el catalogo.
    """
    log = get_logger("concept_extractor")
    pdfs_folder = Path(pdfs_folder)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Estado previo
    catalog = {
        "version":     "1.0",
        "generated":   "",
        "by_pdf":      {},     # filename -> {modulo, tema, concepts}
        "by_concept":  {},     # slug -> [referencias]
    }
    if output_path.exists():
        try:
            catalog = json.loads(output_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    catalog.setdefault("by_pdf", {})
    catalog.setdefault("by_concept", {})

    pdfs = sorted([p for p in pdfs_folder.glob("*.pdf")])
    log.info(f"Encontrados {len(pdfs)} PDFs en {pdfs_folder}")

    processed = 0
    skipped = 0
    errors = 0

    for i, pdf in enumerate(pdfs, start=1):
        modulo, tema = _parse_module_topic(pdf.name)
        if skip_existing and pdf.name in catalog["by_pdf"]:
            skipped += 1
            log.info(f"  [{i:02d}/{len(pdfs)}] SKIP {pdf.name} (cacheado)")
            continue

        try:
            pdf_text = _read_pdf(pdf)
            if not pdf_text.strip():
                log.warning(f"  [{i:02d}/{len(pdfs)}] PDF vacio: {pdf.name}")
                errors += 1
                continue
            log.info(f"  [{i:02d}/{len(pdfs)}] {pdf.name} ({len(pdf_text)} chars) -> {modulo}/{tema}")
            data = _ask_claude_for_concepts(pdf_text, modulo, tema, model=model)
            concepts = data.get("concepts", [])
            catalog["by_pdf"][pdf.name] = {
                "modulo":   modulo,
                "tema":     tema,
                "concepts": concepts,
            }
            for c in concepts:
                slug = c.get("slug") or c.get("name", "").lower().replace(" ", "_")
                catalog["by_concept"].setdefault(slug, []).append({
                    "modulo": modulo, "tema": tema, "pdf": pdf.name,
                    "name":   c.get("name"),
                    "definicion": c.get("definicion"),
                    "luma_prompt": c.get("luma_prompt"),
                    "visual_idea": c.get("visual_idea"),
                    "importance":  c.get("importance"),
                })
            processed += 1

            # Persistir parcial cada 5 PDFs
            if processed % 5 == 0:
                output_path.write_text(
                    json.dumps(catalog, indent=2, ensure_ascii=False),
                    encoding="utf-8")
                log.info(f"  ...checkpoint guardado ({processed} procesados)")

        except Exception as exc:
            log.error(f"  Error procesando {pdf.name}: {exc}")
            errors += 1

        time.sleep(delay_seconds)

    # Final
    catalog["generated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    catalog["stats"] = {
        "pdfs_total":     len(pdfs),
        "pdfs_processed": processed,
        "pdfs_skipped":   skipped,
        "pdfs_errors":    errors,
        "concepts_total": sum(len(v["concepts"]) for v in catalog["by_pdf"].values()),
        "concept_slugs":  len(catalog["by_concept"]),
    }
    output_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False),
                           encoding="utf-8")
    log.info(f"Catalogo guardado: {output_path}")
    log.info(f"  procesados={processed} skipped={skipped} errors={errors}")
    log.info(f"  conceptos totales: {catalog['stats']['concepts_total']}")
    log.info(f"  conceptos unicos:  {catalog['stats']['concept_slugs']}")
    return catalog


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdfs", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--model", default="claude-haiku-4-5")
    parser.add_argument("--no-skip", action="store_true")
    args = parser.parse_args()

    # Cargar .env de la raiz real del proyecto
    from dotenv import load_dotenv
    load_dotenv(r"C:\Users\Asus\maquinaria_pesada\.env", override=True)

    extract_all_concepts(args.pdfs, args.out, model=args.model,
                         skip_existing=not args.no_skip)
