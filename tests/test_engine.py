import pytest

from playlistdrop import engine
from playlistdrop.engine import Entry


def test_safe_name_strips_illegal_characters():
    assert engine.safe_name('AC/DC: "Back" <in> Black?') == "AC_DC_ _Back_ _in_ Black_"


def test_safe_name_never_empty_and_trims_dots():
    assert engine.safe_name("  ...  ") == "untitled"
    assert engine.safe_name("") == "untitled"


def test_safe_name_truncates_on_utf8_boundary():
    name = engine.safe_name("é" * 200, max_len=21)
    assert len(name.encode()) <= 21
    name.encode().decode()  # still valid UTF-8


def test_entry_stem_zero_pads():
    assert engine.entry_stem(Entry(7, "id", "Hi", "u"), 3) == "007 - Hi"


@pytest.mark.parametrize("mode", ["video", "audio", "mp3"])
def test_format_opts_valid_modes(mode):
    opts = engine.format_opts(mode, 720)
    assert "format" in opts


def test_video_prefers_iphone_codecs():
    opts = engine.format_opts("video", 1080)
    assert opts["merge_output_format"] == "mp4"
    assert "vcodec:h264" in opts["format_sort"]
    assert "height<=1080" in opts["format"]


def test_audio_converts_to_m4a_and_embeds_cover():
    keys = [pp["key"] for pp in engine.format_opts("audio")["postprocessors"]]
    assert keys[0] == "FFmpegExtractAudio" and "EmbedThumbnail" in keys
    assert engine.format_opts("mp3")["postprocessors"][0]["preferredcodec"] == "mp3"


def test_without_ffmpeg_avoids_merging():
    assert "+" not in engine.format_opts("video", 720, has_ffmpeg=False)["format"]
    assert "postprocessors" not in engine.format_opts("audio", has_ffmpeg=False)


def test_format_opts_rejects_bad_input():
    with pytest.raises(ValueError):
        engine.format_opts("gif")
    with pytest.raises(ValueError):
        engine.format_opts("video", 999)


def test_parse_playlist_skips_private_and_fixes_urls():
    info = {
        "_type": "playlist", "id": "PL", "title": "Mix", "uploader": "Me",
        "entries": [
            {"id": "a", "title": "One", "url": "a", "duration": 61},
            {"id": "b", "title": "[Private video]", "url": "https://www.youtube.com/watch?v=b"},
            None,
            {"id": "c", "title": "Three", "url": "https://www.youtube.com/watch?v=c", "playlist_index": 3},
        ],
    }
    pl = engine.parse_info(info, "src")
    assert [e.title for e in pl.entries] == ["One", "Three"]
    assert pl.entries[0].url == "https://www.youtube.com/watch?v=a"
    assert pl.entries[1].index == 3


def test_parse_single_video_becomes_one_entry():
    pl = engine.parse_info({"id": "v", "title": "Solo", "webpage_url": "https://youtu.be/v"}, "src")
    assert len(pl.entries) == 1 and pl.entries[0].url == "https://youtu.be/v"


def test_find_existing_ignores_partial_files(tmp_path):
    (tmp_path / "01 - A.mp4.part").write_text("x")
    (tmp_path / "01 - A.f137.mp4").write_text("x")
    assert engine.find_existing(tmp_path, "01 - A", "mp4") is None
    (tmp_path / "01 - A.mp4").write_text("x")
    assert engine.find_existing(tmp_path, "01 - A", "mp4").name == "01 - A.mp4"


def test_download_entry_skips_existing_file(tmp_path, monkeypatch):
    (tmp_path / "01 - A.m4a").write_text("x")
    monkeypatch.setattr(engine, "_ydl", lambda opts: pytest.fail("should not hit yt-dlp"))
    p = engine.download_entry(Entry(1, "id", "A", "u"), tmp_path, "audio")
    assert p.name == "01 - A.m4a"
