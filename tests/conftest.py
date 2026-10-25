import time
from pathlib import Path

import pytest

from playlistdrop import engine as real_engine
from playlistdrop.engine import Entry, Playlist


class FakeEngine:
    """Stands in for engine.py: no network, writes tiny files."""

    format_opts = staticmethod(real_engine.format_opts)

    def __init__(self, n=3, fail=(), list_error=None, delay=0.0):
        self.n, self.fail, self.list_error, self.delay = n, set(fail), list_error, delay
        self.calls = []

    def environment(self):
        return {"ytdlp": "test", "ffmpeg": True, "js_runtime": "node"}

    def fetch_playlist(self, url, cookies_from_browser=None):
        if self.list_error:
            raise RuntimeError(self.list_error)
        return Playlist(
            id="PL1", title="My Mix: Vol/1", uploader="Someone",
            entries=[Entry(i, f"vid{i}", f"Song {i}", f"https://youtu.be/vid{i}") for i in range(1, self.n + 1)],
        )

    def download_entry(self, entry, dest, mode, quality=720, on_progress=None, should_cancel=None,
                       cookies_from_browser=None, stem_width=2):
        self.calls.append(entry.index)
        if on_progress:
            on_progress({"stage": "downloading", "fraction": 0.5, "speed": 1000, "eta": 1})
        if self.delay:
            end = time.time() + self.delay
            while time.time() < end:
                if should_cancel and should_cancel():
                    raise real_engine.Cancelled()
                time.sleep(0.01)
        if entry.index in self.fail:
            raise RuntimeError("ERROR: [youtube] vid: Video unavailable")
        dest.mkdir(parents=True, exist_ok=True)
        ext = {"video": "mp4", "audio": "m4a", "mp3": "mp3"}[mode]
        p = Path(dest) / f"{real_engine.entry_stem(entry, stem_width)}.{ext}"
        p.write_bytes(b"x" * 100)
        return p


def wait_for(job, statuses=("done", "error", "cancelled"), timeout=5):
    end = time.time() + timeout
    while time.time() < end:
        if job.status in statuses:
            return job
        time.sleep(0.02)
    raise AssertionError(f"job stuck in {job.status}")


@pytest.fixture
def fake():
    return FakeEngine()
