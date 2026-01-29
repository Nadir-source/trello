from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.auth import admin_required, current_user
from app.trello_client import Trello
from app.trello_schema import parse_payload, audit_add
import app.config as C

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")


def _g(form, *names, default=""):
    for n in names:
        v = (form.get(n) or "").strip()
        if v:
            return v
    return default


def _gb(form, *names) -> bool:
    for n in names:
        if n in form:
            return str(form.get(n)).lower() in ("1", "true", "on", "yes", "y")
    return False


def _load_clients(t: Trello):
    cards = t.list_cards(C.LIST_CLIENTS)
    clients = []
    for c in cards:
        p = parse_payload(c.get("desc", ""))
        label = (p.get("full_name") or c.get("name") or "").strip()
        clients.append({
            "id": c["id"],
            "label": label,
            "full_name": p.get("full_name", label),
            "phone": p.get("phone", ""),
        })
    clients.sort(key=lambda x: (x.get("label") or "").lower())
    return clients


def _load_vehicles(t: Trello):
    cards = t.list_cards(C.LIST_VEHICLES)
    vehicles = []
    for c in cards:
        p = parse_payload(c.get("desc", ""))
        plate = (p.get("plate") or "").strip()
        brand = (p.get("brand") or "").strip()
        model = (p.get("model") or "").strip()
        status = (p.get("status") or "AVAILABLE").strip().upper()

        label = c.get("name", "").strip()
        if plate or brand or model:
            label = f"{plate} — {brand} {model}".strip()

        vehicles.append({
            "id": c["id"],
            "label": label,
            "status": status,
        })

    vehicles.sort(key=lambda x: (x.get("status") != "AVAILABLE", (x.get("label") or "").lower()))
    return vehicles


@bookings_bp.get("/")
@admin_required
def index():
    t = Trello()

    demandes = t.list_cards(C.LIST_DEMANDES)
    reserved = t.list_cards(C.LIST_RESERVED)
    ongoing = t.list_cards(C.LIST_ONGOING)
    done = t.list_cards(C.LIST_DONE)

    clients = _load_clients(t)
    vehicles = _load_vehicles(t)

    stats = {
        "demandes": len(demandes),
        "reserved": len(reserved),
        "ongoing": len(ongoing),
        "done": len(done),
        "clients": len(clients),
        "vehicles_available": sum(1 for v in vehicles if v.get("status") == "AVAILABLE"),
    }

    return render_template(
        "bookings.html",
        stats=stats,
        demandes=demandes,
        reserved=reserved,
        ongoing=ongoing,
        done=done,
        clients=clients,
        vehicles=vehicles,
    )


@bookings_bp.post("/create")
@admin_required
def create():
    form = request.form

    client_id = _g(form, "client_id")
    vehicle_id = _g(form, "vehicle_id")

    start_date = _g(form, "start_date")
    end_date = _g(form, "end_date")

    pickup_location = _g(form, "pickup_location")
    return_location = _g(form, "return_location")

    doc_type = _g(form, "doc_type", default="CNI")
    notes = _g(form, "notes")

    gps = _gb(form, "opt_gps")
    chauffeur = _gb(form, "opt_chauffeur")
    baby_seat = _gb(form, "opt_baby_seat")

    # On peut aussi envoyer les noms, mais l'ID suffit
    payload = {
        "_type": "booking",
        "client_id": client_id,
        "vehicle_id": vehicle_id,
        "start_date": start_date,
        "end_date": end_date,
        "pickup_location": pickup_location,
        "return_location": return_location,
        "doc_type": doc_type,
        "notes": notes,
        "options": {"gps": gps, "chauffeur": chauffeur, "baby_seat": baby_seat},
    }

    role, name = current_user()
    audit_add(payload, name, "booking_create", {"client_id": client_id, "vehicle_id": vehicle_id})

    t = Trello()
    t.create_booking_card(payload)

    flash("✅ Réservation créée.", "success")
    return redirect(url_for("bookings.index"))

