# PlaylistDrop

**Download a whole YouTube playlist in one go, then save it to your iPhone (or any phone) over Wi-Fi.**

There's no Snaptube for iPhone, and doing it by hand means grabbing every video on a computer and then moving the files over. PlaylistDrop runs on your computer and puts a page on your phone instead. You paste a playlist link, pick **Video** or **Audio**, and tap **Save all**.

- **Whole playlists**: every video downloads in parallel, and the page shows live progress for each one.
- **iPhone-ready files**: MP4 video (H.264 + AAC) or M4A/MP3 audio with the title and cover art embedded. These play in Files, Photos and Music players without any conversion.
- **Phone access by QR code**: scan it with the iPhone camera and the app opens in Safari. A private key in the QR link means only you can use it.
- **Save one file or everything as a ZIP**: the Files app on iPhone unpacks a ZIP with one tap.
- **Resume-friendly**: run the same playlist again and it skips what you already have, so only new videos download.
- **Explains failures**: when a video fails (private, removed, region-blocked), the page says why. The rest keep going, and **Retry failed** tries the failed ones again.
- **Stays working**: it updates its download engine ([yt-dlp](https://github.com/yt-dlp/yt-dlp)) on every start, because YouTube changes things every few weeks.

> **Why not just use yt-dlp?** PlaylistDrop *is* yt-dlp underneath. Most people who say "yt-dlp doesn't work" have an outdated copy, are missing YouTube's JavaScript challenge solver (`yt-dlp-ejs` plus a JS runtime), or are missing ffmpeg. PlaylistDrop installs and configures all of that, then gives you a page you can tap on your phone.

---

## Quick start

You need **Python 3.10+** and **ffmpeg**. Install the Node.js or Deno JavaScript runtime too: without one, YouTube hides some formats.

| OS | Install the prerequisites |
|---|---|
| macOS | `brew install python ffmpeg deno pipx` |
| Ubuntu / Debian | `sudo apt install python3 pipx ffmpeg nodejs` |
| Windows | `winget install Python.Python.3.12 Gyan.FFmpeg DenoLand.Deno` then `py -m pip install --user pipx` |

Then install and run PlaylistDrop:

```bash
pipx install git+https://github.com/projectgabis-dotcom/playlistdrop
playlistdrop
```

You'll see something like:

```
  PlaylistDrop 0.1.0  ·  yt-dlp 2026.10.21
  Saving to: /home/you/Downloads/PlaylistDrop

  On this computer:  http://127.0.0.1:8765/
  On your phone:     http://192.168.1.20:8765/?k=…

  Scan with your iPhone camera (same Wi-Fi):
  ▄▄▄▄▄▄▄ ▄▄  ▄ ▄▄▄▄▄▄▄
  …
```

Point your iPhone camera at the QR code and tap the link. That's it.

### Getting files onto the iPhone

1. When an item finishes, tap **Save**, or tap **Save all** to get one ZIP of the whole playlist.
2. Safari asks to download it. Files go to **Files › Downloads**.
3. **ZIP:** tap it once in Files and it unpacks into a folder.
4. **Video to Photos:** open the video in Files, then tap **Share › Save Video**.
5. **Music:** audio plays straight from Files. VLC or *Documents* can play a whole folder as a playlist.

Tip: in Safari, tap **Share › Add to Home Screen** to open PlaylistDrop like an app.

---

## Terminal mode

You don't need a phone for this: it downloads straight to your computer.

```bash
playlistdrop get "https://www.youtube.com/playlist?list=PL…"              # MP4, up to 720p
playlistdrop get "https://www.youtube.com/playlist?list=PL…" --quality 1080
playlistdrop get "https://www.youtube.com/playlist?list=PL…" --audio      # M4A
playlistdrop get "https://www.youtube.com/playlist?list=PL…" --mp3
playlistdrop update                                                       # update yt-dlp now
```

## Options

| Option | What it does |
|---|---|
| `--dir PATH` | Where files are saved (default `~/Downloads/PlaylistDrop`, or the `PLAYLISTDROP_DIR` environment variable) |
| `--port 8765` | Web port (or `PLAYLISTDROP_PORT`) |
| `--workers 3` | How many videos download at the same time |
| `--cookies-from-browser firefox` | Uses your logged-in YouTube session from firefox/chrome/brave/edge/safari. This fixes "Sign in to confirm you're not a bot", age-restricted videos, and your private playlists |
| `--no-update` | Skip the yt-dlp update on start |
| `--no-key` | Don't require the private key (only do this on a network you trust) |
| `--public-host IP` | The address to put in the QR code (or `PLAYLISTDROP_HOST_IP`) |

## Docker (home server, NAS, Raspberry Pi)

```bash
docker run -d --name playlistdrop -p 8765:8765 \
  -v ~/Downloads/PlaylistDrop:/downloads \
  -e PLAYLISTDROP_HOST_IP=192.168.1.20 \
  ghcr.io/projectgabis-dotcom/playlistdrop:latest
docker logs playlistdrop    # shows the QR code
```

The image includes ffmpeg and Deno, and it's built for `amd64` and `arm64`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Confirm you're not a bot" | Restart with `--cookies-from-browser firefox` (or chrome), with that browser logged in to YouTube |
| Phone can't open the link | Phone and computer must be on the same Wi-Fi. Allow port 8765 through the firewall: on Windows, accept the prompt; on Linux, `sudo ufw allow 8765` |
| Only low-quality formats | Install Deno or Node.js, then restart |
| Merging or MP3 fails | Install ffmpeg |
| Something that worked last week broke | `playlistdrop update`, since YouTube changed something and yt-dlp has usually fixed it already |

## Why there's no public website

A hosted "paste a link" site sounds easier, but it doesn't work in practice. YouTube blocks downloads from cloud servers (every free host is a cloud server). Free hosts also cut off long downloads, and a public downloader attracts takedowns. Running it on your own computer is free, faster, and uses your own home connection.

## Development

```bash
git clone https://github.com/projectgabis-dotcom/playlistdrop && cd playlistdrop
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest -m "not network"     # fast tests, no internet
pytest -m network           # real YouTube round-trip
python -m playlistdrop --no-update
```

The code is small and has no build step:

```
src/playlistdrop/
  engine.py    yt-dlp options (iPhone-friendly formats, JS runtime, ffmpeg detection)
  jobs.py      background downloads: one job per playlist, parallel workers, retry/cancel
  server.py    FastAPI: JSON API, file + ZIP downloads, QR-key access control
  static/      the phone UI (plain HTML/CSS/JS)
```

## Legal

PlaylistDrop is for downloading content you have the right to download: your own uploads, Creative Commons or public-domain videos, or anything the copyright holder allows. Respect YouTube's Terms of Service and your local laws. The authors aren't responsible for misuse.

## Credits

All the hard work of talking to YouTube is done by [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [ffmpeg](https://ffmpeg.org). PlaylistDrop is MIT-licensed.
