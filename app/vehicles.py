from flask import Blueprint, render_template, request, redirect, url_for
from app.auth import login_required, admin_required, current_user
from app.trello_client import Trello
from app.trello_schema import parse_payload, dump_payload, audit_add

vehicles_bp = Blueprint("vehicles", __name__, url_prefix="/vehicles")

@vehicles_bp.get("")
@login_required
def index():
    t = Trello()
    cards = t.list_cards(__import__("app.config").config.LIST_VEHICLES)
    vehicles = []
    for c in cards:
        p = parse_payload(c.get("desc",""))
        vehicles.append({"id": c["id"], "title": c["name"], **p})
    return render_template("vehicles.html", vehicles=vehicles)

@vehicles_bp.post("/create")
@login_required
@admin_required
def create():
    t = Trello()
    plate = request.form.get("plate","").strip()
    brand = request.form.get("brand","").strip()
    model = request.form.get("model","").strip()
    year = request.form.get("year","").strip()
    color = request.form.get("color","").strip()
    km = request.form.get("km","0").strip()

    payload = {
        "type": "vehicle",
        "plate": plate,
        "brand": brand,
        "model": model,
        "year": int(year) if year.isdigit() else None,
        "color": color,
        "km": int(km) if km.isdigit() else 0,
        "status": "AVAILABLE",
        "insurance_expiry": "",
        "technical_control_expiry": "",
        "notes": ""
    }
    role, name = current_user()
    audit_add(payload, name, "vehicle_create", {"plate": plate})
    title = f"{plate} — {brand} {model}".strip()
    t.create_card(__import__("app.config").config.LIST_VEHICLES, title, dump_payload(payload))
    return redirect(url_for("vehicles.index"))
