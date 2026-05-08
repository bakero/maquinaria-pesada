#!/usr/bin/env python3
"""
Genera el catalogo v2 de clips de estudio con Kling 1.6 Pro (via fal.ai).

18 clips de 10s cada uno:
  - 4 Maria sola hablando (image-to-video desde Maria.png)
  - 4 Yago solo hablando (image-to-video desde Yago.png)
  - 5 Two-shot Maria activa / Yago escucha (desde establishing.png)
  - 5 Two-shot Yago activa / Maria escucha (desde establishing.png)

Coste estimado: 18 x ~$0.90 = ~$16

Uso:
    python tools/generate_studio_clips_kling.py            # genera los que falten
    python tools/generate_studio_clips_kling.py --slug studio_maria_solo_v1
    python tools/generate_studio_clips_kling.py --force    # regenera incluso cacheados
"""

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(r"C:\Users\Asus\maquinaria_pesada\.env", override=True)

from pipeline.logger import get_logger
from pipeline.scene_library import SceneLibrary
from pipeline.kling_generator import KlingGenerator


# URLs publicas de las imagenes de referencia (raw GitHub).
# Nota: el repo es publico en master. Si rotas, actualiza estas URLs.
REFS = {
    "maria":         "https://raw.githubusercontent.com/bakero/maquinaria-pesada/master/Videos/escenas_biblioteca/refs/Maria.png",
    "yago":          "https://raw.githubusercontent.com/bakero/maquinaria-pesada/master/Videos/escenas_biblioteca/refs/Yago.png",
    "establishing":  "https://raw.githubusercontent.com/bakero/maquinaria-pesada/master/Videos/escenas_biblioteca/refs/establishing.png",
    "studio":        "https://raw.githubusercontent.com/bakero/maquinaria-pesada/master/Videos/escenas_biblioteca/refs/studio.png",
}


# ── Prompts comunes ────────────────────────────────────────────────────

# Setting comun a todos los clips (mantiene coherencia estetica)
SETTING = (
    "Heavy industrial podcast studio, dark metal walls, MAQUINARIA PESADA "
    "logo on background wall, yellow industrial table, blue podcast "
    "microphones, blue Beats-style headphones, warm cinematic lighting, "
    "shallow depth of field, professional broadcast quality, 4K"
)

# Negative reforzado (encima del default del generator)
NEGATIVE_SOLO = (
    "second person, additional person, two people, duplicate face, "
    "twin, mirror image, blurry, frozen, static, robotic motion, "
    "exaggerated mouth, lip sync error, cartoon, anime, watermark, "
    "text overlay, brand logo, CAT, caterpillar, commercial brand"
)
NEGATIVE_TWOSHOT = (
    "third person, extra people, duplicate Maria, duplicate Yago, "
    "wrong gender swap, blurry, frozen, robotic motion, exaggerated mouth, "
    "lip sync error, cartoon, watermark, text overlay, brand logo, CAT, "
    "caterpillar, commercial brand"
)


# ── Catalogo de 18 clips ──────────────────────────────────────────────

def _maria_solo(slug: str, action: str) -> dict:
    return {
        "slug":            slug,
        "category":        "estudio",
        "duration":        10,
        "target_duration": 20,
        "extend_prompt":   "continue scene naturally, same person, same studio, subtle natural motion, mouth movements continue speaking, no scene change",
        "image_url":       REFS["maria"],
        "negative_prompt": NEGATIVE_SOLO,
        "tags":            ["estudio", "maria", "solo"],
        "description":     f"Maria sola, plano medio frontal. {action}",
        "prompt": (
            f"A single woman with dark wavy hair sitting at a yellow podcast "
            f"table with a blue microphone, blue headphones around her neck, "
            f"wearing dark blazer. {action}. Subtle natural facial movements, "
            f"realistic mouth motion synced with speech, gentle eye blinks, "
            f"slight head tilts. {SETTING}. Camera locked off, medium shot, "
            f"only one person in the frame at all times."
        ),
    }


