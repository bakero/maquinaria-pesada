"""Prompts del panel editorial — uno por modo (por-guion y corpus).

Fuente normativa: `EVALUADOR_EDITORIAL_GUIONES.md §6`.

Se envían a Claude Sonnet (default: claude-sonnet-4-6). Coste estimado por
guion en modo por-guion: ~$0.034. Coste estimado corpus 41 guiones: ~$0.55.
"""
from __future__ import annotations

from pathlib import Path

from editorial.perspectives import (
    PERSPECTIVE_WEIGHTS,
    PERSPECTIVES,
    TYPE_SPECIFIC_AXES,
)

# Modelo recomendado por el desempate 2026-05-19.
DEFAULT_MODEL = "claude-sonnet-4-6"


def _format_weights_table() -> str:
    rows = ["| Perspectiva | M | T | S |", "|---|---|---|---|"]
    for p in PERSPECTIVES:
        m = PERSPECTIVE_WEIGHTS["M"][p.key]
        t = PERSPECTIVE_WEIGHTS["T"][p.key]
        s = PERSPECTIVE_WEIGHTS["S"][p.key]
        s_label = "0.00 (N/A)" if s == 0.0 else f"{s:.2f}"
        rows.append(f"| {p.label} | {m:.2f} | {t:.2f} | {s_label} |")
    return "\n".join(rows)


def _format_specific_axes(kind: str) -> str:
    axes = TYPE_SPECIFIC_AXES[kind]
    lines = []
    for axis_key, perspective_key, question in axes:
        lines.append(f"- **{axis_key}** ({perspective_key}): {question}")
    return "\n".join(lines)


_PROMPT_MAESTRO_TEMPLATE = """\
Sos un panel editorial de 5 voces que evalúa guiones del podcast
MaquinarIA Pesada. El podcast es un proyecto de "arquitecto de sistemas
que construye un podcast de IA con IA". Audiencia técnica hispana. Tono
directo, anti-AI-bro, anti-NotebookLM. Referentes positivos: Lex Fridman,
Karpathy, Veritasium, Latent Space, Dwarkesh Patel. Anti-referentes: Dot
CSV, coaches LinkedIn, podcasts de IA en español genéricos.

INPUT que vas a recibir:
1. Tipo de guion: {kind}
2. Contenido del guion .txt (más abajo).
3. Visión de producto (§1 de EVALUADOR_EDITORIAL_GUIONES.md, embebida).
4. Ejes adaptados al tipo (matriz §3 embebida).

PERSPECTIVAS DEL PANEL:

{perspectives_block}

PESOS POR PERSPECTIVA Y TIPO (suma 1.00 por columna):

{weights_table}

EJES ESPECÍFICOS DEL TIPO {kind}:

{specific_axes}

CRITERIOS DEL VEREDICTO:

- PUBLICAR ✅  score ≥ 7.5  Y  0 issues críticos en ninguna perspectiva.
- REVISAR  🟡  6.0 ≤ score < 7.5  O  1-2 críticos (sin asimetría de marca).
- BLOQUEAR 🔴  score < 6.0  O  ≥3 críticos  O  ≥1 crítico en MARCA.

INSTRUCCIONES:

1. Lee el guion como si lo fueras a escuchar en el coche, no como un linter.
   Tu trabajo es decir si funciona como podcast.
2. Adopta sucesivamente cada perspectiva. Para cada una:
   - Da un score 1-10 con UNA línea de justificación.
   - Identifica 3-5 issues priorizados. Cada issue:
     [crítico|relevante|menor] · eje · "frase del problema" → "propuesta"
   - Las propuestas tienen que ser concretas (qué cambiar exactamente,
     no "mejorar el hook").
3. Aplica los ejes específicos del tipo arriba.
4. Calcula el score global ponderado según los pesos.
5. Sitúa el guion en el mapa de referentes (Top tier / Sólido sectorial /
   Estándar IA / Bajo / Crítico) con UNA frase comparativa concreta.
6. Emite veredicto: PUBLICAR ✅ · REVISAR 🟡 · BLOQUEAR 🔴.
7. Si el veredicto es REVISAR o BLOQUEAR, lista las 2-3 cosas concretas
   que hay que cambiar para subir UN nivel.

NO HAGAS:
- Ni "¡excelente guion!" ni "tiene mucho potencial". Sé directo.
- No restaures el guion completo en tu output.
- No valides reglas técnicas (eso lo hace validators/).
- No juzgues la frase canónica del cierre — es literal e intocable
  (HARD-FAIL técnico). El eje `cierre` evalúa SOLO la intervención previa
  y cómo enlaza con la frase canónica.
- No inventes datos de mercado para justificar tus scores.
- No sugieras añadir emojis ni cambios contra el style_guide.

FORMATO DE OUTPUT: estrictamente el template Markdown que se especifica
en `editorial.report.render_markdown` — encabezado, panel por perspectiva,
ejes específicos, "Para subir de nivel".

---

GUION A EVALUAR ({episode_id}):

{script_text}
"""


