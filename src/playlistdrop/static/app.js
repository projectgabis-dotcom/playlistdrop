"use strict";

const $ = (sel, el = document) => el.querySelector(sel);
const jobsEl = $("#jobs");
const views = new Map(); // job id -> { el, items: Map(index -> el) }
let pollTimer = null;

// ------------------------------------------------------------------ api

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    ...opts,
  });
  let data = null;
  try { data = await res.json(); } catch { /* empty body */ }
  if (!res.ok) throw new Error((data && data.detail) || `Request failed (${res.status})`);
  return data;
}

// ------------------------------------------------------------------ formatting

function fmtBytes(n) {
  if (!n && n !== 0) return "";
  const u = ["B", "KB", "MB", "GB"];
  let i = 0;
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(n < 10 && i > 0 ? 1 : 0)} ${u[i]}`;
}
function fmtEta(s) {
  if (s == null) return "";
  if (s < 60) return `${Math.max(1, Math.round(s))}s left`;
  return `${Math.round(s / 60)} min left`;
}
function fmtDur(s) {
  if (!s) return "";
  s = Math.round(s);
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
  return h ? `${h}:${String(m).padStart(2, "0")}:${String(r).padStart(2, "0")}` : `${m}:${String(r).padStart(2, "0")}`;
}
const MODE_LABEL = { video: "Video", audio: "Audio · M4A", mp3: "Audio · MP3" };
const dlHref = (rel) => "/dl/" + rel.split("/").map(encodeURIComponent).join("/");
const zipHref = (folder) => "/zip/" + encodeURIComponent(folder);

// ------------------------------------------------------------------ composer

const form = $("#composer");
const urlInput = $("#url");
const goBtn = $("#go");
const formError = $("#formError");
const qualityWrap = $("#qualityWrap");

function syncQuality() {
  const mode = form.elements.mode.value;
  const off = mode !== "video";
  qualityWrap.classList.toggle("off", off);
  $("#quality").disabled = off;
}
form.addEventListener("change", syncQuality);
syncQuality();

try {
  const saved = JSON.parse(localStorage.getItem("pd-prefs") || "{}");
  if (saved.mode) form.elements.mode.value = saved.mode;
  if (saved.quality) $("#quality").value = String(saved.quality);
  syncQuality();
} catch { /* storage unavailable */ }

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  formError.hidden = true;
  const url = urlInput.value.trim();
  const mode = form.elements.mode.value;
  const quality = Number($("#quality").value);
  if (!/^https?:\/\//i.test(url)) {
    showFormError("Paste the full link, starting with https://");
    return;
  }
  goBtn.disabled = true;
  try {
    const job = await api("/api/jobs", { method: "POST", body: JSON.stringify({ url, mode, quality }) });
    try { localStorage.setItem("pd-prefs", JSON.stringify({ mode, quality })); } catch { /* ignore */ }
    urlInput.value = "";
    urlInput.blur();
    renderJob(job, true);
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

// Accept links shared into the page as ?url=...
const shared = new URLSearchParams(location.search).get("url");
if (shared) urlInput.value = shared;

// ------------------------------------------------------------------ help

const helpBtn = $("#helpBtn");
helpBtn.addEventListener("click", () => {
  const help = $("#help");
  help.hidden = !help.hidden;
  helpBtn.setAttribute("aria-expanded", String(!help.hidden));
});

// ------------------------------------------------------------------ rendering

function renderJob(job, prepend = false) {
  let view = views.get(job.id);
  if (!view) {
    const el = $("#jobTpl").content.firstElementChild.cloneNode(true);
    view = { el, items: new Map() };
    views.set(job.id, view);
    $(".stop", el).addEventListener("click", () => act(job.id, "cancel"));
    $(".retry", el).addEventListener("click", () => act(job.id, "retry"));
    $(".dismiss", el).addEventListener("click", async () => {
      try { await api(`/api/jobs/${job.id}`, { method: "DELETE" }); } catch { /* already gone */ }
      el.remove();
      views.delete(job.id);
      syncEmpty();
    });
    prepend ? jobsEl.prepend(el) : jobsEl.append(el);
  }
  const el = view.el;
  view.folder = job.folder;
  const c = job.counts;
  const active = job.status === "listing" || job.status === "running";
  el.className = `job ${job.status}`;

  $(".job-title", el).textContent = job.title || (job.status === "listing" ? "Reading playlist…" : job.url);
  const bits = [MODE_LABEL[job.mode] + (job.mode === "video" ? ` ≤${job.quality}p` : "")];
  if (c.total) bits.push(`${c.done} of ${c.total} saved`);
  if (c.error) bits.push(`${c.error} failed`);
  if (job.status === "cancelled") bits.push("stopped");
  if (job.status === "done" && !c.error) bits.push("finished");
  $(".job-sub", el).textContent = bits.join(" · ");

  const pct = c.total ? Math.round(((c.done + c.error) / c.total) * 100) : 0;
  const meter = $(".meter", el);
  meter.setAttribute("aria-valuenow", String(pct));
  meter.setAttribute("aria-label", `${job.title || "Playlist"} progress`);
  $(".meter span", el).style.width = job.status === "listing" ? "" : pct + "%";

  const err = $(".job-error", el);
  err.hidden = !job.error;
  err.textContent = job.error || "";

  const saveAll = $(".save-all", el);
  saveAll.hidden = !(job.folder && c.done > 0);
  if (job.folder) {
    saveAll.href = zipHref(job.folder);
    $("span", saveAll).textContent = active ? `Save ${c.done} so far` : "Save all";
  }
  $(".stop", el).hidden = !active;
  $(".retry", el).hidden = active || !(c.error || job.items.some((i) => i.status === "cancelled"));
  $(".dismiss", el).hidden = active;

  const list = $(".items", el);
  for (const it of job.items) {
    let row = view.items.get(it.index);
    if (!row) {
      row = $("#itemTpl").content.firstElementChild.cloneNode(true);
      $(".idx", row).textContent = it.index;
      $(".title", row).textContent = it.title;
      row.title = it.title;
      const thumb = it.id ? `https://i.ytimg.com/vi/${encodeURIComponent(it.id)}/mqdefault.jpg` : it.thumbnail;
      if (thumb) {
        const img = Object.assign(document.createElement("img"), {
          className: "thumb", alt: "", loading: "lazy", decoding: "async", referrerPolicy: "no-referrer",
        });
        img.addEventListener("error", () => { img.style.visibility = "hidden"; }, { once: true });
        img.src = thumb;
        $(".thumb", row).replaceWith(img);
      }
      list.append(row);
      view.items.set(it.index, row);
    }
    updateItem(row, it);
  }
  syncEmpty();
}

