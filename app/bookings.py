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
        # ton clients.py met full_name/phone/... dans le payload
        label = (p.get("full_name") or c.get("name") or "").strip()
        clients.append({
            "id": c["id"],
            "label": label,
            "full_name": p.get("full_name", label),
            "phone": p.get("phone", ""),
            "doc_id": p.get("doc_id", ""),
            "driver_license": p.get("driver_license", ""),
            "address": p.get("address", ""),
        })
    # tri alpha
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
            "plate": plate,
            "brand": brand,
            "model": model,
            "year": p.get("year", ""),
            "color": p.get("color", ""),
            "km": p.get("km", ""),
            "status": status,
        })

    # afficher disponibles en premier
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

    # ✅ NEW: on charge les listes pour le formulaire
    clients = _load_clients(t)
    vehicles = _load_vehicles(t)

    stats = {
        "demandes": len(demandes),
        "reserved": len(reserved),
        "ongoing": len(ongoing),
        "done": len(done),
        "clients": len(clients),
        "vehicles": len(vehicles),
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

    # soit tu passes un ID, soit un texte
    client_id = _g(form, "client_id")
    vehicle_id = _g(form, "vehicle_id")

    client_name = _g(form, "client_name", "client")
    vehicle_name = _g(form, "vehicle_name", "vehicle")

    start_date = _g(form, "start_date", "start")
    end_date = _g(form, "end_date", "end")

    pickup_location = _g(form, "pickup_location", "pickup", "lieu_remise")
    return_location = _g(form, "return_location", "dropoff", "lieu_retour")

    doc_type = _g(form, "doc_type", "document")
    notes = _g(form, "notes", "remarques")

    chauffeur = _gb(form, "opt_chauffeur", "chauffeur")
    gps = _gb(form, "opt_gps", "gps")
    baby_seat = _gb(form, "opt_baby_seat", "baby_seat", "siege_bebe")

    # titre fallback
    title = _g(form, "title", "name", default="Nouvelle réservation")
    if client_name and vehicle_name:
        title = f"{client_name} — {vehicle_name}"

    payload = {
        "_type": "booking",
        "title": title,
        "client_id": client_id,
        "vehicle_id": vehicle_id,
        "client_name": client_name,
        "vehicle_name": vehicle_name,
        "start_date": start_date,
        "end_date": end_date,
        "pickup_location": pickup_location,
        "return_location": return_location,
        "doc_type": doc_type,
        "notes": notes,
        "options": {
            "gps": gps,
            "chauffeur": chauffeur,
            "baby_seat": baby_seat,
        },
    }

    role, name = current_user()
    audit_add(payload, name, "booking_create", {"client": client_name, "vehicle": vehicle_name})

    t = Trello()
    t.create_booking_card(payload)

    flash("✅ Réservation créée (carte Trello).", "success")
    return redirect(url_for("bookings.index"))

