"""FastAPI app: JSON API + the phone-friendly web UI + file/zip downloads."""

from __future__ import annotations

import hmac
import os
import tempfile
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.background import BackgroundTask

from . import __version__
from . import engine as _engine
from .jobs import JobManager

STATIC = Path(__file__).parent / "static"
MEDIA_EXT = {".mp4", ".m4a", ".mp3", ".webm", ".mkv", ".opus", ".ogg", ".mov"}
COOKIE = "pd_key"


class NewJob(BaseModel):
    url: str
    mode: str = "video"
    quality: int = 720


def create_app(
    manager: JobManager,
    token: Optional[str] = None,
    share_urls: Optional[list[str]] = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        manager.shutdown()

    app = FastAPI(
        title="PlaylistDrop", version=__version__, docs_url=None, redoc_url=None, lifespan=lifespan
    )
    root = manager.root.resolve()

    # ------------------------------------------------------------- access control

    def authorized(request: Request) -> bool:
        if not token:
            return True
        client = request.client.host if request.client else ""
        if client in ("127.0.0.1", "::1"):
            return True
        supplied = (
            request.cookies.get(COOKIE)
            or request.query_params.get("k")
            or request.headers.get("x-playlistdrop-key")
            or ""
        )
        return hmac.compare_digest(supplied, token)

    @app.middleware("http")
    async def guard(request: Request, call_next):
        path = request.url.path
        if path.startswith("/static/") or path in ("/favicon.ico", "/manifest.webmanifest"):
            response = await call_next(request)
            # Revalidate (cheap 304 via ETag) so phones pick up new versions after an update.
            response.headers["Cache-Control"] = "no-cache"
            return response
        if not authorized(request):
            if path.startswith("/api/") or path.startswith("/dl/"):
                return JSONResponse({"detail": "Scan the QR code shown on your computer."}, 401)
            return HTMLResponse(LOCKED_PAGE, status_code=401)
        response = await call_next(request)
        if token and request.query_params.get("k") == token:
            response.set_cookie(COOKIE, token, max_age=60 * 60 * 24 * 365, samesite="lax")
        return response

    # ------------------------------------------------------------- pages

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        if token and request.query_params.get("k"):
            # Drop the key from the address bar once the cookie is set.
            resp = RedirectResponse("/", status_code=303)
            resp.set_cookie(COOKIE, token, max_age=60 * 60 * 24 * 365, samesite="lax")
            return resp
        html = (STATIC / "index.html").read_text(encoding="utf-8")
        # Stamp assets so a phone never runs a stale cached app.js/style.css after an update.
        stamp = str(int(max(p.stat().st_mtime for p in STATIC.iterdir())))
        for asset in ("style.css", "app.js"):
            html = html.replace(f"/static/{asset}", f"/static/{asset}?v={stamp}")
        return HTMLResponse(html)

    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/manifest.webmanifest")
    def manifest():
        return FileResponse(STATIC / "manifest.webmanifest", media_type="application/manifest+json")

    # ------------------------------------------------------------- API

    @app.get("/api/status")
    def status():
        env = manager.engine.environment()
        return {"version": __version__, **env, "share_urls": share_urls or [], "root": str(root)}

    @app.post("/api/jobs")
    def new_job(body: NewJob):
        try:
            job = manager.create(body.url, body.mode, body.quality)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return job.to_dict()

    @app.get("/api/jobs")
    def list_jobs():
        return [j.to_dict() for j in manager.all()]

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str):
        job = manager.get(job_id)
        if not job:
            raise HTTPException(404, "No such job")
        return job.to_dict()

    @app.post("/api/jobs/{job_id}/cancel")
    def cancel_job(job_id: str):
        if not manager.cancel(job_id):
            raise HTTPException(404, "No such job")
        return {"ok": True}

    @app.post("/api/jobs/{job_id}/retry")
    def retry_job(job_id: str):
        if not manager.get(job_id):
            raise HTTPException(404, "No such job")
        return {"retried": manager.retry_failed(job_id)}

    @app.delete("/api/jobs/{job_id}")
    def delete_job(job_id: str):
        if not manager.remove(job_id):
            raise HTTPException(404, "No such job")
        return {"ok": True}

    @app.get("/api/library")
    def library():
        """Every folder of finished media under the downloads root (survives restarts)."""
        folders = []
        if root.is_dir():
            for d in sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                if not d.is_dir() or d.name.startswith("."):
                    continue
                files = [
                    {
                        "name": f.name,
                        "path": f.relative_to(root).as_posix(),
                        "size": f.stat().st_size,
                    }
                    for f in sorted(d.iterdir())
                    if f.is_file() and f.suffix.lower() in MEDIA_EXT
                ]
                if files:
                    folders.append({"name": d.name, "path": d.name, "files": files})
        return folders

    # ------------------------------------------------------------- files

    def resolve_inside(rel: str) -> Path:
        if any(part.startswith(".") for part in Path(rel).parts):
            raise HTTPException(404, "Not found")  # hidden files: key, temp zips, partials
        target = (root / rel).resolve()
        if target != root and root not in target.parents:
            raise HTTPException(404, "Not found")
        return target

    @app.get("/dl/{rel:path}")
    def download_file(rel: str, inline: bool = False):
        target = resolve_inside(rel)
        if not target.is_file():
            raise HTTPException(404, "Not found")
        disp = "inline" if inline else "attachment"
        headers = {"Content-Disposition": f"{disp}; filename*=UTF-8''{quote(target.name)}"}
        return FileResponse(target, headers=headers)

    @app.get("/zip/{rel:path}")
    def download_zip(rel: str):
        folder = resolve_inside(rel)
        if not folder.is_dir() or folder == root:
            raise HTTPException(404, "Not found")
        files = [f for f in sorted(folder.iterdir()) if f.is_file() and f.suffix.lower() in MEDIA_EXT]
        if not files:
            raise HTTPException(404, "Nothing downloaded in this folder yet")
        # Temp zip lives next to the downloads (same disk), hidden from the library.
        fd, tmp = tempfile.mkstemp(prefix=".zip-", suffix=".zip", dir=root)
        os.close(fd)
        # Media is already compressed: STORED is fast and keeps the zip the same size.
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
            for f in files:
                zf.write(f, arcname=f"{folder.name}/{f.name}")
        name = f"{folder.name}.zip"
        headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"}
        return FileResponse(
            tmp,
            media_type="application/zip",
            headers=headers,
            background=BackgroundTask(lambda: os.path.exists(tmp) and os.remove(tmp)),
        )

    return app


LOCKED_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PlaylistDrop · scan to connect</title>
<style>@font-face{font-family:Archivo;src:url(/static/archivo-latin.woff2) format("woff2");font-weight:700 900;font-stretch:62% 100%}
body{font:17px/1.45 -apple-system,system-ui,sans-serif;background:#141414;color:#f1f1ec;
display:grid;place-items:center;min-height:100vh;margin:0;padding:24px}
div{max-width:22rem}h1{font:900 36px/1 Archivo,sans-serif;font-stretch:62%;text-transform:uppercase;margin:18px 0 10px}
.s{width:64px;height:64px;border-radius:50%;background:#ff6a13;transform:rotate(-6deg)}
p{color:#b4b4ad;margin:0}</style></head><body><div>
<div class="s" aria-hidden="true"></div>
<h1>Scan to connect</h1>
<p>Open PlaylistDrop by scanning the QR code in the terminal on your computer.
The code carries a private key, so only you can use this.</p></div></body></html>"""