def _yago_solo(slug: str, action: str) -> dict:
    return {
        "slug":            slug,
        "category":        "estudio",
        "duration":        10,
        "target_duration": 20,
        "extend_prompt":   "continue scene naturally, same person, same studio, subtle natural motion, mouth movements continue speaking, no scene change",
        "image_url":       REFS["yago"],
        "negative_prompt": NEGATIVE_SOLO,
        "tags":            ["estudio", "yago", "solo"],
        "description":     f"Yago solo, plano medio frontal. {action}",
        "prompt": (
            f"A single man with short dark hair and short beard sitting at a "
            f"yellow podcast table with a blue microphone, blue headphones "
            f"around his neck, wearing dark sweater. {action}. Subtle natural "
            f"facial movements, realistic mouth motion synced with speech, "
            f"gentle eye blinks, slight head tilts. {SETTING}. Camera locked "
            f"off, medium shot, only one person in the frame at all times."
        ),
    }


def _two_shot_m_active(slug: str, action: str) -> dict:
    return {
        "slug":            slug,
        "category":        "estudio",
        "duration":        10,
        "target_duration": 20,
        "extend_prompt":   "continue scene naturally, same person, same studio, subtle natural motion, mouth movements continue speaking, no scene change",
        "image_url":       REFS["establishing"],
        "negative_prompt": NEGATIVE_TWOSHOT,
        "tags":            ["estudio", "two_shot", "maria_active"],
        "description":     f"Two-shot. Maria habla, Yago escucha. {action}",
        "prompt": (
            f"Two presenters at a yellow podcast table. The woman on the left "
            f"(dark wavy hair, dark blazer, blue headphones) is speaking. "
            f"The man on the right (short dark hair, beard, dark sweater, blue "
            f"headphones) is listening attentively without speaking. {action}. "
            f"Realistic mouth motion only on the speaking woman, the man's "
            f"mouth stays closed. {SETTING}. Wide two-shot, both faces clearly "
            f"visible, locked-off camera."
        ),
    }


def _two_shot_y_active(slug: str, action: str) -> dict:
    return {
        "slug":            slug,
        "category":        "estudio",
        "duration":        10,
        "target_duration": 20,
        "extend_prompt":   "continue scene naturally, same person, same studio, subtle natural motion, mouth movements continue speaking, no scene change",
        "image_url":       REFS["establishing"],
        "negative_prompt": NEGATIVE_TWOSHOT,
        "tags":            ["estudio", "two_shot", "yago_active"],
        "description":     f"Two-shot. Yago habla, Maria escucha. {action}",
        "prompt": (
            f"Two presenters at a yellow podcast table. The man on the right "
            f"(short dark hair, beard, dark sweater, blue headphones) is "
            f"speaking. The woman on the left (dark wavy hair, dark blazer, "
            f"blue headphones) is listening attentively without speaking. "
            f"{action}. Realistic mouth motion only on the speaking man, the "
            f"woman's mouth stays closed. {SETTING}. Wide two-shot, both faces "
            f"clearly visible, locked-off camera."
        ),
    }


