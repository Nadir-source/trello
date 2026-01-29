from flask import Flask, redirect, url_for
from dotenv import load_dotenv

from app.config import SECRET_KEY

from app.auth import auth_bp
from app.dashboard import dashboard_bp
from app.vehicles import vehicles_bp
from app.clients import clients_bp
from app.bookings import bookings_bp
from app.finance import finance_bp
from app.contracts import contracts_bp

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    # Register blueprints safely (évite les doublons)
    def register_bp(bp):
        if bp.name in app.blueprints:
            return
        app.register_blueprint(bp)

    register_bp(auth_bp)
    register_bp(dashboard_bp)
    register_bp(vehicles_bp)
    register_bp(clients_bp)
    register_bp(bookings_bp)
    register_bp(finance_bp)
    register_bp(contracts_bp)

    @app.get("/")
    def home():
        return redirect(url_for("dashboard.index"))

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

