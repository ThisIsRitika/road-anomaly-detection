// ═══════════════════════════════════════════════════════
//  MODE TOGGLE  (Single / Batch)
// ═══════════════════════════════════════════════════════
function switchMode(mode) {
  document.getElementById("mode-single").classList.toggle("active", mode === "single");
  document.getElementById("mode-batch").classList.toggle("active",  mode === "batch");
  document.getElementById("single-panel").style.display = mode === "single" ? "block" : "none";
  document.getElementById("batch-panel").style.display  = mode === "batch"  ? "block" : "none";

  // Hide inline results when switching
  document.getElementById("section-results").style.display = "none";
  document.getElementById("section-alerts").style.display  = "none";
}

// ═══════════════════════════════════════════════════════
//  CONFIDENCE SCORES  (single file)
// ═══════════════════════════════════════════════════════
const CLASS_COLORS_CSS = {
  HMV:           "#DC5050",
  LMV:           "#50B450",
  Pedestrian:    "#5078DC",
  RoadDamages:   "#DCB428",
  SpeedBump:     "#B450DC",
  UnsurfacedRoad:"#28C8C8",
};
const CLASS_LABELS = {
  HMV:           "Heavy Motor Vehicle",
  LMV:           "Light Motor Vehicle",
  Pedestrian:    "Pedestrian",
  RoadDamages:   "Road Damages",
  SpeedBump:     "Speed Bump",
  UnsurfacedRoad:"Unsurfaced Road",
};

function renderConfidence(confSummary) {
  const section = document.getElementById("conf-section");
  const rows    = document.getElementById("conf-rows");
  rows.innerHTML = "";

  const entries = Object.entries(confSummary);
  if (!entries.length) { section.style.display = "none"; return; }

  section.style.display = "block";

  entries.forEach(([cls, cs]) => {
    const color = CLASS_COLORS_CSS[cls] || "#f0b429";
    const label = CLASS_LABELS[cls]     || cls;
    const pct   = cs.avg;

    const row = document.createElement("div");
    row.className = "conf-row";
    row.innerHTML = `
      <div class="conf-label">${label}</div>
      <div class="conf-bar-wrap">
        <div class="conf-bar-fill" style="width:${pct}%;background:${color}"></div>
      </div>
      <div class="conf-pct">${pct}%</div>
    `;
    rows.appendChild(row);

    // min / max sub-label
    const sub = document.createElement("div");
    sub.style.cssText = "font-size:11px;color:var(--text-muted);margin:-4px 0 10px 130px;";
    sub.textContent = `min ${cs.min}%  ·  max ${cs.max}%  ·  ${cs.all.length} detection(s)`;
    rows.appendChild(sub);
  });
}

// Hook into existing renderResults to also show confidence
const _origRenderResults = renderResults;
window.renderResults = function(data) {
  _origRenderResults(data);
  if (data.conf_summary) renderConfidence(data.conf_summary);
};

// ═══════════════════════════════════════════════════════
//  BATCH UPLOAD
// ═══════════════════════════════════════════════════════
let batchFiles = [];

const batchDrop      = document.getElementById("batch-drop");
const batchInput     = document.getElementById("batch-input");
const batchQueue     = document.getElementById("batch-queue");
const batchAnalyzeBtn= document.getElementById("batch-analyze-btn");
const batchBtnText   = document.getElementById("batch-btn-text");
const batchStatus    = document.getElementById("batch-status");
const batchClearBtn  = document.getElementById("batch-clear-btn");
const batchProgressW = document.getElementById("batch-progress-wrap");
const batchFill      = document.getElementById("batch-progress-fill");
const batchProgLabel = document.getElementById("batch-progress-label");
const batchSummary   = document.getElementById("batch-summary");

document.getElementById("batch-browse-btn").addEventListener("click", e => {
  e.stopPropagation();
  batchInput.click();
});

batchDrop.addEventListener("dragover", e => { e.preventDefault(); batchDrop.classList.add("drag-over"); });
batchDrop.addEventListener("dragleave", () => batchDrop.classList.remove("drag-over"));
batchDrop.addEventListener("drop", e => {
  e.preventDefault();
  batchDrop.classList.remove("drag-over");
  addBatchFiles([...e.dataTransfer.files]);
});
batchDrop.addEventListener("click", e => {
  if (e.target.closest("button")) return;
  batchInput.click();
});
batchInput.addEventListener("change", () => {
  if (batchInput.files.length) addBatchFiles([...batchInput.files]);
});

batchClearBtn.addEventListener("click", () => {
  batchFiles = [];
  batchQueue.innerHTML = "";
  batchAnalyzeBtn.disabled = true;
  batchClearBtn.style.display = "none";
  batchSummary.style.display = "none";
  batchStatus.textContent = "";
  batchInput.value = "";
});

function addBatchFiles(files) {
  const valid = files.filter(f => f.type.startsWith("image/"));
  if (!valid.length) {
    batchStatus.textContent = "Please select image files only.";
    batchStatus.className = "status-msg error";
    return;
  }
  batchFiles = [...batchFiles, ...valid];
  renderBatchQueue();
  batchAnalyzeBtn.disabled = false;
  batchClearBtn.style.display = "inline-flex";
  batchStatus.textContent = `${batchFiles.length} file(s) queued`;
  batchStatus.className = "status-msg";
}

