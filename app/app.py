from flask import Flask, redirect, url_for
from dotenv import load_dotenv
from app.config import SECRET_KEY

from app.auth import auth_bp
from app.dashboard import dashboard_bp
from app.vehicles import vehicles_bp
from app.clients import clients_bp
from app.bookings import bookings_bp
from app.finance import finance_bp
# app/app.py
from flask import Flask
# ...
from app.contracts import contracts_bp 

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(contracts_bp)

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
