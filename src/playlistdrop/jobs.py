"""Background job manager: one job = one playlist link, downloaded item by item."""

from __future__ import annotations

import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from . import engine as _engine
from .engine import Cancelled, Entry, safe_name


@dataclass
class Item:
    index: int
    id: str
    title: str
    url: str
    duration: Optional[float] = None
    thumbnail: Optional[str] = None
    status: str = "queued"  # queued | downloading | processing | done | skipped | error | cancelled
    progress: float = 0.0
    speed: Optional[float] = None
    eta: Optional[int] = None
    file: Optional[str] = None  # path relative to the downloads root
    size: Optional[int] = None
    error: Optional[str] = None


@dataclass
class Job:
    id: str
    url: str
    mode: str
    quality: int
    status: str = "listing"  # listing | running | done | error | cancelled
    title: Optional[str] = None
    uploader: Optional[str] = None
    folder: Optional[str] = None  # relative to downloads root
    error: Optional[str] = None
    created: float = field(default_factory=time.time)
    items: list[Item] = field(default_factory=list)
    cancel_requested: bool = False

    def counts(self) -> dict:
        c = {"total": len(self.items), "done": 0, "error": 0, "active": 0, "queued": 0}
        for it in self.items:
            if it.status in ("done", "skipped"):
                c["done"] += 1
            elif it.status == "error":
                c["error"] += 1
            elif it.status in ("downloading", "processing"):
                c["active"] += 1
            elif it.status == "queued":
                c["queued"] += 1
        return c

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("cancel_requested", None)
        d["counts"] = self.counts()
        return d


class JobManager:
    """Runs jobs on a shared worker pool. `engine` is injectable for tests."""

    def __init__(
        self,
        root: Path,
        engine=_engine,
        workers: int = 3,
        cookies_from_browser: Optional[str] = None,
    ):
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.engine = engine
        self.cookies = cookies_from_browser
        self._pool = ThreadPoolExecutor(max_workers=max(1, workers), thread_name_prefix="dl")
        self._lock = threading.RLock()
        self._jobs: dict[str, Job] = {}

    # ---------------------------------------------------------------- public API

    def create(self, url: str, mode: str = "video", quality: int = 720) -> Job:
        url = (url or "").strip()
        if not url.startswith(("http://", "https://")):
            raise ValueError("Paste a full YouTube link (starting with https://).")
        self.engine.format_opts(mode, quality)  # validates mode/quality early
        job = Job(id=uuid.uuid4().hex[:10], url=url, mode=mode, quality=int(quality))
        with self._lock:
            self._jobs[job.id] = job
        threading.Thread(target=self._list_and_queue, args=(job,), daemon=True).start()
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def all(self) -> list[Job]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.created, reverse=True)

    def cancel(self, job_id: str) -> bool:
        job = self.get(job_id)
        if not job:
            return False
        with self._lock:
            job.cancel_requested = True
            for it in job.items:
                if it.status == "queued":
                    it.status = "cancelled"
            if job.status in ("listing", "running"):
                job.status = "cancelled"
        return True

    def retry_failed(self, job_id: str) -> int:
        job = self.get(job_id)
        if not job or job.status == "listing":
            return 0
        with self._lock:
            job.cancel_requested = False
            todo = [it for it in job.items if it.status in ("error", "cancelled")]
            for it in todo:
                it.status, it.error, it.progress = "queued", None, 0.0
            if todo:
                job.status = "running"
        for it in todo:
            self._pool.submit(self._download, job, it)
        return len(todo)

    def remove(self, job_id: str) -> bool:
        self.cancel(job_id)
        with self._lock:
            return self._jobs.pop(job_id, None) is not None

    def shutdown(self) -> None:
        for job in self.all():
            job.cancel_requested = True
        self._pool.shutdown(wait=False, cancel_futures=True)

    # ---------------------------------------------------------------- workers

    def _list_and_queue(self, job: Job) -> None:
        try:
            pl = self.engine.fetch_playlist(job.url, cookies_from_browser=self.cookies)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            with self._lock:
                job.status, job.error = "error", friendly_error(exc)
            return
        if not pl.entries:
            with self._lock:
                job.status, job.error = "error", "This playlist is empty or private."
            return
        with self._lock:
            if job.cancel_requested:
                return
            job.title, job.uploader = pl.title, pl.uploader
            # Same playlist → same folder, so re-running it skips what you already have.
            job.folder = safe_name(pl.title)
            job.items = [
                Item(e.index, e.id, e.title, e.url, e.duration, e.thumbnail) for e in pl.entries
            ]
            job.status = "running"
        for it in job.items:
            self._pool.submit(self._download, job, it)

    def _download(self, job: Job, item: Item) -> None:
        if job.cancel_requested or item.status != "queued":
            self._maybe_finish(job)
            return
        with self._lock:
            item.status = "downloading"

        def on_progress(p: dict) -> None:
            with self._lock:
                item.status = p.get("stage", item.status)
                if p.get("fraction") is not None:
                    item.progress = round(float(p["fraction"]), 4)
                item.speed, item.eta = p.get("speed"), p.get("eta")

        width = max(2, len(str(max((i.index for i in job.items), default=1))))
        dest = self.root / (job.folder or "downloads")
        try:
            path = self.engine.download_entry(
                Entry(item.index, item.id, item.title, item.url, item.duration, item.thumbnail),
                dest,
                job.mode,
                job.quality,
                on_progress=on_progress,
                should_cancel=lambda: job.cancel_requested,
                cookies_from_browser=self.cookies,
                stem_width=width,
            )
            with self._lock:
                item.status, item.progress = "done", 1.0
                item.file = path.relative_to(self.root).as_posix()
                item.size = path.stat().st_size if path.exists() else None
                item.speed = item.eta = None
        except Cancelled:
            with self._lock:
                item.status = "cancelled"
        except Exception as exc:  # noqa: BLE001 - one bad video must not stop the playlist
            with self._lock:
                item.status, item.error = "error", friendly_error(exc)
                item.speed = item.eta = None
        finally:
            self._maybe_finish(job)

    def _maybe_finish(self, job: Job) -> None:
        with self._lock:
            if job.status != "running":
                return
            if any(it.status in ("queued", "downloading", "processing") for it in job.items):
                return
            job.status = "done"
        if job.folder:
            cleanup = getattr(self.engine, "cleanup_tmp", None)
            if cleanup:
                cleanup(self.root / job.folder)


def friendly_error(exc: Exception) -> str:
    msg = str(exc).replace("ERROR: ", "").strip()
    low = msg.lower()
    if "sign in to confirm" in low or "not a bot" in low:
        return (
            "YouTube asked to confirm you're not a bot. Restart with "
            "--cookies-from-browser firefox (or chrome) while logged in to YouTube."
        )
    if "private video" in low:
        return "This video is private."
    if "video unavailable" in low or "not available" in low:
        return "This video is unavailable (removed or blocked in your country)."
    if "age" in low and "restrict" in low or "confirm your age" in low:
        return "Age-restricted video: use --cookies-from-browser with a logged-in browser."
    if "members-only" in low or "join this channel" in low:
        return "Members-only video."
    if "unsupported url" in low:
        return "That link isn't a YouTube video or playlist."
    # Strip yt-dlp's "[youtube] abc123:" prefix for readability.
    msg = msg.split(": ", 1)[1] if msg.startswith("[") and ": " in msg else msg
    return msg[:300] or exc.__class__.__name__
