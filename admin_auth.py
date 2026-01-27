from functools import wraps
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from config import ADMIN_PASSWORD

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin.login"))
        return fn(*args, **kwargs)
    return wrapper

@admin_bp.get("/login")
def login():
    return render_template("login.html")

@admin_bp.post("/login")
def login_post():
    if request.form.get("password", "") == ADMIN_PASSWORD:
        session["is_admin"] = True
        return redirect(url_for("dashboard.index"))
    flash("Mot de passe incorrect", "error")
    return redirect(url_for("admin.login"))

@admin_bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin.login"))
