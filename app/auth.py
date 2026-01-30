# app/auth.py
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.config import ADMIN_PASSWORD, AGENT_PASSWORD

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ======================
# Helpers
# ======================
def current_user():
    return session.get("user_role"), session.get("user_name", "")


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_role"):
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("user_role") != "admin":
            flash("Accès réservé à l’administrateur.", "error")
            return redirect(url_for("bookings.index"))
        return fn(*args, **kwargs)
    return wrapper


def staff_required(fn):
    """
    Autorise admin OU agent
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("user_role") not in ("admin", "agent"):
            flash("Connexion requise.", "error")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper


# ======================
# Routes auth
# ======================
@auth_bp.get("/login")
def login():
    return render_template("login.html")


@auth_bp.post("/login")
def login_post():
    role = request.form.get("role", "agent")
    password = request.form.get("password", "")
    name = request.form.get("name", "").strip() or ("Admin" if role == "admin" else "Agent")

    if role == "admin" and password == ADMIN_PASSWORD:
        session["user_role"] = "admin"
        session["user_name"] = name
        return redirect(url_for("dashboard.index"))

    if role == "agent" and password == AGENT_PASSWORD:
        session["user_role"] = "agent"
        session["user_name"] = name
        return redirect(url_for("dashboard.index"))

    flash("Login incorrect", "error")
    return redirect(url_for("auth.login"))


@auth_bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

