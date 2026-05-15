"""Fixtures compartidas para los tests de los validadores específicos."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


def _saludo(opener: str, n_words: int = 50) -> str:
    other = "MARIA" if opener == "IAGO" else "IAGO"
    other_name = "Maria" if other == "MARIA" else "Yago"
    opener_name = "Maria" if opener == "MARIA" else "Yago"
    aviso = (" ".join(["palabra"] * (n_words - 22)) +
             " Este episodio lo genera un sistema automatico de inteligencia "
             "artificial que puede contener errores. Contrastalo si dudas.")
    return (
        f"# SALUDO_Y_PRESENTACION\n"
        f"{opener}: [calido] Bienvenidos. Soy {opener_name}.\n"
        f"{other}: [calido] Y yo soy {other_name}.\n"
        f"{opener}: [serio] Antes de empezar lo de siempre. {aviso}\n"
    )


def _hook(opener: str) -> str:
    other = "MARIA" if opener == "IAGO" else "IAGO"
    return (
        f"# HOOK\n"
        f"{opener}: [directo] Una frase potente que sostiene la atención del oyente con un dato concreto del mercado de la inteligencia artificial moderna en empresas.\n"
        f"{other}: [curioso] Y una pregunta de matiz que abre el episodio sin perder la energía inicial. Esto es MaquinarIA Pesada. Arrancamos.\n"
    )


def _dev_block(name: str, leader: str, n_leader: int = 4,
               n_support: int = 1, words_per: int = 80) -> str:
    """Construye un bloque de desarrollo con líder y apoyo balanceados."""
    other = "MARIA" if leader == "IAGO" else "IAGO"
    out = [f"# {name}"]
    for i in range(n_leader):
        body = (" ".join(["palabra"] * (words_per - 12)) +
                f" Esta es la intervencion {i+1} del líder con suficiente cuerpo "
                "de desarrollo para sostener el bloque.")
        out.append(f"{leader}: [explicativo] {body}")
    for _ in range(n_support):
        out.append(f"{other}: [curioso] Una pregunta de matiz al hilo del bloque, no muy larga.")
    return "\n".join(out) + "\n"


def _cierre_conceptos(n: int = 3) -> str:
    out = ["# CIERRE_CONCEPTOS"]
    out.append("IAGO: [directo] No te puedes ir de este capitulo sin haber entendido estos conceptos. Primero, una idea técnica con su aterrizaje correspondiente.")
    speakers = ["MARIA", "IAGO", "MARIA", "IAGO"]
    for i in range(1, n):
        spk = speakers[(i - 1) % len(speakers)]
        out.append(f"{spk}: [analitica] Concepto número {i+1} que cierra el capítulo con una idea memorable para el oyente.")
    return "\n".join(out) + "\n"


def _cierre_final(opener: str) -> str:
    return (
        f"# CIERRE_FINAL\n"
        f"{opener}: [calido] Y hasta aqui ha llegado nuestro episodio de "
        f"MaquinarIA Pesada. Siguenos para nuevos capitulos donde la I.A. crea "
        f"contenido sobre I.A. Los episodios del módulo ya están disponibles en plataformas.\n"
    )


def _verificaciones() -> str:
    return "# VERIFICACIONES\n[verificaciones internas]\n"


def _intro_sonido() -> str:
    return "# INTRO_SONIDO\n[INTRO - SONIDO DE MAQUINAS ARRANCANDO - 8-10 segundos]\n"


def _bloque_fuentes_m() -> str:
    """BLOQUE_FUENTES con 3 fuentes-marco detectables."""
    return (
        "# BLOQUE_FUENTES\n"
        "IAGO: [explicativo] La primera fuente que importa para este módulo es "
        "el paper de Vaswani de 2017, que introdujo los Transformers y abrió "
        "todo el camino que hoy seguimos en la práctica del lenguaje.\n"
        "MARIA: [analitica] La segunda es el informe McKinsey de dos mil veintitres, "
        "una encuesta amplia sobre adopción real de IA en empresas grandes.\n"
        "IAGO: [didactico] La tercera, Hinton y otros de 2012, el trabajo "
        "fundacional del deep learning aplicado a imagen que cambió el campo "
        "de la inteligencia artificial moderna.\n"
    )


def _bloque_fuentes_t() -> str:
    """BLOQUE_FUENTES con exactamente 3 fuentes para T."""
    return _bloque_fuentes_m()


def _bloque_casos_t() -> str:
    """BLOQUE_CASOS con 2 empresas reconocibles."""
    return (
        "# BLOQUE_CASOS\n"
        "MARIA: [analitica] En este punto conviene mirar dos casos reales. "
        "OpenAI publicó un estudio sobre el uso de su API en empresas que muestra patrones de adopción interesantes.\n"
        "IAGO: [explicativo] El caso de Anthropic es complementario y aterriza el concepto con cifras concretas. Conviene observar ambos en paralelo.\n"
        "MARIA: [directo] Y una segunda observación de la encuesta de Anthropic, "
        "que confirma la tendencia de los últimos meses en este sector. La adopción crece pero la escalabilidad sigue siendo el reto.\n"
        "MARIA: [analitica] Una tercera intervención de desarrollo para sostener el peso de Maria en el bloque sin caer en exceso de líder, "
        "aterrizando con un caso conocido del corpus reciente de la industria.\n"
        "MARIA: [firme] Y cerramos el bloque con una observación contundente sobre el patrón general de adopción que vemos en el corpus.\n"
    )


def _bloque_limites_t() -> str:
    """BLOQUE_LIMITES con patrón semántico."""
    return (
        "# BLOQUE_LIMITES\n"
        "IAGO: [serio] Conviene aclarar qué NO es esto. No es una solución universal y no debe confundirse con la búsqueda semántica clásica de hace años.\n"
        "MARIA: [analitica] Y el error común es asumir que cuando no hay datos el modelo dirá no sé. No es así en la mayoría de los casos en producción real.\n"
        "IAGO: [didactico] Otro límite importante es la latencia. No aplica bien en flujos de tiempo real estrictos sin compromisos de calidad.\n"
        "IAGO: [firme] Y una última observación de cierre del bloque que mantiene a Yago como líder con suficiente peso de palabras.\n"
    )
