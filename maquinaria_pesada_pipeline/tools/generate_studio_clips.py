#!/usr/bin/env python3
"""
Genera las tomas reutilizables del estudio con Luma usando las imagenes
de referencia ya subidas a un host publico (catbox).

Uso:
    python tools/generate_studio_clips.py --test     # solo 1 toma de prueba
    python tools/generate_studio_clips.py --all      # las 8 tomas
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Cargar .env
from dotenv import load_dotenv
load_dotenv(ROOT.parent / ".env", override=True)

from pipeline.scene_library import SceneLibrary
from pipeline.luma_generator import LumaGenerator
from pipeline.logger import get_logger


LIBRARY_BASE = str(ROOT.parent / "Videos" / "escenas_biblioteca")
REFS_INDEX = Path(LIBRARY_BASE) / "refs" / "_refs_index.json"


# Definicion de las 8 tomas reutilizables
STUDIO_CLIPS = [
    {
        "slug":     "studio_establishing_general",
        "ref":      "establishing",
        "duration": 9,
        "category": "estudio",
        "tags":     ["establishing", "two_shot", "intro"],
        "description": "Plano amplio del estudio, ambos en posicion, ligero dolly-in",
        "prompt":   (
            "Cinematic slow dolly-in shot of an industrial podcast studio. "
            "Two presenters seated face-to-face across a weathered matte CAT-yellow "
            "steel table: a Mediterranean woman with shoulder-length dark brown hair "
            "in a black mock-neck sweater on the left, and a Mediterranean man "
            "with short light brown hair, three-day stubble and a black "
            "zipped technical hoodie on the right. Both wearing matte black "
            "studio headphones, hands resting on the table. Black matte podcast "
            "microphones with blue windscreens on boom arms. Behind them, a large "
            "welded steel sign 'MaquinarIA Pesada' on a concrete wall, illuminated "
            "by warm cenital spotlights. Natural micro-expressions, slight body sway, "
            "subtle blink. Camera moves forward and slightly down very smoothly. "
            "Photorealistic, anamorphic 35mm, warm 3200K lighting, deep shadows."
        ),
    },
    {
        "slug":     "studio_maria_speaking_close",
        "ref":      "maria",
        "duration": 5,
        "category": "estudio",
        "tags":     ["close_up", "maria", "speaking"],
        "description": "Maria en primer plano hablando con calma",
        "prompt":   (
            "Cinematic medium close-up of the same Mediterranean woman, 33, "
            "dark brown shoulder-length hair half pulled back, black mock-neck "
            "sweater. She is calmly speaking into a black matte podcast microphone "
            "with blue windscreen, looking slightly off-camera, natural lip "
            "movement, occasional small hand gestures, intelligent direct expression. "
            "Industrial podcast studio background heavily blurred: matte yellow "
            "steel table, warm spotlight, 'MaquinarIA Pesada' sign barely visible. "
            "Subtle yellow rim light on her hair. Camera locked, very slight "
            "shoulder movement. Photorealistic, anamorphic 35mm, shallow depth "
            "of field, fine grain."
        ),
    },
    {
        "slug":     "studio_yago_speaking_close",
        "ref":      "yago",
        "duration": 5,
        "category": "estudio",
        "tags":     ["close_up", "yago", "speaking"],
        "description": "Yago en primer plano hablando con energia contenida",
        "prompt":   (
            "Cinematic medium close-up of the same Mediterranean man, 38, "
            "short light brown hair, three-day stubble, black technical t-shirt "
            "under open dark zipped hoodie, matte black studio headphones around "
            "his neck. He is speaking into a black matte podcast microphone with "
            "blue windscreen, looking slightly off-camera with focused analytical "
            "expression and the occasional knowing half-smile. Natural lip "
            "movement, hands occasionally lifting from the table for emphasis. "
            "Industrial podcast studio background blurred: matte yellow steel "
            "table, warm spotlight, 'MaquinarIA Pesada' sign behind. Subtle "
            "electric blue rim light on his hair edge. Camera locked, slight "
            "lean forward when emphasizing. Photorealistic, anamorphic 35mm, "
            "shallow depth of field, fine grain."
        ),
    },
    {
        "slug":     "studio_maria_speaks_yago_listens",
        "ref":      "establishing",
        "duration": 5,
        "category": "estudio",
        "tags":     ["two_shot", "maria_active"],
        "description": "Plano dos personas, Maria habla, Yago escucha y asiente",
        "prompt":   (
            "Cinematic two-shot of the same industrial podcast studio. "
            "On the LEFT, the Mediterranean woman (33, dark brown hair, black "
            "mock-neck sweater) is speaking calmly into her microphone, hands "
            "gesturing slightly. On the RIGHT, the Mediterranean man (38, "
            "stubble, dark hoodie) is listening attentively, occasionally nodding "
            "or making small notes in a black notebook. Matte CAT-yellow steel "
            "table between them with two black microphones with blue windscreens. "
            "Background: 'MaquinarIA Pesada' welded steel sign, warm cenital "
            "spotlights, deep shadows. Natural body language, micro-blinks, "
            "subtle breathing. Camera locked at medium distance. Photorealistic, "
            "anamorphic 35mm, warm color grade, fine grain."
        ),
    },
    {
        "slug":     "studio_yago_speaks_maria_listens",
        "ref":      "establishing",
        "duration": 5,
        "category": "estudio",
        "tags":     ["two_shot", "yago_active"],
        "description": "Plano dos personas, Yago habla, Maria escucha",
        "prompt":   (
            "Cinematic two-shot of the same industrial podcast studio. "
            "On the LEFT, the Mediterranean woman (33, dark brown hair, black "
            "mock-neck sweater) is listening with composed attention, occasionally "
            "tilting her head slightly. On the RIGHT, the Mediterranean man (38, "
            "stubble, dark hoodie) is speaking into his microphone with focused "
            "energy, hands gesturing to emphasize a point. Matte CAT-yellow steel "
            "table between them with two black microphones with blue windscreens. "
            "Background: 'MaquinarIA Pesada' welded steel sign, warm cenital "
            "spotlights, deep shadows. Natural body language, micro-blinks. "
            "Camera locked at medium distance. Photorealistic, anamorphic 35mm, "
            "warm color grade, fine grain."
        ),
    },
    {
        "slug":     "studio_both_complicit",
        "ref":      "establishing",
        "duration": 5,
        "category": "estudio",
        "tags":     ["two_shot", "humor", "complicity"],
        "description": "Ambos sonriendo / asintiendo en complicidad",
        "prompt":   (
            "Cinematic two-shot of the same industrial podcast studio. Both "
            "presenters share a brief moment of complicity: the Mediterranean "
            "woman on the left smiles knowingly while the Mediterranean man on "
            "the right shakes his head softly with a small ironic smirk. "
            "Both at the matte CAT-yellow steel table with black microphones. "
            "Background: 'MaquinarIA Pesada' sign, warm spotlights, deep "
            "shadows. Natural micro-expressions, brief eye contact between them. "
            "Photorealistic, anamorphic 35mm, fine grain."
        ),
    },
    {
        "slug":     "studio_detail_microphone",
        "ref":      "studio",
        "duration": 5,
        "category": "estudio",
        "tags":     ["detail", "broll", "transition"],
        "description": "Detail shot: micrófono, mano sobre la mesa amarilla",
        "prompt":   (
            "Cinematic close-up detail shot in the same industrial podcast "
            "studio. A black matte broadcast microphone with blue windscreen "
            "in sharp focus, on a metal boom arm. In soft background: a hand "
            "resting on the worn matte yellow steel table next to a small "
            "black notebook, fingers slowly tapping. Warm cenital spotlight "
            "creates rim light on the microphone mesh. Subtle steam-like dust "
            "motes drifting through the warm light. Background out of focus: "
            "weathered yellow steel surface, hint of the 'MaquinarIA Pesada' "
            "sign in the deep blur. Photorealistic, anamorphic 35mm, very "
            "shallow depth of field, fine grain."
        ),
    },
    {
        "slug":     "studio_outro_closing",
        "ref":      "establishing",
        "duration": 5,
        "category": "cierres",
        "tags":     ["outro", "two_shot", "closing"],
        "description": "Cierre: ambos quitandose los auriculares lentamente",
        "prompt":   (
            "Cinematic two-shot of the same industrial podcast studio at the "
            "end of the recording. The Mediterranean woman on the left and the "
            "Mediterranean man on the right both slowly lift their hands to "
            "remove their black studio headphones, sharing a brief glance. "
            "The warm spotlights begin to dim subtly. Background: matte "
            "CAT-yellow steel table, 'MaquinarIA Pesada' welded steel sign, "
            "deep shadows. Natural unhurried movement, soft breathing visible. "
            "Camera locked at medium distance, slight pull-back at the end. "
            "Photorealistic, anamorphic 35mm, warm color grade, fine grain."
        ),
    },
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true",
                        help="Genera solo 1 toma de prueba (Yago hablando)")
    parser.add_argument("--all", action="store_true",
                        help="Genera las 8 tomas")
    parser.add_argument("--slug", default=None,
                        help="Genera una toma especifica por slug")
    args = parser.parse_args()

    log = get_logger("generate_studio_clips")

    refs = json.loads(REFS_INDEX.read_text(encoding="utf-8"))["refs"]
    library = SceneLibrary(LIBRARY_BASE)
    gen = LumaGenerator(library, model="ray-2", default_aspect="16:9")

    if args.test:
        clips_to_gen = [c for c in STUDIO_CLIPS
                        if c["slug"] == "studio_yago_speaking_close"]
    elif args.slug:
        clips_to_gen = [c for c in STUDIO_CLIPS if c["slug"] == args.slug]
    elif args.all:
        clips_to_gen = STUDIO_CLIPS
    else:
        log.error("Pasa --test o --all o --slug <slug>")
        return 1

    log.info(f"Voy a generar {len(clips_to_gen)} toma(s).")

    for clip in clips_to_gen:
        ref = refs[clip["ref"]]
        log.info(f"  >>> {clip['slug']}  (ref={clip['ref']})")
        try:
            scene = gen.generate_concept(
                slug=clip["slug"],
                prompt=clip["prompt"],
                duration=clip["duration"],
                aspect_ratio="16:9",
                category=clip["category"],
                modulo=None,
                tags=clip["tags"],
                description=clip["description"],
                frame0_url=ref["url"],
            )
            log.info(f"      OK -> {scene['path']}")
        except Exception as exc:
            log.error(f"      FAIL: {exc}")

    print()
    print("Estado de la biblioteca:")
    print(json.dumps(library.stats(), indent=2))
    return 0


if __name__ == "__main__":
    # Bitácora diaria centralizada (logs/run/). Localiza daylog.py subiendo
    # directorios; si fallara, el script sigue con un nullcontext de respaldo.
    import sys as _sys
    from pathlib import Path as _Path
    for _p in _Path(__file__).resolve().parents:
        if (_p / "daylog.py").exists():
            if str(_p) not in _sys.path:
                _sys.path.insert(0, str(_p))
            break
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script=_Path(__file__).name, params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        raise SystemExit(main())
