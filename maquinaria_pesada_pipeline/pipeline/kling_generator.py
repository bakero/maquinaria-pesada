"""
Generador de escenas con Kling 1.6 Pro - API OFICIAL Kuaishou.

Por que Kling y no Luma:
  - Mantiene mucho mejor la consistencia facial cuando se usa una imagen
    como frame inicial. Luma alucinaba al segundo presentador en planos
    individuales (en clips de Yago aparecia una mujer que no era Maria).
  - Soporta clips de 5s y 10s nativos en modo Pro.

Auth (oficial Kuaishou):
  Kling usa **JWT firmado HS256** con dos claves:
    - access_key (publica)  -> va en el campo `iss` del JWT
    - secret_key (privada)  -> firma el JWT
  El JWT se regenera por peticion (caduca a los 30 min).

Endpoints (api.klingai.com):
  - POST /v1/videos/image2video       crear tarea
  - GET  /v1/videos/image2video/{id}  consultar tarea

Variables de entorno necesarias:
  KLING_ACCESS_KEY=AKxxxxxx
  KLING_SECRET_KEY=SKxxxxxx

Uso:
    from pipeline.kling_generator import KlingGenerator
    g = KlingGenerator(library)
    g.generate_concept(slug="studio_maria_solo_v1",
                       prompt="...", image_url="...",
                       duration=10, category="estudio")
"""

import os
import time
from pathlib import Path

from . import qa
from .kling_tasks import get_tracker
from .logger import get_logger
from .scene_library import SceneLibrary, _slugify

KLING_BASE = "https://api.klingai.com"
KLING_IMG2VIDEO_PATH = "/v1/videos/image2video"
KLING_EXTEND_PATH    = "/v1/videos/video-extend"

# Negative prompt comun para evitar problemas tipicos en planos de podcast
DEFAULT_NEGATIVE = (
    "blurry, low quality, distorted face, extra fingers, extra limbs, "
    "mutated hands, deformed, additional people, second person appearing, "
    "duplicate person, cartoon, anime, watermark, logo, text overlay, "
    "subtitle, brand name, CAT logo, lip sync error, mouth not matching, "
    "frozen face, robotic motion"
)


def _build_jwt(access_key: str, secret_key: str,
               ttl_seconds: int = 1800) -> str:
    """Genera el JWT que Kling oficial requiere en Authorization: Bearer."""
    try:
        import jwt
    except ImportError as exc:
        raise RuntimeError("Falta PyJWT. pip install PyJWT") from exc
    now = int(time.time())
    payload = {
        "iss":  access_key,
        "exp":  now + ttl_seconds,
        "nbf":  now - 5,
    }
    headers = {"alg": "HS256", "typ": "JWT"}
    token = jwt.encode(payload, secret_key, algorithm="HS256", headers=headers)
    # PyJWT >=2 devuelve str directamente
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


