---
name: PlaylistDrop
description: A record crate on your phone. Each playlist is a divider card, each finished track a day-glo price sticker you tap to take home.
colors:
  sticker: "#ff6a13"
  cobalt: "#2b4bdb"
  tomato: "#e5482f"
  mustard: "#e8b21c"
  green: "#17784e"
  pink: "#e86fa4"
  stock-ink: "#141414"
  ground: "#f1f1ec"
  sleeve: "#ffffff"
  seam: "#e2e2dc"
  ink: "#141414"
  ink-2: "#5c5c57"
  ink-3: "#6b6b66"
  inverse: "#141414"
  inverse-ink: "#f6f6f2"
  fail: "#c8321e"
  ground-dark: "#0f0f0f"
  sleeve-dark: "#1a1a19"
  seam-dark: "#2b2b29"
  ink-dark: "#f1f1ec"
  ink-2-dark: "#b4b4ad"
  ink-3-dark: "#85857f"
  inverse-dark: "#050505"
  plain-stock-dark: "#262624"
  fail-dark: "#ff7a63"
typography:
  display:
    fontFamily: "Archivo, Arial Narrow, sans-serif"
    fontSize: "24px"
    fontWeight: 900
    lineHeight: 1
    letterSpacing: "0.01em"
    fontVariation: "\"wdth\" 62"
  headline:
    fontFamily: "Archivo, Arial Narrow, sans-serif"
    fontSize: "21px"
    fontWeight: 900
    lineHeight: 1.05
    letterSpacing: "0.015em"
    fontVariation: "\"wdth\" 62"
  title:
    fontFamily: "Archivo, Arial Narrow, sans-serif"
    fontSize: "20px"
    fontWeight: 900
    lineHeight: 1
    letterSpacing: "0.02em"
    fontVariation: "\"wdth\" 70"
  numeral:
    fontFamily: "Archivo, Arial Narrow, sans-serif"
    fontSize: "15px"
    fontWeight: 900
    lineHeight: 0.95
    fontVariation: "\"wdth\" 70"
    fontFeature: "\"tnum\""
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Text, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.4
  input:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Text, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.2
  body-strong:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Text, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "14.5px"
    fontWeight: 600
    lineHeight: 1.25
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Text, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "13.5px"
    fontWeight: 700
    lineHeight: 1
    fontFeature: "\"tnum\""
  meta:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Text, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "12.5px"
    fontWeight: 400
    lineHeight: 1.4
    fontFeature: "\"tnum\""
rounded:
  none: "0px"
  sticker: "50%"
spacing:
  xs: "6px"
  sm: "8px"
  md: "10px"
  gutter: "12px"
  lg: "14px"
  xl: "16px"
  crate-gap: "26px"
components:
  button-get:
    backgroundColor: "{colors.sticker}"
    textColor: "{colors.stock-ink}"
    typography: "{typography.title}"
    rounded: "{rounded.none}"
    padding: "0 18px"
    height: "48px"
  button-act-solid:
    backgroundColor: "{colors.stock-ink}"
    textColor: "{colors.sleeve}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "0 13px"
    height: "36px"
  button-act-line:
    backgroundColor: "transparent"
    textColor: "{colors.stock-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "0 13px"
    height: "36px"
  button-act-save:
    backgroundColor: "{colors.sticker}"
    textColor: "{colors.stock-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "0 13px"
    height: "36px"
  sticker:
    backgroundColor: "{colors.sticker}"
    textColor: "{colors.stock-ink}"
    typography: "{typography.numeral}"
    rounded: "{rounded.sticker}"
    size: "52px"
  input-link:
    backgroundColor: "{colors.sleeve}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "0 12px"
    height: "48px"
  segment:
    backgroundColor: "transparent"
    textColor: "{colors.inverse-ink}"
    rounded: "{rounded.none}"
    height: "40px"
  segment-selected:
    backgroundColor: "{colors.inverse-ink}"
    textColor: "{colors.inverse}"
    rounded: "{rounded.none}"
    height: "40px"
  divider-tab:
    backgroundColor: "{colors.cobalt}"
    textColor: "{colors.sleeve}"
    typography: "{typography.headline}"
    rounded: "{rounded.none}"
    padding: "9px 14px 6px"
  divider-band:
    backgroundColor: "{colors.cobalt}"
    textColor: "{colors.sleeve}"
    rounded: "{rounded.none}"
    padding: "8px 10px 8px 14px"
  track-row:
    backgroundColor: "{colors.sleeve}"
    textColor: "{colors.ink}"
    typography: "{typography.body-strong}"
    rounded: "{rounded.none}"
    padding: "10px 10px 10px 8px"
  dock:
    backgroundColor: "{colors.inverse}"
    textColor: "{colors.inverse-ink}"
    rounded: "{rounded.none}"
    padding: "10px 12px"
