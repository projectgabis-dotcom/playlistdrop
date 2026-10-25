import pytest

from conftest import FakeEngine, wait_for
from playlistdrop.jobs import JobManager, friendly_error


def test_full_playlist_downloads(tmp_path, fake):
    m = JobManager(tmp_path, engine=fake)
    job = wait_for(m.create("https://youtube.com/playlist?list=PL1", "audio"))
    assert job.status == "done"
    assert job.folder == "My Mix_ Vol_1"
    assert [i.status for i in job.items] == ["done"] * 3
    assert job.items[0].file == "My Mix_ Vol_1/01 - Song 1.m4a"
    assert (tmp_path / job.items[0].file).exists()


def test_one_failure_does_not_stop_the_rest(tmp_path):
    m = JobManager(tmp_path, engine=FakeEngine(n=4, fail={2}))
    job = wait_for(m.create("https://x.test/p", "video"))
    assert job.status == "done"
    assert job.counts() == {"total": 4, "done": 3, "error": 1, "active": 0, "queued": 0}
    assert "unavailable" in job.items[1].error


def test_retry_failed_items(tmp_path):
    eng = FakeEngine(n=2, fail={1})
    m = JobManager(tmp_path, engine=eng)
    job = wait_for(m.create("https://x.test/p"))
    eng.fail.clear()
    assert m.retry_failed(job.id) == 1
    wait_for(job)
    assert job.counts()["error"] == 0


def test_listing_error_is_reported(tmp_path):
    m = JobManager(tmp_path, engine=FakeEngine(list_error="ERROR: Unsupported URL: https://x"))
    job = wait_for(m.create("https://x.test/p"))
    assert job.status == "error" and "isn't a YouTube" in job.error


def test_cancel_stops_queued_and_running(tmp_path):
    m = JobManager(tmp_path, engine=FakeEngine(n=6, delay=0.5), workers=1)
    job = m.create("https://x.test/p")
    wait_for(job, statuses=("running",))
    m.cancel(job.id)
    wait_for(job, statuses=("cancelled",))
    import time
    time.sleep(0.7)
    assert all(i.status in ("cancelled", "done") for i in job.items)
    assert sum(i.status == "done" for i in job.items) <= 1


def test_rejects_non_links(tmp_path, fake):
    m = JobManager(tmp_path, engine=fake)
    with pytest.raises(ValueError):
        m.create("not a link")
    with pytest.raises(ValueError):
        m.create("https://x.test/p", mode="gif")


@pytest.mark.parametrize(
    "raw,needle",
    [
        ("ERROR: [youtube] x: Sign in to confirm you're not a bot", "cookies-from-browser"),
        ("ERROR: [youtube] x: Private video. Sign in", "private"),
        ("ERROR: [youtube] x: Video unavailable", "unavailable"),
    ],
)
def test_friendly_errors(raw, needle):
    assert needle in friendly_error(RuntimeError(raw))


def test_relative_download_dir_works(tmp_path, monkeypatch):
    # yt-dlp reports absolute paths; a relative --dir must still map back to the library.
    monkeypatch.chdir(tmp_path)

    class AbsEngine(FakeEngine):
        def download_entry(self, entry, dest, *a, **kw):
            return super().download_entry(entry, dest, *a, **kw).resolve()

    m = JobManager("./dl", engine=AbsEngine(n=1))
    job = wait_for(m.create("https://x.test/p"))
    assert job.items[0].status == "done", job.items[0].error
    assert job.items[0].file == "My Mix_ Vol_1/01 - Song 1.mp4"