CLIPS: list[dict] = [
    # 4 Maria sola
    _maria_solo("studio_maria_solo_v1",
                "She talks calmly to camera with a serene neutral expression"),
    _maria_solo("studio_maria_solo_v2",
                "She talks while gesturing softly with her right hand to "
                "explain a point"),
    _maria_solo("studio_maria_solo_v3",
                "She talks emphatically, slightly leaning forward, raising her "
                "eyebrows to underline a key idea"),
    _maria_solo("studio_maria_solo_v4",
                "She talks with a warm complicit smile, brief soft laugh, "
                "relaxed and friendly tone"),

    # 4 Yago solo
    _yago_solo("studio_yago_solo_v1",
               "He talks calmly to camera with a serene neutral expression"),
    _yago_solo("studio_yago_solo_v2",
               "He talks while resting his chin briefly on his hand, "
               "thoughtful gesture"),
    _yago_solo("studio_yago_solo_v3",
               "He talks emphatically, points slightly forward with his hand "
               "to underline a key idea"),
    _yago_solo("studio_yago_solo_v4",
               "He talks with a warm complicit smile, brief soft laugh, "
               "relaxed and friendly tone"),

    # 5 Two-shot Maria activa
    _two_shot_m_active("studio_two_m_active_v1",
                       "Maria looks at the camera while speaking, Yago nods "
                       "slowly listening"),
    _two_shot_m_active("studio_two_m_active_v2",
                       "Maria turns her head toward Yago while speaking, Yago "
                       "looks back at her attentively"),
    _two_shot_m_active("studio_two_m_active_v3",
                       "Maria speaks to camera, Yago in profile listens with "
                       "calm attention, hands on table"),
    _two_shot_m_active("studio_two_m_active_v4",
                       "Maria gesticulates softly while explaining, Yago "
                       "writes briefly in a notebook on the table"),
    _two_shot_m_active("studio_two_m_active_v5",
                       "Maria speaks with a warm smile, Yago smiles back "
                       "complicitly without speaking"),

    # 5 Two-shot Yago activa
    _two_shot_y_active("studio_two_y_active_v1",
                       "Yago looks at the camera while speaking, Maria nods "
                       "slowly listening"),
    _two_shot_y_active("studio_two_y_active_v2",
                       "Yago turns his head toward Maria while speaking, "
                       "Maria looks back at him attentively"),
    _two_shot_y_active("studio_two_y_active_v3",
                       "Yago speaks to camera, Maria in profile listens with "
                       "calm attention, hands resting on table"),
    _two_shot_y_active("studio_two_y_active_v4",
                       "Yago gesticulates softly while explaining, Maria "
                       "writes briefly in a notebook on the table"),
    _two_shot_y_active("studio_two_y_active_v5",
                       "Yago speaks with a warm smile, Maria smiles back "
                       "complicitly without speaking"),
]


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", default=None,
                        help="Generar solo este slug (default: todos los faltantes)")
    parser.add_argument("--force", action="store_true",
                        help="Regenerar incluso si ya existe en la library")
    parser.add_argument("--dry-run", action="store_true",
                        help="Solo muestra lo que generaria, no llama a la API")
    args = parser.parse_args()

    log = get_logger("generate_studio_clips_kling")
    library_base = Path(r"C:\Users\Asus\maquinaria_pesada\Videos\escenas_biblioteca")
    library = SceneLibrary(library_base)

    target = [c for c in CLIPS if (args.slug is None or c["slug"] == args.slug)]
    if not target:
        log.error(f"slug {args.slug} no encontrado en CLIPS.")
        return 1

    if args.dry_run:
        for c in target:
            existing = library.find(c["slug"])
            mark = "EXISTS" if existing else "TO GEN"
            log.info(f"[{mark}] {c['slug']:35s} dur={c['duration']}s "
                     f"img={c['image_url'].rsplit('/',1)[-1]}")
        return 0

    if args.force:
        for c in target:
            c["force"] = True

    gen = KlingGenerator(library)
    log.info(f"Generando {len(target)} clip(s) con Kling 1.6 Pro...")
    # 20s = base 10s + 2 extends de ~5s. Coste: ~$0.70 base + 2*$0.35 extend
    log.info(f"Coste estimado: ~${len(target) * 1.40:.2f} (10s base + 2 extends)")
    t0 = time.time()
    res = gen.generate_batch(target, delay_seconds=3.0)
    dt = time.time() - t0
    log.info(f"Tiempo total: {dt/60:.1f}min")
    log.info(f"  generated: {len(res['generated'])} -> {res['generated']}")
    log.info(f"  skipped:   {len(res['skipped'])} -> {res['skipped']}")
    log.info(f"  errors:    {len(res['errors'])}")
    for e in res["errors"]:
        log.error(f"    {e}")
    return 0 if not res["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
