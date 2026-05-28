// ═══════════════════════════════════════════════════════
//  CONSTANTS
// ═══════════════════════════════════════════════════════
const CLASS_COLORS = {
  HMV:"#DC5050",LMV:"#50B450",Pedestrian:"#5078DC",
  RoadDamages:"#DCB428",SpeedBump:"#B450DC",UnsurfacedRoad:"#28C8C8"
};
const CLASS_LABELS = {
  HMV:"HMV",LMV:"LMV",Pedestrian:"Pedestrian",
  RoadDamages:"Road Damages",SpeedBump:"Speed Bump",UnsurfacedRoad:"Unsurfaced Rd"
};
const CLASS_ICONS = {
  HMV:"fa-truck",LMV:"fa-car",Pedestrian:"fa-person-walking",
  RoadDamages:"fa-circle-exclamation",SpeedBump:"fa-road-barrier",UnsurfacedRoad:"fa-triangle-exclamation"
};

let currentPage = 1;
let debTimer    = null;

// ═══════════════════════════════════════════════════════
//  INIT
// ═══════════════════════════════════════════════════════
document.addEventListener("DOMContentLoaded", () => {
  loadStats();
  loadHistory(1);
});

// ═══════════════════════════════════════════════════════
//  STATS + TREND
// ═══════════════════════════════════════════════════════
async function loadStats() {
  const res  = await fetch("/api/history/stats");
  const data = await res.json();
  const s    = data.stats;

  document.getElementById("hs-total").textContent    = s.total_analyses;
  document.getElementById("hs-hazards").textContent  = s.total_hazards;
  document.getElementById("hs-objects").textContent  = s.total_objects;
  document.getElementById("hs-critical").textContent = s.critical_count;
  document.getElementById("hs-vehicles").textContent = s.total_vehicles;
  document.getElementById("db-count").textContent    = `${s.total_analyses} records`;

  renderTrend(data.trend);
}

function renderTrend(trend) {
  const el  = document.getElementById("trend-chart");
  el.innerHTML = "";

  // Fill missing days in the last 7
  const days = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    days.push(d.toISOString().slice(0,10));
  }

  const byDay = {};
  trend.forEach(t => { byDay[t.day] = t; });

  const maxRuns    = Math.max(1, ...days.map(d => (byDay[d]?.runs    || 0)));
  const maxHazards = Math.max(1, ...days.map(d => (byDay[d]?.hazards || 0)));
  const maxVal     = Math.max(maxRuns, maxHazards);

  days.forEach(day => {
    const t       = byDay[day] || {runs:0, hazards:0};
    const runsH   = Math.round((t.runs    / maxVal) * 64) + 2;
    const hazardsH= Math.round((t.hazards / maxVal) * 64) + 2;
    const label   = day.slice(5); // MM-DD

    const col = document.createElement("div");
    col.className = "trend-col";
    col.innerHTML = `
      <div class="trend-bar-wrap">
        <div class="trend-bar runs"    style="height:${runsH}px"    title="${t.runs} analyses on ${day}"></div>
        <div class="trend-bar hazards" style="height:${hazardsH}px" title="${t.hazards} hazards on ${day}"></div>
      </div>
      <div class="trend-day">${label}</div>
    `;
    el.appendChild(col);
  });
}

// ═══════════════════════════════════════════════════════
//  HISTORY LIST
// ═══════════════════════════════════════════════════════
function debounceLoad() {
  clearTimeout(debTimer);
  debTimer = setTimeout(() => loadHistory(1), 350);
}

