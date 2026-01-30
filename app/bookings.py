# app/bookings.py
from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.auth import login_required, admin_required, current_user
from app.trello_client import Trello
from app.trello_schema import parse_payload, dump_payload, audit_add
from app.pdf_generator import build_contract_pdf
from app import config as C

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")


def _as_booking(card: dict) -> dict:
    p = parse_payload(card.get("desc", "")) or {}
    return {
        "id": card["id"],
        "name": card.get("name", ""),
        "desc": card.get("desc", ""),
        "payload": p,
    }


def _safe_list_cards(t: Trello, list_id: str):
    try:
        return t.list_cards(list_id) or []
    except Exception as e:
        flash(f"Erreur Trello (list_cards): {e}", "error")
        return []


@bookings_bp.get("/")
@login_required
def index():
    t = Trello()

    demandes = [_as_booking(c) for c in _safe_list_cards(t, C.LIST_DEMANDES)]
    reserved = [_as_booking(c) for c in _safe_list_cards(t, C.LIST_RESERVED)]
    ongoing = [_as_booking(c) for c in _safe_list_cards(t, C.LIST_ONGOING)]
    done = [_as_booking(c) for c in _safe_list_cards(t, C.LIST_DONE)]
    canceled = [_as_booking(c) for c in _safe_list_cards(t, C.LIST_CANCELED)]

    stats = {
        "demandes": len(demandes),
        "reserved": len(reserved),
        "ongoing": len(ongoing),
        "done": len(done),
        "canceled": len(canceled),
    }

    # ✅ Référentiels pour aider à remplir vite
    clients_cards = _safe_list_cards(t, C.LIST_CLIENTS)
    vehicles_cards = _safe_list_cards(t, C.LIST_VEHICLES)

    clients = []
    for c in clients_cards:
        p = parse_payload(c.get("desc", "")) or {}
        clients.append({"id": c.get("id"), "name": c.get("name", ""), **p})

    vehicles = []
    for c in vehicles_cards:
        p = parse_payload(c.get("desc", "")) or {}
        vehicles.append({"id": c.get("id"), "name": c.get("name", ""), **p})

    # ✅ Events calendrier (on n’affiche pas Terminé / Annulé)
    def to_event(b, status: str):
        p = b.get("payload", {}) or {}
        start = p.get("start_date", "") or ""
        end = p.get("end_date", "") or ""
        title = b.get("name", "")
        client_name = p.get("client_name", "") or ""
        vehicle_name = p.get("vehicle_name", "") or ""
        return {
            "id": b.get("id"),
            "title": title,
            "status": status,
            "start": start,
            "end": end,
            "client_name": client_name,
            "vehicle_name": vehicle_name,
            "payload": p,
        }

    calendar_events = []
    for b in demandes:
        calendar_events.append(to_event(b, "demandes"))
    for b in reserved:
        calendar_events.append(to_event(b, "reserved"))
    for b in ongoing:
        calendar_events.append(to_event(b, "ongoing"))

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
        calendar_events=calendar_events,
    )


@bookings_bp.post("/create")
@login_required
@admin_required
def create():
    """
    Création réservation via formulaire -> carte Trello avec desc JSON _type=booking
    (L’utilisateur ne fait JAMAIS du JSON : c’est le site qui le génère)
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
        }
    }

    role, name = current_user()
    audit_add(payload, name, "booking_create", {"client_name": client_name, "vehicle_name": vehicle_name})

    title = f"{client_name} — {vehicle_name}".strip(" —")
    try:
        t.create_card(C.LIST_DEMANDES, title or "Nouvelle réservation", dump_payload(payload))
        flash("Réservation créée dans DEMANDES ✅", "success")
    except Exception as e:
        flash(f"Erreur création carte Trello: {e}", "error")

    return redirect(url_for("bookings.index"))


@bookings_bp.post("/move/<card_id>/<action>")
@login_required
@admin_required
def move(card_id: str, action: str):
    """
    Déplacer une réservation vers une liste Trello.
    Actions supportées:
      - reserved (Réservé)
      - ongoing (En location)
      - done (Terminé)
      - cancel / canceled (Annulé)
      - demandes (Retour demandes)
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
    try:
        t.move_card(card_id, target)
        flash("Carte déplacée ✅", "success")
    except Exception as e:
        flash(f"Erreur déplacement Trello: {e}", "error")

    return redirect(url_for("bookings.index"))


@bookings_bp.post("/contract_and_move/<card_id>")
@login_required
@admin_required
def contract_and_move(card_id: str):
    """
    1) Générer contrat PDF
    2) Attacher PDF à la carte Trello
    3) Déplacer vers EN LOCATION
    """
    t = Trello()

    try:
        card = t.get_card(card_id)
    except Exception as e:
        flash(f"Impossible de lire la carte Trello: {e}", "error")
        return redirect(url_for("bookings.index"))

    payload = parse_payload(card.get("desc", "")) or {}

    if payload.get("_type") != "booking":
        flash("La carte n'a pas une desc JSON _type=booking.", "error")
        return redirect(url_for("bookings.index"))

    payload["trello_card_id"] = card_id
    payload["trello_card_name"] = card.get("name", "")

    try:
        pdf_bytes = build_contract_pdf(payload)
    except Exception as e:
        flash(f"Erreur génération PDF: {e}", "error")
        return redirect(url_for("bookings.index"))

    try:
        filename = f"contrat_{card_id}.pdf"
        t.attach_file_to_card(card_id, filename, pdf_bytes)
    except Exception as e:
        flash(f"PDF généré mais erreur attach Trello: {e}", "error")
        return redirect(url_for("bookings.index"))

    try:
        t.move_card(card_id, C.LIST_ONGOING)
        flash("Contrat généré + attaché + passé en location ✅", "success")
    except Exception as e:
        flash(f"PDF attaché mais erreur déplacement vers EN LOCATION: {e}", "error")

    return redirect(url_for("bookings.index"))


@bookings_bp.post("/delete/<card_id>")
@login_required
@admin_required
def delete(card_id: str):
    """
    Supprimer une carte Trello (peu importe la colonne)
    """
    t = Trello()
    try:
        t.delete_card(card_id)  # ⚠️ nécessite la méthode dans Trello client (voir note en bas)
        flash("Carte supprimée ✅", "success")
    except Exception as e:
        flash(f"Erreur suppression carte: {e}", "error")
    return redirect(url_for("bookings.index"))

