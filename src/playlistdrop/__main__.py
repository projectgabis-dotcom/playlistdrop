"""Command line: `playlistdrop` (start the phone UI), `playlistdrop get URL`, `playlistdrop update`."""

from __future__ import annotations

import argparse
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

from . import __version__

DEFAULT_DIR = Path(os.environ.get("PLAYLISTDROP_DIR", Path.home() / "Downloads" / "PlaylistDrop"))
DEFAULT_PORT = int(os.environ.get("PLAYLISTDROP_PORT", "8765"))


def update_engine(quiet: bool = False) -> bool:
    """Upgrade yt-dlp in this Python environment. YouTube changes often; this keeps us working."""
    if getattr(sys, "frozen", False):
        return False
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "--disable-pip-version-check",
           "--progress-bar", "off", "yt-dlp[default,deno]"]
    if quiet:
        cmd.append("-q")
    try:
        return subprocess.run(cmd, timeout=180, check=False).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def load_key(root: Path) -> str:
    """Private key for the QR link. Saved so your phone stays connected across restarts."""
    if os.environ.get("PLAYLISTDROP_KEY"):
        return os.environ["PLAYLISTDROP_KEY"]
    path = root / ".playlistdrop-key"
    try:
        key = path.read_text().strip()
        if key:
            return key
    except OSError:
        pass
    key = secrets.token_urlsafe(12)
    try:
        root.mkdir(parents=True, exist_ok=True)
        path.write_text(key)
        path.chmod(0o600)
    except OSError:
        pass
    return key


def cmd_serve(args: argparse.Namespace) -> int:
    if not args.no_update:
        print("Checking for yt-dlp updates…", flush=True)
        if not update_engine(quiet=True):
            print("  (couldn't update yt-dlp — continuing with the installed version)")

    import uvicorn

    from . import engine
    from .jobs import JobManager
    from .netinfo import lan_ips, terminal_qr
    from .server import create_app

    root = Path(args.dir).expanduser()
    token = None if args.no_key else load_key(root)
    if args.public_host:
        host_ips = [args.public_host]
    else:
        host_ips = lan_ips() if args.host in ("0.0.0.0", "::") else [args.host]
    q = f"/?k={token}" if token else "/"
    share = [f"http://{ip}:{args.port}{q}" for ip in host_ips]

    env = engine.environment()
    js = f"  ·  JS: {env['js_runtime']}" if env["js_runtime"] else ""
    print(f"\n  PlaylistDrop {__version__}  ·  yt-dlp {env['ytdlp']}{js}")
    print(f"  Saving to: {root}")
    if not env["ffmpeg"]:
        print("  ! ffmpeg not found: videos limited to single-file MP4s, no MP3 conversion.")
    if not env["js_runtime"]:
        old = f" (found {', '.join(env['js_too_old'])} — too old)" if env["js_too_old"] else ""
        print(f"  ! No usable JavaScript runtime{old}. Run `playlistdrop update` to install Deno,")
        print("    or install Node 22+. Without it YouTube may block some videos/formats.")
    print(f"\n  On this computer:  http://127.0.0.1:{args.port}/")
    for url in share:
        print(f"  On your phone:     {url}")
    if share:
        print("\n  Scan with your iPhone camera (same Wi-Fi):\n")
        print(terminal_qr(share[0]))
    print("  Press Ctrl+C to stop.\n", flush=True)

    manager = JobManager(root, workers=args.workers, cookies_from_browser=args.cookies_from_browser)
    app = create_app(manager, token=token, share_urls=share)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    from .jobs import JobManager

    root = Path(args.dir).expanduser()
    manager = JobManager(root, workers=args.workers, cookies_from_browser=args.cookies_from_browser)
    mode = "mp3" if args.mp3 else "audio" if args.audio else "video"
    job = manager.create(args.url, mode, args.quality)
    shown: set[int] = set()
    announced = False
    print("Reading playlist…", flush=True)
    while job.status in ("listing", "running"):
        time.sleep(0.5)
        if job.items and not announced:
            announced = True
            print(f"{job.title} — {len(job.items)} items → {root / (job.folder or '')}")
        for it in job.items:
            if it.index not in shown and it.status in ("done", "skipped", "error", "cancelled"):
                shown.add(it.index)
                mark = "✓" if it.status in ("done", "skipped") else "✗"
                extra = f"  ({it.error})" if it.error else ""
                c = job.counts()
                print(f"  [{c['done'] + c['error']}/{c['total']}] {mark} {it.title}{extra}", flush=True)
    if job.status == "error":
        print(f"Error: {job.error}", file=sys.stderr)
        return 1
    c = job.counts()
    print(f"Done: {c['done']} downloaded, {c['error']} failed.")
    manager.shutdown()
    return 0 if c["error"] == 0 else 2


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="playlistdrop",
        description="Download whole YouTube playlists and grab them on your phone over Wi-Fi.",
    )
    p.add_argument("--version", action="version", version=f"playlistdrop {__version__}")
    sub = p.add_subparsers(dest="cmd")

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--dir", default=str(DEFAULT_DIR), help=f"where files go (default {DEFAULT_DIR})")
        sp.add_argument("--workers", type=int, default=3, help="parallel downloads (default 3)")
        sp.add_argument("--cookies-from-browser", metavar="BROWSER",
                        help="use your logged-in YouTube session from firefox/chrome/brave/edge/safari "
                             "(fixes 'confirm you're not a bot' and age-restricted videos)")

    s = sub.add_parser("serve", help="start the web app (default)")
    common(s)
    s.add_argument("--host", default="0.0.0.0", help="bind address (default 0.0.0.0 = reachable on Wi-Fi)")
    s.add_argument("--port", type=int, default=DEFAULT_PORT)
    s.add_argument("--no-update", action="store_true", help="don't auto-update yt-dlp on start")
    s.add_argument("--no-key", action="store_true", help="don't require the private key from the QR code")
    s.add_argument("--public-host", default=os.environ.get("PLAYLISTDROP_HOST_IP"), metavar="IP",
                   help="address to put in the QR code (e.g. your PC's IP when running in Docker)")
    s.set_defaults(func=cmd_serve)

    g = sub.add_parser("get", help="download a playlist from the terminal")
    common(g)
    g.add_argument("url")
    g.add_argument("--audio", action="store_true", help="audio only (M4A, plays natively on iPhone)")
    g.add_argument("--mp3", action="store_true", help="audio only as MP3")
    g.add_argument("--quality", type=int, default=720, help="max video height: 360/480/720/1080/1440/2160")
    g.set_defaults(func=cmd_get)

    u = sub.add_parser("update", help="update the yt-dlp engine")
    u.set_defaults(func=lambda a: 0 if update_engine() else 1)

    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0].startswith("-") and argv[0] not in ("-h", "--help", "--version"):
        argv = ["serve", *argv]
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
