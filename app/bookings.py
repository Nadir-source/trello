from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.auth import admin_required
from app.trello_client import Trello
import app.config as C

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")


def _bool(v) -> bool:
    return str(v).lower() in ("1", "true", "on", "yes", "y")


def _g(form, *names, default=""):
    """Get first non-empty value from request.form for multiple possible keys."""
    for n in names:
        v = (form.get(n) or "").strip()
        if v:
            return v
    return default


def _gb(form, *names) -> bool:
    """Get boolean from checkbox names."""
    for n in names:
        if n in form:
            return str(form.get(n)).lower() in ("1", "true", "on", "yes", "y")
    return False


@bookings_bp.get("/")
@admin_required
def index():
    t = Trello()

    demandes = t.list_cards(C.LIST_DEMANDES)
    reserved = t.list_cards(C.LIST_RESERVED)
    ongoing = t.list_cards(C.LIST_ONGOING)
    done = t.list_cards(C.LIST_DONE)

    # ✅ IMPORTANT: ton template bookings.html utilise stats.*
    stats = {
        "demandes": len(demandes),
        "reserved": len(reserved),
        "ongoing": len(ongoing),
        "done": len(done),
    }

    return render_template(
        "bookings.html",
        stats=stats,
        demandes=demandes,
        reserved=reserved,
        ongoing=ongoing,
        done=done,
    )


@bookings_bp.post("/create")
@admin_required
def create():
    form = request.form

    title = _g(form, "title", "name", default="Nouvelle réservation")
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

    payload = {
        "title": title,
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

    # Debug Render logs (super utile)
    print("FORM DATA:", dict(form))
    print("BOOKING PAYLOAD:", payload)

    t = Trello()
    t.create_booking_card(payload)

    flash("✅ Demande créée dans Trello.", "success")
    return redirect(url_for("bookings.index"))


@bookings_bp.post("/move/<card_id>/<target>")
@admin_required
def move(card_id: str, target: str):
    t = Trello()

    mapping = {
        "demandes": C.LIST_DEMANDES,
        "reserved": C.LIST_RESERVED,
        "ongoing": C.LIST_ONGOING,
        "done": C.LIST_DONE,
        "cancel": C.LIST_CANCEL,      # alias dans config.py
        "canceled": C.LIST_CANCELED,
    }

    if target not in mapping:
        flash("❌ Action inconnue.", "error")
        return redirect(url_for("bookings.index"))

    t.move_card(card_id, mapping[target])
    flash("✅ Carte déplacée.", "success")
    return redirect(url_for("bookings.index"))

