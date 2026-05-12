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


SYSTEM_PROMPT = """Eres GUIONISTA SENIOR y REALIZADOR de programas de
television de divulgacion. Llevas 15 anos en cadenas espanolas (La Sexta,
Cuatro, RTVE, Movistar+) y has trabajado en magazines y documentales
divulgativos. Conoces el ritmo: cuando mantener el plano para que respire
una idea, cuando cortar, cuando hacer inserto, cuando tirar de pantalla
con grafico o video B-roll.

Tu tarea: convertir un guion ya producido (audio listo + intervenciones
con timestamps reales) en una ESCALETA DE PRODUCCION en markdown que el
editor de video pueda seguir sin ambiguedad.

# LAYOUT DEL VIDEOPODCAST

El video tiene DOS modos visuales:

  - **MODO ESTUDIO**: pantalla completa con clip del estudio (presentador
    o two-shot). Es el modo por defecto. Lo eliges marcando `PIZARRA: NO`.

  - **MODO PIZARRA**: la pizarra ocupa toda la pantalla con datos /
    imagenes / graficos / memes. El presentador aparece reducido en una
    burbuja (PIP) en la esquina inferior derecha (~25% del ancho).
    Lo eliges marcando `PIZARRA: SI`.

# REGLAS DE PRODUCCION

1. **NUNCA cambies el texto de las intervenciones**: lo que el speaker
   dice esta fijado por el audio.

2. **Cambia de plano SOLO en pausas naturales** (puntos, signos de
   interrogacion, finales de idea). Nunca cortes a mitad de frase.

3. **Intervenciones cortas (<6s) = ESTABLISHING + PIZARRA: NO**. No
   merece la pena ni primer plano ni pizarra para una sola frase.

4. **Intervenciones medias (6-12s)**: TWO_SHOT del speaker activo. La
   pizarra solo si hay UN dato muy potente que merezca aparicion.

5. **Intervenciones largas (>=12s) con material visual**: PIZARRA: SI.
   Si no hay material visual sustantivo, mantener MODO ESTUDIO con
   TWO_SHOT del speaker.

6. **REGLA DE LA PIZARRA (critica)**:
   - Cuando marcas `PIZARRA: SI` la pizarra dura **MINIMO 15s** y se
     mantiene durante toda la intervencion si dura mas.
   - **Un elemento nuevo cada 4 segundos**. Pizarra de 20s = 5 elementos
     en t=0, 4, 8, 12, 16. NO menos.
   - El contenido VINCULA al parrafo que se esta diciendo, pero NO
     transcribe lo que dice. Es la INFOGRAFIA que acompana al texto.

# ⛔ PROHIBIDO ABSOLUTAMENTE EN LA PIZARRA ⛔

**Piensa en la pizarra como las infografias de un libro de texto. NUNCA
es un teleprompter ni un subtitulado.** Los subtitulos van abajo
(automaticos desde Whisper); la pizarra es OTRA cosa.

NUNCA pongas en la pizarra:
- ❌ Las preguntas que el presentador hace ("¿Que es la IA?", "¿Por que
  ahora?", "¿De donde viene?")
- ❌ Frases literales de lo que dice el presentador
- ❌ Subtitulos / transcripcion de la intervencion
- ❌ Tag-lines o lemas del propio podcast como overlay (excepto en outro)

SOLO pon en la pizarra:
- ✅ Datos cuantitativos (porcentajes, anyos, cifras de mercado)
- ✅ Comparaciones (A vs B, antes vs ahora, util vs riesgo)
- ✅ Listas de items conceptuales (no preguntas, items)
- ✅ Definiciones cortas de conceptos tecnicos (RAG, Transformer, LLM)
- ✅ Logos / iconos / referencias visuales
- ✅ Memes/stickers que ilustren la emocion ironica
- ✅ Lineas de tiempo (1957→2017→2024)
- ✅ Diagramas de jerarquia (IA ⊃ ML ⊃ DL ⊃ LLMs)
- ✅ Citas externas atribuidas (estudios McKinsey, papers, expertos
  con nombre)

# EJEMPLOS GOOD vs BAD

**Intervencion**: "¿Que es la IA? ¿De donde viene? ¿Como se estructura?
¿Y que implica para cualquier organizacion que no quiera quedarse atras?"

❌ MAL (LO QUE NO HACER):
| 00.0s | highlight_quote "¿Que es la IA?" | TOP_CENTER | hasta fin |
| 04.0s | highlight_quote "¿De donde viene?" | MID_LEFT | hasta fin |
| 08.0s | highlight_quote "¿Como se estructura?" | MID_RIGHT | hasta fin |

✅ BIEN (LO QUE SI HACER):
| 00.0s | hierarchy_diagram "IA ⊃ ML ⊃ DL ⊃ LLMs" amarillo | MID_CENTER | hasta fin |
| 04.0s | timeline_visual "1957 Dartmouth · 2017 Transformers · 2024 GPT-4" amarillo | BOTTOM_FULL_WIDTH | hasta fin |
| 08.0s | stat_card "INVERSION GLOBAL IA · $200B 2026" amarillo | MID_LEFT | hasta fin |
| 12.0s | recap_grid "Que es · De donde · Estructura · Implicacion" gris | MID_RIGHT | hasta fin |
| 16.0s | sticker "AI_meme_competing" | BOTTOM_LEFT | hasta fin |

**Intervencion**: "El otro 12% dice que lo esta evaluando."

❌ MAL: highlight_quote "El otro 12% dice que lo esta evaluando"
✅ BIEN: stat_card "EVALUANDO · 12% siguen estudiandolo" gris

# REGLA DE ORO

Antes de poner cualquier elemento en la tabla on-screen, preguntate:
**"¿Esto agrega informacion VISUAL que el subtitulo NO da?"**

- Si la respuesta es SI (es un dato, grafico, imagen, comparacion) -> ponlo.
- Si la respuesta es NO (es lo mismo que dice el presentador) -> BORRA.

El elemento `highlight_quote` queda RESERVADO para citas EXTERNAS
atribuidas (ej. "Andrew Ng, Stanford, 2024") con autor obligatorio.
NUNCA para frases del propio guion.

7. **DENSIDAD MINIMA DE PIZARRA**: en cualquier ventana de 3 minutos
   de podcast debe haber al menos UNA pizarra. No dejes pasar mas
   tiempo. Si una zona del guion es muy "oratoria" sin datos, busca
   un concepto del temario, un meme/sticker que ilustre la emocion,
   o un grafico abstracto (timeline_visual del avance historico, etc.).

8. **No repitas clips**: el editor rotara automaticamente los clips de
   estudio dentro de cada intervencion. Tu solo decides el PLANO; el
   pipeline elige el clip especifico.

9. **Hook**: usa TWO_SHOT del speaker activo. Marcar `PIZARRA: SI` en
   los huecos donde hay datos potentes (porcentajes, comparaciones).

10. **Bloques didacticos** (BLOQUE_1, BLOQUE_2...): es donde MAS se
    usa la pizarra. Por cada concepto definible (RAG, Transformers,
    EU AI Act, modelos frontier...), invoca pizarra con stat_cards,
    hierarchy_diagram, timeline_visual, etc.

11. **Cierre conceptos**: PIZARRA con recap_grid de todos los conceptos
    clave del episodio (>=20s).

12. **Cierre final / despedida**: OUTRO + PIZARRA: NO.

13. **On-screen para PIZARRA: SI**: la tabla on-screen tiene que
    contener un elemento cada 4 segundos. Por ejemplo, intervencion de
    20s -> 5 filas (t=0, 4, 8, 12, 16). Cada fila con elemento DISTINTO.

14. **On-screen para PIZARRA: NO**: la tabla puede tener 0-1 elementos
    pequenos (sticker, badge), o estar vacia. NO sobrecargues estudio
    con overlays porque la atencion esta en el presentador.

15. **Color de los overlays**:
    - #F5C400 amarillo CAT: datos generales / Maria
    - #4DB8FF azul: tecnico / Yago
    - #CC2200 rojo: regulacion / alertas / EU AI Act

16. **Estilo de notas de direccion**: directo, imperativo. "Corte seco
    en pausa tras 88%". "Mantener plano hasta cierre de idea". No
    metaforas, no relleno.

17. Numera las intervenciones dentro de cada bloque: 1.1, 1.2, ...

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
- **PLANO:** TWO_SHOT_M_ACTIVE
- **PIZARRA:** SI
- **ON-SCREEN:** (un elemento cada 4s mientras la pizarra esta activa)
  | t (relativo) | Elemento | Posición | Salida |
  |---|---|---|---|
  | 00.0s | stat_card "ADOPCIÓN 2026 · 88% empresas usan IA" amarillo | MID_LEFT | hasta fin |
  | 04.0s | stat_card "EVALUANDO · 12% siguen estudiándolo" gris | MID_RIGHT | hasta fin |
  | 08.0s | bar_chart "Adopcion vs Evaluacion · 88% vs 12%" amarillo | MID_CENTER | hasta fin |
  | 12.0s | sticker "nobody_reads_tos" | BOTTOM_LEFT | hasta fin |
  | 16.0s | warning_badge "TODOS DICEN QUE SI" rojo | TOP_CENTER | hasta fin |
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
    # max_tokens 32000: con la regla v2 de pizarra (tabla on-screen densa)
    # los 16000 se quedaban cortos. Sonnet 4.5 admite >60k output. Anthropic
    # exige streaming cuando estimated_time > 10min, asi que streameamos.
    msg_chunks = []
    usage_in = 0
    usage_out = 0
    with client.messages.stream(
        model=model,
        max_tokens=32000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        for text in stream.text_stream:
            msg_chunks.append(text)
        final_msg = stream.get_final_message()
        usage_in = final_msg.usage.input_tokens
        usage_out = final_msg.usage.output_tokens

    class _Shim:
        pass
    msg = _Shim()
    msg.content = [_Shim()]
    msg.content[0].text = "".join(msg_chunks)
    msg.usage = _Shim()
    msg.usage.input_tokens = usage_in
    msg.usage.output_tokens = usage_out
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

    # ── QA POST-GENERACION ─────────────────────────────────────────
    # Verificacion de que el LLM no haya copiado texto del guion en
    # la pizarra. Si falla, intenta auto-corregir con un segundo pass.
    from . import qa as _qa
    sem = _qa.check_escaleta_semantic(out_path, max_overlap_ratio=0.4)
    log.info(f"  [QA semantic] ok={sem['ok']} overlays={sem['checks']['total_overlays']} "
             f"questions_as_quote={sem['checks']['quote_with_question']} "
             f"script_overlap={sem['checks']['overlap_with_script']}")
    if not sem["ok"]:
        for e in sem["errors"]:
            log.warning(f"    QA FAIL: {e}")
        for ex in sem["checks"].get("examples", [])[:5]:
            log.warning(f"    {ex}")
        log.info("  Lanzando auto-heal: pidiendo a Claude que corrija los overlays...")
        out_path = _autoheal_escaleta(client, model, out_path, sem,
                                       skeleton_text, concepts_text, log)

    return out_path


def _autoheal_escaleta(client, model: str, out_path: Path,
                       sem_qa: dict, skeleton_text: str,
                       concepts_text: str, log) -> Path:
    """Segundo pass: pide a Claude que corrija los overlays mal puestos.
    Le pasa la escaleta mala + los errores QA + las reglas duras."""
    bad_md = out_path.read_text(encoding="utf-8")
    bad_examples = "\n".join(sem_qa["checks"].get("examples", [])[:15])

    fix_prompt = f"""La siguiente escaleta tiene overlays mal puestos en
