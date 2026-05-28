import os, uuid, zipfile, cv2
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from ..config import (IS_PROD, UPLOAD_FOLDER, OUTPUT_FOLDER,
                      BATCH_FOLDER, CLASS_COLORS)
from ..detection import (process_image, process_video, process_video_tracked,
                         compute_alerts, summarise_conf)
from ..pdf_report import generate_pdf
from ..database   import save_analysis, save_batch_files

predict_bp = Blueprint("predict", __name__)
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def file_url(abs_path: str) -> str:
    """
    Convert an absolute file path to a browser-accessible URL.

    Production (Render):
        /tmp/rad/outputs/abc_out.jpg  →  /files/outputs/abc_out.jpg
        served by main_bp.serve_file()

    Local:
        /path/to/project/static/outputs/abc_out.jpg  →  /static/outputs/abc_out.jpg
        served by Flask's built-in static handler
    """
    if IS_PROD:
        # Strip the /tmp/rad prefix; the /files route handles the rest
        rel = os.path.relpath(abs_path, "/tmp/rad")
        return "/files/" + rel.replace("\\", "/")
    else:
        # Strip everything up to and including "static/"
        parts = abs_path.replace("\\", "/").split("static/", 1)
        return "/static/" + parts[-1]


# ── Single file ───────────────────────────────────────────────────────────────

@predict_bp.route("/predict", methods=["POST"])
def predict():
    file      = request.files["file"]
    orig_name = file.filename
    ext       = os.path.splitext(orig_name)[1].lower()
    uid       = str(uuid.uuid4())[:8]
    filepath  = os.path.join(UPLOAD_FOLDER, uid + ext)
    file.save(filepath)

    is_video  = ext in VIDEO_EXTS
    thumb_url = None

    if is_video:
        output_path = os.path.join(OUTPUT_FOLDER, uid + "_out.mp4")
        counts, thumb_path, conf_map = process_video(filepath, output_path, uid)
        result_url = file_url(output_path)
        file_type  = "video"
        if thumb_path:
            thumb_url = file_url(thumb_path)
    else:
        output_path = os.path.join(OUTPUT_FOLDER, uid + "_out" + ext)
        img, counts, conf_map = process_image(filepath)
        cv2.imwrite(output_path, img)
        result_url = file_url(output_path)
        file_type  = "image"

    conf_summary = summarise_conf(conf_map)
    alerts       = compute_alerts(counts)
    generate_pdf(counts, alerts, file_type, filepath, output_path, uid,
                 video_mode=is_video, conf_summary=conf_summary)
    save_analysis(uid, file_type, orig_name, counts, alerts, conf_summary,
                  result_url, file_url(filepath),
                  thumb_url=thumb_url, pdf_id=uid)

    payload = {
        "result_url":   result_url,
        "original_url": file_url(filepath),
        "thumb_url":    thumb_url,
        "file_type":    file_type,
        "counts":       counts,
        "alerts":       alerts,
        "conf_summary": conf_summary,
        "pdf_id":       uid,
        "timestamp":    datetime.now().strftime("%B %d, %Y at %H:%M:%S"),
    }
    session["last_result"] = payload
    return jsonify(payload)


# ── Single file (tracked) ─────────────────────────────────────────────────────