async function loadHistory(page=1) {
  currentPage = page;
  const grid  = document.getElementById("hist-grid");
  grid.innerHTML = skeletons(6);

  const params = new URLSearchParams({
    page,
    per_page: 12,
    severity:  document.getElementById("sev-filter").value,
    file_type: document.getElementById("type-filter").value,
    search:    document.getElementById("search-input").value,
  });

  const res  = await fetch("/api/history?" + params);
  const data = await res.json();

  document.getElementById("total-label").textContent =
    `${data.total} result${data.total !== 1 ? "s" : ""}`;

  if (!data.rows.length) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1">
        <i class="fa-solid fa-clock-rotate-left"></i>
        <h3>No analyses found</h3>
        <p>Run an analysis on the main page — it will appear here automatically.</p>
        <a href="/" class="btn btn-primary" style="margin-top:8px">
          <i class="fa-solid fa-upload"></i> Go Analyze
        </a>
      </div>`;
    document.getElementById("pagination").innerHTML = "";
    return;
  }

  grid.innerHTML = "";
  data.rows.forEach(row => grid.appendChild(makeCard(row)));
  renderPagination(data.page, data.total_pages);
}

function skeletons(n) {
  return Array.from({length:n}, () => `
    <div class="skeleton-card">
      <div class="sk-thumb"></div>
      <div class="sk-body">
        <div class="sk-line" style="width:70%"></div>
        <div class="sk-line" style="width:45%"></div>
        <div class="sk-line" style="width:60%"></div>
      </div>
    </div>`).join("");
}

function makeCard(row) {
  const counts = JSON.parse(row.counts_json || "{}");
  const hazards= row.hazards;
  const card   = document.createElement("div");
  card.className = `hist-card ${row.severity}`;

  const typeIcon = row.file_type==="video"?"fa-film":
                   row.file_type==="batch"?"fa-layer-group":"fa-image";

  const thumb = row.thumb_url
    ? `<img class="hcard-thumb" src="${row.thumb_url}" alt="thumb" onerror="this.style.display='none';this.nextSibling.style.display='flex'">`
    : "";
  const placeholder = `<div class="hcard-thumb-placeholder" ${row.thumb_url ? 'style="display:none"' : ""}>
                          <i class="fa-solid fa-image"></i></div>`;

  card.innerHTML = `
    ${thumb}${placeholder}
    <div class="hcard-body">
      <div class="hcard-top">
        <div class="hcard-name" title="${row.original_name}">${row.original_name || "Unnamed"}</div>
        <span class="hcard-sev ${row.severity}">${cap(row.severity)}</span>
      </div>
      <div class="hcard-meta">
        <i class="fa-solid ${typeIcon}"></i>${cap(row.file_type)}
        <span>·</span>
        <i class="fa-solid fa-clock"></i>${row.created_at}
      </div>
      <div class="hcard-chips">
        <span class="chip"><i class="fa-solid fa-cube" style="color:var(--accent)"></i>${row.total_objects} objects</span>
        ${hazards>0
          ? `<span class="chip danger"><i class="fa-solid fa-triangle-exclamation"></i>${hazards} hazard${hazards>1?"s":""}</span>`
          : `<span class="chip" style="background:rgba(34,197,94,.1);color:var(--success)"><i class="fa-solid fa-check"></i>Safe</span>`}
        ${row.alert_count>0
          ? `<span class="chip accent"><i class="fa-solid fa-bell"></i>${row.alert_count} alert${row.alert_count>1?"s":""}</span>`
          : ""}
      </div>
      <div class="hcard-actions">
        <button class="btn btn-outline btn-sm" onclick="event.stopPropagation();openModal('${row.uid}')">
          <i class="fa-solid fa-eye"></i> View
        </button>
        ${row.pdf_id
          ? `<a class="btn btn-ghost btn-sm" href="/download-pdf/${row.pdf_id}" target="_blank" onclick="event.stopPropagation()">
               <i class="fa-solid fa-file-pdf"></i> PDF
             </a>`
          : ""}
        <button class="btn btn-ghost btn-sm" style="color:var(--danger)"
                onclick="event.stopPropagation();deleteAnalysis('${row.uid}')">
          <i class="fa-solid fa-trash"></i>
        </button>
      </div>
    </div>`;

  card.addEventListener("click", () => openModal(row.uid));
  return card;
}

// ═══════════════════════════════════════════════════════
//  PAGINATION
// ═══════════════════════════════════════════════════════
function renderPagination(page, totalPages) {
  const el = document.getElementById("pagination");
  if (totalPages <= 1) { el.innerHTML=""; return; }

  let html = `<button class="page-btn" ${page<=1?"disabled":""} onclick="loadHistory(${page-1})">
                <i class="fa-solid fa-chevron-left"></i></button>`;

  for (let p=1; p<=totalPages; p++) {
    if (totalPages>7 && Math.abs(p-page)>2 && p!==1 && p!==totalPages) {
      if (p===2 || p===totalPages-1) html += `<span style="color:var(--text-muted);padding:0 4px">…</span>`;
      continue;
    }
    html += `<button class="page-btn ${p===page?"active":""}" onclick="loadHistory(${p})">${p}</button>`;
  }

  html += `<button class="page-btn" ${page>=totalPages?"disabled":""} onclick="loadHistory(${page+1})">
             <i class="fa-solid fa-chevron-right"></i></button>`;
  el.innerHTML = html;
}

// ═══════════════════════════════════════════════════════
//  DETAIL MODAL
// ═══════════════════════════════════════════════════════
async function openModal(uid) {
  const backdrop = document.getElementById("modal-backdrop");
  const body     = document.getElementById("modal-body");
  const footer   = document.getElementById("modal-footer");
  document.getElementById("modal-title").textContent = "Loading…";
  body.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-muted)">
                      <i class="fa-solid fa-spinner fa-spin fa-2x"></i></div>`;
  footer.innerHTML = "";
  backdrop.classList.add("open");

  const res = await fetch(`/api/history/${uid}`);
  const d   = await res.json();
  if (d.error) { body.innerHTML = `<p style="color:var(--danger)">${d.error}</p>`; return; }

  document.getElementById("modal-title").textContent = d.original_name || "Analysis Detail";

  // Images
  let imgsHtml = "";
  if (d.original_url && d.result_url && d.file_type !== "batch") {
    imgsHtml = `
      <div class="modal-imgs">
        <div class="modal-img-panel">
          <div class="modal-img-label">Original</div>
          <img src="${d.original_url}" alt="original"/>
        </div>
        <div class="modal-img-panel">
          <div class="modal-img-label">Detected</div>
          <img src="${d.thumb_url || d.result_url}" alt="result"/>
        </div>
      </div>`;
  }

  // Counts
  const countsHtml = Object.entries(d.counts).map(([k,v]) => `
    <div class="mc">
      <div class="mc-dot" style="background:${CLASS_COLORS[k]||'#999'}"></div>
      <div>
        <div class="mc-val">${v}</div>
        <div class="mc-lbl">${CLASS_LABELS[k]||k}</div>
      </div>
    </div>`).join("");

  // Confidence
  let confHtml = "";
  const cs = d.conf_summary || {};
  if (Object.keys(cs).length) {
    confHtml = `<div class="modal-conf">
      <h5><i class="fa-solid fa-gauge-high"></i> Confidence Scores</h5>
      ${Object.entries(cs).map(([k,c]) => `
        <div class="mconf-row">
          <div class="mconf-lbl">${CLASS_LABELS[k]||k}</div>
          <div class="mconf-bar"><div class="mconf-fill" style="width:${c.avg}%;background:${CLASS_COLORS[k]||'#999'}"></div></div>
          <div class="mconf-pct">${c.avg}%</div>
        </div>`).join("")}
    </div>`;
  }

  // Alerts
  const alertLevel = {"critical":"⚠ Critical Hazard","warning":"🔶 Warning","safe":"✅ Safe"};
  const alertsHtml = (d.alerts||[]).map(a => `
    <div class="mal ${a.level}">
      <div class="mal-icon">${a.icon||""}</div>
      <div>
        <div style="font-weight:700;font-size:13px;">${alertLevel[a.level]||"Notice"}</div>
        <div class="mal-msg">${a.message}</div>
      </div>
    </div>`).join("") || `<div class="mal safe"><div class="mal-icon">✅</div><div>No alerts generated.</div></div>`;

  // Batch children
  let batchHtml = "";
  if (d.file_type === "batch" && d.batch_files?.length) {
    batchHtml = `<h5 style="font-family:'Syne',sans-serif;font-size:13px;font-weight:700;color:var(--text);margin:16px 0 10px;">
                   <i class="fa-solid fa-layer-group" style="color:var(--accent);margin-right:6px;"></i>
                   Files in Batch (${d.batch_files.length})</h5>
      ${d.batch_files.map(f => {
        const fhaz = (f.counts.RoadDamages||0)+(f.counts.UnsurfacedRoad||0);
        return `<div style="display:flex;align-items:center;justify-content:space-between;
                             padding:10px 14px;background:var(--surface2);border-radius:var(--radius-sm);
                             margin-bottom:6px;font-size:13px;gap:12px;">
          <span style="color:var(--text);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
            <i class="fa-solid fa-file-image" style="color:var(--accent);margin-right:6px;"></i>${f.filename}
          </span>
          <span style="color:var(--text-muted);flex-shrink:0;">${Object.values(f.counts).reduce((a,b)=>a+b,0)} obj</span>
          ${fhaz>0
            ? `<span style="color:var(--danger);font-size:11px;font-weight:700;flex-shrink:0;">⚠ ${fhaz} hazard${fhaz>1?"s":""}</span>`
            : `<span style="color:var(--success);font-size:11px;font-weight:700;flex-shrink:0;">✅ Safe</span>`}
          <a href="${f.result_url}" target="_blank" class="btn btn-ghost btn-sm" style="flex-shrink:0;font-size:11px;">
            <i class="fa-solid fa-image"></i>
          </a>
        </div>`;
      }).join("")}`;
  }

  body.innerHTML = `
    ${imgsHtml}
    <div class="modal-counts">${countsHtml}</div>
    ${confHtml}
    <div class="modal-alerts">
      <h5 style="font-family:'Syne',sans-serif;font-size:13px;font-weight:700;color:var(--text);margin-bottom:10px;">
        <i class="fa-solid fa-triangle-exclamation" style="color:var(--accent);margin-right:6px;"></i>Alerts
      </h5>
      ${alertsHtml}
    </div>
    ${batchHtml}
    <div style="font-size:11px;color:var(--text-muted);margin-top:8px;">
      <i class="fa-solid fa-clock" style="margin-right:4px;"></i>${d.created_at}
      &nbsp;·&nbsp;
      <i class="fa-solid fa-tag" style="margin-right:4px;"></i>${cap(d.file_type)}
      &nbsp;·&nbsp; UID: ${d.uid}
    </div>`;

  footer.innerHTML = `
    ${d.pdf_id
      ? `<a href="/download-pdf/${d.pdf_id}" target="_blank" class="btn btn-primary btn-sm">
           <i class="fa-solid fa-file-pdf"></i> Download PDF</a>`
      : ""}
    <button class="btn btn-ghost btn-sm" style="color:var(--danger)"
            onclick="deleteAnalysis('${d.uid}',true)">
      <i class="fa-solid fa-trash"></i> Delete
    </button>
    <button class="btn btn-outline btn-sm" onclick="closeModalDirect()" style="margin-left:auto;">
      Close
    </button>`;
}

function closeModal(e) {
  if (e.target === document.getElementById("modal-backdrop")) closeModalDirect();
}
function closeModalDirect() {
  document.getElementById("modal-backdrop").classList.remove("open");
}

// ═══════════════════════════════════════════════════════
//  DELETE
// ═══════════════════════════════════════════════════════
async function deleteAnalysis(uid, fromModal=false) {
  if (!confirm("Delete this analysis from history?")) return;
  await fetch(`/api/history/${uid}`, {method:"DELETE"});
  if (fromModal) closeModalDirect();
  loadStats();
  loadHistory(currentPage);
}

// ═══════════════════════════════════════════════════════
//  UTIL
// ═══════════════════════════════════════════════════════
function cap(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : ""; }