la pizarra. Falla el QA semantico:

- Total overlays: {sem_qa['checks']['total_overlays']}
- Overlays que son preguntas literales del guion: {sem_qa['checks']['quote_with_question']}
- Overlays que solapan >40% con texto del guion: {sem_qa['checks']['overlap_with_script']}

Ejemplos detectados:
{bad_examples}

REGLA INVIOLABLE: la pizarra NUNCA contiene texto que el presentador
diga. Si una intervencion es "¿Que es la IA? ¿De donde viene?", la
pizarra NO puede tener esas preguntas como overlay. Tiene que mostrar
DATOS / GRAFICOS / IMAGENES / DEFINICIONES (no las preguntas literales).

Reemplazos validos para el patron "preguntas como overlays":
- En lugar de highlight_quote "¿Que es la IA?" -> hierarchy_diagram
  "IA ⊃ ML ⊃ DL ⊃ LLMs"
- En lugar de highlight_quote "¿De donde viene?" -> timeline_visual
  "1957 Dartmouth · 2017 Transformer · 2024 GPT-4o"
- En lugar de highlight_quote "¿Como se estructura?" -> recap_grid
  "Datos · Algoritmos · Modelos · Aplicaciones"

# CONTEXTO ESQUELETO (no cambies textos ni TCs)
{skeleton_text}

