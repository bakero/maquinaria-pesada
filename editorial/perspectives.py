"""Las 5 perspectivas del panel editorial y sus pesos por tipo (M/T/S).

Fuente normativa: `EVALUADOR_EDITORIAL_GUIONES.md §2 + §3.1`.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Perspective:
    """Una perspectiva del panel editorial."""

    key: str               # identificador interno: "productor", "marca", ...
    label: str             # nombre legible: "Productor"
    persona: str           # biografía corta del evaluador
    axes: tuple[str, ...]  # 4 ejes generales
    applies_to_s: bool     # ¿se aplica también a Shorts?


PRODUCTOR = Perspective(
    key="productor",
    label="Productor",
    persona=(
        "Productor con 15 años en podcasting de larga forma. Ha producido "
        "formatos tipo Hard Fork, Practical AI, podcasts técnicos en "
        "español. Sabe dónde aburre la gente. Su pregunta favorita es "
        "'¿por qué debería seguir escuchando esto en el minuto 7?'."
    ),
    axes=("hook", "pacing", "retencion", "cierre"),
    applies_to_s=True,
)

EDITOR_MARCA = Perspective(
    key="marca",
    label="Editor de marca",
    persona=(
        "Editor de marca que conoce a fondo el style_guide de MaquinarIA "
        "Pesada. Sabe distinguir entre Lex Fridman y Dot CSV en 30 segundos. "
        "Le obsesiona que el podcast no suene a 'uno más de IA en español'."
    ),
    axes=("anti_ai_bro", "anti_notebook_lm", "posicionamiento", "voz_humana"),
    applies_to_s=True,
)

OYENTE = Perspective(
    key="oyente",
    label="Oyente prototipo (CTO/CIO/CEO)",
    persona=(
        "CTO de empresa española mediana, 42 años, escucha podcasts en el "
        "coche. Le sobran ofertas de podcasts de IA. Cierra el podcast a "
        "los 4 minutos si no se justifica su tiempo. Detecta humo a "
        "kilómetros."
    ),
    axes=("densidad_valor", "aplicabilidad", "tolerancia_tecnica", "credibilidad"),
    applies_to_s=False,  # en S la audiencia es masiva, no se filtra por CTOs.
)

EXPERTO = Perspective(
    key="experto",
    label="Experto técnico",
    persona=(
        "Investigador/a senior en IA con doctorado, ha hecho papers sobre "
        "los temas del corpus. Lee directamente los originales (Anthropic, "
        "DeepMind, OpenAI, Google, papers de NeurIPS). Detecta "
        "simplificaciones engañosas al instante."
    ),
    axes=("precision", "profundidad", "casos", "cobertura"),
    applies_to_s=True,
)

SEO = Perspective(
    key="seo",
    label="SEO/distribución",
    persona=(
        "Director/a de distribución de un podcast network. Le importa que "
        "el episodio funcione en YouTube, Spotify, iVoox, LinkedIn, X, "
        "Shorts. Piensa en 'qué fragmento de 60s se hace clip' antes de "
        "oír el episodio entero."
    ),
    axes=("hook_como_clip", "frase_fuerza", "keyword_density", "titulo_preview"),
    applies_to_s=True,
)


PERSPECTIVES: tuple[Perspective, ...] = (
    PRODUCTOR, EDITOR_MARCA, OYENTE, EXPERTO, SEO,
)


# Pesos por perspectiva y tipo. La suma por columna debe ser 1.0.
# Ver `EVALUADOR_EDITORIAL_GUIONES.md §3.1`.
PERSPECTIVE_WEIGHTS: dict[str, dict[str, float]] = {
    "M": {
        "productor": 0.25,
        "marca":     0.25,
        "oyente":    0.10,
        "experto":   0.15,
        "seo":       0.25,
    },
    "T": {
        "productor": 0.20,
        "marca":     0.15,
        "oyente":    0.25,
        "experto":   0.30,
        "seo":       0.10,
    },
    "S": {
        "productor": 0.30,
        "marca":     0.25,
        "oyente":    0.00,   # N/A
        "experto":   0.15,
        "seo":       0.30,
    },
}


# Ejes específicos adicionales por tipo. Cada uno responde a una perspectiva.
TYPE_SPECIFIC_AXES: dict[str, tuple[tuple[str, str, str], ...]] = {
    "M": (
        ("m_aplicacion_practica_resonancia", "marca",
         "¿APLICACION_PRACTICA conecta el sistema generador con el módulo "
         "de forma resonante o suena pegada y promocional?"),
        ("m_aviso_ia_engancha", "productor",
         "¿La versión enganche del aviso IA (M-specific) funciona como "
         "gancho o suena rutinaria?"),
        ("m_cta_T_natural", "seo",
         "¿La CTA hacia los T del módulo en CIERRE_FINAL suena natural o "
         "como anuncio?"),
    ),
    "T": (
        ("t_bloque_casos_verificable", "experto",
         "¿BLOQUE_CASOS contiene casos con nombre propio + fuente + "
         "resultado concreto, o son genéricos?"),
        ("t_bloque_limites_honesto", "experto",
         "¿BLOQUE_LIMITES reconoce de verdad los límites o los maquilla?"),
        ("t_maria_voz_experta", "marca",
         "¿Maria en BLOQUE_CASOS es realmente voz experta empresarial o "
         "solo presenta datos sin postura?"),
    ),
    "S": (
        ("s_hook_template_funciona", "productor",
         "¿El hook encaja en H1/H2/H3 y funciona, o es genérico?"),
        ("s_cierre_canonico_resuena", "seo",
         "¿El cierre canónico hacia el T del tema suena como CTA real o "
         "como muletilla?"),
        ("s_termino_unico_claro", "experto",
         "¿El short define UN solo concepto claramente o intenta cubrir "
         "varios?"),
    ),
}


def weights_for(kind: str) -> dict[str, float]:
    """Devuelve el mapa perspectiva→peso para el tipo de guion."""
    if kind not in PERSPECTIVE_WEIGHTS:
        raise ValueError(f"Tipo de guion desconocido: {kind!r} (esperado M/T/S)")
    return dict(PERSPECTIVE_WEIGHTS[kind])


def applies(perspective_key: str, kind: str) -> bool:
    """¿Aplica esta perspectiva a este tipo de guion?"""
    return PERSPECTIVE_WEIGHTS[kind].get(perspective_key, 0.0) > 0.0
