# app/bookings.py
from __future__ import annotations

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from app.auth import login_required, admin_required, current_user
from app.trello_client import Trello
from app.trello_schema import parse_payload, dump_payload, audit_add
from app.pdf_generator import build_contract_pdf
from app import config as C

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")


def _as_booking(card: dict) -> dict:
    p = parse_payload(card.get("desc", ""))
    return {
        "id": card["id"],
        "name": card.get("name", ""),
        "desc": card.get("desc", ""),
        "payload": p,
    }


def _safe_iso(dt_str: str) -> str:
    """
    Supporte:
    - "2026-01-29T10:00"
    - "2026-01-29 10:00"
    Retourne ISO ou "".
    """
    s = (dt_str or "").strip()
    if not s:
        return ""
    try:
        # datetime-local -> déjà ISO
        if "T" in s:
            datetime.fromisoformat(s)
            return s
        # fallback "YYYY-MM-DD HH:MM"
        d = datetime.strptime(s, "%Y-%m-%d %H:%M")
        return d.strftime("%Y-%m-%dT%H:%M")
    except Exception:
        return ""


def _build_calendar_events(cards: list[dict], status: str) -> list[dict]:
    events = []
    for c in cards:
        p = parse_payload(c.get("desc", ""))
        if p.get("_type") != "booking":
            continue

        start = _safe_iso(p.get("start_date", ""))
        end = _safe_iso(p.get("end_date", ""))
        title = (c.get("name") or "").strip() or f"Booking {c.get('id','')}"
        vehicle = (p.get("vehicle_name") or "").strip()
        client = (p.get("client_name") or "").strip()

        # si on a vehicle/client, on enrichit le titre
        if client or vehicle:
            title = " — ".join([x for x in [client, vehicle] if x])

        events.append(
            {
                "id": c.get("id"),
                "title": title,
                "start": start or None,
                "end": end or None,
                "extendedProps": {
                    "status": status,
                    "client": client,
                    "vehicle": vehicle,
                },
            }
        )
    # On garde même si start est vide : FullCalendar ignorera, mais au moins on voit via "Détails"
    return events


@bookings_bp.get("/")
@login_required
def index():
    t = Trello()

    demandes_cards = t.list_cards(C.LIST_DEMANDES)
    reserved_cards = t.list_cards(C.LIST_RESERVED)
    ongoing_cards = t.list_cards(C.LIST_ONGOING)
    done_cards = t.list_cards(C.LIST_DONE)
    canceled_cards = t.list_cards(C.LIST_CANCELED)

    demandes = [_as_booking(c) for c in demandes_cards]
    reserved = [_as_booking(c) for c in reserved_cards]
    ongoing = [_as_booking(c) for c in ongoing_cards]
    done = [_as_booking(c) for c in done_cards]
    canceled = [_as_booking(c) for c in canceled_cards]

    stats = {
        "demandes": len(demandes),
        "reserved": len(reserved),
        "ongoing": len(ongoing),
        "done": len(done),
        "canceled": len(canceled),
    }

    # ✅ Listes pour aider à remplir rapidement
    clients_cards = t.list_cards(C.LIST_CLIENTS)
    vehicles_cards = t.list_cards(C.LIST_VEHICLES)

    clients = []
    for c in clients_cards:
        p = parse_payload(c.get("desc", ""))
        clients.append({"id": c["id"], "name": c.get("name", ""), **p})

    vehicles = []
    for c in vehicles_cards:
        p = parse_payload(c.get("desc", ""))
        vehicles.append({"id": c["id"], "name": c.get("name", ""), **p})

    # ✅ Calendrier: on affiche Réservé + En cours uniquement
    events = []
    events += _build_calendar_events(reserved_cards, "reserved")
    events += _build_calendar_events(ongoing_cards, "ongoing")

    return render_template(
        "bookings.html",
        demandes=demandes,
        reserved=reserved,
        ongoing=ongoing,
        done=done,
        canceled=canceled,
        stats=stats,
        clients=clients,
        vehicles=vehicles,
        calendar_events=events,
    )