class KlingGenerator:
    def __init__(self, library: SceneLibrary,
                 access_key: str | None = None,
                 secret_key: str | None = None,
                 default_aspect: str = "16:9",
                 model_name: str = "kling-v1-6",
                 mode: str = "pro",
                 tracker_path: str | Path | None = None):
        self.library = library
        self.access_key = access_key or os.getenv("KLING_ACCESS_KEY")
        self.secret_key = secret_key or os.getenv("KLING_SECRET_KEY")
        if not self.access_key or not self.secret_key:
            raise RuntimeError(
                "KLING_ACCESS_KEY y KLING_SECRET_KEY requeridas. "
                "Anyadelas a .env (https://app.klingai.com/global/dev/account)."
            )
        self.default_aspect = default_aspect
        self.model_name = model_name
        self.mode = mode
        self.log = get_logger("kling_generator")
        self._http_session = None
        # Tracker persistente: cualquier submit se loguea ANTES de devolver
        self.tracker = get_tracker(
            output_folder=Path(tracker_path).parent if tracker_path else None
        )

    @property
    def http(self):
        """Sesion HTTP. Cada request regenera el JWT (cheap)."""
        if self._http_session is None:
            try:
                import requests
            except ImportError as exc:
                raise RuntimeError("pip install requests") from exc
            self._http_session = requests.Session()
        return self._http_session

    def _auth_headers(self) -> dict:
        token = _build_jwt(self.access_key, self.secret_key)
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
        }

    # ── API ─────────────────────────────────────────────────────────

    def _submit(self, prompt: str, image_url: str,
                duration: int = 10,
                aspect_ratio: str | None = None,
                negative_prompt: str | None = None,
                cfg_scale: float = 0.5) -> str:
        """POST image2video. Devuelve task_id. Retry exponencial en 429."""
        if duration not in (5, 10):
            self.log.warning(f"  duration={duration} no soportado; uso 10s")
            duration = 10
        payload = {
            "model_name":      self.model_name,
            "mode":            self.mode,
            "duration":        str(duration),
            "image":           image_url,
            "prompt":          prompt,
            "negative_prompt": negative_prompt or DEFAULT_NEGATIVE,
            "cfg_scale":       cfg_scale,
            "aspect_ratio":    aspect_ratio or self.default_aspect,
        }
        url = KLING_BASE + KLING_IMG2VIDEO_PATH
        # Retry con backoff exponencial para 429 (rate limit Kling)
        import time as _t
        for attempt in range(6):
            r = self.http.post(url, json=payload,
                               headers=self._auth_headers(), timeout=60)
            if r.status_code == 429:
                wait = min(120, 10 * (2 ** attempt))
                self.log.warning(f"  Kling 429 rate limit, esperando {wait}s "
                                 f"(intento {attempt+1}/6)")
                _t.sleep(wait)
                continue
            if r.status_code >= 400:
                self.log.error(f"  Kling submit {r.status_code}: {r.text[:500]}")
            r.raise_for_status()
            body = r.json()
            if body.get("code") != 0:
                raise RuntimeError(f"Kling submit error: {body}")
            task_id = body.get("data", {}).get("task_id")
            if not task_id:
                raise RuntimeError(f"Submit sin task_id: {body}")
            return task_id
        raise RuntimeError("Kling rate limit persistente tras 6 reintentos")

    def _poll(self, task_id: str, path: str = KLING_IMG2VIDEO_PATH,
              max_seconds: int = 1800,
              poll_interval: int = 10) -> dict:
        """Espera a que la tarea termine. Kling Pro 10s ~3-5 min, extend ~3-5 min.
        Robusto a errores transitorios de red: hasta 5 reintentos por GET."""
        url = KLING_BASE + path + f"/{task_id}"
        elapsed = 0
        consecutive_failures = 0
        while elapsed < max_seconds:
            try:
                r = self.http.get(url, headers=self._auth_headers(), timeout=90)
                r.raise_for_status()
                body = r.json()
                consecutive_failures = 0
            except Exception as exc:
                consecutive_failures += 1
                self.log.warning(f"  poll fallo ({consecutive_failures}): {type(exc).__name__}: {str(exc)[:120]}")
                if consecutive_failures >= 5:
                    raise RuntimeError(f"5 fallos consecutivos al pollear {task_id}") from exc
                time.sleep(min(30, poll_interval * consecutive_failures))
                elapsed += min(30, poll_interval * consecutive_failures)
                continue
            data = body.get("data", {})
            status = (data.get("task_status") or "").lower()
            self.log.debug(f"  Kling task {task_id[:8]}... status={status}")
            if status == "succeed":
                return data
            if status in ("failed", "error", "cancelled"):
                raise RuntimeError(f"Kling task fallo: {body}")
            time.sleep(poll_interval)
            elapsed += poll_interval
        raise TimeoutError(f"Kling timeout tras {max_seconds}s")

    def _extend(self, video_id: str, prompt: str | None = None,
                negative_prompt: str | None = None,
                cfg_scale: float = 0.5) -> str:
        """POST video-extend: continua la escena +5s. Retry en 429."""
        payload = {
            "video_id":        video_id,
            "prompt":          prompt or "continue scene naturally, same setting and characters, subtle natural motion",
            "negative_prompt": negative_prompt or DEFAULT_NEGATIVE,
            "cfg_scale":       cfg_scale,
        }
        url = KLING_BASE + KLING_EXTEND_PATH
        import time as _t
        for attempt in range(6):
            r = self.http.post(url, json=payload,
                               headers=self._auth_headers(), timeout=60)
            if r.status_code == 429:
                wait = min(120, 10 * (2 ** attempt))
                self.log.warning(f"  Kling extend 429, esperando {wait}s")
                _t.sleep(wait)
                continue
            if r.status_code >= 400:
                self.log.error(f"  Kling extend {r.status_code}: {r.text[:500]}")
            r.raise_for_status()
            body = r.json()
            if body.get("code") != 0:
                raise RuntimeError(f"Kling extend error: {body}")
            task_id = body.get("data", {}).get("task_id")
            if not task_id:
                raise RuntimeError(f"Extend sin task_id: {body}")
            return task_id
        raise RuntimeError("Kling extend rate limit persistente")

    def _download_video(self, url: str, dest: Path,
                        max_retries: int = 4) -> Path:
        """Descarga robusta. Reintenta hasta 4 veces, valida tamano minimo
        (>1MB) para detectar truncamientos, y verifica integridad mp4
        (moov atom) si ffprobe esta disponible."""
        import shutil
        import subprocess

        import requests
        Path(dest).parent.mkdir(parents=True, exist_ok=True)

        last_err = None
        for attempt in range(1, max_retries + 1):
            try:
                tmp = dest.with_suffix(dest.suffix + ".part")
                with requests.get(url, stream=True, timeout=600) as r:
                    r.raise_for_status()
                    with open(tmp, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1 << 15):
                            if chunk:
                                f.write(chunk)
                size = tmp.stat().st_size
                if size < 1_000_000:  # <1MB indica truncamiento (clip 20s pesa ~45MB)
                    raise OSError(f"download truncado: {size} bytes")
                # Verificar integridad mp4 con ffprobe si esta disponible
                if shutil.which("ffprobe"):
                    res = subprocess.run(
                        ["ffprobe", "-v", "error", "-show_entries",
                         "format=duration", "-of", "default=nw=1:nk=1", str(tmp)],
                        capture_output=True, text=True,
                    )
                    if res.returncode != 0:
                        raise OSError(f"mp4 corrupto: {res.stderr.strip()[:200]}")
                # OK: rename atomico
                if dest.exists():
                    dest.unlink()
                tmp.rename(dest)
                return dest
            except Exception as exc:
                last_err = exc
                self.log.warning(f"  download attempt {attempt}/{max_retries} fallo: "
                                 f"{type(exc).__name__}: {str(exc)[:200]}")
                # Limpiar fichero parcial
                try:
                    if tmp.exists():
                        tmp.unlink()
                except Exception:
                    pass
                if attempt < max_retries:
                    import time as _t
                    _t.sleep(min(60, 5 * attempt))
        raise RuntimeError(f"_download_video fallo tras {max_retries} intentos: {last_err}")

    # ── flujo de alto nivel ─────────────────────────────────────────

    def generate_concept(self, slug: str, prompt: str,
                         image_url: str,
                         duration: int = 10,
                         target_duration: int | None = None,
                         aspect_ratio: str | None = None,
                         category: str = "estudio",
                         modulo: str | None = None,
                         tags: list[str] | None = None,
                         description: str = "",
                         negative_prompt: str | None = None,
                         extend_prompt: str | None = None,
                         force: bool = False,
                         run_qa: bool = True) -> dict:
        """Genera un clip Kling. Si target_duration > duration, encadena
        extends (+5s cada uno) hasta alcanzar target. Persiste cada paso
        en kling_tasks.jsonl ANTES de continuar (recovery-friendly)."""
        slug = _slugify(slug)
        existing = self.library.find(slug)
        if existing and not force:
            self.log.info(f"  Reutilizando escena cacheada: {slug}")
            return existing

        target = target_duration or duration
        self.log.info(f"  Generando Kling 1.6 {self.mode}: {slug} "
                      f"(base={duration}s, target={target}s)")
        self.log.info(f"    prompt: {prompt[:100]}{'...' if len(prompt)>100 else ''}")
        self.log.info(f"    image:  {image_url}")

        # 1) Image2video base
        try:
            task_id = self._submit(prompt, image_url, duration, aspect_ratio,
                                    negative_prompt=negative_prompt)
        except Exception as exc:
            self.tracker.log_failure(slug, None, f"submit base: {exc}")
            raise
        # CRITICO: persistir ANTES de pollear (si morimos aqui, recovery
        # encuentra el task_id y descarga el resultado huerfano).
        self.tracker.log_submit(slug, task_id, kind="base", extend_step=0,
                                 image_url=image_url, duration=duration,
                                 prompt=prompt, target_duration=target)
        self.log.info(f"    [base] task_id={task_id}")

        try:
            result = self._poll(task_id, path=KLING_IMG2VIDEO_PATH)
        except Exception as exc:
            self.tracker.log_failure(slug, task_id, f"poll base: {exc}")
            raise
        videos = (result.get("task_result") or {}).get("videos") or []
        if not videos:
            self.tracker.log_failure(slug, task_id, "succeed sin videos")
            raise RuntimeError(f"Tarea succeed sin videos: {result}")
        last_video = videos[0]
        last_video_id = last_video.get("id")
        last_video_url = last_video.get("url")
        self.tracker.log_complete(slug, task_id, last_video_id, last_video_url)

        # 2) Extends sucesivos (+~5s cada uno) hasta target
        EXTEND_INCREMENT = 5
        n_extends = max(0, (target - duration + EXTEND_INCREMENT - 1) // EXTEND_INCREMENT)
        for i in range(n_extends):
            self.log.info(f"    [extend {i+1}/{n_extends}] desde video_id={last_video_id}")
            try:
                ext_task = self._extend(
                    video_id=last_video_id,
                    prompt=extend_prompt,
                    negative_prompt=negative_prompt,
                )
            except Exception as exc:
                self.tracker.log_failure(slug, None, f"submit ext{i+1}: {exc}")
                raise
            self.tracker.log_submit(slug, ext_task, kind="extend",
                                     extend_step=i + 1,
                                     parent_video_id=last_video_id,
                                     prompt=extend_prompt or "",
                                     duration=EXTEND_INCREMENT,
                                     target_duration=target)
            try:
                ext_result = self._poll(ext_task, path=KLING_EXTEND_PATH)
            except Exception as exc:
                self.tracker.log_failure(slug, ext_task, f"poll ext{i+1}: {exc}")
                raise
            ext_videos = (ext_result.get("task_result") or {}).get("videos") or []
            if not ext_videos:
                self.tracker.log_failure(slug, ext_task, "extend succeed sin videos")
                raise RuntimeError(f"Extend sin videos: {ext_result}")
            last_video = ext_videos[0]
            last_video_id = last_video.get("id")
            last_video_url = last_video.get("url")
            self.tracker.log_complete(slug, ext_task, last_video_id, last_video_url)

        # 3) Descargar
        if not last_video_url:
            raise RuntimeError(f"Sin URL final: {last_video}")
        dest = self.library.base / category / f"{slug}.mp4"
        self._download_video(last_video_url, dest)
        self.log.info(f"    descargado: {dest}")
        self.tracker.log_download(slug, dest, dest.stat().st_size)

        # 4) QA antes de registrar
        if run_qa:
            qa_min = max(0.0, target - 2)   # tolerancia 2s menos
            qa_max = target + 5
            qa_res = qa.check_kling_clip(dest,
                                          expected_min_duration=qa_min,
                                          expected_max_duration=qa_max)
            self.tracker.log_qa(slug, qa_res["ok"], qa_res["checks"])
            if not qa_res["ok"]:
                self.log.error(f"    QA FAILED {slug}: {qa_res['errors']}")
                # Borrar fichero QA-fallido para no contaminar la library
                try:
                    dest.unlink()
                except Exception:
                    pass
                raise RuntimeError(f"QA failed for {slug}: {qa_res['errors']}")

        # 5) Registrar
        try:
            scene = self.library.register(
                slug=slug, path=dest,
                category=category, prompt=prompt,
                description=description,
                tags=tags or [], modulo=modulo,
                source=f"kling-1.6-{self.mode}-{target}s",
            )
            self.tracker.log_register(slug, ok=True)
        except Exception as exc:
            self.tracker.log_register(slug, ok=False, error=str(exc))
            raise
        return scene

    # ── Batch paralelo (oleadas) ────────────────────────────────────

    def generate_batch_parallel(self, items: list[dict],
                                 submit_spacing: float = 1.5,
                                 poll_interval: int = 15,
                                 max_phase_seconds: int = 1800) -> dict:
        """Submitea TODAS las tareas en paralelo y espera a que cada fase
        complete antes de la siguiente (base -> extend1 -> extend2 -> download).
        Mucho mas rapido que sequential: 18 clips ~30 min vs ~8h.

        Args:
            items: [{slug, prompt, image_url, target_duration, ...}]
            submit_spacing: pausa (s) entre submissions para evitar rate limit
            poll_interval: cada cuanto pollear el estado en cada fase
            max_phase_seconds: timeout por fase
        """
        import time


        EXTEND_INCREMENT = 5
        results = {"generated": [], "errors": [], "skipped": []}

        # 0) Filtrar items: skipear los ya cacheados
        active = []
        for it in items:
            slug = _slugify(it.get("slug") or "")
            if not slug or not it.get("prompt") or not it.get("image_url"):
                results["errors"].append({"slug": slug, "error": "faltan campos"})
                continue
            existing = self.library.find(slug)
            if existing and not it.get("force"):
                # Verificar fisico
                from pathlib import Path as _P
                if _P(existing.get("path", "")).exists():
                    results["skipped"].append(slug)
                    continue
            it["slug"] = slug
            active.append(it)

        if not active:
            self.log.info("  Nada que generar (todo cacheado)")
            return results

        n_extends_per = max(0, (
            (active[0].get("target_duration", active[0].get("duration", 10))
             - active[0].get("duration", 10)
             + EXTEND_INCREMENT - 1)
            // EXTEND_INCREMENT
        ))
        self.log.info(f"  Batch paralelo: {len(active)} clips · "
                      f"base + {n_extends_per} extends c/u")

        # ── Fase 1: submit todas las bases ──
        self.log.info("  [Fase 1/3] Submitting bases en paralelo...")
        for it in active:
            try:
                tid = self._submit(
                    prompt=it["prompt"],
                    image_url=it["image_url"],
                    duration=it.get("duration", 10),
                    aspect_ratio=it.get("aspect_ratio"),
                    negative_prompt=it.get("negative_prompt"),
                )
                # Persistir ANTES de continuar
                self.tracker.log_submit(
                    slug=it["slug"], task_id=tid, kind="base", extend_step=0,
                    image_url=it["image_url"],
                    duration=it.get("duration", 10),
                    prompt=it["prompt"],
                    target_duration=it.get("target_duration"),
                )
                it["_base_task"] = tid
                self.log.info(f"    {it['slug']}: base task={tid}")
            except Exception as exc:
                self.log.error(f"    {it['slug']}: submit fallo: {exc}")
                self.tracker.log_failure(it["slug"], None, f"submit base: {exc}")
                it["_error"] = str(exc)
            time.sleep(submit_spacing)

        # ── Fase 2: poll bases ──
        self.log.info("  [Fase 1/3] Polling bases...")
        self._wait_phase(active, "_base_task", "_base_video_id",
                         "_base_video_url", KLING_IMG2VIDEO_PATH,
                         poll_interval, max_phase_seconds, extend_step=0)

        # ── Fase 3+: extends ──
        for ext_idx in range(n_extends_per):
            phase_label = f"extend {ext_idx+1}/{n_extends_per}"
            prev_id_key = "_base_video_id" if ext_idx == 0 else f"_ext{ext_idx-1}_video_id"
            ext_task_key = f"_ext{ext_idx}_task"
            ext_id_key = f"_ext{ext_idx}_video_id"
            ext_url_key = f"_ext{ext_idx}_video_url"

            self.log.info(f"  [Fase {ext_idx+2}] Submitting {phase_label}...")
            for it in active:
                if it.get("_error"):
                    continue
                prev_video_id = it.get(prev_id_key)
                if not prev_video_id:
                    it["_error"] = f"sin {prev_id_key}, salto extend"
                    continue
                try:
                    tid = self._extend(
                        video_id=prev_video_id,
                        prompt=it.get("extend_prompt"),
                        negative_prompt=it.get("negative_prompt"),
                    )
                    # Persistir ANTES de continuar
                    self.tracker.log_submit(
                        slug=it["slug"], task_id=tid, kind="extend",
                        extend_step=ext_idx + 1,
                        parent_video_id=prev_video_id,
                        prompt=it.get("extend_prompt") or "",
                        duration=5,
                        target_duration=it.get("target_duration"),
                    )
                    it[ext_task_key] = tid
                    self.log.info(f"    {it['slug']}: {phase_label} task={tid}")
                except Exception as exc:
                    self.log.error(f"    {it['slug']}: {phase_label} fallo: {exc}")
                    self.tracker.log_failure(it["slug"], None, f"submit ext{ext_idx+1}: {exc}")
                    it["_error"] = str(exc)
                time.sleep(submit_spacing)

            self.log.info(f"  [Fase {ext_idx+2}] Polling {phase_label}...")
            self._wait_phase(active, ext_task_key, ext_id_key, ext_url_key,
                             KLING_EXTEND_PATH, poll_interval, max_phase_seconds,
                             extend_step=ext_idx + 1)

        # ── Fase final: descargar, QA y registrar ──
        self.log.info("  [Fase final] Descargando + QA + registrando...")
        last_url_key = (f"_ext{n_extends_per-1}_video_url"
                         if n_extends_per > 0 else "_base_video_url")
        for it in active:
            if it.get("_error"):
                results["errors"].append({"slug": it["slug"], "error": it["_error"]})
                continue
            url = it.get(last_url_key)
            if not url:
                results["errors"].append({"slug": it["slug"], "error": "sin URL final"})
                continue
            try:
                cat = it.get("category", "estudio")
                dest = self.library.base / cat / f"{it['slug']}.mp4"
                self._download_video(url, dest)
                self.tracker.log_download(it["slug"], dest, dest.stat().st_size)

                # QA del clip
                target = it.get("target_duration") or it.get("duration", 10)
                qa_min = max(0.0, target - 2)
                qa_res = qa.check_kling_clip(dest,
                                              expected_min_duration=qa_min,
                                              expected_max_duration=target + 5)
                self.tracker.log_qa(it["slug"], qa_res["ok"], qa_res["checks"])
                if not qa_res["ok"]:
                    self.log.error(f"    QA FAILED {it['slug']}: {qa_res['errors']}")
                    try:
                        dest.unlink()
                    except Exception:  # noqa: BLE001
                        pass
                    results["errors"].append({"slug": it["slug"],
                                              "error": f"QA: {qa_res['errors']}"})
                    continue

                self.library.register(
                    slug=it["slug"], path=dest,
                    category=cat, prompt=it["prompt"],
                    description=it.get("description") or "",
                    tags=it.get("tags") or [], modulo=it.get("modulo"),
                    source=f"kling-1.6-{self.mode}-parallel",
                )
                self.tracker.log_register(it["slug"], ok=True)
                results["generated"].append(it["slug"])
                self.log.info(f"    {it['slug']}: OK (QA + registered)")
            except Exception as exc:
                results["errors"].append({"slug": it["slug"], "error": str(exc)})
                self.tracker.log_register(it["slug"], ok=False, error=str(exc))
                self.log.error(f"    {it['slug']}: download/register fallo: {exc}")

        return results

    def _wait_phase(self, items: list[dict], task_key: str,
                    out_id_key: str, out_url_key: str,
                    path: str, poll_interval: int, max_seconds: int,
                    extend_step: int = 0):
        """Pollea TODAS las tareas en una fase hasta completar (o fallar).
        Modifica items in-place anyadiendo out_id_key / out_url_key.
        Ademas loguea complete/fail en el tracker (recovery-friendly)."""
        import time
        pending = {it["slug"]: it for it in items
                   if it.get(task_key) and not it.get("_error")}
        elapsed = 0
        while pending and elapsed < max_seconds:
            done_now = []
            for slug, it in pending.items():
                tid = it[task_key]
                try:
                    url = KLING_BASE + path + f"/{tid}"
                    r = self.http.get(url, headers=self._auth_headers(), timeout=60)
                    if r.status_code != 200:
                        continue
                    body = r.json()
                    data = body.get("data", {})
                    status = (data.get("task_status") or "").lower()
                    if status == "succeed":
                        videos = (data.get("task_result") or {}).get("videos") or []
                        if videos:
                            vid = videos[0].get("id")
                            vurl = videos[0].get("url")
                            it[out_id_key] = vid
                            it[out_url_key] = vurl
                            self.tracker.log_complete(slug, tid, vid, vurl)
                            done_now.append(slug)
                            self.log.info(f"    OK {slug} ({tid[:10]}...)")
                        else:
                            it["_error"] = "succeed sin videos"
                            self.tracker.log_failure(slug, tid, "succeed sin videos")
                            done_now.append(slug)
                    elif status in ("failed", "error", "cancelled"):
                        it["_error"] = f"task fallo: {body}"
                        self.tracker.log_failure(slug, tid, f"task fallo: {status}")
                        done_now.append(slug)
                except Exception as exc:
                    self.log.warning(f"    poll {slug} fallo: {type(exc).__name__}")
            for slug in done_now:
                del pending[slug]
            if pending:
                self.log.info(f"    quedan {len(pending)} pendientes...")
                time.sleep(poll_interval)
                elapsed += poll_interval
        # Marca timeouts (NO loguea como fail en tracker porque puede que en el
        # futuro complete; el reconcile lo recogera)
        for _slug, it in pending.items():
            it["_error"] = f"timeout fase tras {max_seconds}s"

    def generate_batch(self, items: list[dict],
                       delay_seconds: float = 3.0) -> dict:
        results = {"generated": [], "errors": [], "skipped": []}
        for it in items:
            slug = _slugify(it.get("slug") or "")
            if not slug or not it.get("prompt") or not it.get("image_url"):
                results["errors"].append({"slug": slug, "error": "faltan campos"})
                continue
            if self.library.find(slug) and not it.get("force"):
                results["skipped"].append(slug)
                continue
            try:
                self.generate_concept(
                    slug=slug,
                    prompt=it["prompt"],
                    image_url=it["image_url"],
                    duration=it.get("duration", 10),
                    target_duration=it.get("target_duration"),
                    aspect_ratio=it.get("aspect_ratio"),
                    category=it.get("category", "estudio"),
                    modulo=it.get("modulo"),
                    tags=it.get("tags") or [],
                    description=it.get("description") or "",
                    negative_prompt=it.get("negative_prompt"),
                    extend_prompt=it.get("extend_prompt"),
                    force=it.get("force", False),
                )
                results["generated"].append(slug)
            except Exception as exc:
                self.log.error(f"  Error en {slug}: {exc}")
                results["errors"].append({"slug": slug, "error": str(exc)})
            time.sleep(delay_seconds)
        return results