---

# Design System: PlaylistDrop

## Overview

**Creative North Star: "The Crate Digger"**

PlaylistDrop is a record-shop crate held in one hand. Every playlist is a divider card: a flat, unmodulated band of card stock (cobalt, mustard, tomato, green, pink) with a condensed all-caps tab naming it. Behind each divider sit the tracks as plain white sleeves separated by hairline seams. When a track has landed on the computer, it earns a fluorescent orange price sticker, slightly askew, and tapping that sticker is how the file comes home to the iPhone. The bin is ink black and bin-liner off-white in light mode, a black bin with charcoal sleeves in dark mode; the divider stock and the stickers never change with the theme, because card stock and day-glo paper do not.

The surface is dense and operational, built for a thumb: everything you act on is in the black dock at the bottom of the screen, everything you read fills the crate above it. Depth comes from flat fields laid next to each other, never from shadows or gradients. Corners are square throughout; the only circle in the world is the sticker. Two typographic voices split the work: heavy condensed Archivo caps for the things that behave like printed labels (wordmark, divider tabs, the GET IT button, numerals on stickers and rows), and the phone's own system face for everything you read.

The world deliberately refuses the generic rounded-card dashboard with soft shadows and a single blue Download button, and it refuses the sketchy-downloader look (popups, fake buttons, YouTube-red chrome).

**Key Characteristics:**
- Flat divider-card colour fields own whole bands, one per playlist, never two the same colour in a row.
- Day-glo orange is the "take it home" colour: stickers, the GET IT button, file Save buttons, focus.
- Square corners and 1px hairline seams; zero shadows, zero gradients.
- Condensed heavy Archivo caps for labels, system UI for reading.
- A fixed black dock at the bottom carries every input; the crate scrolls above it.
- Track state is shown by form (a duration rule that is dashed, filling, solid or struck), not by colour badges.

## Colors

A neutral bin of off-white and ink, five flat card-stock colours that each own a whole playlist, and one fluorescent orange that means "save".

### Primary
- **Day-Glo Sticker Orange** (`sticker`): The price-sticker colour and the only action colour. Used for the track save sticker, the GET IT dock button, the per-file Save buttons in the library, the DROP highlight in the wordmark, the text caret, text selection and every focus ring. Always carries ink-black text, never white.

### Secondary
The divider card stock. Theme-independent: identical in light and dark mode. Each fills a playlist's tab and band as one flat field.
- **Press Cobalt** (`cobalt`): Divider stock; white text.
- **Mustard Board** (`mustard`): Divider stock; ink text.
- **Tomato Card** (`tomato`): Divider stock; ink text. A red-orange card colour, not a YouTube red.
- **Bin Green** (`green`): Divider stock; white text.
- **Sleeve Pink** (`pink`): Divider stock; ink text.
- **Stock Ink** (`stock-ink`): The near-black used for text on light stocks, for the solid Save-all button on every band, and for text on orange.

### Neutral
- **Bin-Liner Off-White** (`ground`; dark `ground-dark`): Page background, the floor of the crate.
- **Sleeve White** (`sleeve`; dark `sleeve-dark`, a charcoal): Track rows, library shelves, the link input. The surface that holds readable content.
- **Hairline Seam** (`seam`; dark `seam-dark`): 1px row separators, empty duration rules, thumbnail and skeleton placeholders.
- **Crate Ink** (`ink`; dark `ink-dark`): Primary text and the filled duration rule.
- **Faded Ink** (`ink-2`; dark `ink-2-dark`): Meta lines, counts, file sizes, the library heading, waiting-track titles.
- **Pencil Grey** (`ink-3`; dark `ink-3-dark`): Row index numerals, placeholders, the dashed waiting rule, the engine footer, struck-through failed titles. Raised to clear 4.5:1 on both ground and sleeve.
- **Dock Black** (`inverse`; dark `inverse-dark`): The dock and the help panel. Stays black in both themes (`#050505` in dark so it still separates from the `#0f0f0f` ground). Its text is `inverse-ink`.
- **Charcoal Stock** (`plain-stock-dark`): The neutral divider stock in dark mode (empty-crate card); in light mode the neutral divider uses Dock Black.
- **Failure Red** (`fail`; dark `fail-dark`): Failed-track meta text, the failed duration rule, playlist-level error text, and the dock's form-error strip.

### Named Rules
**The Sticker Is The Save Rule.** Day-glo orange marks only things that move a file onto the phone (stickers, GET IT, file Save) plus focus, caret and selection. It is never decoration, never a background band, never a divider colour.

**The Card Stock Rule.** Divider colours are printed card, not theme: the same five hexes in light and dark mode, always as a flat full-width field shared by tab and band, never tinted, faded, gradiented or used as a thin accent line except on the library shelf's 4px top edge.

