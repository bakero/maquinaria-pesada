"""
Generador de escaletas de produccion para los videopodcasts.

Una escaleta es el documento maestro que un guionista de programa entrega
a edicion: dice momento a momento que pasa en pantalla, que camara, que
elementos aparecen, que transiciones.

Workflow:
  1. Recolecta inputs: aligned_interventions, audio_structure, conceptos
     del PDF y del catalogo, log de produccion.
  2. Construye un esqueleto deterministico (bloques + intervenciones con
     timestamps absolutos).
  3. Pasa el esqueleto + conceptos a Claude (Sonnet) con prompt de
     guionista profesional.
  4. Claude devuelve un markdown estructurado con planos, on-screen y
     transiciones por intervencion.
  5. Se guarda en escaletas/<episode_id>_escaleta.md.

Uso:
    from pipeline.escaleta_generator import generate_escaleta
    md_path = generate_escaleta(
        episode_id="EP-MOD000",
        modulo="M0",
        ...
    )
"""

import json
import os
import re
import time
from pathlib import Path

from .logger import get_logger


# ─── Plantillas y constantes ─────────────────────────────────────────────

PLANOS_DISPONIBLES = """
- ESTABLISHING        plano amplio del estudio con ambos visibles
- TWO_SHOT_M_ACTIVE   ambos en cuadro, Maria habla, Yago escucha
- TWO_SHOT_Y_ACTIVE   ambos en cuadro, Yago habla, Maria escucha
- CLOSE_UP_MARIA      primer plano Maria
- CLOSE_UP_YAGO       primer plano Yago
- DETAIL              detalle (microfono, manos, libreta)
- BOTH_COMPLICIT      ambos sonriendo / asintiendo (humor)
- OUTRO               cierre, ambos quitando auriculares
- PIZARRA             frame de pizarra con datos / graficos / imagenes
""".strip()


