"""Renderer markdown."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime


def render_markdown(results: list[dict], directory: str) -> str:
    out: list[str] = []
    out.append(f"# Informe de evaluación · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    out.append("")
    out.append(f"**Directorio:** `{directory}`  ")
    out.append(f"**Ficheros:** {len(results)}")
    out.append("")

    # Resumen por tipo
    out.append("## Resumen")
    out.append("")
    out.append("| Tipo | Ficheros | PASS | hard-fail | soft-warn |")
    out.append("|------|----------|------|-----------|-----------|")
    by_kind: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_kind[r.get("kind", "?")].append(r)
    for kind in sorted(by_kind):
        items = by_kind[kind]
        h = sum(sum(1 for f in r.get("findings", []) if f["severity"] == "hard") for r in items)
        s = sum(sum(1 for f in r.get("findings", []) if f["severity"] == "soft") for r in items)
        p = sum(
            1
            for r in items
            if not any(f["severity"] == "hard" for f in r.get("findings", []))
        )
        out.append(f"| {kind} | {len(items)} | {p} | {h} | {s} |")
    out.append("")

    # Top reglas violadas
    out.append("## Top reglas violadas")
    out.append("")
    out.append("| Código | Severidad | Ocurrencias | Ficheros afectados |")
    out.append("|--------|-----------|-------------|--------------------|")
    rule_counts: Counter = Counter()
    rule_files: dict[str, set[str]] = defaultdict(set)
    rule_sev: dict[str, str] = {}
    for r in results:
        for f in r.get("findings", []):
            rule_counts[f["code"]] += 1
            rule_files[f["code"]].add(r["filename"].split("/")[-1].replace(".txt", "").replace(".md", ""))
            rule_sev[f["code"]] = f["severity"]
    for code, count in rule_counts.most_common(20):
        files = sorted(rule_files[code])
        files_str = ", ".join(files[:8]) + ("…" if len(files) > 8 else "")
        out.append(f"| `{code}` | {rule_sev[code]} | {count} | {files_str} |")
    out.append("")

    # Detalle
    out.append("## Detalle por fichero")
    out.append("")
    for r in results:
        out.append(f"### {r['filename'].split('/')[-1]} · {r.get('kind', '?')}")
        out.append("")
        if r.get("error"):
            out.append(f"**ERROR:** {r['error']}")
            out.append("")
            continue
        findings = r.get("findings", [])
        if not findings:
            out.append("✓ Sin findings")
            out.append("")
            continue
        for f in findings:
            line = f"L{f['line']}" if f.get("line") else "—"
            sev = "**HARD**" if f["severity"] == "hard" else "*soft*"
            out.append(f"- {sev} `{f['code']}` {line} — {f['message']}")
        out.append("")
    return "\n".join(out)