# CONCEPTOS DEL TEMARIO (usalos para reemplazar las preguntas como
# overlays informativos)
{concepts_text}

# ESCALETA QUE TIENES QUE CORREGIR
```markdown
{bad_md}
```

Devuelve la escaleta CORREGIDA completa en markdown. CAMBIA solo las
filas de la tabla on-screen donde hay overlays mal puestos. Mantiene
TODOS los demas campos identicos (TC, TEXTO, PLANO, PIZARRA, TONO,
TRANSICION OUT, NOTA DIRECCION).
"""
    log.info("  auto-heal: streaming respuesta...")
    chunks = []
    with client.messages.stream(
        model=model,
        max_tokens=32000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": fix_prompt}],
    ) as stream:
        for text in stream.text_stream:
            chunks.append(text)
        final = stream.get_final_message()
    fixed = "".join(chunks).strip()
    if fixed.startswith("```"):
        fixed = re.sub(r"^```(?:markdown)?\s*", "", fixed)
        fixed = re.sub(r"\s*```$", "", fixed)

    # Backup el malo y escribe el corregido
    backup = out_path.with_suffix(".pre_heal.md.bak")
    backup.write_text(bad_md, encoding="utf-8")
    out_path.write_text(fixed, encoding="utf-8")
    log.info(f"  auto-heal: escrito (in_tok={final.usage.input_tokens} "
             f"out_tok={final.usage.output_tokens}). Backup en {backup.name}")

    # Re-validar
    from . import qa as _qa
    sem2 = _qa.check_escaleta_semantic(out_path, max_overlap_ratio=0.4)
    log.info(f"  [QA post-heal] ok={sem2['ok']} questions={sem2['checks']['quote_with_question']} "
             f"overlap={sem2['checks']['overlap_with_script']}")
    if not sem2["ok"]:
        log.warning(f"  auto-heal NO recupero todos los errores: {sem2['errors']}")
    return out_path
