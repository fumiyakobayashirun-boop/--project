"use strict";

const $ = (sel) => document.querySelector(sel);
const jobsEl = $("#jobs");
const zipBtn = $("#zip-btn");
const doneIds = new Set();

// ---------- 設定 ----------

function currentOptions() {
  return {
    mode: document.querySelector('input[name="mode"]:checked').value,
    scale: $("#scale").value,
    sharpen: $("#sharpen").value,
    denoise: $("#denoise").value,
    contrast: $("#contrast").checked ? "1" : "0",
    ai_strength: $("#ai_strength").value,
  };
}

function syncOutputs() {
  $('output[for="sharpen"]').textContent = Number($("#sharpen").value).toFixed(1);
  $('output[for="ai_strength"]').textContent = `${Math.round($("#ai_strength").value * 100)}%`;
  $("#ai-strength-field").hidden = currentOptions().mode !== "ai";
}

document.querySelectorAll('input[name="mode"]').forEach((el) =>
  el.addEventListener("change", () => {
    // AIは線がくっきり出るので、シャープは控えめを既定にする
    $("#sharpen").value = el.value === "ai" ? "0.5" : "1.0";
    syncOutputs();
  }),
);
$("#sharpen").addEventListener("input", syncOutputs);
$("#ai_strength").addEventListener("input", syncOutputs);
syncOutputs();

// ---------- ファイル受付 ----------

const dropzone = $("#dropzone");
$("#file-input").addEventListener("change", (e) => {
  addFiles(e.target.files);
  e.target.value = "";
});
["dragenter", "dragover"].forEach((t) =>
  dropzone.addEventListener(t, (e) => {
    e.preventDefault();
    dropzone.classList.add("over");
  }),
);
["dragleave", "drop"].forEach((t) => dropzone.addEventListener(t, () => dropzone.classList.remove("over")));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  addFiles(e.dataTransfer.files);
});
// ドロップ領域の外に落としたときにブラウザがファイルを開いてしまうのを防ぐ
window.addEventListener("dragover", (e) => e.preventDefault());
window.addEventListener("drop", (e) => e.preventDefault());

function addFiles(files) {
  const opts = currentOptions();
  for (const file of files) startJob(file, opts);
}

// ---------- ジョブ ----------

async function startJob(file, opts) {
  const el = $("#job-template").content.firstElementChild.cloneNode(true);
  el.querySelector(".job-name").textContent = file.name;
  setStatus(el, "送信中…");
  jobsEl.prepend(el);
  $("#list-header").hidden = false;

  const form = new FormData();
  form.append("file", file);
  for (const [k, v] of Object.entries(opts)) form.append(k, v);

  try {
    const res = await fetch("/api/jobs", { method: "POST", body: form });
    const job = await res.json();
    if (!res.ok) throw new Error(job.error || `エラー (${res.status})`);
    poll(el, job.id);
  } catch (err) {
    showError(el, err.message);
  }
}

async function poll(el, id) {
  let job;
  try {
    const res = await fetch(`/api/jobs/${id}`);
    if (!res.ok) throw new Error("処理状況を取得できませんでした（ツールを再起動した可能性があります）");
    job = await res.json();
  } catch (err) {
    showError(el, err.message);
    return;
  }

  if (job.status === "queued") setStatus(el, "順番待ち…");
  if (job.status === "running") setStatus(el, `処理中… ${Math.round(job.progress * 100)}%`);
  el.querySelector(".bar").style.width = `${job.progress * 100}%`;

  if (job.status === "error") return showError(el, job.error);
  if (job.status !== "done") {
    setTimeout(() => poll(el, id), 600);
    return;
  }

  el.classList.add("done");
  setStatus(el, `完了 → ${job.output}`);
  const notes = el.querySelector(".job-notes");
  for (const n of job.notes) {
    const li = document.createElement("li");
    li.textContent = n;
    notes.append(li);
  }
  const dl = el.querySelector(".download-btn");
  dl.href = `/api/jobs/${id}/download`;
  dl.hidden = false;
  const cmp = el.querySelector(".compare-btn");
  cmp.hidden = false;
  cmp.addEventListener("click", () => openViewer(id, job.filename));
  doneIds.add(id);
  el.dataset.id = id;
  zipBtn.disabled = false;
}

function setStatus(el, text) {
  el.querySelector(".job-status").textContent = text;
}

function showError(el, message) {
  el.classList.add("error");
  setStatus(el, `失敗：${message}`);
}

zipBtn.addEventListener("click", () => {
  location.href = `/api/download-all?ids=${[...doneIds].join(",")}`;
});

$("#clear-btn").addEventListener("click", () => {
  jobsEl.innerHTML = "";
  doneIds.clear();
  zipBtn.disabled = true;
  $("#list-header").hidden = true;
});

// ---------- 補正前後の比較 ----------

const viewer = $("#viewer");
const compare = $("#compare");
const imgBefore = $("#img-before");
const divider = $("#divider");

function openViewer(id, name) {
  $("#viewer-title").textContent = name;
  $("#img-after").src = `/api/jobs/${id}/preview/after`;
  imgBefore.src = `/api/jobs/${id}/preview/before`;
  setSplit(50);
  viewer.showModal();
}

function setSplit(pct) {
  pct = Math.min(100, Math.max(0, pct));
  imgBefore.style.clipPath = `inset(0 ${100 - pct}% 0 0)`;
  divider.style.left = `${pct}%`;
}

function splitFromEvent(e) {
  const rect = compare.getBoundingClientRect();
  setSplit(((e.clientX - rect.left) / rect.width) * 100);
}

let dragging = false;
compare.addEventListener("pointerdown", (e) => {
  dragging = true;
  compare.setPointerCapture(e.pointerId);
  splitFromEvent(e);
});
compare.addEventListener("pointermove", (e) => dragging && splitFromEvent(e));
compare.addEventListener("pointerup", () => (dragging = false));
compare.addEventListener("pointercancel", () => (dragging = false));

$("#actual-size").addEventListener("change", (e) => compare.classList.toggle("actual", e.target.checked));
$("#viewer-close").addEventListener("click", () => viewer.close());
viewer.addEventListener("click", (e) => e.target === viewer && viewer.close());
