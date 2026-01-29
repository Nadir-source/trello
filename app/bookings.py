from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.auth import admin_required
from app.trello_client import Trello
import app.config as C

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")


def _bool(v) -> bool:
    return str(v).lower() in ("1", "true", "on", "yes", "y")


@bookings_bp.get("/")
@admin_required
def index():
    t = Trello()

    demandes = t.list_cards(C.LIST_DEMANDES)
    reserved = t.list_cards(C.LIST_RESERVED)
    ongoing = t.list_cards(C.LIST_ONGOING)
    done = t.list_cards(C.LIST_DONE)

    return render_template(
        "bookings.html",
        demandes=demandes,
        reserved=reserved,
        ongoing=ongoing,
        done=done,
    )


@bookings_bp.post("/create")
@admin_required
def create():
    # Champs venant du formulaire
    title = (request.form.get("title") or "").strip() or "Nouvelle réservation"
    client_name = (request.form.get("client_name") or "").strip()
    vehicle_name = (request.form.get("vehicle_name") or "").strip()

    # Dates (tu peux envoyer "2026-01-29" ou "2026-01-29T10:30")
    start_date = (request.form.get("start_date") or "").strip()
    end_date = (request.form.get("end_date") or "").strip()

    pickup_location = (request.form.get("pickup_location") or "").strip()
    return_location = (request.form.get("return_location") or "").strip()

    doc_type = (request.form.get("doc_type") or "").strip()  # ex: "CNI", "Passport"
    notes = (request.form.get("notes") or "").strip()

    # Options
    chauffeur = _bool(request.form.get("opt_chauffeur"))
    gps = _bool(request.form.get("opt_gps"))
    baby_seat = _bool(request.form.get("opt_baby_seat"))

    # ✅ Payload JSON stable (le PDF va lire EXACTEMENT ça)
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
            "chauffeur": chauffeur,
            "gps": gps,
            "baby_seat": baby_seat,
        },
    }

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
        "cancel": C.LIST_CANCEL,   # alias OK dans config.py
        "canceled": C.LIST_CANCELED,
    }

    if target not in mapping:
        flash("❌ Action inconnue.", "error")
        return redirect(url_for("bookings.index"))

    t.move_card(card_id, mapping[target])
    flash("✅ Carte déplacée.", "success")
    return redirect(url_for("bookings.index"))

