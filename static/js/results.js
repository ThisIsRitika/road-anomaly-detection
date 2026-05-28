// ─────────────────────────────────────────────
// results.js  —  Results page logic
// ─────────────────────────────────────────────

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('panel-' + tab.dataset.tab)?.classList.add('active');
  });
});

// ── Sidebar nav active state ──────────────────
// Mark "Alerts" nav item active when the alerts tab is open
function syncSidebarToTab(tabName) {
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  if (tabName === 'alerts') {
    document.getElementById('nav-alerts')?.classList.add('active');
  } else {
    // "Results" covers overview + detections tabs
    document.querySelector('.nav-item[href="/results"]')?.classList.add('active');
  }
}

// Hook tab clicks to also update sidebar highlight
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => syncSidebarToTab(tab.dataset.tab));
});

// ── Sidebar "Alerts" link ─────────────────────
// Always navigate to /results#alerts so it works
// whether or not an analysis has been run yet.
document.getElementById('nav-alerts')?.addEventListener('click', e => {
  e.preventDefault();
  // If we're already on the results page, just switch the tab
  const alertsTab = document.querySelector('[data-tab="alerts"]');
  if (alertsTab) {
    alertsTab.click();
    document.getElementById('alerts-anchor')?.scrollIntoView({ behavior: 'smooth' });
  } else {
    window.location.href = '/results#alerts';
  }
});

// ── Handle #alerts hash on page load ─────────
if (window.location.hash === '#alerts') {
  const alertsTab = document.querySelector('[data-tab="alerts"]');
  alertsTab?.click();
}

// Set initial sidebar state based on hash
syncSidebarToTab(window.location.hash === '#alerts' ? 'alerts' : 'overview');