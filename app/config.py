import os

# ── Environment detection ──────────────────────────────────────────────────────
# Render automatically sets the RENDER environment variable.
IS_PROD = os.environ.get("RENDER") is not None

# ── Base directory (project root, one level above this file) ──────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── File-storage paths ────────────────────────────────────────────────────────
# On Render, only /tmp is writable at runtime.
# Locally, we keep everything inside static/ as before.
if IS_PROD:
    _STORE = "/tmp/rad"
else:
    _STORE = os.path.join(BASE_DIR, "static")

UPLOAD_FOLDER = os.path.join(_STORE, "uploads")
OUTPUT_FOLDER = os.path.join(_STORE, "outputs")
PDF_FOLDER    = os.path.join(_STORE, "pdfs")
FRAMES_FOLDER = os.path.join(_STORE, "frames")
BATCH_FOLDER  = os.path.join(_STORE, "batch")

# DB also needs to live in /tmp on Render (static/ is read-only)
DB_PATH    = "/tmp/rad_history.db" if IS_PROD else os.path.join(BASE_DIR, "rad_history.db")

# Model lives in the repo — read-only is fine here
MODEL_PATH = os.path.join(BASE_DIR, "models", "pothole_yolov8_best.pt")

# ── Detection settings ────────────────────────────────────────────────────────
MAX_SAMPLE_FRAMES = 40
CONF_THRESHOLD    = 0.35

CLASS_COLORS = {
    "HMV":            (220, 80,  80),
    "LMV":            (80,  180, 80),
    "Pedestrian":     (80,  120, 220),
    "RoadDamages":    (220, 180, 40),
    "SpeedBump":      (180, 80,  220),
    "UnsurfacedRoad": (40,  200, 200),
}

ALERT_THRESHOLDS     = {"RoadDamages": 3, "UnsurfacedRoad": 2, "SpeedBump": 5}
HIGH_SEVERITY_CLASSES = {"RoadDamages", "UnsurfacedRoad"}

TRACKER_PALETTE = [
    (220, 80, 80), (80, 180, 80),  (80, 120, 220), (220, 180, 40),
    (180, 80, 220),(40, 200, 200), (255, 140, 0),  (0,  200, 160),
    (255, 60, 120),(160, 255, 80), (80, 160, 255), (255, 200, 40),
]

def track_color(tid: int):
    return TRACKER_PALETTE[tid % len(TRACKER_PALETTE)]

def ensure_folders():
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, PDF_FOLDER,
                   FRAMES_FOLDER, BATCH_FOLDER]:
        os.makedirs(folder, exist_ok=True)