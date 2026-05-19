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
2. ⚠️ WORD COUNT OBLIGATORIO: entre 157 y 198 palabras (~75s a 1.10× TTS).
   APUNTA A 180 PALABRAS. NUNCA por debajo de 157, NUNCA por encima de 198.
   Cuenta mentalmente las palabras DE TU RESPUESTA final antes de entregarla.
   Si necesitas más palabras, añade un caso o métrica concreta antes del
   cierre. Si tienes demasiadas, recorta el ejemplo. El rango operativo
   es 170-190 — apunta ahí. PROHIBIDO entregar 130-155 o 200+.
3. Estructura interna (OBLIGATORIA, sin cabeceras): HOOK 5-7s,
   DEFINICIÓN 18-22s, EJEMPLO 28-35s, APLICACIÓN/GANCHO 12-18s.

3.1 ⚠️ EJEMPLO OBLIGATORIO con CASO REAL DE EMPRESA + RESULTADO MEDIDO en cifra.
   Antes del cierre canónico, INCLUYE SIEMPRE una frase de la forma:
   "[Empresa real] [implementó esto/aplicó esta técnica/desplegó X] y
   consiguió [cifra concreta]".
   Empresas válidas: Morgan Stanley, JPMorgan, Harvey AI, Lemonade, OpenAI,
   Anthropic, Google, Microsoft, IBM, BBVA, Santander, Zara, Netflix,
   Spotify, Meta, NVIDIA, GitHub, Stripe, Walmart, Amazon, Pfizer, Roche.
   La cifra debe ser concreta y en palabras: "el ochenta por ciento", "diez
   veces más rápido", "tres semanas a tres horas", "millones de dolares de
   ahorro". Sin este ejemplo NO entregues el Short.
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
   - Frases AI-bro: "En el mundo actual de la IA", "Sin más preámbulos",
     "Es importante destacar que", "Cabe mencionar".
   - Frases coach motivacional: "¡Excelente pregunta!", "Espero que esto
     te ayude", "¡Adelante con tu proyecto!".
   - Cliffhangers genéricos: "Stay tuned", "lo veremos en próximos
     episodios" (el cierre canónico ya remite al T, no necesitas otro).
7. "MaquinarIA Pesada" solo se menciona UNA vez, en el cierre canónico.
8. Aviso de IA: NO se narra. Va en la descripción + texto en pantalla.
9. Una idea técnica central, máximo un tecnicismo secundario aterrizado.
10. Frases ≤28 palabras. No más de 2 frases cortas seguidas.
11. ⚠️⚠️ CUENTA LAS PALABRAS antes de entregar. DEBE estar entre 157 y 198.
    Si te quedas en 110-156 (corto), EXPANDE el EJEMPLO (regla 3.1) con
    una métrica adicional o un segundo caso de empresa, hasta llegar a
    170-185. NO ENTREGUES un Short por debajo de 157 palabras — el
    validador lo rechaza HARD-FAIL. Apunta a 175 palabras como objetivo.

Devuelve SOLO el texto narrado del Short. PROHIBIDO devolver:
- Cabeceras tipo "# BORRADOR", "## PLAN", "# TEXTO NARRADO", "# HOOK", "# CIERRE".
- Cualquier listado de pasos, planning, target o checklist en el output.
- Frases como "Hook template:", "Target total:", "Estructura palabra a palabra:".
- Comentarios meta tipo "Aquí va el guion:" o "Esta es mi respuesta:".

Tu output empieza DIRECTAMENTE con la primera palabra del HOOK del Short y
termina LITERALMENTE con la frase canónica de cierre. Nada antes, nada
después, sin saltos de sección. El validador rechaza meta-texto como
HARD-FAIL (cuenta como palabras del Short).
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
        # S es muy barato (Haiku) — 3 retries cubre el grueso del retry-rate.
        # El system prompt no llega a 4096 tokens, así que no aplicamos cache.
        # S sube a 5 retries (antes 3) tras smoke test 2026-05-18: Haiku
        # tiende a quedarse en 130-150 palabras y necesita 2-3 retries con
        # feedback explícito para llegar al target 157-198. Coste marginal
        # (~$0.001 por retry extra de Haiku).
        max_retries=bg.env_max_retries("S", 5),
        # En Shorts el patch retry no aporta (es texto único, sin secciones).
        retry_strategy="full",
    )
    return bg.run_pipeline(request)
