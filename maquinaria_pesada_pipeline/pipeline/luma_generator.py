"""
Generador de escenas con Luma Dream Machine API.

Cuesta dinero: cada generacion son ~$0.4. Usa cache (hash del prompt) para
no regenerar.

Endpoint: https://api.lumalabs.ai/dream-machine/v1/generations
Docs: https://docs.lumalabs.ai/docs/api

Uso:
    from pipeline.luma_generator import LumaGenerator
    g = LumaGenerator(library)
    g.generate_concept(
        slug="transformers",
        prompt="...",
        duration=5,
        aspect_ratio="16:9",
        modulo="M5",
    )
"""

import os
import time
from pathlib import Path
from urllib.parse import urljoin

from .logger import get_logger
from .scene_library import SceneLibrary, _slugify

LUMA_BASE = "https://api.lumalabs.ai/dream-machine/v1/"


class LumaGenerator:
    def __init__(self, library: SceneLibrary,
                 api_key: str | None = None,
                 model: str = "ray-2",
                 default_aspect: str = "16:9"):
        self.library = library
        self.api_key = api_key or os.getenv("LUMA_API_KEY")
        if not self.api_key:
            raise RuntimeError("LUMA_API_KEY no definida en entorno ni en .env")
        self.model = model
        self.default_aspect = default_aspect
        self.log = get_logger("luma_generator")
        self._http_session = None

    @property
    def http(self):
        if self._http_session is None:
            try:
                import requests
            except ImportError as exc:
                raise RuntimeError(
                    "Falta el paquete 'requests'. Instalalo: pip install requests"
                ) from exc
            s = requests.Session()
            s.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Accept":        "application/json",
                "Content-Type":  "application/json",
            })
            self._http_session = s
        return self._http_session

    # ── API ─────────────────────────────────────────────────────────

    def _create_generation(self, prompt: str,
                            duration: int = 5,
                            aspect_ratio: str | None = None,
                            loop: bool = False,
                            frame0_url: str | None = None,
                            frame1_url: str | None = None) -> dict:
        """
        POST /generations -> {id, state, ...}

        Si se proporciona frame0_url, hace image-to-video usando esa imagen
        como primer frame (mantiene consistencia de personajes/estudio).
        Si tambien se da frame1_url, interpola entre ambas (rare, util para
        transiciones).

        El endpoint Luma Dream Machine v1 acepta:
          /dream-machine/v1/generations/video
        con keyframes.frame0/frame1 segun docs.
        """
        # Endpoint correcto para video (no imagen)
        url = urljoin(LUMA_BASE, "generations/video")
        payload = {
            "prompt":       prompt,
            "model":        self.model,
            "aspect_ratio": aspect_ratio or self.default_aspect,
            "duration":     f"{duration}s",
            "loop":         loop,
        }
        keyframes = {}
        if frame0_url:
            keyframes["frame0"] = {"type": "image", "url": frame0_url}
        if frame1_url:
            keyframes["frame1"] = {"type": "image", "url": frame1_url}
        if keyframes:
            payload["keyframes"] = keyframes
        r = self.http.post(url, json=payload, timeout=60)
        if r.status_code >= 400:
            self.log.error(f"  Luma API {r.status_code}: {r.text[:500]}")
        r.raise_for_status()
        return r.json()

    def _get_generation(self, gen_id: str) -> dict:
        # endpoint de polling (no requiere /video aqui, ambos id formats funcionan)
        for path in (f"generations/{gen_id}", f"generations/video/{gen_id}"):
            url = urljoin(LUMA_BASE, path)
            r = self.http.get(url, timeout=30)
            if r.status_code == 200:
                return r.json()
        r.raise_for_status()
        return r.json()

    def _wait(self, gen_id: str, max_seconds: int = 600,
              poll: int = 6) -> dict:
        elapsed = 0
        while elapsed < max_seconds:
            data = self._get_generation(gen_id)
            state = data.get("state")
            self.log.debug(f"  Luma {gen_id} state={state}")
            if state == "completed":
                return data
            if state == "failed":
                raise RuntimeError(f"Luma fallo: {data.get('failure_reason')}")
            time.sleep(poll)
            elapsed += poll
        raise TimeoutError(f"Luma timeout tras {max_seconds}s")

    def _download_video(self, url: str, dest: Path) -> Path:
        import requests
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 15):
                    if chunk:
                        f.write(chunk)
        return dest

    # ── flujo de alto nivel ─────────────────────────────────────────

    def generate_concept(self, slug: str, prompt: str,
                         duration: int = 5,
                         aspect_ratio: str | None = None,
                         category: str = "conceptos",
                         modulo: str | None = None,
                         tags: list[str] | None = None,
                         description: str = "",
                         force: bool = False,
                         frame0_url: str | None = None,
                         frame1_url: str | None = None) -> dict:
        """
        Genera (o reutiliza) una escena con Luma. Si ya existe en la library
        con el mismo slug, retorna esa. Si frame0_url se da, usa image-to-video.
        """
        slug = _slugify(slug)
        existing = self.library.find(slug)
        if existing and not force:
            self.log.info(f"  Reutilizando escena cacheada: {slug}")
            return existing

        mode = "image-to-video" if frame0_url else "text-to-video"
        self.log.info(f"  Generando con Luma ({mode}): {slug} (duracion={duration}s)")
        self.log.info(f"    prompt: {prompt[:100]}{'...' if len(prompt)>100 else ''}")
        if frame0_url:
            self.log.info(f"    frame0: {frame0_url}")

        # 1) Crear generacion
        gen = self._create_generation(prompt, duration, aspect_ratio,
                                       frame0_url=frame0_url, frame1_url=frame1_url)
        gen_id = gen.get("id")
        if not gen_id:
            raise RuntimeError(f"Respuesta Luma sin id: {gen}")

        # 2) Esperar completacion
        completed = self._wait(gen_id)

        # 3) Descargar
        video_url = completed.get("assets", {}).get("video")
        if not video_url:
            raise RuntimeError(f"Generacion completada sin video URL: {completed}")
        tmp_path = self.library.base / category / f"{slug}.mp4"
        self._download_video(video_url, tmp_path)
        self.log.info(f"    descargado: {tmp_path}")

        # 4) Registrar en biblioteca
        scene = self.library.register(
            slug=slug, path=tmp_path,
            category=category, prompt=prompt,
            description=description,
            tags=tags or [], modulo=modulo,
            source="luma",
        )
        return scene

    def generate_batch(self, items: list[dict],
                        delay_seconds: float = 2.0) -> dict:
        """
        items = [{"slug","prompt","duration","modulo","tags","description"}, ...]
        Devuelve {"generated":[...], "errors":[...], "skipped":[...]}.
        """
        results = {"generated": [], "errors": [], "skipped": []}
        for it in items:
            slug = _slugify(it.get("slug") or it.get("name") or "")
            if not slug or not it.get("prompt"):
                continue
            if self.library.find(slug):
                results["skipped"].append(slug)
                continue
            try:
                self.generate_concept(
                    slug=slug, prompt=it["prompt"],
                    duration=it.get("duration", 5),
                    modulo=it.get("modulo"),
                    tags=it.get("tags") or [],
                    description=it.get("description") or "",
                )
                results["generated"].append(slug)
            except Exception as exc:
                self.log.error(f"  Error en {slug}: {exc}")
                results["errors"].append({"slug": slug, "error": str(exc)})
            time.sleep(delay_seconds)
        return results
