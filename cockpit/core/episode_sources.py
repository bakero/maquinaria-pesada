"""Fuente de verdad única: mapeo episodio → PDF fuente + script generador.

Lo consumen tanto `lanzar_guiones.py` (batch) como `web_server.py`
(generación bajo demanda desde la app visual).

Convención de ids de episodio (igual que `cockpit.core.episodes`):
  * Módulo M:  "M3"          → generar_guion.py   --modulo 3 --pdf <resumen>
  * Tema   T:  "M7_T1"       → generar_guion_t.py --pdf <tema>
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Mapeo crudo (rutas relativas a la raíz del repo)
# ---------------------------------------------------------------------------

# Módulos M0–M14 → PDF resumen
M_PDFS: dict[int, str] = {
    0:  "PDFs/resumenes/RESUMEN_M0_Introduccion_Estrategica.pdf",
    1:  "PDFs/resumenes/RESUMEN_M1_Fundamentos_Razonamiento.pdf",
    2:  "PDFs/resumenes/RESUMEN_M2_Matematicas_Fundamentos.pdf",
    3:  "PDFs/resumenes/RESUMEN_M3_Machine_Learning_Clasico.pdf",
    4:  "PDFs/resumenes/RESUMEN_M4_Deep_Learning.pdf",
    5:  "PDFs/resumenes/RESUMEN_M5_NLP_LLMs.pdf",
    6:  "PDFs/resumenes/RESUMEN_M6_Ingenieria_Prompts.pdf",
    7:  "PDFs/resumenes/RESUMEN_M7_Sistemas_RAG.pdf",
    8:  "PDFs/resumenes/RESUMEN_M8_Ingenieria_LLMOps.pdf",
    9:  "PDFs/resumenes/RESUMEN_M9_Infraestructura_Despliegue.pdf",
    10: "PDFs/resumenes/RESUMEN_M10_Sistemas_Agentes.pdf",
    11: "PDFs/resumenes/RESUMEN_M11_Automatizacion.pdf",
    12: "PDFs/resumenes/RESUMEN_M12_Seguridad_IA.pdf",
    13: "PDFs/resumenes/RESUMEN_M13_Gobernanza_Etica.pdf",
    14: "PDFs/resumenes/RESUMEN_M14_Estrategia_Empresa.pdf",
}

# Episodios T → PDF temático
T_PDF_LIST: list[str] = [
    "PDFs/temas/M1_T10_tokenizacion.pdf",
    "PDFs/temas/M1_T11_limitaciones_llms.pdf",
    "PDFs/temas/M12_T2_prompt_injection.pdf",
    "PDFs/temas/M8_T1_ciclo_vida_modelos_llm.pdf",
    "PDFs/temas/M7_T1_que_es_rag.pdf",
    "PDFs/temas/M3_T2_modelos_clasicos.pdf",
    "PDFs/temas/M10_T5_tool_use_function_calling.pdf",
]

_T_PDF_RE = re.compile(r"M(\d+)_T(\d+)_", re.IGNORECASE)


def _t_ep_id(pdf_rel: str) -> str | None:
    """Deriva el id de episodio T ("M7_T1") del nombre del PDF temático."""
    m = _T_PDF_RE.search(pdf_rel.rsplit("/", 1)[-1])
    if not m:
        return None
    return f"M{int(m.group(1))}_T{int(m.group(2))}"


# Episodios T → PDF, indexado por id de episodio
T_PDFS: dict[str, str] = {
    ep_id: pdf for pdf in T_PDF_LIST if (ep_id := _t_ep_id(pdf))
}


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


@dataclass
class EpisodeSource:
    ep_id: str          # "M3" | "M7_T1"
    kind: str           # "M" | "T"
    module: str         # "M3"
    script: str         # "generar_guion.py" | "generar_guion_t.py"
    pdf: str            # ruta relativa al repo
    flags: list[str]    # flags listos para pasar al script

    def as_dict(self) -> dict:
        return {
            "ep_id": self.ep_id,
            "kind": self.kind,
            "module": self.module,
            "script": self.script,
            "pdf": self.pdf,
            "flags": self.flags,
        }


def source_for(ep_id: str) -> EpisodeSource | None:
    """Devuelve la fuente (PDF + script + flags) para un id de episodio.

    Devuelve None si el episodio no está configurado."""
    ep_id = (ep_id or "").strip()

    # Short S → "S1" (píldora de glosario, formato v6, sin PDF fuente)
    if re.fullmatch(r"S(\d+)", ep_id, re.IGNORECASE):
        # Necesitamos el `--term` (RAG, Fine-tuning, …). Lo leemos del
        # registro de Shorts mantenido por cockpit.core.shorts.
        try:
            from cockpit.core import shorts as _shorts
            sh = _shorts.get_short(ep_id.upper())
        except Exception:
            sh = None
        if sh is None:
            return None
        return EpisodeSource(
            ep_id=ep_id.upper(),
            kind="S",
            module="",
            script="lanzar_produccion_v6.py",
            pdf="",                         # los Shorts no usan PDF fuente
            flags=["--kind", "S", "--ep", ep_id.upper(), "--term", sh.term],
        )

    # Tema T → "M7_T1"
    if "_T" in ep_id:
        pdf = T_PDFS.get(ep_id)
        if not pdf:
            return None
        return EpisodeSource(
            ep_id=ep_id,
            kind="T",
            module=ep_id.split("_T")[0],
            script="generar_guion_t.py",
            pdf=pdf,
            flags=["--pdf", pdf],
        )

    # Módulo M → "M3"
    m = re.fullmatch(r"M(\d+)", ep_id, re.IGNORECASE)
    if not m:
        return None
    modulo_n = int(m.group(1))
    pdf = M_PDFS.get(modulo_n)
    if not pdf:
        return None
    return EpisodeSource(
        ep_id=f"M{modulo_n}",
        kind="M",
        module=f"M{modulo_n}",
        script="generar_guion.py",
        pdf=pdf,
        flags=["--modulo", str(modulo_n), "--pdf", pdf],
    )


def all_sources() -> list[EpisodeSource]:
    """Todas las fuentes configuradas (M primero, luego T), para el batch."""
    out: list[EpisodeSource] = []
    for modulo_n in sorted(M_PDFS):
        src = source_for(f"M{modulo_n}")
        if src:
            out.append(src)
    for ep_id in T_PDFS:
        src = source_for(ep_id)
        if src:
            out.append(src)
    return out
