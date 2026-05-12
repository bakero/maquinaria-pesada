"""
Parser de escaletas markdown -> estructura canonica consumible por el
pipeline de render.

La escaleta tiene este formato:

  ---
  episode_id: ...
  ...
  ---

  # ESCALETA DE PRODUCCION ...

  ## BLOQUE_NAME
  **TC IN:** `00:02.06`  **TC OUT:** `00:34.05`  **DUR:** 31.99s

  ### 1.1 — Speaker
  - **TC:** `00:02.06 → 00:18.99` · **DUR:** 16.93s
  - **TONO:** [ironico]
  - **TEXTO:**
    > ...
  - **PLANO:** TWO_SHOT_M_ACTIVE
  - **ON-SCREEN:**
    | t (relativo) | Elemento | Posición | Salida |
    |---|---|---|---|
    | 03.0s | stat_card "ADOPCION 88%" amarillo | MID_LEFT | hasta 18.9s |
  - **TRANSICION OUT:** corte seco en pausa.

  > **NOTA DIRECCION:** ...

Salida del parser:
  {
    "metadata": {...},                # frontmatter YAML parseado
    "blocks": [
      {
        "name": "HOOK",
        "tc_in": 2.06, "tc_out": 34.05, "duration": 31.99,
        "interventions": [
          {
            "id": "1.1", "speaker": "MARIA",
            "tc_in": 2.06, "tc_out": 18.99, "duration": 16.93,
            "tono": "ironico",
            "text": "...",
            "plano": "TWO_SHOT_M_ACTIVE",
            "on_screen": [
              {"t_rel": 3.0, "element": "stat_card", "raw_text": "...",
               "position": "MID_LEFT", "out_t_rel": 16.84, "color_hint": "amarillo"},
              ...
            ],
            "transition_out": "corte seco en pausa",
          },
          ...
        ],
        "direction_note": "...",
      },
      ...
    ],
  }
"""

import json
import re
from pathlib import Path

from .logger import get_logger


# ─── Helpers ────────────────────────────────────────────────────────────


def _tc_to_seconds(tc: str) -> float:
    """Convierte 'MM:SS.mmm' a segundos."""
    tc = tc.strip().lstrip("`").rstrip("`").strip()
    m = re.match(r"(\d+):(\d+(?:\.\d+)?)", tc)
    if not m:
        return 0.0
    minutes = int(m.group(1))
    secs = float(m.group(2))
    return round(minutes * 60 + secs, 3)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parsea frontmatter YAML simple (sin lib). Devuelve (metadata, resto)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    fm = text[3:end].strip()
    rest = text[end + 4:].lstrip("\n")
    metadata = {}
    current_key = None
    for line in fm.splitlines():
        if not line.strip():
            continue
        if line.startswith("  ") and current_key:
            metadata.setdefault(current_key, [])
            if isinstance(metadata[current_key], list):
                metadata[current_key].append(line.strip("- ").strip())
            continue
        if ":" in line:
            k, _, v = line.partition(":")
            v = v.strip().strip('"').strip("'")
            if v:
                metadata[k.strip()] = v
                current_key = None
            else:
                metadata[k.strip()] = []
                current_key = k.strip()
    return metadata, rest


