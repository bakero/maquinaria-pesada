#!/usr/bin/env python3
"""
Genera la escaleta de produccion de un episodio.

Uso:
    python tools/generate_escaleta.py --episode EP-MOD000 --modulo M0
    python tools/generate_escaleta.py --episode EP-MOD000 --modulo M0 --dry-run
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(r"C:\Users\Asus\maquinaria_pesada\.env", override=True)

from pipeline.escaleta_generator import generate_escaleta


PROJECT_ROOT = Path(r"C:\Users\Asus\maquinaria_pesada")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", required=True,
                        help="Episode ID (ej. EP-MOD000)")
    parser.add_argument("--modulo", required=True,
                        help="Modulo (ej. M0, M1, ...)")
    parser.add_argument("--aligned",
                        default=str(PROJECT_ROOT / "maquinaria_pesada_pipeline" /
                                    "outputs" / "aligned_interventions.json"))
    parser.add_argument("--audio-structure",
                        default=str(PROJECT_ROOT / "maquinaria_pesada_pipeline" /
                                    "outputs" / "audio_structure.json"))
    parser.add_argument("--concepts",
                        default=str(PROJECT_ROOT / "Videos" / "escenas_biblioteca" /
                                    "_concepts_index.json"))
    parser.add_argument("--out-dir",
                        default=str(PROJECT_ROOT / "escaletas"))
    parser.add_argument("--model", default="claude-sonnet-4-5")
    parser.add_argument("--dry-run", action="store_true",
                        help="No llama al LLM; genera solo el esqueleto.")
    args = parser.parse_args()

    out_path = generate_escaleta(
        episode_id=args.episode,
        modulo=args.modulo,
        aligned_interventions_path=args.aligned,
        audio_structure_path=args.audio_structure,
        concepts_index_path=args.concepts,
        output_dir=args.out_dir,
        model=args.model,
        dry_run=args.dry_run,
    )
    print(f"\nEscaleta -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