SYSTEM_PROMPT = """Eres GUIONISTA SENIOR de programas de television de
divulgacion. Llevas 15 anos en cadenas espanolas (La Sexta, Cuatro,
RTVE, Movistar+) y has trabajado tanto en magazines como en documentales
divulgativos. Conoces a la perfeccion el ritmo de un programa: cuando
mantener el plano para que respire una idea, cuando cortar, cuando hacer
inserto, cuando tirar de pantalla con grafico o video B-roll.

Tu tarea: convertir un guion ya producido (audio listo + intervenciones
con timestamps reales) en una ESCALETA DE PRODUCCION en markdown que el
editor de video pueda seguir sin ambiguedad.

Reglas firmes:

1. **NUNCA cambies el texto de las intervenciones**: lo que el speaker
   dice esta fijado por el audio.

2. **Cambia de plano SOLO en pausas naturales** (puntos, signos de
   interrogacion, finales de idea). Nunca cortes a mitad de frase.

3. **Intervenciones cortas (<6s) = plano amplio (ESTABLISHING)**. No
   merece la pena un primer plano para una sola frase.

4. **Intervenciones largas (>=12s) con un solo speaker = TWO_SHOT del
   speaker activo o CLOSE_UP**. Alterna entre ambas variantes para no
   aburrir.

5. **Hook**: usa TWO_SHOT del speaker activo. Pizarra solo si hay un dato
   muy potente (88%, 12%) que merezca aparicion.

6. **Bloques didacticos** (BLOQUE_1, BLOQUE_2...): es donde mas se
   usa la PIZARRA. Cuando el speaker explica un concepto definible
   (RAG, Transformers, EU AI Act, modelos frontier...), la pizarra
   muestra el concepto con su definicion + imagen / icono.

7. **Cierre conceptos**: PIZARRA con recap_grid de todos los conceptos
   clave del episodio.

8. **Cierre final / despedida**: OUTRO.

9. **On-screen**: para cada intervencion, decide:
   - Que overlay aparece (stat_card, hierarchy, timeline_visual,
     concept_card_image, regulation_alert, etc.)
   - Cuando entra (segundo dentro de la intervencion)
   - Cuando sale (en la pausa / al final / cuando cambia el tema)
   - Posicion en pantalla
   - Color (#F5C400 amarillo Maria/datos, #4DB8FF azul Yago/tecnico,
     #CC2200 rojo regulacion/alertas)

10. Usa los CONCEPTOS DEL MASTER que te paso para inspirar las cards
    visuales: si un concepto del temario aparece en la intervencion,
    proponlo como overlay con su definicion sintetizada.

11. **Estilo de notas de direccion**: directo, en imperativo. "Corte
    seco en pausa tras 88%". "Mantener plano hasta cierre de idea".
    No metaforas, no relleno.

12. Numera las intervenciones dentro de cada bloque: 1.1, 1.2, ...

# FORMATO DE SALIDA

Markdown estructurado. Empieza con un frontmatter YAML, luego un bloque
por seccion del guion. Cada intervencion en una tabla limpia. Notas de
direccion al final de cada bloque.

Ejemplo de bloque:

```
## BLOQUE 1 · HOOK
**TC IN:** `00:01.91`  **TC OUT:** `00:35.21`  **DUR:** 33.30s

### 1.1 — María
- **TC:** `00:01.91 → 00:18.95` · **DUR:** 17.04s
- **TONO:** [ironico]
- **TEXTO:**
  > En 2026, el 88% de las empresas dice que ya usa inteligencia
  > artificial. El otro 12% dice que lo está evaluando...
- **PLANO:** TWO_SHOT_M_ACTIVE (camara fija, ligera respiracion)
- **ON-SCREEN:**
  | t (relativo) | Elemento | Posición | Salida |
  |---|---|---|---|
  | 03.0s | stat_card "ADOPCIÓN 2026 · 88% empresas usan IA" amarillo | MID_LEFT | hasta fin |
  | 06.5s | stat_card "EVALUANDO · 12% siguen estudiándolo" gris | MID_RIGHT | hasta fin |
  | 14.0s | sticker "nobody_reads_tos" | BOTTOM_LEFT | 17.0s |
- **TRANSICION OUT:** corte seco en la pausa tras "exactamente nadie".

### 1.2 — María
...

> **NOTA DIRECCION:** El hook tira de ironia. Mantener clima visual
> oscuro y tipografia grande. Ningun corte hasta que la idea cierre.
```

Devuelve SOLO el markdown completo de la escaleta. Empieza con el
frontmatter `---`. No anyadas explicaciones fuera del documento.
"""


# ─── Helpers ─────────────────────────────────────────────────────────────


