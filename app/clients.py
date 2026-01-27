from flask import Blueprint, render_template, request, redirect, url_for
from app.auth import login_required, admin_required, current_user
from app.trello_client import Trello
from app.trello_schema import parse_payload, dump_payload, audit_add

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")

@clients_bp.get("")
@login_required
def index():
    t = Trello()
    cards = t.list_cards(__import__("app.config").config.LIST_CLIENTS)
    clients = []
    for c in cards:
        p = parse_payload(c.get("desc",""))
        clients.append({"id": c["id"], "title": c["name"], **p})
    return render_template("clients.html", clients=clients)

@clients_bp.post("/create")
@login_required
def create():
    # Agent peut créer un client (utile)
    t = Trello()
    full_name = request.form.get("full_name","").strip()
    phone = request.form.get("phone","").strip()
    doc_id = request.form.get("doc_id","").strip()
    driver_license = request.form.get("driver_license","").strip()
    address = request.form.get("address","").strip()

    payload = {
        "type": "client",
        "full_name": full_name,
        "phone": phone,
        "doc_id": doc_id,
        "driver_license": driver_license,
        "address": address,
        "notes": "",
        "blacklisted": False
    }
    role, name = current_user()
    audit_add(payload, name, "client_create", {"full_name": full_name})
    t.create_card(__import__("app.config").config.LIST_CLIENTS, full_name, dump_payload(payload))
    return redirect(url_for("clients.index"))
