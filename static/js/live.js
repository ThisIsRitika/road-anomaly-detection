// ─────────────────────────────────────────────
//  State
// ─────────────────────────────────────────────
let streaming    = false;
let fpsTimer     = null;
let countsTimer  = null;
let frameCount   = 0;
let lastFpsTime  = Date.now();

let sessionHazards  = 0;
let sessionVehicles = 0;
let sessionTracks   = new Set();

// ─────────────────────────────────────────────
//  Camera start / stop
// ─────────────────────────────────────────────
async function startCamera() {
  if (streaming) return;

  await fetch("/webcam/start", { method: "POST" });

  streaming = true;
  const feed = document.getElementById("live-feed");
  feed.src   = "/webcam/feed?" + Date.now();
  feed.style.display = "block";
  document.getElementById("feed-placeholder").style.display = "none";
  document.getElementById("live-badge").classList.add("visible");
  document.getElementById("fps-chip").classList.add("visible");
  document.getElementById("start-btn").disabled = true;
  document.getElementById("stop-btn").disabled  = false;
  document.getElementById("status-dot").classList.add("active");
  document.getElementById("status-text").textContent = "Camera Live";

  // Reset sidebar stats
  ["HMV","LMV","Pedestrian","RoadDamages","SpeedBump","UnsurfacedRoad"].forEach(k => {
    document.getElementById("ls-" + k).textContent = "0";
  });

  // Reset session tiles
  sessionHazards = 0; sessionVehicles = 0;
  document.getElementById("tile-hazards").textContent  = "0";
  document.getElementById("tile-vehicles").textContent = "0";
  document.getElementById("tile-tracks").textContent   = "0";

  frameCount  = 0;
  lastFpsTime = Date.now();
  feed.addEventListener("load", onFrameLoad);

  startFpsInterval();
  startCountsPolling();
  showToast("Live detection started — ByteTrack active");
}

async function stopCamera() {
  if (!streaming) return;

  await fetch("/webcam/stop", { method: "POST" });

  streaming = false;
  const feed = document.getElementById("live-feed");
  feed.src   = "";
  feed.style.display = "none";
  feed.removeEventListener("load", onFrameLoad);

  document.getElementById("feed-placeholder").style.display = "flex";
  document.getElementById("live-badge").classList.remove("visible");
  document.getElementById("fps-chip").classList.remove("visible");
  document.getElementById("start-btn").disabled = false;
  document.getElementById("stop-btn").disabled  = true;
  document.getElementById("status-dot").classList.remove("active");
  document.getElementById("status-text").textContent = "Camera Off";
  document.getElementById("hazard-banner").classList.remove("visible");

  clearInterval(fpsTimer);
  stopCountsPolling();
  showToast("Camera stopped");
}

// ─────────────────────────────────────────────
//  FPS tracking
// ─────────────────────────────────────────────
function onFrameLoad() {
  frameCount++;
}

function startFpsInterval() {
  fpsTimer = setInterval(() => {
    if (!streaming) return;
    const now     = Date.now();
    const elapsed = (now - lastFpsTime) / 1000;
    const fps     = Math.round(frameCount / elapsed);
    document.getElementById("fps-chip").textContent = fps + " FPS";
    frameCount  = 0;
    lastFpsTime = now;
  }, 1500);
}

// ─────────────────────────────────────────────
//  Poll /webcam/counts every 800 ms
// ─────────────────────────────────────────────
function startCountsPolling() {
  countsTimer = setInterval(pollCounts, 800);
}

function stopCountsPolling() {
  clearInterval(countsTimer);
  countsTimer = null;
}

async function pollCounts() {
  if (!streaming) return;
  try {
    const res  = await fetch("/webcam/counts");
    const data = await res.json();

    // Update sidebar per-class rows
    ["HMV","LMV","Pedestrian","RoadDamages","SpeedBump","UnsurfacedRoad"].forEach(k => {
      const el = document.getElementById("ls-" + k);
      if (el) el.textContent = data[k] ?? 0;
    });

    // Hazard banner + session tile (peak seen this session)
    const hz = (data.RoadDamages || 0) + (data.UnsurfacedRoad || 0);
    if (hz > 0) {
      if (hz > sessionHazards) {
        sessionHazards = hz;
        document.getElementById("tile-hazards").textContent = sessionHazards;
      }
      document.getElementById("hazard-banner").classList.add("visible");
      document.getElementById("hazard-text").textContent =
        `Road hazard detected — ${hz} zone(s) in current frame`;
    } else {
      document.getElementById("hazard-banner").classList.remove("visible");
    }

    // Vehicles tile (peak seen in any single frame this session)
    const vehicles = (data.HMV || 0) + (data.LMV || 0);
    if (vehicles > sessionVehicles) {
      sessionVehicles = vehicles;
      document.getElementById("tile-vehicles").textContent = sessionVehicles;
    }

  } catch (_) { /* stream may be mid-frame; skip */ }
}

// ─────────────────────────────────────────────
//  Toast helper
// ─────────────────────────────────────────────
function showToast(msg) {
  const t = document.getElementById("toast");
  document.getElementById("toast-msg").textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 3000);
}

// ─────────────────────────────────────────────
//  Keyboard shortcut: Space = toggle camera
// ─────────────────────────────────────────────
document.addEventListener("keydown", e => {
  if (e.code === "Space" && e.target.tagName !== "INPUT") {
    e.preventDefault();
    streaming ? stopCamera() : startCamera();
  }
});