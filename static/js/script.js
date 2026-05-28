// ─────────────────────────────────────────────
// Elements
// ─────────────────────────────────────────────
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const uploadInner = document.getElementById("upload-inner");
const previewWrap = document.getElementById("preview-wrap");
const imgPreview = document.getElementById("img-preview");
const vidPreview = document.getElementById("vid-preview");
const previewLabel = document.getElementById("preview-label");
const clearBtn = document.getElementById("clear-btn");

const analyzeBtn = document.getElementById("analyze-btn");
const analyzeBtnText = document.getElementById("analyze-btn-text");
const statusMsg = document.getElementById("status-msg");
const progressWrap = document.getElementById("progress-wrap");
const progressFill = document.getElementById("progress-fill");
const progressLabel = document.getElementById("progress-label");

const sectionResults = document.getElementById("section-results");
const sectionAlerts = document.getElementById("section-alerts");
const resultsCta = document.getElementById("results-cta");

const originalResultImg = document.getElementById("original-result-img");
const originalResultVid = document.getElementById("original-result-vid");
const resultImg = document.getElementById("result-img");
const resultVid = document.getElementById("result-vid");

const downloadPdfBtn = document.getElementById("download-pdf-btn");
const resetBtn = document.getElementById("reset-btn");
const alertsContainer = document.getElementById("alerts-container");

// ─────────────────────────────────────────────
// State
// ─────────────────────────────────────────────
let currentFile = null;
let currentPdfId = null;

// ─────────────────────────────────────────────
// Browse button — stop propagation so the
// dropZone click handler doesn't fire a second
// fileInput.click(), which causes the double-
// dialog bug on first selection.
// ─────────────────────────────────────────────
document.getElementById("browse-btn")?.addEventListener("click", (e) => {
  e.stopPropagation();
  fileInput.click();
});

// ─────────────────────────────────────────────
// Drag & Drop / Drop-zone click
// ─────────────────────────────────────────────
dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("drag-over");
});
dropZone.addEventListener("dragleave", () =>
  dropZone.classList.remove("drag-over"),
);
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) handleFileSelected(file);
});

// Only open dialog when clicking the bare drop zone (not buttons/preview)
dropZone.addEventListener("click", (e) => {
  if (e.target.closest(".preview-wrap")) return;
  if (e.target.closest("button")) return; // buttons handle themselves
  if (previewWrap.style.display === "none" || !previewWrap.style.display) {
    fileInput.click();
  }
});

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) handleFileSelected(fileInput.files[0]);
});

clearBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  resetUploadArea();
});

// ─────────────────────────────────────────────
// File Handling
// ─────────────────────────────────────────────
function handleFileSelected(file) {
  const isVideo = file.type.startsWith("video/");
  const isImage = file.type.startsWith("image/");

  if (!isVideo && !isImage) {
    setStatus("Unsupported file type. Please use an image or video.", "error");
    return;
  }

  currentFile = file;
  uploadInner.style.display = "none";
  previewWrap.style.display = "flex";
  previewLabel.textContent = `${file.name} — ${formatBytes(file.size)}`;

  const url = URL.createObjectURL(file);
  if (isImage) {
    imgPreview.src = url;
    imgPreview.style.display = "block";
    vidPreview.style.display = "none";
  } else {
    vidPreview.src = url;
    vidPreview.style.display = "block";
    imgPreview.style.display = "none";
  }

  analyzeBtn.disabled = false;
  setStatus("File ready. Click Analyze to start.", "");
  resultsCta.style.display = "none";
}

function resetUploadArea() {
  currentFile = null;
  fileInput.value = "";
  imgPreview.src = "";
  vidPreview.src = "";
  imgPreview.style.display = "none";
  vidPreview.style.display = "none";
  uploadInner.style.display = "flex";
  previewWrap.style.display = "none";
  analyzeBtn.disabled = true;
  setStatus("", "");
  resultsCta.style.display = "none";
}

// ─────────────────────────────────────────────
// Analysis
// ─────────────────────────────────────────────
analyzeBtn.addEventListener("click", async () => {
  if (!currentFile) return;

  analyzeBtn.disabled = true;
  analyzeBtnText.textContent = "Analyzing…";
  setStatus("Sending file to model…", "processing");
  progressWrap.style.display = "block";
  resultsCta.style.display = "none";
  animateProgress();

  const formData = new FormData();
  formData.append("file", currentFile);

  try {
    const endpoint = "/predict";
    const res = await fetch(endpoint, { method: "POST", body: formData });
    const data = await res.json();

    progressFill.style.width = "100%";
    progressLabel.textContent = "Done!";
    setTimeout(() => {
      progressWrap.style.display = "none";
    }, 600);

    renderResults(data);
    renderAlerts(data.alerts);

    currentPdfId = data.pdf_id;

    if (downloadPdfBtn) {
      downloadPdfBtn.onclick = () => {
        window.open(`/download-pdf/${currentPdfId}`, "_blank");
      };
    }

    resultsCta.style.display = "flex";
    setStatus("Analysis complete ✓", "done");
    analyzeBtnText.textContent = "Analyze";
    analyzeBtn.disabled = false;

    sectionResults.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    setStatus("Error during analysis. Please try again.", "error");
    progressWrap.style.display = "none";
    analyzeBtnText.textContent = "Analyze";
    analyzeBtn.disabled = false;
  }
});

