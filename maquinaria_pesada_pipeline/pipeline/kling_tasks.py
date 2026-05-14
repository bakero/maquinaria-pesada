"""
Tracker persistente de tareas Kling.

Por que existe:
  Cada submit a Kling consume creditos. Si el proceso se muere antes de
  descargar el resultado, la tarea queda HUERFANA en Kling: pagada pero
  invisible para nosotros (Kling no tiene endpoint list-tasks).

  Solucion: escribir CADA submit a un append-only journal en disco
  ANTES de devolver del submit. Si el proceso muere, kling_reconcile
  lee este journal y descarga todo lo que este 'succeed' en Kling.

Formato kling_tasks.jsonl (1 linea por evento):
  {"event":"submit", "ts":"...", "slug":"studio_maria_solo_v1",
   "task_id":"...", "kind":"base"|"extend", "extend_step":0,
   "image_url":"...", "duration":10, "expected_after":"video_id"}
  {"event":"complete", "ts":"...", "slug":"...", "task_id":"...",
   "video_id":"...", "video_url":"..."}
  {"event":"download", "ts":"...", "slug":"...", "path":"...", "size":12345}
  {"event":"register", "ts":"...", "slug":"...", "ok":true}

Reglas:
  1. NUNCA mutar lineas previas. Append-only.
  2. fsync por linea para sobrevivir a crashes.
  3. Cada slug puede tener varias submits (retries) — ok, todas quedan.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class KlingTaskTracker:
    """Append-only JSONL journal de tareas Kling con fsync."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _append(self, record: dict[str, Any]) -> None:
        record.setdefault("ts", _now_iso())
        line = json.dumps(record, ensure_ascii=False) + "\n"
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            try:
                os.fsync(f.fileno())
            except (OSError, AttributeError):
                pass  # filesystem sin fsync (worktree raro)

    def log_submit(self, slug: str, task_id: str,
                   kind: str = "base",
                   extend_step: int = 0,
                   image_url: str | None = None,
                   duration: int = 10,
                   prompt: str | None = None,
                   target_duration: int | None = None,
                   parent_video_id: str | None = None) -> None:
        self._append({
            "event":           "submit",
            "slug":            slug,
            "task_id":         task_id,
            "kind":            kind,           # "base" o "extend"
            "extend_step":     extend_step,    # 0 para base, 1..N para extends
            "image_url":       image_url,
            "duration":        duration,
            "target_duration": target_duration,
            "parent_video_id": parent_video_id,
            "prompt":          (prompt or "")[:200],
        })

    def log_complete(self, slug: str, task_id: str,
                     video_id: str | None,
                     video_url: str | None) -> None:
        self._append({
            "event":     "complete",
            "slug":      slug,
            "task_id":   task_id,
            "video_id":  video_id,
            "video_url": video_url,
        })

    def log_failure(self, slug: str, task_id: str | None,
                    reason: str) -> None:
        self._append({
            "event":   "fail",
            "slug":    slug,
            "task_id": task_id,
            "reason":  reason[:300],
        })

    def log_download(self, slug: str, path: str | Path, size: int) -> None:
        self._append({
            "event": "download",
            "slug":  slug,
            "path":  str(path),
            "size":  int(size),
        })

    def log_register(self, slug: str, ok: bool, error: str = "") -> None:
        self._append({
            "event": "register",
            "slug":  slug,
            "ok":    ok,
            "error": error[:200] if error else "",
        })

    def log_qa(self, slug: str, ok: bool, checks: dict[str, Any]) -> None:
        self._append({
            "event":  "qa",
            "slug":   slug,
            "ok":     ok,
            "checks": checks,
        })

    # ── Lectura / agregacion ──────────────────────────────────────

    def read_all(self) -> list[dict]:
        if not self.path.exists():
            return []
        with open(self.path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def aggregate(self) -> dict[str, dict]:
        """Devuelve por slug el ultimo estado conocido:
          {slug: {
            base_task: tid, base_status: 'submit|complete|fail',
            extends: [{task, status, video_id}],
            downloaded: bool, registered: bool, qa_ok: bool|None,
          }}
        """
        out: dict[str, dict] = {}
        for r in self.read_all():
            slug = r.get("slug")
            if not slug:
                continue
            entry = out.setdefault(slug, {
                "base_task": None, "base_status": None, "base_video_id": None,
                "extends": {}, "downloaded": False, "registered": False,
                "qa_ok": None, "failures": [],
            })
            ev = r.get("event")
            if ev == "submit":
                step = r.get("extend_step", 0)
                if step == 0:
                    entry["base_task"] = r.get("task_id")
                    entry["base_status"] = "submit"
                else:
                    entry["extends"][step] = {
                        "task_id": r.get("task_id"),
                        "status":  "submit",
                        "video_id": None,
                    }
            elif ev == "complete":
                tid = r.get("task_id")
                if tid == entry["base_task"]:
                    entry["base_status"] = "complete"
                    entry["base_video_id"] = r.get("video_id")
                else:
                    for _step, ext in entry["extends"].items():
                        if ext["task_id"] == tid:
                            ext["status"] = "complete"
                            ext["video_id"] = r.get("video_id")
                            ext["video_url"] = r.get("video_url")
            elif ev == "fail":
                entry["failures"].append(r.get("reason"))
            elif ev == "download":
                entry["downloaded"] = True
                entry["download_path"] = r.get("path")
            elif ev == "register":
                entry["registered"] = bool(r.get("ok"))
            elif ev == "qa":
                entry["qa_ok"] = bool(r.get("ok"))
                entry["qa_checks"] = r.get("checks")
        return out

    def pending_orphans(self) -> list[dict]:
        """Tareas que se submitearon pero nunca se descargaron ni
        registraron en library. Candidatas a recuperar via reconcile."""
        agg = self.aggregate()
        out = []
        for slug, e in agg.items():
            if e["downloaded"] and e["registered"] and e["qa_ok"]:
                continue   # ya OK
            # Reportar el estado parcial
            out.append({"slug": slug, **e})
        return out


def get_tracker(output_folder: str | Path | None = None) -> KlingTaskTracker:
    """Factory. Default: outputs/kling_tasks.jsonl"""
    if output_folder is None:
        output_folder = Path(__file__).parent.parent / "outputs"
    path = Path(output_folder) / "kling_tasks.jsonl"
    return KlingTaskTracker(path)