**The Neighbour Rule.** A playlist's colour is derived from its name so it stays the same across visits, but two adjacent dividers never share a colour; the lower one steps to the next stock.

**The Black Dock Rule.** The dock is black in both themes. It never takes the page ground colour.

## Typography

**Display Font:** Archivo (variable, self-hosted `archivo-latin.woff2`, weights 700–900, width 62–100%; SIL Open Font License), falling back to Arial Narrow
**Body Font:** The platform system face (-apple-system / SF Pro Text on iPhone), with Segoe UI, Roboto, Helvetica Neue and Arial fallbacks

**Character:** Archivo set very heavy and very condensed reads like the stamped and screen-printed labels on shop dividers; the system face keeps everything you actually read native to the phone.

### Hierarchy
- **Display** (Archivo 900, 24px, width 62%, uppercase, line-height 1): The PLAYLIST[DROP] wordmark only. "DROP" sits on a sticker-orange block.
- **Headline** (Archivo 900, 21px rising to 24px at ≥640px, width 62%, uppercase, line-height 1.05): Divider tabs (playlist names). Same voice at 20px for the help panel heading and 17px in Faded Ink for the library heading.
- **Title** (Archivo 900, 20px, width 70%, uppercase, letter-spacing 0.02em): The GET IT dock button.
- **Numeral** (Archivo 800–900, 13–15px, width 70–80%, tabular): Sticker sizes (15px), live percentages (15px), row index numbers (13px, Pencil Grey).
- **Body** (system 400, 15px, line-height 1.4): Default text; help steps. The link input runs at 16.5px so iOS never zooms on focus.
- **Body Strong** (system 600, 14.5px, line-height 1.25, clamped to two lines): Track titles.
- **Label** (system 600–700, 13.5px, tabular): Band summaries (mode · count) and band action buttons; segmented options at 14px 700.
- **Meta** (system 400, 12.5px, tabular): Track meta lines, file sizes, counts; 12px for the engine footer.

### Named Rules
**The Two Voices Rule.** Archivo is only ever heavy, condensed and (except numerals) uppercase, and only on things that behave like printed labels: wordmark, divider tabs, panel headings, the GET IT button, numerals. Sentences, titles, meta and form text are always the system face.

**The Tabular Rule.** Every number that changes (counts, sizes, speeds, durations, percentages, indexes) uses tabular figures so columns hold still while a playlist fills.

## Layout

A single centred column, max 720px wide (dock contents 696px), with a 12px side gutter in the crate and 16px in the top bar. Order from top: a slim top bar (wordmark left, 44px help button right), the crate (dividers stacked 26px apart, newest first), the "Already on this computer" library shelves, a centred engine footer. A fixed dock is pinned to the bottom edge; the crate's bottom padding tracks the dock's real height (measured live) plus the safe-area inset and 28px, so nothing ever hides under it. All edges respect `env(safe-area-inset-*)`.

Track rows are a fixed four-column grid: index (22px), 16:9 thumbnail (64px), body (flexible), sticker slot (56px), with 10px gaps and a 66px minimum height. At ≥640px the columns widen to 26 / 80 / flexible / 60px and tabs grow to 24px. The dock is two rows: link field + GET IT, then a three-way Video / M4A / MP3 segment + a quality select.

Spacing is a tight, near-continuous rhythm of 6–16px inside components, with 26px between dividers and 30px before the library. Every tap target is at least 36px tall inside bands and 44–52px elsewhere.

### Named Rules
**The Thumb Dock Rule.** Inputs live in the bottom dock, content lives in the crate. Never put the link form above the list.

## Elevation & Depth

This world is completely flat. There are no shadows and no gradients anywhere. Depth is tonal and positional: the off-white ground sits behind white sleeves, coloured card stock sits above the sleeves it labels, and the black dock sits over everything by being black and fixed. Separation inside a surface is a 1px seam line, never a gap with a shadow.

### Named Rules
**The Flat Stock Rule.** No `box-shadow`, no `text-shadow`, no gradient, no blur, in any state. If something needs to read as on top, it gets a different flat field (black, card stock or orange).

## Shapes

Every rectangle is square-cornered (0 radius): tabs, bands, rows, buttons, the input, segments, the select, panels, thumbnails. The tab is an inline block narrower than the band beneath it, which gives each divider its index-card silhouette. Borders are hairlines (1px seams) or 1.5px outline strokes on line buttons and segments, always in the current text colour. The one exception is the sticker: a 52px circle, rotated by a slightly different angle per track (between -9° and -3°) so a column of stickers looks hand-applied. Icons are stroked 24-unit line icons at 22px, 1.9 stroke, round caps.

### Named Rules
**The One Circle Rule.** The sticker is the only round thing in the world. Nothing else gets a radius.

## Components