@predict_bp.route("/predict_tracked", methods=["POST"])
def predict_tracked():
    file      = request.files["file"]
    orig_name = file.filename
    ext       = os.path.splitext(orig_name)[1].lower()
    uid       = str(uuid.uuid4())[:8]
    filepath  = os.path.join(UPLOAD_FOLDER, uid + ext)
    file.save(filepath)

    is_video  = ext in VIDEO_EXTS
    thumb_url = None

    if is_video:
        output_path = os.path.join(OUTPUT_FOLDER, uid + "_tracked_out.mp4")
        counts, thumb_path, conf_map = process_video_tracked(filepath, output_path, uid)
        result_url = file_url(output_path)
        file_type  = "video"
        if thumb_path:
            thumb_url = file_url(thumb_path)
    else:
        output_path = os.path.join(OUTPUT_FOLDER, uid + "_out" + ext)
        img, counts, conf_map = process_image(filepath)
        cv2.imwrite(output_path, img)
        result_url = file_url(output_path)
        file_type  = "image"

    conf_summary = summarise_conf(conf_map)
    alerts       = compute_alerts(counts)
    generate_pdf(counts, alerts, file_type, filepath, output_path, uid,
                 video_mode=is_video, conf_summary=conf_summary)
    save_analysis(uid, file_type, orig_name, counts, alerts, conf_summary,
                  result_url, file_url(filepath),
                  thumb_url=thumb_url, pdf_id=uid)

    payload = {
        "result_url":   result_url,
        "original_url": file_url(filepath),
        "thumb_url":    thumb_url,
        "file_type":    file_type,
        "counts":       counts,
        "alerts":       alerts,
        "conf_summary": conf_summary,
        "pdf_id":       uid,
        "tracked":      True,
        "timestamp":    datetime.now().strftime("%B %d, %Y at %H:%M:%S"),
    }
    session["last_result"] = payload
    return jsonify(payload)


# ── Batch ─────────────────────────────────────────────────────────────────────

@predict_bp.route("/predict_batch", methods=["POST"])
def predict_batch():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files"}), 400

    batch_uid  = str(uuid.uuid4())[:8]
    batch_dir  = os.path.join(BATCH_FOLDER, batch_uid)
    os.makedirs(batch_dir, exist_ok=True)

    results_list   = []
    total_counts   = {k: 0  for k in CLASS_COLORS}
    all_conf_accum = {k: [] for k in CLASS_COLORS}
    annotated_paths = []

    for f in files:
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
            continue
        uid      = str(uuid.uuid4())[:8]
        filepath = os.path.join(UPLOAD_FOLDER, uid + ext)
        f.save(filepath)
        img, counts, conf_map = process_image(filepath)
        out_path = os.path.join(batch_dir, uid + "_out" + ext)
        cv2.imwrite(out_path, img)
        annotated_paths.append(out_path)
        conf_summary = summarise_conf(conf_map)
        alerts       = compute_alerts(counts)
        for k in CLASS_COLORS:
            total_counts[k]   += counts.get(k, 0)
            all_conf_accum[k] += conf_map.get(k, [])
        results_list.append({
            "filename":    f.filename,
            "result_url":  file_url(out_path),
            "original_url":file_url(filepath),
            "counts":      counts,
            "alerts":      alerts,
            "conf_summary":conf_summary,
        })

    if not results_list:
        return jsonify({"error": "No valid images"}), 400

    combined_conf   = summarise_conf(all_conf_accum)
    combined_alerts = compute_alerts(total_counts)
    generate_pdf(total_counts, combined_alerts, "batch (images)", "", "",
                 batch_uid, conf_summary=combined_conf)

    zip_path = os.path.join(BATCH_FOLDER, f"batch_{batch_uid}_annotated.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in annotated_paths:
            zf.write(p, os.path.basename(p))

    save_analysis(batch_uid, "batch", f"Batch ({len(results_list)} images)",
                  total_counts, combined_alerts, combined_conf,
                  f"/batch/download-zip/{batch_uid}", "", pdf_id=batch_uid)
    save_batch_files(batch_uid, results_list)

    payload = {
        "batch_uid":       batch_uid,
        "file_count":      len(results_list),
        "results":         results_list,
        "total_counts":    total_counts,
        "combined_alerts": combined_alerts,
        "combined_conf":   combined_conf,
        "pdf_id":          batch_uid,
        "zip_url":         f"/batch/download-zip/{batch_uid}",
        "timestamp":       datetime.now().strftime("%B %d, %Y at %H:%M:%S"),
    }
    session["last_batch"] = payload
    return jsonify(payload)