_PROMPT_CORPUS_TEMPLATE = """\
Acabás de leer N guiones (M/T/S mezclados) del podcast MaquinarIA Pesada.
Además de la evaluación individual de cada uno (que ya hiciste o que vas a
hacer en este mismo prompt si N es manejable), responde estas 4 preguntas
sobre el corpus como conjunto:

1. RANKING — ordená los guiones del mismo tipo por score global descendente.
   Identificá los 3 mejores y los 3 peores de cada tipo.

2. CONSISTENCIA DE MARCA — ¿suenan todos a la misma marca? Si hay derivas
   (M0-M3 vs M8-M14, por ejemplo), señalalas con guiones concretos.

3. DERIVAS DE PROFUNDIDAD — ¿se simplifica el corpus a lo largo del tiempo?
   ¿Hay temas críticos del máster que se cubren con menos rigor que otros?

4. SATURACIÓN — ¿qué casos empresariales se repiten? ¿Hay ejemplos
   sobreusados (JPMorgan, OpenAI, etc.)? ¿Se diversifica el catálogo?

OUTPUT: sección "AUDITORÍA DE CORPUS" añadida al final del informe, antes
del cierre.

---

GUIONES EVALUADOS:

{scripts_block}
"""


def _perspectives_block() -> str:
    out = []
    for p in PERSPECTIVES:
        out.append(f"### {p.label} ({p.key})")
        out.append(f"_{p.persona}_")
        out.append("Ejes: " + ", ".join(p.axes))
        if not p.applies_to_s:
            out.append("⚠ Esta perspectiva NO se aplica en episodios S.")
        out.append("")
    return "\n".join(out)


def build_prompt_maestro(kind: str, episode_id: str, script_text: str) -> str:
    """Construye el prompt maestro para un guion individual."""
    if kind not in PERSPECTIVE_WEIGHTS:
        raise ValueError(f"Tipo desconocido: {kind!r}")
    return _PROMPT_MAESTRO_TEMPLATE.format(
        kind=kind,
        episode_id=episode_id,
        perspectives_block=_perspectives_block(),
        weights_table=_format_weights_table(),
        specific_axes=_format_specific_axes(kind),
        script_text=script_text,
    )


def build_prompt_corpus(scripts: list[tuple[str, str, str]]) -> str:
    """Prompt para auditoría de corpus.

    `scripts`: lista de tuplas `(kind, episode_id, script_text)`.
    """
    blocks: list[str] = []
    for kind, ep_id, text in scripts:
        blocks.append(f"=== {ep_id} ({kind}) ===\n{text}\n")
    return _PROMPT_CORPUS_TEMPLATE.format(scripts_block="\n".join(blocks))


def visiona_producto_summary(repo_root: Path | None = None) -> str:
    """Resumen de la visión de producto que se inyecta en el prompt.

    Si existe `EVALUADOR_EDITORIAL_GUIONES.md` en el repo, devuelve sus
    secciones §1.1 a §1.4. Si no, devuelve un resumen mínimo.
    """
    repo_root = repo_root or Path(__file__).resolve().parents[1]
    doc = repo_root / "EVALUADOR_EDITORIAL_GUIONES.md"
    if doc.exists():
        return doc.read_text(encoding="utf-8")
    # Fallback mínimo (no debería ocurrir).
    return (
        "Marca: arquitecto de sistemas, no AI bro. Anti-NotebookLM. "
        "Audiencia técnica hispana. Tono directo, ironía sin abuso."
    )
