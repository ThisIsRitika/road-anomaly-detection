from flask import Blueprint, jsonify, request
from ..database import get_history, get_analysis_detail, get_stats, delete_analysis

history_bp = Blueprint("history", __name__)


@history_bp.route("/api/history")
def api_history():
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 12))
    rows, total = get_history(
        limit=per_page, offset=(page-1)*per_page,
        severity =request.args.get("severity")  or None,
        file_type=request.args.get("file_type") or None,
        search   =request.args.get("search")    or None)
    return jsonify({"rows":rows, "total":total, "page":page,
                    "per_page":per_page,
                    "total_pages":max(1, -(-total // per_page))})


@history_bp.route("/api/history/stats")
def api_history_stats():
    stats, trend = get_stats()
    return jsonify({"stats":stats, "trend":trend})


@history_bp.route("/api/history/<uid>")
def api_history_detail(uid):
    d = get_analysis_detail(uid)
    if not d:
        return jsonify({"error": "Not found"}), 404
    return jsonify(d)


@history_bp.route("/api/history/<uid>", methods=["DELETE"])
def api_history_delete(uid):
    delete_analysis(uid)
    return jsonify({"deleted": uid})