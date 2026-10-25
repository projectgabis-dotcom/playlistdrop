"""Thin, well-configured wrapper around yt-dlp.

Most "yt-dlp doesn't work" reports come from three things this module handles for you:
an outdated yt-dlp, no JavaScript runtime for YouTube's challenge solver, and missing ffmpeg.
"""

from __future__ import annotations

import os
import re
import shutil
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

MODES = ("video", "audio", "mp3")
QUALITIES = (360, 480, 720, 1080, 1440, 2160)
DEFAULT_QUALITY = 720

ProgressCallback = Callable[[dict], None]


class Cancelled(Exception):
    """Raised from a progress hook to abort an in-flight download."""


@dataclass
class Entry:
    index: int
    id: str
    title: str
    url: str
    duration: Optional[float] = None
    thumbnail: Optional[str] = None


@dataclass
class Playlist:
    id: str
    title: str
    uploader: Optional[str]
    entries: list[Entry] = field(default_factory=list)


# --------------------------------------------------------------------------- environment


def js_runtimes() -> list[dict]:
    """Every JS runtime on this machine, as yt-dlp sees it (it enforces minimum versions)."""
    found = []
    try:
        from yt_dlp.utils import _jsruntime as jr

        candidates = [
            ("deno", jr.DenoJsRuntime),
            ("node", jr.NodeJsRuntime),
            ("bun", jr.BunJsRuntime),
            ("quickjs", jr.QuickJsRuntime),
        ]
        for name, cls in candidates:
            try:
                info = cls().info
            except Exception:  # noqa: BLE001 - a broken runtime is just "not found"
                info = None
            if info:
                found.append(
                    {"name": name, "path": info.path, "version": info.version, "ok": bool(info.supported)}
                )
    except ImportError:  # pragma: no cover - very old yt-dlp without the EJS system
        for name in ("deno", "node", "bun"):
            if path := shutil.which(name):
                found.append({"name": name, "path": path, "version": "?", "ok": True})
    return found


def find_js_runtime() -> Optional[tuple[str, str]]:
    """(name, path) of the first runtime new enough for YouTube's challenge solver."""
    for rt in js_runtimes():
        if rt["ok"]:
            return rt["name"], rt["path"]
    return None


def find_ffmpeg() -> Optional[str]:
    return shutil.which("ffmpeg")


def ytdlp_version() -> str:
    try:
        from yt_dlp.version import __version__

        return __version__
    except Exception:  # pragma: no cover - only when yt-dlp is missing
        return "not installed"


def environment() -> dict:
    runtimes = js_runtimes()
    ok = next((r for r in runtimes if r["ok"]), None)
    too_old = [f"{r['name']} {r['version']}" for r in runtimes if not r["ok"]]
    return {
        "ytdlp": ytdlp_version(),
        "ffmpeg": bool(find_ffmpeg()),
        "js_runtime": f"{ok['name']} {ok['version']}" if ok else None,
        "js_too_old": too_old,
    }


# --------------------------------------------------------------------------- options


class _SilentLogger:
    """yt-dlp prints errors even when quiet; we report them ourselves."""

    def debug(self, msg: str) -> None: ...

    def info(self, msg: str) -> None: ...

    def warning(self, msg: str) -> None: ...

    def error(self, msg: str) -> None: ...


def base_opts(cookies_from_browser: Optional[str] = None) -> dict:
    opts: dict = {
        "logger": _SilentLogger(),
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "retries": 10,
        "fragment_retries": 10,
        "extractor_retries": 3,
        "concurrent_fragment_downloads": 4,
        "ignoreerrors": False,
        "noplaylist": True,
    }
    js = find_js_runtime()
    if js:
        opts["js_runtimes"] = {js[0]: {"path": js[1]}}
    ffmpeg = find_ffmpeg()
    if ffmpeg:
        opts["ffmpeg_location"] = ffmpeg
    if cookies_from_browser:
        opts["cookiesfrombrowser"] = (cookies_from_browser, None, None, None)
    return opts


