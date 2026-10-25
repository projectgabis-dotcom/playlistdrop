---
version: 1
slug: "src-playlistdrop-static-index-html"
primary_target: "src/playlistdrop/static/index.html"
related_targets: []
---

Scope: the PlaylistDrop phone web app (src/playlistdrop/static/). Visitor mode: **Operate**.
Audience: iPhone owner at home, phone in one hand, PC elsewhere; moving whole YouTube playlists (mostly music) onto the phone.
Task: paste link → pick Video / M4A / MP3 → watch tracks land → save each file or the whole playlist as ZIP.
Constraints: keep the flow, auto light/dark, per-track thumbnails. No build step, vanilla HTML/CSS/JS, self-hosted assets (LAN, may be offline except thumbnails).
Owner feedback: previous build read as generic AI app (dark rounded cards, soft shadows, one blue button), no personality, templated wording, default form-on-top layout.

## Direction contract

THESIS: Each playlist is a divider card in a record crate and every finished track earns a day-glo price sticker you tap to take it home. Refuses the generic rounded-card dashboard with a blue Download button and a form stacked above a list.

OWN-WORLD: Flat, unmodulated divider-card colors (cobalt, tomato, mustard, green, pink) owning whole bands, one per playlist, rotating; fluorescent orange stickers; ink black and bin-liner off-white (dark: black bin, charcoal sleeves). Square corners, hairline row seams, no shadows, no gradients. Heavy condensed Archivo caps on divider tabs and the dock button only; system SF for everything else.

STORY: The visitor sees their playlists as labelled sections of a crate, reads at a glance which tracks are waiting, landing, done or gone, and taps orange stickers (or Save all) to pull files onto the iPhone.

FIRST VIEWPORT: Top bar: PLAYLIST[DROP] wordmark left, help right. Crate fills the screen: per playlist a colored tab with the name, a band with mode·count and actions (Save all in black on the band; Stop/Remove isolated at the far end), then white track rows: index, 16:9 thumb, title, duration rule (length = running time, fills with progress; dashed waiting, struck failed), meta line, sticker slot. Empty crate teaches the flow. Bottom dock (black, safe-area aware): link field, Video/M4A/MP3 segmented, orange GET IT button.

FORM: Crate Digger, #4 on my ordered grounded list (record-shop crate dividers & price stickers). seed:706a74f11998a946. Raises: flat fields (zoo map), isolated destructive actions (dev console), duration rule (labanotation), state by form (emission rail), fixed row furniture (goods catalog).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