@bookings_bp.get("/api/card/<card_id>")
@login_required
def api_card(card_id: str):
    """
    Pour le popup "Détails" côté front.
    """
    t = Trello()
    card = t.get_card(card_id)
    payload = parse_payload(card.get("desc", ""))
    return jsonify(
        {
            "id": card_id,
            "name": card.get("name", ""),
            "url": card.get("url", ""),
            "payload": payload,
        }
    )


@bookings_bp.post("/create")
@login_required
@admin_required
def create():
    """
    Création réservation via formulaire -> carte Trello avec desc JSON _type=booking.
    """
    t = Trello()

    client_name = request.form.get("client_name", "").strip()
    vehicle_name = request.form.get("vehicle_name", "").strip()

    payload = {
        "_type": "booking",
        "client_name": client_name,
        "client_phone": request.form.get("client_phone", "").strip(),
        "client_address": request.form.get("client_address", "").strip(),
        "doc_id": request.form.get("doc_id", "").strip(),
        "driver_license": request.form.get("driver_license", "").strip(),
        "vehicle_name": vehicle_name,
        "vehicle_plate": request.form.get("vehicle_plate", "").strip(),
        "vehicle_model": request.form.get("vehicle_model", "").strip(),
        "vehicle_vin": request.form.get("vehicle_vin", "").strip(),
        "start_date": request.form.get("start_date", "").strip(),
        "end_date": request.form.get("end_date", "").strip(),
        "pickup_location": request.form.get("pickup_location", "").strip(),
        "return_location": request.form.get("return_location", "").strip(),
        "notes": request.form.get("notes", "").strip(),
        "options": {
            "gps": bool(request.form.get("opt_gps")),
            "chauffeur": bool(request.form.get("opt_driver")),
            "baby_seat": bool(request.form.get("opt_baby_seat")),
        },
    }

    role, name = current_user()
    audit_add(payload, name, "booking_create", {"client_name": client_name, "vehicle_name": vehicle_name})

    title = " — ".join([x for x in [client_name, vehicle_name] if x]).strip()
    t.create_card(C.LIST_DEMANDES, title or "Nouvelle réservation", dump_payload(payload))

    flash("Réservation créée dans DEMANDES ✅", "success")
    return redirect(url_for("bookings.index"))


@bookings_bp.post("/move/<card_id>/<action>")
@login_required
@admin_required
def move(card_id: str, action: str):
    """
    Déplacer une réservation vers une liste Trello.
    Actions: reserved / ongoing / done / cancel / canceled / demandes
    """
    mapping = {
        "demandes": C.LIST_DEMANDES,
        "reserved": C.LIST_RESERVED,
        "ongoing": C.LIST_ONGOING,
        "done": C.LIST_DONE,
        "cancel": C.LIST_CANCELED,
        "canceled": C.LIST_CANCELED,
    }
    target = mapping.get(action)
    if not target:
        flash(f"Action inconnue: {action}", "error")
        return redirect(url_for("bookings.index"))

    t = Trello()
    t.move_card(card_id, target)
    flash("Carte déplacée ✅", "success")
    return redirect(url_for("bookings.index"))


@bookings_bp.post("/archive/<card_id>")
@login_required
@admin_required
def archive(card_id: str):
    """
    "Supprimer" = archiver la carte Trello (closed=true)
    """
    t = Trello()
    t.archive_card(card_id)
    flash("Carte archivée ✅", "success")
    return redirect(url_for("bookings.index"))


@bookings_bp.post("/contract_and_move/<card_id>")
@login_required
@admin_required
def contract_and_move(card_id: str):
    """
    1) générer contrat PDF
    2) attacher PDF à la carte Trello
    3) déplacer vers EN LOCATION (LIST_ONGOING)
    """
    t = Trello()
    card = t.get_card(card_id)
    payload = parse_payload(card.get("desc", ""))

    if payload.get("_type") != "booking":
        flash("La carte n'a pas une desc JSON _type=booking.", "error")
        return redirect(url_for("bookings.index"))

    # 1) PDF
    pdf_bytes = build_contract_pdf(payload)

    # 2) attach Trello
    filename = f"contrat_{card_id}.pdf"
    t.attach_file_to_card(card_id, filename, pdf_bytes)

    # 3) move en location
    t.move_card(card_id, C.LIST_ONGOING)

    flash("Contrat généré + attaché + passé en location ✅", "success")
    return redirect(url_for("bookings.index"))

