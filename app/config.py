import os

# Base directory = the project root (one level above this file)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "static", "outputs")
PDF_FOLDER    = os.path.join(BASE_DIR, "static", "pdfs")
FRAMES_FOLDER = os.path.join(BASE_DIR, "static", "frames")
BATCH_FOLDER  = os.path.join(BASE_DIR, "static", "batch")

DB_PATH       = os.path.join(BASE_DIR, "rad_history.db")
MODEL_PATH    = os.path.join(BASE_DIR, "models", "pothole_yolov8_best.pt")

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

ALERT_THRESHOLDS = {"RoadDamages": 3, "UnsurfacedRoad": 2, "SpeedBump": 5}
HIGH_SEVERITY_CLASSES = {"RoadDamages", "UnsurfacedRoad"}

TRACKER_PALETTE = [
    (220,80,80),(80,180,80),(80,120,220),(220,180,40),(180,80,220),(40,200,200),
    (255,140,0),(0,200,160),(255,60,120),(160,255,80),(80,160,255),(255,200,40),
]

def track_color(tid: int):
    return TRACKER_PALETTE[tid % len(TRACKER_PALETTE)]

def ensure_folders():
    for f in [UPLOAD_FOLDER, OUTPUT_FOLDER, PDF_FOLDER, FRAMES_FOLDER, BATCH_FOLDER]:
        os.makedirs(f, exist_ok=True)