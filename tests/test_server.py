import zipfile
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from conftest import FakeEngine, wait_for
from playlistdrop.jobs import JobManager
from playlistdrop.server import create_app

KEY = "secret-key"


@pytest.fixture
def setup(tmp_path):
    m = JobManager(tmp_path, engine=FakeEngine())
    app = create_app(m, token=KEY)
    return m, TestClient(app), tmp_path


def authed(client):
    client.cookies.set("pd_key", KEY)
    return client


def test_locked_without_key(setup):
    _, c, _ = setup
    assert c.get("/").status_code == 401
    assert c.get("/api/jobs").status_code == 401
    assert c.get("/static/style.css").status_code == 200  # assets stay public


def test_key_in_qr_link_sets_cookie_and_redirects(setup):
    _, c, _ = setup
    r = c.get(f"/?k={KEY}", follow_redirects=False)
    assert r.status_code == 303 and r.cookies.get("pd_key") == KEY
    assert c.get("/").status_code == 200


def test_wrong_key_rejected(setup):
    _, c, _ = setup
    c.cookies.set("pd_key", "nope")
    assert c.get("/api/jobs").status_code == 401


def test_job_lifecycle_and_downloads(setup):
    m, c, root = setup
    authed(c)
    r = c.post("/api/jobs", json={"url": "https://youtube.com/playlist?list=PL1", "mode": "audio"})
    assert r.status_code == 200
    job = wait_for(m.get(r.json()["id"]))
    data = c.get(f"/api/jobs/{job.id}").json()
    assert data["counts"]["done"] == 3

    f = c.get("/dl/" + data["items"][0]["file"])
    assert f.status_code == 200 and f.content == b"x" * 100
    assert "attachment" in f.headers["content-disposition"]

    z = c.get("/zip/" + data["folder"])
    assert z.status_code == 200
    names = zipfile.ZipFile(BytesIO(z.content)).namelist()
    assert len(names) == 3 and names[0].startswith(data["folder"] + "/")
    assert not list(root.glob(".zip-*"))  # temp zip cleaned up

    lib = c.get("/api/library").json()
    assert lib[0]["name"] == data["folder"] and len(lib[0]["files"]) == 3


def test_bad_job_input(setup):
    _, c, _ = setup
    authed(c)
    assert c.post("/api/jobs", json={"url": "hello"}).status_code == 400
    assert c.get("/api/jobs/nope").status_code == 404


def test_path_traversal_blocked(setup, tmp_path_factory):
    _, c, root = setup
    authed(c)
    secret = root.parent / "secret.txt"
    secret.write_text("top secret")
    (root / ".playlistdrop-key").write_text("top secret")
    for path in ["/dl/.playlistdrop-key", "/dl/../secret.txt", "/dl/%2e%2e/secret.txt", "/dl/..%2Fsecret.txt", "/zip/%2e%2e", "/zip/.%2e"]:
        r = c.get(path)
        assert r.status_code == 404, path
        assert b"top secret" not in r.content


def test_status_reports_engine(setup):
    _, c, _ = setup
    authed(c)
    s = c.get("/api/status").json()
    assert s["ytdlp"] == "test" and s["ffmpeg"] is True
