from flask import Flask
from .config import ensure_folders
from .database import init_db


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

    return app