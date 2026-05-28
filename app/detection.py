import os, cv2
from .config import (CLASS_COLORS, ALERT_THRESHOLDS, HIGH_SEVERITY_CLASSES,
                     MAX_SAMPLE_FRAMES, CONF_THRESHOLD, FRAMES_FOLDER, track_color)
from .model import yolo


# ── Alerts ────────────────────────────────────────────────────────────────────

def compute_alerts(counts):
    alerts = []
    total_hazards = counts.get("RoadDamages", 0) + counts.get("UnsurfacedRoad", 0)
    if counts.get("RoadDamages", 0) >= ALERT_THRESHOLDS["RoadDamages"]:
        alerts.append({"level":"critical","icon":"⚠️",
            "message":f"HIGH HAZARD: {counts['RoadDamages']} road damage zones. Immediate maintenance required."})
    elif counts.get("RoadDamages", 0) > 0:
        alerts.append({"level":"warning","icon":"🔶",
            "message":f"{counts['RoadDamages']} road damage area(s) detected. Inspection recommended."})
    if counts.get("UnsurfacedRoad", 0) >= ALERT_THRESHOLDS["UnsurfacedRoad"]:
        alerts.append({"level":"critical","icon":"🚧",
            "message":f"CRITICAL: {counts['UnsurfacedRoad']} unsurfaced road sections. High accident risk."})
    elif counts.get("UnsurfacedRoad", 0) > 0:
        alerts.append({"level":"warning","icon":"🔶",
            "message":f"{counts['UnsurfacedRoad']} unsurfaced road section(s) found."})
    if total_hazards == 0 and any(counts.values()):
        alerts.append({"level":"safe","icon":"✅",
            "message":"No critical road surface hazards detected. Road appears safe."})
    return alerts


# ── Confidence summary ────────────────────────────────────────────────────────

def summarise_conf(conf_map):
    out = {}
    for cls, vals in conf_map.items():
        if vals:
            out[cls] = {"avg":round(sum(vals)/len(vals),1),
                        "min":round(min(vals),1),
                        "max":round(max(vals),1),
                        "all":vals}
    return out


# ── Shared drawing helper ─────────────────────────────────────────────────────

def _draw_box(img, x1, y1, x2, y2, color, text):
    cv2.rectangle(img, (x1,y1), (x2,y2), color, 2)
    (tw,th),_ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.50, 1)
    cv2.rectangle(img, (x1,y1-th-8), (x1+tw+6,y1), color, -1)
    cv2.putText(img, text, (x1+3,y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255,255,255), 1)


# ── Image ─────────────────────────────────────────────────────────────────────

def process_image(filepath):
    results  = yolo(filepath, conf=CONF_THRESHOLD, imgsz=416)[0]
    img      = cv2.imread(filepath)
    counts   = {k: 0  for k in CLASS_COLORS}
    conf_map = {k: [] for k in CLASS_COLORS}
    for box in results.boxes:
        cls_id   = int(box.cls[0])
        label    = yolo.names[cls_id]
        conf_val = float(box.conf[0])
        if label in counts:
            counts[label]   += 1
            conf_map[label].append(round(conf_val*100, 1))
        x1,y1,x2,y2 = map(int, box.xyxy[0])
        _draw_box(img, x1, y1, x2, y2,
                  CLASS_COLORS.get(label,(0,255,0)),
                  f"{label}  {conf_val*100:.0f}%")
    return img, counts, conf_map


# ── Video (standard) ──────────────────────────────────────────────────────────