def format_opts(mode: str, quality: int = DEFAULT_QUALITY, has_ffmpeg: bool = True) -> dict:
    """yt-dlp options that produce files an iPhone plays natively."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    quality = int(quality)
    if quality not in QUALITIES:
        raise ValueError(f"quality must be one of {QUALITIES}")

    if mode == "video":
        if not has_ffmpeg:
            # Without ffmpeg we cannot merge separate streams; take the best single mp4.
            return {"format": f"b[ext=mp4][height<={quality}]/b[ext=mp4]/b"}
        return {
            "format": f"bv*[height<={quality}]+ba/b[height<={quality}]/bv*+ba/b",
            # Prefer H.264 + AAC in MP4: plays in iOS Photos/Files/Safari with no conversion.
            "format_sort": [f"res:{quality}", "vcodec:h264", "acodec:aac", "ext:mp4:m4a"],
            "merge_output_format": "mp4",
            "postprocessors": [
                {"key": "FFmpegMetadata", "add_metadata": True},
            ],
        }

    audio_fmt = {"format": "bestaudio[ext=m4a]/bestaudio/b"}
    if not has_ffmpeg:
        return {"format": "bestaudio[ext=m4a]/bestaudio"}
    codec = "mp3" if mode == "mp3" else "m4a"
    pps = [{"key": "FFmpegExtractAudio", "preferredcodec": codec, "preferredquality": "0"}]
    pps.append({"key": "FFmpegMetadata", "add_metadata": True})
    pps.append({"key": "EmbedThumbnail", "already_have_thumbnail": False})
    return {**audio_fmt, "postprocessors": pps, "writethumbnail": True}


def final_ext(mode: str, has_ffmpeg: bool = True) -> Optional[str]:
    if not has_ffmpeg:
        return None
    return {"video": "mp4", "audio": "m4a", "mp3": "mp3"}[mode]


# --------------------------------------------------------------------------- naming

_BAD = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def safe_name(text: str, max_len: int = 120) -> str:
    """Make a string safe as a file/folder name on Windows, macOS, Linux and iOS Files."""
    text = unicodedata.normalize("NFC", text or "").strip()
    text = _BAD.sub("_", text)
    text = re.sub(r"\s+", " ", text).strip(" .")
    if len(text.encode("utf-8")) > max_len:
        text = text.encode("utf-8")[:max_len].decode("utf-8", "ignore").rstrip(" .")
    return text or "untitled"


def entry_stem(entry: Entry, width: int = 2) -> str:
    return f"{entry.index:0{width}d} - {safe_name(entry.title)}"


def find_existing(dest: Path, stem: str, ext: Optional[str]) -> Optional[Path]:
    """Return a finished file for this entry if one is already on disk."""
    if not dest.is_dir():
        return None
    for p in dest.iterdir():
        if not p.is_file() or p.stem != stem:
            continue
        if p.suffix in (".part", ".ytdl", ".webp", ".jpg", ".png") or ".f" in p.suffix:
            continue
        if ext is None or p.suffix == f".{ext}":
            return p
    return None


# --------------------------------------------------------------------------- yt-dlp calls


def _ydl(opts: dict):
    from yt_dlp import YoutubeDL

    return YoutubeDL(opts)


def parse_info(info: dict, source_url: str) -> Playlist:
    """Turn a flat yt-dlp info dict (playlist or single video) into a Playlist."""
    if info.get("_type") in ("playlist", "multi_video") or "entries" in info:
        entries = []
        for i, e in enumerate(info.get("entries") or [], start=1):
            if not e:
                continue
            vid = e.get("id") or ""
            url = e.get("url") or e.get("webpage_url") or f"https://www.youtube.com/watch?v={vid}"
            if url and not url.startswith("http"):
                url = f"https://www.youtube.com/watch?v={vid}"
            title = e.get("title") or vid
            if title in ("[Private video]", "[Deleted video]"):
                continue
            thumbs = e.get("thumbnails") or []
            entries.append(
                Entry(
                    index=e.get("playlist_index") or i,
                    id=vid,
                    title=title,
                    url=url,
                    duration=e.get("duration"),
                    thumbnail=(thumbs[-1].get("url") if thumbs else e.get("thumbnail")),
                )
            )
        return Playlist(
            id=info.get("id") or "",
            title=info.get("title") or "Playlist",
            uploader=info.get("uploader") or info.get("channel"),
            entries=entries,
        )

    vid = info.get("id") or ""
    return Playlist(
        id=vid,
        title=info.get("title") or vid,
        uploader=info.get("uploader") or info.get("channel"),
        entries=[
            Entry(
                index=1,
                id=vid,
                title=info.get("title") or vid,
                url=info.get("webpage_url") or source_url,
                duration=info.get("duration"),
                thumbnail=info.get("thumbnail"),
            )
        ],
    )


def fetch_playlist(url: str, cookies_from_browser: Optional[str] = None) -> Playlist:
    opts = base_opts(cookies_from_browser)
    opts.update({"extract_flat": "in_playlist", "noplaylist": False, "skip_download": True})
    with _ydl(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise RuntimeError("Nothing found at that link.")
    return parse_info(ydl.sanitize_info(info), url)


def download_entry(
    entry: Entry,
    dest: Path,
    mode: str,
    quality: int = DEFAULT_QUALITY,
    on_progress: Optional[ProgressCallback] = None,
    should_cancel: Optional[Callable[[], bool]] = None,
    cookies_from_browser: Optional[str] = None,
    stem_width: int = 2,
) -> Path:
    """Download one entry into `dest`. Returns the final file path."""
    has_ffmpeg = bool(find_ffmpeg())
    stem = entry_stem(entry, stem_width)
    ext = final_ext(mode, has_ffmpeg)
    existing = find_existing(dest, stem, ext)
    if existing:
        return existing

    dest.mkdir(parents=True, exist_ok=True)

    def hook(d: dict) -> None:
        if should_cancel and should_cancel():
            raise Cancelled()
        if not on_progress:
            return
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done = d.get("downloaded_bytes") or 0
            on_progress(
                {
                    "stage": "downloading",
                    "fraction": (done / total) if total else None,
                    "speed": d.get("speed"),
                    "eta": d.get("eta"),
                    "part": (d.get("info_dict") or {}).get("format_id"),
                }
            )
        elif d.get("status") == "finished":
            on_progress({"stage": "processing", "fraction": 1.0})

    def pp_hook(d: dict) -> None:
        if should_cancel and should_cancel():
            raise Cancelled()
        if on_progress and d.get("status") == "started":
            on_progress({"stage": "processing", "fraction": 1.0})

    opts = base_opts(cookies_from_browser)
    opts.update(format_opts(mode, quality, has_ffmpeg))
    opts.update(
        {
            # Partial files live in .tmp; only finished files appear in the folder.
            "paths": {"home": str(dest), "temp": str(dest / ".tmp")},
            "outtmpl": {"default": f"{stem}.%(ext)s"},
            "progress_hooks": [hook],
            "postprocessor_hooks": [pp_hook],
        }
    )
    with _ydl(opts) as ydl:
        info = ydl.extract_info(entry.url, download=True)

    path = None
    for req in (info or {}).get("requested_downloads") or []:
        if req.get("filepath"):
            path = Path(req["filepath"])
    if not path or not path.exists():
        path = find_existing(dest, stem, ext) or find_existing(dest, stem, None)
    if not path:
        raise RuntimeError("Download finished but the file was not found.")
    return path


def cleanup_tmp(dest: Path) -> None:
    """Remove the temp folder once nothing in the playlist is downloading."""
    try:
        os.rmdir(dest / ".tmp")  # only succeeds when empty
    except OSError:
        pass