def _format_tc(seconds: float) -> str:
    """MM:SS.mmm format."""
    seconds = max(0.0, float(seconds))
    m = int(seconds // 60)
    s = seconds - m * 60
    return f"{m:02d}:{s:06.3f}"


def _filter_concepts_by_module(concepts_index: dict, modulo: str) -> list[dict]:
    """Devuelve la lista de conceptos del catalogo que pertenecen a `modulo`."""
    out = []
    for fname, data in concepts_index.get("by_pdf", {}).items():
        if data.get("modulo", "").upper() == modulo.upper():
            for c in data.get("concepts", []):
                out.append({
                    "name":         c.get("name"),
                    "slug":         c.get("slug"),
                    "definicion":   c.get("definicion"),
                    "sinonimos":    c.get("sinonimos", []),
                    "visual_idea":  c.get("visual_idea"),
                    "luma_prompt":  c.get("luma_prompt"),
                    "importance":   c.get("importance"),
                    "tema":         data.get("tema"),
                })
    return out


def _ensure_timestamps(interventions: list[dict],
                        audio_structure: dict) -> list[dict]:
    """
    Garantiza que cada intervencion tenga `start` y `end`. Si no los tiene,
    los reconstruye distribuyendo proporcionalmente en su rango (HOOK o
    CONTENT) segun audio_structure.
    """
    if all("start" in iv and "end" in iv for iv in interventions):
        return interventions

    hook_start = float(audio_structure.get("hook_start") or 0.0)
    hook_end = float(audio_structure.get("hook_end") or hook_start)
    content_start = float(audio_structure.get("content_start") or hook_end)
    content_end = float(audio_structure.get("content_end") or
                        audio_structure.get("audio_duration") or
                        content_start + 600)

    SKIP = {"INTRO_SONIDO", "SINTONIA", "VERIFICACIONES"}
    hook_ivs = [iv for iv in interventions
                if (iv.get("section") or "").upper() == "HOOK"]
    content_ivs = [iv for iv in interventions
                   if (iv.get("section") or "").upper() not in (SKIP | {"HOOK"})]

    def _distribute(group, t_a, t_b):
        if not group or t_b <= t_a:
            return
        total = sum(max(len((iv.get("text") or "").split()), 1) for iv in group) or 1
        cur = t_a
        for iv in group:
            share = max(len((iv.get("text") or "").split()), 1) / total
            dur = (t_b - t_a) * share
            iv["start"] = round(cur, 3)
            iv["end"] = round(min(cur + dur, t_b), 3)
            cur += dur

    _distribute(hook_ivs, hook_start, hook_end)
    _distribute(content_ivs, content_start, content_end)
    return interventions


def _build_skeleton(aligned_interventions: list[dict],
                    audio_structure: dict) -> dict:
    """
    Construye un esqueleto con bloques por seccion + intervenciones con TC.
    """
    aligned_interventions = _ensure_timestamps(aligned_interventions, audio_structure)
    blocks = {}  # section -> [interventions]
    for iv in aligned_interventions:
        sec = (iv.get("section") or "UNKNOWN").upper()
        blocks.setdefault(sec, []).append(iv)

    structure = {
        "audio_duration":  audio_structure.get("audio_duration"),
        "lead_silence":    [0.0, audio_structure.get("hook_start") or 0.0],
        "hook":            [audio_structure.get("hook_start") or 0.0,
                           audio_structure.get("hook_end") or 0.0],
        "sintonia":        [audio_structure.get("sintonia_start"),
                           audio_structure.get("sintonia_end")],
        "content_start":   audio_structure.get("content_start"),
        "content_end":     audio_structure.get("content_end"),
        "blocks":          blocks,
    }
    return structure


def _serialize_skeleton_for_llm(skeleton: dict, max_text_chars: int = 600) -> str:
    """Serializa el esqueleto en formato que el LLM puede consumir."""
    out = []
    out.append(f"AUDIO DURATION: {skeleton['audio_duration']:.2f}s")
    out.append(f"LEAD SILENCE:   [{skeleton['lead_silence'][0]:.2f}, {skeleton['lead_silence'][1]:.2f}]")
    out.append(f"SINTONIA:       [{skeleton['sintonia'][0]}, {skeleton['sintonia'][1]}]")
    out.append(f"CONTENT START:  {skeleton['content_start']}")
    out.append(f"CONTENT END:    {skeleton['content_end']}")
    out.append("")
    out.append("# INTERVENCIONES POR BLOQUE")
    for sec, ivs in skeleton["blocks"].items():
        if sec in ("INTRO_SONIDO", "VERIFICACIONES"):
            continue
        out.append(f"\n## {sec}")
        for i, iv in enumerate(ivs, 1):
            text = (iv.get("text") or "").strip()
            if len(text) > max_text_chars:
                text = text[:max_text_chars] + "..."
            tones = iv.get("tones", [])
            tones_s = " ".join(f"[{t}]" for t in tones) if tones else ""
            out.append(
                f"  {i}. tc=[{iv['start']:.3f}, {iv['end']:.3f}] "
                f"speaker={iv['speaker']} {tones_s}\n"
                f"     {text}"
            )
    return "\n".join(out)


def _serialize_concepts_for_llm(concepts: list[dict], limit: int = 60) -> str:
    """Serializa conceptos del modulo de forma compacta."""
    if not concepts:
        return "(sin conceptos extraidos del PDF)"
    lines = []
    for i, c in enumerate(concepts[:limit], 1):
        defn = (c.get("definicion") or "")[:120]
        lines.append(f"  {i}. **{c.get('name')}** — {defn}")
    return "\n".join(lines)


# ─── Funcion publica ─────────────────────────────────────────────────────


def generate_escaleta(episode_id: str,
                     modulo: str,
                     aligned_interventions_path: str | Path,
                     audio_structure_path: str | Path,
                     concepts_index_path: str | Path | None,
                     output_dir: str | Path,
                     audio_duration_s: float | None = None,
                     model: str = "claude-sonnet-4-5",
                     dry_run: bool = False) -> Path:
    """
    Genera la escaleta del episodio en markdown.

    Returns: Path al archivo escaletas/<episode_id>_escaleta.md
    """
    log = get_logger("escaleta_generator")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{episode_id}_escaleta.md"

    # Cargar inputs
    aligned = json.loads(Path(aligned_interventions_path).read_text(encoding="utf-8"))
    audio_structure = json.loads(Path(audio_structure_path).read_text(encoding="utf-8"))

    concepts = []
    if concepts_index_path and Path(concepts_index_path).exists():
        idx = json.loads(Path(concepts_index_path).read_text(encoding="utf-8"))
        concepts = _filter_concepts_by_module(idx, modulo)
        log.info(f"  conceptos del modulo {modulo}: {len(concepts)}")

    skeleton = _build_skeleton(aligned, audio_structure)
    skeleton_text = _serialize_skeleton_for_llm(skeleton)
    concepts_text = _serialize_concepts_for_llm(concepts)

    log.info(f"  esqueleto construido: {sum(len(v) for v in skeleton['blocks'].values())} "
             f"intervenciones en {len(skeleton['blocks'])} bloques")

    if dry_run:
        out_path.write_text(
            f"# DRY-RUN ESCALETA · {episode_id}\n\n"
            f"```\n{skeleton_text}\n```\n\n"
            f"## Conceptos del modulo\n{concepts_text}\n",
            encoding="utf-8")
        log.info(f"  dry-run guardado en {out_path}")
        return out_path

    # Llamar a Claude
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY no definida")
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("Paquete 'anthropic' no instalado")

    client = anthropic.Anthropic()
    user_msg = (
        f"# CONTEXTO DEL EPISODIO\n"
        f"Episode ID: {episode_id}\n"
        f"Modulo: {modulo}\n\n"
        f"# ESQUELETO TEMPORAL\n{skeleton_text}\n\n"
        f"# CONCEPTOS DEL TEMARIO (para inspirar pizarra)\n{concepts_text}\n\n"
        f"# PLANOS DISPONIBLES\n{PLANOS_DISPONIBLES}\n\n"
        f"Genera la escaleta de produccion completa en markdown."
    )

    log.info(f"  solicitando escaleta a Claude ({model})...")
    t0 = time.time()
    msg = client.messages.create(
        model=model,
        max_tokens=12000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    elapsed = time.time() - t0

    if not msg.content:
        raise RuntimeError("Respuesta vacia de Claude")
    md = msg.content[0].text.strip()
    if md.startswith("```"):
        md = re.sub(r"^```(?:markdown)?\s*", "", md)
        md = re.sub(r"\s*```$", "", md)

    out_path.write_text(md, encoding="utf-8")
    log.info(f"  escaleta generada en {elapsed:.1f}s "
             f"(in_tok={msg.usage.input_tokens} out_tok={msg.usage.output_tokens}) "
             f"-> {out_path}")
    return out_path
