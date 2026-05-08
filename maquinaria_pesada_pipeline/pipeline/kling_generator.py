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
                 mode: str = "pro"):
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
        """POST image2video. Devuelve task_id."""
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
        r = self.http.post(url, json=payload,
                           headers=self._auth_headers(), timeout=60)
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
        """POST video-extend: continua la escena +5s desde el ultimo frame."""
        payload = {
            "video_id":        video_id,
            "prompt":          prompt or "continue scene naturally, same setting and characters, subtle natural motion",
            "negative_prompt": negative_prompt or DEFAULT_NEGATIVE,
            "cfg_scale":       cfg_scale,
        }
        url = KLING_BASE + KLING_EXTEND_PATH
        r = self.http.post(url, json=payload,
                           headers=self._auth_headers(), timeout=60)
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

    def _download_video(self, url: str, dest: Path) -> Path:
        import requests
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 15):
                    if chunk:
                        f.write(chunk)
        return dest

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
                         force: bool = False) -> dict:
        """Genera un clip Kling. Si target_duration > duration, encadena
        extends (+5s cada uno) hasta alcanzar target."""
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
        task_id = self._submit(prompt, image_url, duration, aspect_ratio,
                                negative_prompt=negative_prompt)
        self.log.info(f"    [base] task_id={task_id}")
        result = self._poll(task_id, path=KLING_IMG2VIDEO_PATH)
        videos = (result.get("task_result") or {}).get("videos") or []
        if not videos:
            raise RuntimeError(f"Tarea succeed sin videos: {result}")
        last_video = videos[0]
        last_video_id = last_video.get("id")
        last_video_url = last_video.get("url")

        # 2) Extends sucesivos (+~5s cada uno) hasta target
        EXTEND_INCREMENT = 5
        n_extends = max(0, (target - duration + EXTEND_INCREMENT - 1) // EXTEND_INCREMENT)
        for i in range(n_extends):
            self.log.info(f"    [extend {i+1}/{n_extends}] desde video_id={last_video_id}")
            ext_task = self._extend(
                video_id=last_video_id,
                prompt=extend_prompt,
                negative_prompt=negative_prompt,
            )
            ext_result = self._poll(ext_task, path=KLING_EXTEND_PATH)
            ext_videos = (ext_result.get("task_result") or {}).get("videos") or []
            if not ext_videos:
                raise RuntimeError(f"Extend sin videos: {ext_result}")
            last_video = ext_videos[0]
            last_video_id = last_video.get("id")
            last_video_url = last_video.get("url")

        # 3) Descargar el ultimo (Kling devuelve un video acumulado con cada extend)
        if not last_video_url:
            raise RuntimeError(f"Sin URL final: {last_video}")
        dest = self.library.base / category / f"{slug}.mp4"
        self._download_video(last_video_url, dest)
        self.log.info(f"    descargado: {dest}")

        scene = self.library.register(
            slug=slug, path=dest,
            category=category, prompt=prompt,
            description=description,
            tags=tags or [], modulo=modulo,
            source=f"kling-1.6-{self.mode}-{target}s",
        )
        return scene

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
