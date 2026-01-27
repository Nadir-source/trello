from flask import Flask, redirect, url_for
from dotenv import load_dotenv
from config import SECRET_KEY

from admin_auth import admin_bp
from dashboard import dashboard_bp
from bookings_tab import bookings_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.register_blueprint(admin_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(bookings_bp)

@app.get("/")
def home():
    return redirect(url_for("dashboard.index"))

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(debug=True)
