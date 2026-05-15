"""Selector y ordenador automático de Shorts (formato S) — v6.

Aplica el filtro y la fórmula de score definidos en `PODCAST_S_SPEC.md` sobre
`PDFs/auxiliares/glosario_unificado.md`. Idempotente y estable:

- Filtro: ≥2 módulos distintos OR ≥4 menciones OR aparece en RESUMEN.
- Score:  transversalidad × 3 + min(densidad, 20) + 5 si aparece en RESUMEN.
- Desempate: transversalidad > densidad > alfabético del nombre canónico.
- Estable: añadir términos nuevos no reordena los existentes que ya tienen
  `**S:** N`; los nuevos se enumeran tras el último ya asignado.
- Idempotente: ejecutar dos veces sobre el mismo glosario produce el mismo
  resultado.

Salida:
- Modifica `glosario_unificado.md` insertando `**S:** N` debajo de `**Fuentes:**`.
- Escribe `PDFs/auxiliares/glosario_shorts_ranking.md` con el ranking y los
  excluidos por filtro (auditoría).

Uso:
    python -m scripts.seleccionar_y_ordenar_shorts [--repo-root .]
                                                   [--dry-run]
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from generadores.shared.fuentes_loader import (
    GlosarioEntry,
    load_glosario,
    write_s_number,
)


@dataclass(frozen=True)
class Candidate:
    """Entrada seleccionada con su score y los componentes del cálculo."""

    name: str
    transversalidad: int
    densidad: int
    en_resumen: bool
    motivo: str
    existing_s: int | None
    score: int


def es_candidato(entry: GlosarioEntry) -> tuple[bool, str]:
    """Aplica el filtro v6. Devuelve `(es_candidato, motivo)`."""
    modulos = len(entry.modulos_distintos)
    menciones = len(entry.fuentes)
    if modulos >= 2:
        return True, "transversal_2plus_modulos"
    if menciones >= 4:
        return True, "denso_4plus_menciones"
    if entry.aparece_en_resumen:
        return True, "concepto_marco_resumen"
    return False, "excluido_por_filtro"


def calcular_score(entry: GlosarioEntry) -> int:
    """Fórmula del spec v6."""
    transversalidad = len(entry.modulos_distintos)
    densidad = len(entry.fuentes)
    score = transversalidad * 3 + min(densidad, 20)
    if entry.aparece_en_resumen:
        score += 5
    return score


def _tiebreak_key(c: Candidate) -> tuple:
    """Orden: mayor score → mayor transversalidad → mayor densidad → alfabético."""
    return (-c.score, -c.transversalidad, -c.densidad, c.name.lower())


def seleccionar_y_ordenar(entries: list[GlosarioEntry]) -> tuple[list[Candidate], list[GlosarioEntry]]:
    """Aplica filtro + score + estabilidad. Devuelve `(seleccionados_ordenados, excluidos)`.

    - Las entradas con `**S:** N` ya escrito conservan su N (estabilidad).
    - Las nuevas seleccionadas se ordenan por score y se enumeran a partir del
      siguiente N libre por encima del máximo existente.
    """
    seleccionados_existentes: list[Candidate] = []
    seleccionados_nuevos: list[Candidate] = []
    excluidos: list[GlosarioEntry] = []

    for e in entries:
        ok, motivo = es_candidato(e)
        if not ok:
            excluidos.append(e)
            continue
        c = Candidate(
            name=e.name,
            transversalidad=len(e.modulos_distintos),
            densidad=len(e.fuentes),
            en_resumen=e.aparece_en_resumen,
            motivo=motivo,
            existing_s=e.s_number,
            score=calcular_score(e),
        )
        if c.existing_s is not None:
            seleccionados_existentes.append(c)
        else:
            seleccionados_nuevos.append(c)

    # Estabilidad: respeta el orden de los que ya tienen S; añade nuevos al final.
    seleccionados_existentes.sort(key=lambda c: c.existing_s)
    seleccionados_nuevos.sort(key=_tiebreak_key)

    # Renumeramos: los existentes mantienen su N, los nuevos toman los huecos
    # libres por encima del máximo.
    next_n = (max((c.existing_s for c in seleccionados_existentes), default=0) + 1)
    renumbered: list[Candidate] = list(seleccionados_existentes)
    for c in seleccionados_nuevos:
        renumbered.append(Candidate(
            name=c.name, transversalidad=c.transversalidad,
            densidad=c.densidad, en_resumen=c.en_resumen,
            motivo=c.motivo, existing_s=next_n, score=c.score,
        ))
        next_n += 1

    return renumbered, excluidos


def escribir_glosario(path: Path, asignaciones: list[Candidate]) -> int:
    """Escribe la línea `**S:** N` en cada entrada del glosario seleccionada.

    Idempotente: si la línea ya tiene el valor correcto, no toca el fichero.
    Devuelve el número de entradas escritas/actualizadas.
    """
    written = 0
    for c in asignaciones:
        if c.existing_s is None:
            raise AssertionError("escribir_glosario espera N ya asignado")
        ok = write_s_number(path, c.name, c.existing_s)
        if ok:
            written += 1
    return written


def render_reporte(asignaciones: list[Candidate],
                   excluidos: list[GlosarioEntry],
                   total_entries: int) -> str:
    """Construye el `glosario_shorts_ranking.md`."""
    from datetime import datetime
    lines = [
        f"# Ranking de Shorts generado el {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Top ordenado (mayor probabilidad de gancho primero)",
        "",
        "| # | Término | Score | Transversalidad | Densidad | En RESUMEN | Motivo |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in asignaciones:
        lines.append(
            f"| {c.existing_s} | {c.name} | {c.score} | {c.transversalidad} | "
            f"{c.densidad} | {'sí' if c.en_resumen else 'no'} | {c.motivo} |"
        )
    lines += [
        "",
        f"## Excluidos por filtro ({len(excluidos)})",
        "",
    ]
    for e in sorted(excluidos, key=lambda e: e.name.lower()):
        lines.append(
            f"- **{e.name}** "
            f"(módulos: {len(e.modulos_distintos)}, "
            f"menciones: {len(e.fuentes)}, "
            f"resumen: {'sí' if e.aparece_en_resumen else 'no'})"
        )
    lines += [
        "",
        "## Totales",
        "",
        f"- Términos en glosario: {total_entries}",
        f"- Seleccionados: {len(asignaciones)}",
        f"- Excluidos: {len(excluidos)}",
    ]
    return "\n".join(lines) + "\n"


def run(repo_root: Path, *, dry_run: bool = False) -> dict:
    """Ejecuta el pipeline completo y devuelve un resumen."""
    glosario_path = repo_root / "PDFs" / "auxiliares" / "glosario_unificado.md"
    entries = load_glosario(glosario_path)
    asignaciones, excluidos = seleccionar_y_ordenar(entries)

    summary = {
        "total_entries": len(entries),
        "selected": len(asignaciones),
        "excluded": len(excluidos),
        "glosario_updated": 0,
        "report_path": None,
    }

    if not dry_run and glosario_path.exists():
        summary["glosario_updated"] = escribir_glosario(glosario_path, asignaciones)
        report_path = repo_root / "PDFs" / "auxiliares" / "glosario_shorts_ranking.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            render_reporte(asignaciones, excluidos, len(entries)),
            encoding="utf-8",
        )
        summary["report_path"] = str(report_path.relative_to(repo_root))

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".",
                        help="Raíz del repo (por defecto: directorio actual)")
    parser.add_argument("--dry-run", action="store_true",
                        help="No modifica el glosario ni escribe el ranking")
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    summary = run(repo_root, dry_run=args.dry_run)
    print(f"Total entradas: {summary['total_entries']}")
    print(f"Seleccionados: {summary['selected']}")
    print(f"Excluidos: {summary['excluded']}")
    if not args.dry_run:
        print(f"Glosario actualizado: {summary['glosario_updated']} entradas")
        if summary["report_path"]:
            print(f"Ranking: {summary['report_path']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    # Bitácora diaria centralizada (logs/run/): toda corrida del selector queda
    # trazada. Si daylog fallara, el script sigue funcionando vía nullcontext.
    import sys as _sys
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="scripts/seleccionar_y_ordenar_shorts.py",
                            params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        raise SystemExit(main())
