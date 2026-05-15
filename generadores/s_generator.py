"""Generador especialista de episodios S (Short) — v6."""
from __future__ import annotations

import re
from pathlib import Path

from generadores import base_generator as bg
from generadores.shared import fuentes_loader
from validators import s_validator
from validators.result import ValidationResult
from validators.shared.parity import opener_for

MODEL = "claude-haiku-4-5-20251001"  # texto corto + plantilla rígida → Haiku

SYSTEM_PROMPT = """\
Eres un guionista del podcast MaquinarIA Pesada generando un episodio S
(Short de 60-90s para Reels/Shorts/TikTok).

Reglas duras de formato v6:

1. UNA SOLA VOZ NARRADORA. Sin diálogo. NUNCA escribas "IAGO:" o "MARIA:".
2. Word count OBLIGATORIO entre 157 y 198 palabras (~75s a 1.10× TTS).
   Cuenta las palabras antes de entregar. Por debajo de 157 NO sirve:
   amplía con un ejemplo extra o desarrolla la aplicación. Por encima
   de 198 tampoco: recorta. Apunta a 175-185 para tener margen.
3. Estructura interna (no obligatoria como cabeceras): HOOK 5-7s,
   DEFINICIÓN 18-22s, EJEMPLO 28-35s, APLICACIÓN/GANCHO 12-18s.
4. La PRIMERA frase del Short es el HOOK y debe encajar en UNA de estas
   plantillas (elige una y aplícala SIN AMBIGÜEDAD):
   - H1 contradicción: empieza con una afirmación adversativa explícita
     usando alguno de "no es / no son / no entienden / nunca / aunque /
     incluso / a pesar de / puede inventar".
     Ejemplo: "Los LLM no son bases de datos. Son predictores estadísticos."
   - H2 número: la primera frase contiene un número en palabras
     ("ochenta y ocho por ciento", "dos mil veintitres", "diez veces más"),
     que sea la cifra impactante del Short.
   - H3 pregunta: la primera frase empieza con "¿" y cierra con "?".
5. Cierre canónico LITERAL al final, palabra por palabra (no la parafrasees,
   no cambies "T" por "correspondiente" ni añadas adjetivos):
   "Más sobre [tema] en el episodio T de MaquinarIA Pesada."
   donde [tema] se te indica en el user prompt. La palabra "T" es literal
   (una letra), no la sustituyas.
6. PROHIBIDO en el audio:
   - Etiquetas TTS de tono [didactico/etc.]
   - URLs o "https" o "punto com"
   - Citas tipo "Lewis et al. 2020" (los papers van en la descripción)
   - Interjecciones de coro ("exactamente", "exacto", etc.)
   - Apellidos para Maria/Yago
   - CUALQUIER meta-texto: NO escribas "Word count: 180" ni "✓" ni
     "Hook template: H1" ni "S3:" ni nada que no sea el texto narrado.
   - NO uses cabeceras de sección como `# HOOK`.
7. "MaquinarIA Pesada" solo se menciona UNA vez, en el cierre canónico.
8. Aviso de IA: NO se narra. Va en la descripción + texto en pantalla.
9. Una idea técnica central, máximo un tecnicismo secundario aterrizado.
10. Frases ≤28 palabras. No más de 2 frases cortas seguidas.
11. CUENTA las palabras antes de entregar — debe estar entre 157 y 198.
    Si te quedas corto, AÑADE un ejemplo concreto antes del cierre.

Devuelve SOLO el texto narrado del Short, sin cabeceras de sección ni tags
ni meta-texto. Empieza directamente con la primera frase (que es el HOOK)
y termina con la frase canónica de cierre.
"""


def _s_number(episode_id: str) -> int:
    m = re.match(r"^S(\d+)", episode_id)
    if not m:
        raise ValueError(f"episode_id no es S{{N}}: {episode_id!r}")
    return int(m.group(1))


def _tema_label(entry: fuentes_loader.GlosarioEntry) -> str:
    """Construye el [tema] que va en el cierre canónico."""
    if entry.fuentes:
        first = entry.fuentes[0]
        if first.tema and first.tema != "RESUMEN":
            return entry.name.lower()
    return entry.name.lower()


def build_user_prompt(*, episode_id: str, term: str,
                      repo_root: Path) -> str:
    """Inyecta la entrada del glosario en el user prompt."""
    glosario_path = repo_root / "PDFs" / "auxiliares" / "glosario_unificado.md"
    entries = fuentes_loader.load_glosario(glosario_path)
    entry = fuentes_loader.find_entry(entries, term)
    parts = [f"Genera el Short {episode_id} sobre el término '{term}'."]
    if entry is None:
        parts.append(
            f"\n## AVISO: el término '{term}' no está en el glosario. "
            "Devuelve un guion mínimo coherente con las reglas."
        )
        return "\n".join(parts)
    parts.append("\n## Definición canónica (úsala como fuente)")
    parts.append(entry.definicion)
    parts.append(f"\n## Cierre obligatorio (literal): "
                 f"\"Más sobre {_tema_label(entry)} en el episodio T de MaquinarIA Pesada.\"")
    return "\n".join(parts)


def _validate_factory(s_number: int, voice: str, filename: str):
    def validate(text: str, episode_id: str) -> list[ValidationResult]:
        return s_validator.validate(
            text, episode_id,
            s_number=s_number, voice=voice, filename=filename,
        )
    return validate


def generate(episode_id: str, term: str,
             repo_root: Path | None = None) -> bg.PipelineResult:
    """Genera el guion de un Short S{N} sobre `term`."""
    repo_root = (repo_root or Path(__file__).resolve().parents[1]).resolve()
    n = _s_number(episode_id)
    voice = opener_for(n)
    # filename canónico: S{N}_<term>.mp3 (con _ por espacios).
    slug = re.sub(r"\s+", "_", term.strip())
    slug = re.sub(r"[^\wáéíóúñÁÉÍÓÚÑ\-]", "", slug)
    filename = f"S{n}_{slug or term}.mp3"

    user_prompt = build_user_prompt(
        episode_id=episode_id, term=term, repo_root=repo_root)
    request = bg.PipelineRequest(
        episode_id=episode_id, kind="S",
        system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt,
        model=MODEL, repo_root=repo_root,
        max_output_tokens=1000, temperature=0.7,
        apply_ssml_pauses=False,  # S es texto narrativo, sin secciones
        validate_fn=_validate_factory(n, voice, filename),
    )
    return bg.run_pipeline(request)