def _parse_on_screen_table(lines: list[str], duration: float) -> list[dict]:
    """
    Parsea las filas de la tabla on-screen.
    Formato esperado por fila:
      | 03.0s | stat_card "ADOPCION 88%" amarillo | MID_LEFT | hasta 18.9s |
    """
    items = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        # cells = [t_rel, element_desc, position, out]
        # encabezado tiene 't (relativo)' como primera celda; lo skip.
        if cells[0].lower().startswith("t (relativo") or cells[0].lower() == "t (relativo)":
            continue

        t_rel_raw = cells[0]
        m_t = re.match(r"^\s*(\d+(?:\.\d+)?)\s*s?\s*$", t_rel_raw)
        if not m_t:
            # No es una fila de datos
            continue
        t_rel = float(m_t.group(1))

        element_desc = cells[1] if len(cells) > 1 else ""
        position = cells[2].strip() if len(cells) > 2 else "MID_CENTER"
        out_raw = cells[3] if len(cells) > 3 else "hasta fin"

        # Parsear element_desc: tipo "stat_card \"texto\" color" o "sticker name"
        # Detectar tipo (primera palabra) y resto como descripcion + posibles
        # adjetivos de color.
        type_match = re.match(r"^([\w_]+)", element_desc)
        elem_type = type_match.group(1) if type_match else "highlight_quote"

        # Detectar color por palabra clave
        color_hint = None
        elem_lower = element_desc.lower()
        for col, hex_ in [
            ("amarillo", "#F5C400"), ("yellow", "#F5C400"),
            ("azul", "#4DB8FF"), ("blue", "#4DB8FF"),
            ("rojo", "#CC2200"), ("red", "#CC2200"),
            ("gris", "#888888"), ("grey", "#888888"), ("gray", "#888888"),
            ("blanco", "#E8E8E8"), ("white", "#E8E8E8"),
        ]:
            if col in elem_lower:
                color_hint = hex_
                break

        # Parsear out: "hasta fin", "hasta 18.0s", "18.5s"
        out_t_rel = duration  # por defecto hasta el final
        out_lower = out_raw.lower().strip()
        if "fin" in out_lower:
            out_t_rel = duration
        else:
            m_out = re.search(r"(\d+(?:\.\d+)?)\s*s?", out_raw)
            if m_out:
                out_t_rel = float(m_out.group(1))

        # Texto entre comillas (etiqueta + valor)
        quoted = re.findall(r'"([^"]+)"', element_desc)
        label_text = quoted[0] if quoted else element_desc

        items.append({
            "t_rel":       t_rel,
            "out_t_rel":   out_t_rel,
            "element":     elem_type,
            "raw":         element_desc,
            "label_text":  label_text,
            "position":    position,
            "color":       color_hint,
        })
    return items


# ─── Parser principal ───────────────────────────────────────────────────


_BLOCK_HEADER_RE = re.compile(
    r"^##\s+([^\n]+?)\s*$\s*\*\*TC IN:\*\*\s*`([0-9:.]+)`\s+\*\*TC OUT:\*\*\s*`([0-9:.]+)`",
    re.MULTILINE,
)
_INTERV_HEADER_RE = re.compile(
    r"^###\s+([\d.]+)\s*[—–\-]\s*([^\n]+?)\s*$",
    re.MULTILINE,
)


def parse_escaleta(escaleta_path: str | Path) -> dict:
    """
    Parsea el archivo de escaleta y devuelve la estructura canonica.
    """
    log = get_logger("escaleta_parser")
    text = Path(escaleta_path).read_text(encoding="utf-8")

    metadata, body = _parse_frontmatter(text)

    # Encontrar todos los headers de bloque
    block_headers = list(_BLOCK_HEADER_RE.finditer(body))
    if not block_headers:
        log.warning("No se encontraron bloques '## NOMBRE TC IN... TC OUT...' en la escaleta")

    blocks = []
    for i, m in enumerate(block_headers):
        block_name = m.group(1).strip().split("·")[0].strip().upper().replace(" ", "_")
        tc_in = _tc_to_seconds(m.group(2))
        tc_out = _tc_to_seconds(m.group(3))

        block_start = m.start()
        block_end = block_headers[i + 1].start() if i + 1 < len(block_headers) else len(body)
        block_text = body[block_start:block_end]

        # Parsear intervenciones dentro del bloque
        interv_headers = list(_INTERV_HEADER_RE.finditer(block_text))
        interventions = []
        for j, im in enumerate(interv_headers):
            iv_id = im.group(1)
            raw_label = im.group(2).strip()
            # Si la etiqueta es un nombre conocido de speaker, normalizamos.
            # Si es descriptivo ("Silencio tecnico"), guardamos descripcion
            # y dejamos speaker vacio.
            label_norm = raw_label.upper().replace("Á", "A").replace("Í", "I")
            if any(label_norm.startswith(s) for s in ("MARIA", "YAGO", "IAGO")):
                speaker = label_norm.split()[0]
            else:
                speaker = ""
            iv_start = im.start()
            iv_end = (interv_headers[j + 1].start()
                      if j + 1 < len(interv_headers) else len(block_text))
            iv_block = block_text[iv_start:iv_end]
            interv = _parse_intervention_body(iv_id, speaker, iv_block)
            if interv:
                interventions.append(interv)

        # Nota de direccion
        m_note = re.search(r"^>\s*\*\*NOTA\s+DIRECCI[ÓO]N\s*:?\*\*\s*(.+?)(?=^---|^##|\Z)",
                           block_text, re.MULTILINE | re.DOTALL)
        note = m_note.group(1).strip().replace("\n>", " ") if m_note else ""

        blocks.append({
            "name":            block_name,
            "tc_in":           tc_in,
            "tc_out":          tc_out,
            "duration":        round(tc_out - tc_in, 3),
            "interventions":   interventions,
            "direction_note":  note,
        })

    log.info(f"  parsed {len(blocks)} bloques, "
             f"{sum(len(b['interventions']) for b in blocks)} intervenciones")
    return {"metadata": metadata, "blocks": blocks}