### Buttons
Blunt, square and printed; pressing any of them scales it to 0.96.
- **Shape:** Square corners (0px).
- **GET IT (dock primary):** Day-Glo Sticker Orange field, ink text in the Title voice, 48px tall, 18px side padding. Disabled while submitting at 60% opacity with a progress cursor.
- **Save all (band solid):** Stock Ink field with white Label text on every band colour and in both themes, 36px tall, 13px padding; hover deepens to pure black. Reads "Save N so far · size" while running, "Save all · size" when done.
- **Line actions (Retry failed, Stop, Remove):** Transparent with a 1.5px outline in the band's text colour; on hover the field inverts (band text colour fill, band stock text).
- **File Save / ZIP (library):** Save is orange with ink text; ZIP uses the dock black with inverse ink.
- **Icon button (help):** 44px square, no background, stroked icon in Crate Ink.
- **Focus:** A 3px Day-Glo Sticker Orange outline at 2px offset, everywhere.

### Divider (signature)
The playlist container. A tab (Headline voice, 9px 14px 6px padding) sits on top of a band (min 48px, 8px 10px 8px 14px padding, wraps on narrow widths) in the same flat stock colour. The band carries the summary (mode · quality · "N of M saved" · failures) then the actions: Save all first, Retry next, and Stop / Remove pushed to the far end. Below it, the track rows on sleeve white. A playlist-level error appears as a Failure Red line on sleeve between band and rows. The empty crate reuses the divider in the neutral stock to teach the three-step flow.

### Track Row
Fixed furniture: index numeral, 16:9 thumbnail (seam-coloured while loading, hidden if it fails), title (two lines max), duration rule, meta line, and a slot on the right. Rows are separated by 1px seams.
- **Duration rule:** A 3px bar whose length is the track's running time relative to the longest track in the playlist (minimum 18%). States by form: waiting and stopped are a 3px dashed Pencil Grey line; downloading fills in Crate Ink from the left; processing, done and skipped are solid ink; failed is a 2px Failure Red line with the title struck through in Pencil Grey and the reason in the meta line.
- **Slot:** empty while waiting, a live Archivo percentage while downloading or processing, the sticker once the file exists.
- **Skeleton:** while YouTube returns the track list, three ghost rows with seam-coloured bars stand in.

### Sticker (signature)
The save button for one track: a 52px Day-Glo orange circle showing the file size (Numeral voice) over its unit, tilted per track. Hover scales to 1.06, press to 0.94. When a track lands while you watch, the sticker slaps on: from -24° at 40% scale, overshooting to 1.06, settling at its tilt in 320ms.

### Inputs / Fields
- **Link field:** Sleeve-white, square, 48px, 16.5px text, a 1px hairline outline, orange caret, Pencil Grey placeholder. Focus swaps to the 3px orange ring.
- **Format segment:** Three equal square cells, 40px, 1.5px inverse-ink outline on the dock; the selected cell fills inverse-ink with dock-black text.
- **Quality select:** Same outline treatment, 82px wide, stroked chevron icon; drops to 35% opacity and disables when an audio format is chosen.
- **Form error:** A full-width Failure Red strip with white text inside the dock, above the safe area.

### Navigation
There is no navigation beyond the top bar: the wordmark (links home) and the help toggle, which opens a Dock Black panel with numbered instructions inline above the crate.

### Library Shelf
Earlier sessions as collapsible shelves on sleeve white, each with a 4px top edge in its playlist's stock colour, a bold name, a file count and a ZIP button. Expanded, files list with name, size and an orange Save.

## Do's and Don'ts

### Do:
- **Do** give every playlist one flat card-stock field shared by its tab and band, and keep adjacent dividers different colours.
- **Do** reserve Day-Glo Sticker Orange (#ff6a13) for saving files and for focus; put ink text on it, never white.
- **Do** keep every corner square; the 52px sticker is the only circle.
- **Do** set labels in Archivo 900 condensed caps and everything readable in the system face, with tabular figures for all changing numbers.
- **Do** show track state by the duration rule's form (dashed, filling, solid, struck) and keep the row's furniture in fixed positions.
- **Do** keep destructive actions (Stop, Remove) as line buttons pushed to the far end of the band, away from Save all.
- **Do** keep the dock black in both themes and keep every input in it.
- **Do** honour reduced motion: transitions and animations collapse to 1ms, and motion never hides content.

### Don't:
- **Don't** add shadows, gradients, blur or glass to any surface.
- **Don't** round cards, buttons or inputs, and don't use pill buttons.
- **Don't** introduce a blue primary button or a rounded-card dashboard layout.
- **Don't** use YouTube red, play-button motifs or anything that resembles a downloader ad site (popups, fake download buttons).
- **Don't** tint or theme the card-stock colours for dark mode; they are printed card.
- **Don't** use orange as decoration, a divider colour or a background band.
- **Don't** put the link form at the top of the page above the list.
