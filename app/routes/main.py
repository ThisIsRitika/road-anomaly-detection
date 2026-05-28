import os
from flask import Blueprint, render_template, session, send_file
from ..config import PDF_FOLDER, BATCH_FOLDER

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template("index.html")


@main_bp.route("/results")
def results_page():
    data = session.get("last_result")
    if not data:
        return render_template("results.html", no_data=True)
    return render_template("results.html", no_data=False, data=data)


@main_bp.route("/live")
def live_page():
    return render_template("live.html")


@main_bp.route("/history")
def history_page():
    return render_template("history.html")


@main_bp.route("/download-pdf/<uid>")
def download_pdf(uid):
    pdf_path = os.path.join(PDF_FOLDER, f"report_{uid}.pdf")
    if not os.path.exists(pdf_path):
        return "PDF not found", 404
    return send_file(pdf_path, as_attachment=True,
                     download_name=f"road_anomaly_report_{uid}.pdf")


@main_bp.route("/batch/download-zip/<batch_uid>")
def download_batch_zip(batch_uid):
    zip_path = os.path.join(BATCH_FOLDER, f"batch_{batch_uid}_annotated.zip")
    if not os.path.exists(zip_path):
        return "ZIP not found", 404
    return send_file(zip_path, as_attachment=True,
                     download_name=f"rad_batch_{batch_uid}.zip")