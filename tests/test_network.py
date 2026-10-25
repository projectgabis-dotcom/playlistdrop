"""Real YouTube round-trip. Run with: pytest -m network"""

import pytest

from playlistdrop import engine

pytestmark = pytest.mark.network

# "Me at the zoo" — the first YouTube video, 19 s, unlikely to disappear.
VIDEO = "https://www.youtube.com/watch?v=jNQXAC9IVRw"


def test_fetch_and_download_audio(tmp_path):
    pl = engine.fetch_playlist(VIDEO)
    assert pl.entries and pl.entries[0].id == "jNQXAC9IVRw"
    path = engine.download_entry(pl.entries[0], tmp_path, "audio")
    assert path.suffix == ".m4a" and path.stat().st_size > 50_000


def test_download_video_mp4(tmp_path):
    pl = engine.fetch_playlist(VIDEO)
    path = engine.download_entry(pl.entries[0], tmp_path, "video", 360)
    assert path.suffix == ".mp4" and path.stat().st_size > 100_000