def _parse_intervention_body(iv_id: str, speaker: str, body: str) -> dict | None:
    """Parsea el cuerpo de una intervencion (entre headers ###)."""
    # TC: el bloque entre backticks contiene "MM:SS.mmm → MM:SS.mmm"
    # (un solo par de backticks). Aceptamos varios separadores.
    m_tc = re.search(r"\*\*TC:\*\*\s*`([^`]+)`", body)
    if not m_tc:
        return None
    tc_inner = m_tc.group(1)
    m_pair = re.search(
        r"(\d+:\d+(?:\.\d+)?)\s*(?:→|->|—|-|–)+\s*(\d+:\d+(?:\.\d+)?)",
        tc_inner,
    )
    if not m_pair:
        return None
    tc_in = _tc_to_seconds(m_pair.group(1))
    tc_out = _tc_to_seconds(m_pair.group(2))
    duration = round(tc_out - tc_in, 3)

    # Tono
    m_tono = re.search(r"\*\*TONO:\*\*\s*\[?([^\]\n]+?)\]?(?:\n|$)", body)
    tono = m_tono.group(1).strip() if m_tono else ""

    # Texto (linea(s) que comienzan con > tras **TEXTO:**)
    text_lines = []
    in_text = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("**TEXTO:**"):
            in_text = True
            continue
        if in_text:
            if stripped.startswith(">"):
                text_lines.append(stripped.lstrip(">").strip())
            elif stripped.startswith("- **") or stripped.startswith("**"):
                in_text = False
            elif stripped == "":
                # vacio dentro de la cita; lo skipeamos
                continue
    text = " ".join(text_lines).strip()

    # Plano
    m_plano = re.search(r"\*\*PLANO:\*\*\s*([A-Z_]+)", body)
    plano = m_plano.group(1) if m_plano else "ESTABLISHING"

    # PIZARRA: SI/NO (escaleta v2). Si no esta presente, lo deja None y
    # escaleta_to_pipeline aplica heuristica de retro-compat.
    m_piz = re.search(r"\*\*PIZARRA:\*\*\s*(SI|S[ÍI]|YES|NO)\b",
                      body, re.IGNORECASE)
    uses_pizarra = None
    if m_piz:
        token = m_piz.group(1).upper()
        uses_pizarra = token in ("SI", "SÍ", "YES")

    # On-screen table
    on_screen = []
    m_os = re.search(r"\*\*ON-?SCREEN:\*\*", body)
    if m_os:
        # Tomar las lineas siguientes que sean parte de tabla
        rest = body[m_os.end():]
        table_lines = []
        for line in rest.splitlines():
            if line.strip().startswith("|"):
                table_lines.append(line)
            elif table_lines and not line.strip().startswith("|"):
                # tabla terminada
                if line.strip().startswith("- **") or line.strip().startswith("**"):
                    break
        on_screen = _parse_on_screen_table(table_lines, duration)

    # Transicion OUT
    m_trans = re.search(r"\*\*TRANSICI[ÓO]N\s*OUT:?\*\*\s*([^\n]+)", body)
    transition_out = m_trans.group(1).strip().rstrip(".") if m_trans else "corte"

    out = {
        "id":             iv_id,
        "speaker":        speaker,
        "tc_in":          tc_in,
        "tc_out":         tc_out,
        "duration":       duration,
        "tono":           tono,
        "text":           text,
        "plano":          plano,
        "on_screen":      on_screen,
        "transition_out": transition_out,
    }
    if uses_pizarra is not None:
        out["uses_pizarra"] = uses_pizarra
    return out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("escaleta")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    parsed = parse_escaleta(args.escaleta)
    out = args.out or args.escaleta.replace(".md", "_parsed.json")
    Path(out).write_text(json.dumps(parsed, indent=2, ensure_ascii=False),
                         encoding="utf-8")
    print(f"OK -> {out}")