function renderBatchQueue() {
  batchQueue.innerHTML = "";
  batchFiles.forEach((f, i) => {
    const item = document.createElement("div");
    item.className = "batch-file-item";
    item.id = `bf-${i}`;
    item.innerHTML = `
      <i class="fa-solid fa-file-image"></i>
      <span class="fname">${f.name}</span>
      <span class="fsize">${formatBytes(f.size)}</span>
      <span class="fstatus queued" id="bfs-${i}">Queued</span>
    `;
    batchQueue.appendChild(item);
  });
}

batchAnalyzeBtn.addEventListener("click", async () => {
  if (!batchFiles.length) return;

  batchAnalyzeBtn.disabled = true;
  batchBtnText.textContent = "Processing…";
  batchProgressW.style.display = "block";
  batchFill.style.width = "0%";
  batchProgLabel.textContent = "Uploading files…";
  batchSummary.style.display = "none";

  // Mark all as running
  batchFiles.forEach((_, i) => {
    const el = document.getElementById(`bfs-${i}`);
    if (el) { el.textContent = "Queued"; el.className = "fstatus queued"; }
  });

  const formData = new FormData();
  batchFiles.forEach(f => formData.append("files", f));

  // Animate progress
  let pct = 0;
  const iv = setInterval(() => {
    pct = Math.min(pct + 3, 88);
    batchFill.style.width = pct + "%";
    if (pct > 20) batchProgLabel.textContent = "Running YOLO on each image…";
    if (pct > 60) batchProgLabel.textContent = "Generating confidence scores…";
    if (pct > 80) batchProgLabel.textContent = "Compiling report & ZIP…";
  }, 400);

  try {
    const res  = await fetch("/predict_batch", { method: "POST", body: formData });
    const data = await res.json();
    clearInterval(iv);

    batchFill.style.width = "100%";
    batchProgLabel.textContent = "Done!";
    setTimeout(() => { batchProgressW.style.display = "none"; }, 700);

    renderBatchResults(data);
    batchBtnText.textContent = "Analyze All";
    batchAnalyzeBtn.disabled = false;

  } catch (err) {
    clearInterval(iv);
    batchStatus.textContent = "Error during batch analysis.";
    batchStatus.className = "status-msg error";
    batchProgressW.style.display = "none";
    batchBtnText.textContent = "Analyze All";
    batchAnalyzeBtn.disabled = false;
  }
});

function renderBatchResults(data) {
  batchSummary.style.display = "block";

  // Summary stats
  const total   = Object.values(data.total_counts).reduce((a,b) => a+b, 0);
  const hazards = (data.total_counts.RoadDamages || 0) + (data.total_counts.UnsurfacedRoad || 0);
  document.getElementById("bstat-files").textContent   = data.file_count;
  document.getElementById("bstat-objects").textContent  = total;
  document.getElementById("bstat-hazards").textContent  = hazards;
  document.getElementById("bstat-alerts").textContent   = data.combined_alerts.length;

  // Mark file statuses
  data.results.forEach((r, i) => {
    const el = document.getElementById(`bfs-${i}`);
    if (el) { el.textContent = "Done"; el.className = "fstatus done"; }
  });

  // Download buttons
  document.getElementById("batch-download-zip-btn").onclick = () => {
    window.open(data.zip_url, "_blank");
  };
  document.getElementById("batch-download-pdf-btn").onclick = () => {
    window.open(`/download-pdf/${data.pdf_id}`, "_blank");
  };

  // Per-file accordion
  const list = document.getElementById("file-results-list");
  list.innerHTML = "";

  data.results.forEach((r, i) => {
    const haz  = (r.counts.RoadDamages || 0) + (r.counts.UnsurfacedRoad || 0);
    const objs = Object.values(r.counts).reduce((a,b)=>a+b, 0);

    const card = document.createElement("div");
    card.className = "file-result-card";
    card.innerHTML = `
      <div class="file-result-header" onclick="toggleFileResult(${i})">
        <span class="frh-name"><i class="fa-solid fa-file-image" style="margin-right:8px;color:var(--accent);"></i>${r.filename}</span>
        <div class="frh-pills">
          <span class="frh-pill">${objs} objects</span>
          ${haz > 0
            ? `<span class="frh-pill hazard">⚠ ${haz} hazard${haz>1?'s':''}</span>`
            : `<span class="frh-pill safe">✅ Safe</span>`}
        </div>
        <i class="fa-solid fa-chevron-down" style="color:var(--text-muted);font-size:12px;margin-left:8px;"></i>
      </div>
      <div class="file-result-body" id="frb-${i}">
        <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:14px;">
          <a href="${r.result_url}" target="_blank" class="btn btn-outline btn-sm">
            <i class="fa-solid fa-image"></i> View Annotated
          </a>
        </div>
        <div>${buildConfRows(r.conf_summary)}</div>
      </div>
    `;
    list.appendChild(card);
  });

  batchSummary.scrollIntoView({ behavior: "smooth" });
}

function buildConfRows(confSummary) {
  if (!confSummary || !Object.keys(confSummary).length) return '<p style="font-size:12px;color:var(--text-muted)">No detections.</p>';
  return Object.entries(confSummary).map(([cls, cs]) => {
    const color = CLASS_COLORS_CSS[cls] || "#f0b429";
    const label = CLASS_LABELS[cls] || cls;
    return `
      <div class="conf-row">
        <div class="conf-label" style="font-size:12px;">${label}</div>
        <div class="conf-bar-wrap">
          <div class="conf-bar-fill" style="width:${cs.avg}%;background:${color}"></div>
        </div>
        <div class="conf-pct">${cs.avg}%</div>
      </div>`;
  }).join("");
}

function toggleFileResult(i) {
  const body = document.getElementById(`frb-${i}`);
  body.classList.toggle("open");
}