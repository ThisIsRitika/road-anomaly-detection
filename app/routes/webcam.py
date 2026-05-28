from flask import Blueprint, jsonify, Response, stream_with_context
from ..detection import webcam_frame_generator

webcam_bp = Blueprint("webcam", __name__)
_active = [False]   # mutable ref passed into generator

# Shared state: generator writes here each frame, /webcam/counts reads it
_latest_counts = {
    "HMV": 0, "LMV": 0, "Pedestrian": 0,
    "RoadDamages": 0, "SpeedBump": 0, "UnsurfacedRoad": 0
}


@webcam_bp.route("/webcam/start", methods=["POST"])
def webcam_start():
    _active[0] = True
    for k in _latest_counts:          # reset on each new session
        _latest_counts[k] = 0
    return jsonify({"status": "started"})


@webcam_bp.route("/webcam/stop", methods=["POST"])
def webcam_stop():
    _active[0] = False
    return jsonify({"status": "stopped"})


@webcam_bp.route("/webcam/counts")
def webcam_counts():
    return jsonify(_latest_counts)


@webcam_bp.route("/webcam/feed")
def webcam_feed():
    return Response(
        stream_with_context(webcam_frame_generator(_active, _latest_counts)),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )