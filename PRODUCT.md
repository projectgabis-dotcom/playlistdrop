# PlaylistDrop — product context

_Inferred from the owner's brief (they asked Claude to proceed without an interview); assumptions marked._

## What it is
A self-hosted tool that downloads an entire YouTube playlist in one go on your computer and hands the
files to your phone over Wi-Fi. Engine: yt-dlp, kept up to date automatically.

## Who and where
- The owner: switched from Android (Snaptube) to iPhone; no native playlist downloader exists on iOS.
- Scene (assumption): at home, phone in hand, PC running in another room; Safari on iPhone is the
  main client, desktop browser secondary.

## Job
Paste a playlist link → pick Video / Audio → watch it fill → save files (or one ZIP) to the iPhone.

## Success
A 50-item playlist lands on the phone with zero terminal work after first start; failed items are
named with a reason and can be retried; re-running a playlist skips what's already downloaded.

## Anti-goals
- A hosted public website (YouTube blocks datacenter IPs; legal exposure).
- Ads, accounts, telemetry.
- Anything that feels like a sketchy downloader site (popups, fake buttons, red YouTube cosplay).

## Surface modes
- Web app (`src/playlistdrop/static/`): **Operate**.
- README / GitHub Pages landing: **Read** with a light Persuade opening.
