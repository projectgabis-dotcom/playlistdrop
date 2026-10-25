"use strict";

const $ = (sel, el = document) => el.querySelector(sel);
const jobsEl = $("#jobs");
const views = new Map(); // job id -> { el, items: Map(index -> row), folder, color }
let pollTimer = null;
let firstPoll = true;

// ------------------------------------------------------------------ api

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    ...opts,
  });
  let data = null;
  try { data = await res.json(); } catch { /* empty body */ }
  if (!res.ok) throw new Error((data && data.detail) || `Something went wrong (${res.status}).`);
  return data;
}

// ------------------------------------------------------------------ formatting

function sizeParts(n) {
  if (n == null) return null;
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return [n.toFixed(n < 10 && i > 1 ? 1 : 0), units[i]];
}
const fmtBytes = (n) => (n == null ? "" : sizeParts(n).join(" "));
function fmtEta(s) {
  if (s == null) return "";
  return s < 60 ? `${Math.max(1, Math.round(s))}s left` : `${Math.round(s / 60)} min left`;
}
function fmtDur(s) {
  if (!s) return "";
  s = Math.round(s);
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = String(s % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${r}` : `${m}:${r}`;
}
const MODE = { video: "Video", audio: "Music · M4A", mp3: "Music · MP3" };
const dlHref = (rel) => "/dl/" + rel.split("/").map(encodeURIComponent).join("/");
const zipHref = (folder) => "/zip/" + encodeURIComponent(folder);

// Each playlist keeps one divider color, picked from its name so it never changes between visits.
function colorFor(key) {
  let h = 0;
  for (const ch of key || "") h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return "c" + ((h % 5) + 1);
}

// ------------------------------------------------------------------ composer

const form = $("#composer");
const urlInput = $("#url");
const goBtn = $("#go");
const formError = $("#formError");
const qualityWrap = $("#qualityWrap");

function syncQuality() {
  const off = form.elements.mode.value !== "video";
  qualityWrap.classList.toggle("off", off);
  $("#quality").disabled = off;
}
form.addEventListener("change", syncQuality);

try {
  const saved = JSON.parse(localStorage.getItem("pd-prefs") || "{}");
  if (saved.mode) form.elements.mode.value = saved.mode;
  if (saved.quality) $("#quality").value = String(saved.quality);
} catch { /* storage unavailable */ }
syncQuality();

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  formError.hidden = true;
  const url = urlInput.value.trim();
  const mode = form.elements.mode.value;
  const quality = Number($("#quality").value);
  if (!/^https?:\/\//i.test(url)) {
    showFormError("That doesn't look like a link. Copy it from YouTube's Share button and paste it here.");
    return;
  }
  goBtn.disabled = true;
  try {
    const job = await api("/api/jobs", { method: "POST", body: JSON.stringify({ url, mode, quality }) });
    try { localStorage.setItem("pd-prefs", JSON.stringify({ mode, quality })); } catch { /* ignore */ }
    urlInput.value = "";
    urlInput.blur();
    renderJob(job, true);
    window.scrollTo({ top: 0, behavior: "smooth" });
    schedulePoll(400);
  } catch (err) {
    showFormError(err.message);
  } finally {
    goBtn.disabled = false;
  }
});

function showFormError(msg) {
  formError.textContent = msg;
  formError.hidden = false;
}

const shared = new URLSearchParams(location.search).get("url");
if (shared) urlInput.value = shared;

// Keep the crate's bottom padding equal to the dock's real height (it grows with errors).
const dockObserver = new ResizeObserver(([entry]) => {
  document.documentElement.style.setProperty("--dock-h", Math.ceil(entry.borderBoxSize[0].blockSize) + "px");
});
dockObserver.observe(form);

// ------------------------------------------------------------------ help

const helpBtn = $("#helpBtn");
helpBtn.addEventListener("click", () => {
  const help = $("#help");
  help.hidden = !help.hidden;
  helpBtn.setAttribute("aria-expanded", String(!help.hidden));
});

// ------------------------------------------------------------------ crate rendering

function renderJob(job, prepend = false) {
  let view = views.get(job.id);
  if (!view) {
    const el = $("#jobTpl").content.firstElementChild.cloneNode(true);
    view = { el, items: new Map(), folder: null, color: null };
    views.set(job.id, view);
    $(".stop", el).addEventListener("click", () => act(job.id, "cancel"));
    $(".retry", el).addEventListener("click", () => act(job.id, "retry"));
    $(".dismiss", el).addEventListener("click", async () => {
      try { await api(`/api/jobs/${job.id}`, { method: "DELETE" }); } catch { /* already gone */ }
      el.remove();
      views.delete(job.id);
      libSig = "";
      syncEmpty();
      loadLibrary();
    });
    prepend ? jobsEl.prepend(el) : jobsEl.append(el);
    // A playlist added while you watch slides into the crate; content is never hidden by motion.
    if (!firstPoll && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
      el.animate([{ transform: "translateY(12px)" }, { transform: "none" }], {
        duration: 260, easing: "cubic-bezier(0.2, 0.9, 0.3, 1)",
      });
    }
  }
  const el = view.el;
  const c = job.counts;
  const listing = job.status === "listing";
  const active = listing || job.status === "running";
  view.folder = job.folder;
  if (!view.color && job.title) view.color = colorFor(job.title);

  el.className = `divider ${view.color || "c0"} ${job.status}`;
  el.dataset.color = view.color || "c0";
  el.setAttribute("aria-busy", String(active));
  $(".tab", el).textContent = job.title || (listing ? "Reading playlist…" : "Couldn't open that link");

  const bits = [MODE[job.mode] + (job.mode === "video" ? ` · ${job.quality}p` : "")];
  if (listing) bits.push("asking YouTube for the track list");
  if (c.total) bits.push(`${c.done} of ${c.total} saved`);
  if (c.error) bits.push(`${c.error} failed`);
  if (job.status === "cancelled") bits.push("stopped");
  $(".sum", el).textContent = bits.join(" · ");

  const err = $(".job-error", el);
  err.hidden = !job.error;
  err.textContent = job.error || "";

  const saveAll = $(".save-all", el);
  saveAll.hidden = !(job.folder && c.done > 0);
  if (job.folder) {
    saveAll.href = zipHref(job.folder);
    const total = job.items.reduce((s, it) => s + (it.size || 0), 0);
    saveAll.textContent = (active ? `Save ${c.done} so far` : "Save all") + (total ? ` · ${fmtBytes(total)}` : "");
  }
  $(".stop", el).hidden = !active;
  $(".retry", el).hidden = active || !(c.error || job.items.some((i) => i.status === "cancelled"));
  $(".dismiss", el).hidden = active;

  const list = $(".rows", el);
  if (listing) {
    if (!list.childElementCount) for (let i = 0; i < 3; i++) list.append(ghostRow(i));
  } else {
    list.querySelectorAll(".ghost").forEach((g) => g.remove());
  }
  const longest = Math.max(1, ...job.items.map((i) => i.duration || 0));
  for (const it of job.items) {
    let row = view.items.get(it.index);
    if (!row) {
      row = newRow(it, longest);
      list.append(row);
      view.items.set(it.index, row);
    }
    updateRow(row, it);
  }
  syncEmpty();
}

function ghostRow(i) {
  const row = $("#itemTpl").content.firstElementChild.cloneNode(true);
  row.classList.add("ghost");
  $(".n", row).textContent = i + 1;
  $(".t", row).textContent = "…";
  $(".rule", row).style.setProperty("--len", `${[78, 56, 90][i]}%`);
  return row;
}

function newRow(it, longest) {
  const row = $("#itemTpl").content.firstElementChild.cloneNode(true);
  $(".n", row).textContent = it.index;
  $(".t", row).textContent = it.title;
  const len = it.duration ? Math.max(18, Math.round((it.duration / longest) * 100)) : 100;
  $(".rule", row).style.setProperty("--len", `${len}%`);
  const thumb = it.id ? `https://i.ytimg.com/vi/${encodeURIComponent(it.id)}/mqdefault.jpg` : it.thumbnail;
  if (thumb) {
    const img = Object.assign(document.createElement("img"), {
      className: "thumb", alt: "", loading: "lazy", decoding: "async", referrerPolicy: "no-referrer",
    });
    img.addEventListener("error", () => { img.style.visibility = "hidden"; }, { once: true });
    img.src = thumb;
    $(".thumb", row).replaceWith(img);
  }
  return row;
}

function updateRow(row, it) {
  const prev = row.dataset.status;
  row.dataset.status = it.status;
  row.className = `row ${it.status}`;
  const fill = $(".rule i", row).style;
  if (it.status === "downloading") fill.setProperty("--p", String(it.progress || 0));
  else fill.removeProperty("--p"); // CSS owns the other states (solid when done)

  let meta = "";
  switch (it.status) {
    case "queued": meta = ["Waiting", fmtDur(it.duration)].filter(Boolean).join(" · "); break;
    case "downloading":
      meta = [it.speed ? fmtBytes(it.speed) + "/s" : "Starting", fmtEta(it.eta)].filter(Boolean).join(" · ");
      break;
    case "processing": meta = "Finishing up"; break;
    case "done": case "skipped":
      meta = [fmtDur(it.duration), it.status === "skipped" ? "already here" : ""].filter(Boolean).join(" · ");
      break;
    case "error": meta = it.error || "Couldn't download this one"; break;
    case "cancelled": meta = "Stopped"; break;
  }
  $(".meta", row).textContent = meta;

  const slot = $(".slot", row);
  if (it.file && (it.status === "done" || it.status === "skipped")) {
    if (prev !== it.status || !slot.firstElementChild || slot.firstElementChild.tagName !== "A") {
      const [num, unit] = sizeParts(it.size) || ["", "Save"];
      const a = document.createElement("a");
      a.className = "sticker" + (prev && prev !== "done" && !firstPoll ? " fresh" : "");
      a.style.setProperty("--tilt", `${-6 + ((it.index * 37) % 7) - 3}deg`); // hand-applied, never identical
      a.href = dlHref(it.file);
      a.setAttribute("aria-label", `Save ${it.title}${it.size ? `, ${fmtBytes(it.size)}` : ""}`);
      a.append(num);
      const small = document.createElement("small");
      small.textContent = unit;
      a.append(small);
      slot.replaceChildren(a);
    }
  } else if (it.status === "downloading" || it.status === "processing") {
    const pct = it.status === "processing" ? 100 : Math.round((it.progress || 0) * 100);
    let span = slot.querySelector(".pct");
    if (!span) { span = Object.assign(document.createElement("span"), { className: "pct" }); slot.replaceChildren(span); }
    span.textContent = pct + "%";
  } else {
    slot.replaceChildren();
  }
}

// Neighbouring dividers never share a color: keep each playlist's own color unless the one above has it.
function recolor() {
  let prev = null;
  for (const el of jobsEl.querySelectorAll(":scope > .divider")) {
    let c = el.dataset.color;
    if (c !== "c0" && c === prev) c = "c" + ((Number(c.slice(1)) % 5) + 1);
    el.classList.remove("c0", "c1", "c2", "c3", "c4", "c5");
    el.classList.add(c);
    prev = c;
  }
}

function syncEmpty() {
  recolor();
  $("#empty").hidden = views.size > 0;
}

async function act(id, what) {
  try {
    await api(`/api/jobs/${id}/${what}`, { method: "POST" });
  } catch (err) {
    showFormError(err.message);
  }
  schedulePoll(200);
}

// ------------------------------------------------------------------ library (earlier sessions)

let libSig = "";
async function loadLibrary() {
  let folders;
  try { folders = await api("/api/library"); } catch { return; }
  const inCrate = new Set([...views.values()].map((v) => v.folder).filter(Boolean));
  folders = folders.filter((f) => !inCrate.has(f.path));
  const sig = JSON.stringify(folders.map((f) => [f.path, f.files.length]));
  if (sig === libSig) return;
  libSig = sig;
  const wrap = $("#library");
  wrap.replaceChildren();
  $("#librarySection").hidden = folders.length === 0;
  for (const f of folders) {
    const d = document.createElement("details");
    d.className = `shelf ${colorFor(f.name)}`;
    const s = document.createElement("summary");
    const name = Object.assign(document.createElement("span"), { className: "name", textContent: f.name });
    const count = Object.assign(document.createElement("span"), {
      className: "count", textContent: `${f.files.length} file${f.files.length === 1 ? "" : "s"}`,
    });
    const zip = Object.assign(document.createElement("a"), { className: "act zip", href: zipHref(f.path), textContent: "ZIP" });
    zip.setAttribute("aria-label", `Save ${f.name} as ZIP`);
    zip.addEventListener("click", (e) => e.stopPropagation());
    s.append(name, count, zip);
    const ul = document.createElement("ul");
    ul.className = "files";
    for (const file of f.files) {
      const li = document.createElement("li");
      const n = Object.assign(document.createElement("span"), { className: "name", textContent: file.name });
      const sz = Object.assign(document.createElement("span"), { className: "size", textContent: fmtBytes(file.size) });
      const a = Object.assign(document.createElement("a"), { className: "act", href: dlHref(file.path), textContent: "Save" });
      a.setAttribute("aria-label", `Save ${file.name}`);
      li.append(n, sz, a);
      ul.append(li);
    }
    d.append(s, ul);
    wrap.append(d);
  }
}

// ------------------------------------------------------------------ polling

async function poll() {
  pollTimer = null;
  let jobs;
  try {
    jobs = await api("/api/jobs");
  } catch (err) {
    $("#engine").textContent = "Can't reach your computer. Is PlaylistDrop still running?";
    schedulePoll(4000);
    return;
  }
  const ids = new Set(jobs.map((j) => j.id));
  for (const [id, v] of views) if (!ids.has(id)) { v.el.remove(); views.delete(id); }
  for (const job of [...jobs].reverse()) renderJob(job, true);
  firstPoll = false;
  syncEmpty();
  const busy = jobs.some((j) => j.status === "listing" || j.status === "running");
  if (!busy || Math.random() < 0.15) loadLibrary();
  schedulePoll(busy ? 1000 : 5000);
}

function schedulePoll(ms) {
  if (pollTimer) clearTimeout(pollTimer);
  pollTimer = setTimeout(poll, ms);
}

document.addEventListener("visibilitychange", () => { if (!document.hidden) schedulePoll(50); });

api("/api/status")
  .then((s) => {
    const parts = [`PlaylistDrop ${s.version}`, `yt-dlp ${s.ytdlp}`];
    if (!s.ffmpeg) parts.push("ffmpeg missing: videos limited, no MP3");
    if (!s.js_runtime) parts.push("JS runtime missing: run “playlistdrop update”");
    $("#engine").textContent = parts.join(" · ");
  })
  .catch(() => { $("#engine").textContent = "Can't reach your computer. Is PlaylistDrop still running?"; });

poll();