def process_video(filepath, output_path, uid):
    cap   = cv2.VideoCapture(filepath)
    w     = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h     = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    step  = max(1, total // MAX_SAMPLE_FRAMES)
    sample_indices = list(range(0,total,step))[:MAX_SAMPLE_FRAMES]

    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), # type: ignore
                          max(4,min(10,len(sample_indices)//4)), (w,h))
    max_counts   = {k:0  for k in CLASS_COLORS}
    all_conf_map = {k:[] for k in CLASS_COLORS}
    best_frame, best_hazards = None, -1

    for idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret: continue
        results = yolo(frame, verbose=False, conf=CONF_THRESHOLD, imgsz=416)[0]
        fc = {k:0 for k in CLASS_COLORS}
        for box in results.boxes:
            cls_id   = int(box.cls[0])
            label    = yolo.names[cls_id]
            conf_val = float(box.conf[0])
            if label in fc:
                fc[label] += 1
                all_conf_map[label].append(round(conf_val*100,1))
            x1,y1,x2,y2 = map(int,box.xyxy[0])
            _draw_box(frame, x1, y1, x2, y2,
                      CLASS_COLORS.get(label,(0,255,0)),
                      f"{label}  {conf_val*100:.0f}%")
        cv2.putText(frame, f"Frame {idx}/{total}", (10,28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255,255,255), 2)
        out.write(frame)
        for k in CLASS_COLORS:
            if fc[k] > max_counts[k]: max_counts[k] = fc[k]
        hz = fc.get("RoadDamages",0)+fc.get("UnsurfacedRoad",0)
        if hz > best_hazards: best_hazards=hz; best_frame=frame.copy()

    cap.release(); out.release()
    thumb_path = _save_thumb(filepath, sample_indices, best_frame, uid, "_thumb.jpg")
    return max_counts, thumb_path, all_conf_map


# ── Video (ByteTrack) ─────────────────────────────────────────────────────────

def process_video_tracked(filepath, output_path, uid):
    cap   = cv2.VideoCapture(filepath)
    w     = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h     = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    step  = max(1, total // MAX_SAMPLE_FRAMES)
    sample_indices = list(range(0,total,step))[:MAX_SAMPLE_FRAMES]

    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), # type: ignore
                          max(4,min(10,len(sample_indices)//4)), (w,h))
    max_counts   = {k:0  for k in CLASS_COLORS}
    all_conf_map = {k:[] for k in CLASS_COLORS}
    best_frame, best_hazards = None, -1

    for idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret: continue
        results = yolo.track(frame, persist=True, verbose=False,
                             conf=CONF_THRESHOLD, tracker="bytetrack.yaml", imgsz=416)[0]
        fc = {k:0 for k in CLASS_COLORS}
        if results.boxes is not None:
            for box in results.boxes:
                cls_id   = int(box.cls[0])
                label    = yolo.names[cls_id]
                conf_val = float(box.conf[0])
                tid      = int(box.id[0]) if box.id is not None else 0
                if label in fc:
                    fc[label] += 1
                    all_conf_map[label].append(round(conf_val*100,1))
                x1,y1,x2,y2 = map(int,box.xyxy[0])
                _draw_box(frame, x1, y1, x2, y2, track_color(tid),
                          f"{label} #{tid}  {conf_val*100:.0f}%")
        cv2.putText(frame, f"Frame {idx}/{total}  [TRACKED]", (10,28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255,255,255), 2)
        out.write(frame)
        for k in CLASS_COLORS:
            if fc[k] > max_counts[k]: max_counts[k] = fc[k]
        hz = fc.get("RoadDamages",0)+fc.get("UnsurfacedRoad",0)
        if hz > best_hazards: best_hazards=hz; best_frame=frame.copy()

    cap.release(); out.release()
    thumb_path = _save_thumb(filepath, sample_indices, best_frame, uid, "_track_thumb.jpg")
    return max_counts, thumb_path, all_conf_map


# ── Live webcam MJPEG generator ───────────────────────────────────────────────

def webcam_frame_generator(active_ref, counts_ref=None):
    """Yields MJPEG byte frames while active_ref[0] is True.
    counts_ref: optional dict updated with per-frame counts each frame.
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened(): return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    while active_ref[0]:
        ret, frame = cap.read()
        if not ret: break
        results = yolo.track(frame, persist=True, verbose=False,
                             conf=CONF_THRESHOLD, tracker="bytetrack.yaml", imgsz=416)[0]
        fc = {k:0 for k in CLASS_COLORS}; hz = 0
        if results.boxes is not None:
            for box in results.boxes:
                cls_id   = int(box.cls[0])
                label    = yolo.names[cls_id]
                conf_val = float(box.conf[0])
                tid      = int(box.id[0]) if box.id is not None else 0
                if label in fc: fc[label] += 1
                if label in HIGH_SEVERITY_CLASSES: hz += 1
                x1,y1,x2,y2 = map(int,box.xyxy[0])
                _draw_box(frame, x1, y1, x2, y2, track_color(tid),
                          f"{label} #{tid}  {conf_val*100:.0f}%")

        # Push current frame counts to shared dict so /webcam/counts can serve them
        if counts_ref is not None:
            for k in CLASS_COLORS:
                counts_ref[k] = fc[k]

        hud = [f"HMV:{fc['HMV']}  LMV:{fc['LMV']}  Ped:{fc['Pedestrian']}",
               f"Dmg:{fc['RoadDamages']}  Bump:{fc['SpeedBump']}  Unsfcd:{fc['UnsurfacedRoad']}"]
        y_h = 55; ov = frame.copy()
        cv2.rectangle(ov, (8,36), (420,36+len(hud)*24+10), (0,0,0), -1)
        cv2.addWeighted(ov, 0.55, frame, 0.45, 0, frame)
        for line in hud:
            cv2.putText(frame, line, (14,y_h), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (255,255,255), 1)
            y_h += 24
        if hz > 0:
            hf = frame.shape[0]; ov2 = frame.copy()
            cv2.rectangle(ov2, (0,hf-44), (frame.shape[1],hf), (0,0,180), -1)
            cv2.addWeighted(ov2, 0.6, frame, 0.4, 0, frame)
            cv2.putText(frame, f"HAZARD DETECTED: {hz} zone(s)", (14,hf-14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.70, (255,255,255), 2)

        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"

    cap.release()


# ── Internal ──────────────────────────────────────────────────────────────────

def _save_thumb(filepath, sample_indices, best_frame, uid, suffix):
    if best_frame is None:
        cap2 = cv2.VideoCapture(filepath)
        cap2.set(cv2.CAP_PROP_POS_FRAMES, sample_indices[-1] if sample_indices else 0)
        _, best_frame = cap2.read(); cap2.release()
    if best_frame is None: return None
    path = os.path.join(FRAMES_FOLDER, uid + suffix)
    cv2.imwrite(path, best_frame)
    return path