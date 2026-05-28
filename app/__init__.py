import logging
import traceback
from flask import Flask, jsonify
from .config import ensure_folders
from .database import init_db

logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.secret_key = "rad-ai-secret-key-2024"

    ensure_folders()
    init_db()

    from .routes.main    import main_bp
    from .routes.predict import predict_bp
    from .routes.webcam  import webcam_bp
    from .routes.history import history_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(webcam_bp)
    app.register_blueprint(history_bp)

    # ── Log every unhandled exception so Render shows it in logs ──────────────
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error("Unhandled exception:\n%s", traceback.format_exc())
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

    return app