function updateItem(row, it) {
  row.className = `item ${it.status}`;
  const fill = $(".fill", row);
  const p = it.status === "processing" ? 1 : it.progress || 0;
  fill.style.transform = `scaleX(${["downloading", "processing"].includes(it.status) ? p : it.status === "done" ? 1 : 0})`;

  let status = "";
  switch (it.status) {
    case "queued": status = ["Waiting", fmtDur(it.duration)].filter(Boolean).join(" · "); break;
    case "downloading":
      status = [`${Math.round((it.progress || 0) * 100)}%`, it.speed ? fmtBytes(it.speed) + "/s" : "", fmtEta(it.eta)]
        .filter(Boolean).join(" · ");
      break;
    case "processing": status = "Finishing…"; break;
    case "done": case "skipped": status = [fmtBytes(it.size), fmtDur(it.duration)].filter(Boolean).join(" · "); break;
    case "error": status = it.error || "Failed"; break;
    case "cancelled": status = "Stopped"; break;
  }
  $(".status", row).textContent = status;

  const save = $(".save", row);
  save.hidden = !it.file;
  if (it.file) {
    save.href = dlHref(it.file);
    save.setAttribute("aria-label", `Save ${it.title}`);
  }
  const icon = { error: "#i-alert", cancelled: "#i-x" }[it.status] || "";
  $(".state-ico use", row).setAttribute("href", icon);
}

function syncEmpty() {
  const has = views.size > 0;
  $("#empty").hidden = has;
  $("#jobsTitle").hidden = !has;
}

async function act(id, what) {
  try {
    await api(`/api/jobs/${id}/${what}`, { method: "POST" });
  } catch (err) {
    alert(err.message);
  }
  schedulePoll(200);
}

// ------------------------------------------------------------------ library

let libSig = "";
async function loadLibrary() {
  let folders;
  try { folders = await api("/api/library"); } catch { return; }
  const sig = JSON.stringify([folders.map((f) => [f.path, f.files.length]), [...views.values()].map((v) => v.folder)]);
  if (sig === libSig) return;
  libSig = sig;
  const wrap = $("#library");
  wrap.replaceChildren();
  const shownInJobs = new Set([...views.values()].map((v) => v.folder).filter(Boolean));
  folders = folders.filter((f) => !shownInJobs.has(f.path));
  $("#librarySection").hidden = folders.length === 0;
  for (const f of folders) {
    const d = document.createElement("details");
    d.className = "lib-folder";
    const s = document.createElement("summary");
    s.innerHTML = `<svg class="ico" aria-hidden="true"><use href="#i-folder"/></svg><span class="lib-name"></span><span class="lib-count"></span>`;
    $(".lib-name", s).textContent = f.name;
    $(".lib-count", s).textContent = `${f.files.length} file${f.files.length === 1 ? "" : "s"}`;
    const zip = document.createElement("a");
    zip.className = "btn small";
    zip.href = zipHref(f.path);
    zip.innerHTML = `<svg class="ico" aria-hidden="true"><use href="#i-zip"/></svg><span>ZIP</span>`;
    zip.addEventListener("click", (e) => e.stopPropagation());
    s.append(zip);
    d.append(s);
    const ul = document.createElement("ul");
    ul.className = "lib-files";
    for (const file of f.files) {
      const li = document.createElement("li");
      const name = document.createElement("span");
      name.className = "name";
      name.textContent = file.name;
      const size = document.createElement("span");
      size.className = "size";
      size.textContent = fmtBytes(file.size);
      const a = document.createElement("a");
      a.className = "btn small";
      a.href = dlHref(file.path);
      a.setAttribute("aria-label", `Save ${file.name}`);
      a.innerHTML = `<svg class="ico" aria-hidden="true"><use href="#i-down"/></svg><span>Save</span>`;
      li.append(name, size, a);
      ul.append(li);
    }
    d.append(ul);
    wrap.append(d);
  }
}

// ------------------------------------------------------------------ polling

async function poll() {
  pollTimer = null;
  let jobs = [];
  try {
    jobs = await api("/api/jobs");
  } catch (err) {
    $("#engine").textContent = err.message;
    schedulePoll(4000);
    return;
  }
  const ids = new Set(jobs.map((j) => j.id));
  for (const [id, v] of views) if (!ids.has(id)) { v.el.remove(); views.delete(id); }
  // Server returns newest first; render oldest first so prepend order holds.
  for (const job of [...jobs].reverse()) renderJob(job, true);
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
    if (!s.ffmpeg) parts.push("ffmpeg missing");
    if (!s.js_runtime) parts.push("JS runtime missing: run playlistdrop update");
    $("#engine").textContent = parts.join(" · ");
  })
  .catch((err) => { $("#engine").textContent = err.message; });

poll();