function animateProgress() {
  let pct = 0;
  const labels = [
    "Loading model…",
    "Sampling frames…",
    "Running detection…",
    "Generating bounding boxes…",
    "Finalizing report…",
  ];
  let li = 0;
  progressLabel.textContent = labels[0];

  const iv = setInterval(() => {
    pct += Math.random() * 8;
    if (pct >= 90) {
      pct = 90;
      clearInterval(iv);
    }
    progressFill.style.width = pct + "%";
    const newLi = Math.min(Math.floor(pct / 20), labels.length - 1);
    if (newLi !== li) {
      li = newLi;
      progressLabel.textContent = labels[li];
    }
  }, 600);
}

// ─────────────────────────────────────────────
// Render Results
// ─────────────────────────────────────────────
function renderResults(data) {
  sectionResults.style.display = "block";
  const isVideo = data.file_type === "video";

  if (isVideo) {
    originalResultImg.style.display = "none";
    originalResultVid.src = data.original_url;
    originalResultVid.style.display = "block";

    if (data.thumb_url) {
      resultVid.style.display = "none";
      resultImg.src = data.thumb_url;
      resultImg.style.display = "block";
      resultImg.title =
        "Best detection frame (peak hazard frame from sampled frames)";
    } else {
      resultImg.style.display = "none";
      resultVid.src = data.result_url;
      resultVid.style.display = "block";
    }
  } else {
    originalResultVid.style.display = "none";
    originalResultImg.src = data.original_url;
    originalResultImg.style.display = "block";
    resultVid.style.display = "none";
    resultImg.src = data.result_url;
    resultImg.style.display = "block";
  }

  const counts = data.counts;
  document.getElementById("cnt-HMV").textContent = counts.HMV || 0;
  document.getElementById("cnt-LMV").textContent = counts.LMV || 0;
  document.getElementById("cnt-Pedestrian").textContent =
    counts.Pedestrian || 0;
  document.getElementById("cnt-RoadDamages").textContent =
    counts.RoadDamages || 0;
  document.getElementById("cnt-SpeedBump").textContent = counts.SpeedBump || 0;
  document.getElementById("cnt-UnsurfacedRoad").textContent =
    counts.UnsurfacedRoad || 0;

  document.querySelectorAll(".count-num").forEach((el) => {
    animateNum(el, parseInt(el.textContent));
  });
}

function animateNum(el, target) {
  if (target === 0) return;
  let current = 0;
  const step = Math.max(1, Math.floor(target / 20));
  const iv = setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = current;
    if (current >= target) clearInterval(iv);
  }, 40);
}

// ─────────────────────────────────────────────
// Render Alerts
// ─────────────────────────────────────────────
function renderAlerts(alerts) {
  alertsContainer.innerHTML = "";
  if (!alerts || alerts.length === 0) {
    sectionAlerts.style.display = "none";
    return;
  }
  sectionAlerts.style.display = "block";

  const levelTitles = {
    critical: "⚠ Critical Hazard Detected",
    warning: "🔶 Warning",
    safe: "✅ Road Conditions Safe",
  };

  alerts.forEach((alert) => {
    const el = document.createElement("div");
    el.className = `alert-item ${alert.level}`;
    el.innerHTML = `
      <div class="alert-icon">${alert.icon}</div>
      <div class="alert-body">
        <div class="alert-title">${levelTitles[alert.level] || "Notice"}</div>
        <div class="alert-msg">${alert.message}</div>
      </div>
    `;
    alertsContainer.appendChild(el);
  });
}

// ─────────────────────────────────────────────
// Reset
// ─────────────────────────────────────────────
resetBtn?.addEventListener("click", () => {
  resetUploadArea();
  sectionResults.style.display = "none";
  sectionAlerts.style.display = "none";
  alertsContainer.innerHTML = "";
  resultsCta.style.display = "none";
  currentPdfId = null;
  window.scrollTo({ top: 0, behavior: "smooth" });
});

// ─────────────────────────────────────────────
// Utilities
// ─────────────────────────────────────────────
function setStatus(msg, type) {
  statusMsg.textContent = msg;
  statusMsg.className = "status-msg" + (type ? " " + type : "");
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

// NOTE: Mode toggle (switchMode) and all batch upload logic
// are handled by index_extra.js, which is loaded after this file.