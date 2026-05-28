from ultralytics import YOLO
from .config import MODEL_PATH

# Loaded once; shared across all blueprints
yolo = YOLO(MODEL_PATH)