# app/bookings.py
from __future__ import annotations

from typing import Any, Dict, Optional, List
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from app.auth import login_required, admin_required, current_user
from app.trello_client import Trello
from app.trello_schema import parse_payload, dump_payload, audit_add
from app.pdf_generator import build_contract_pdf
from app import config as C

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")

# =========================================================
# Helpers
# =========================================================

def _normalize_lang(v: Optional[str]) -> str:
    v = (v or "fr").lower().strip()
    return v if v in ("fr", "en", "ar") else "fr"


def _as_booking(card: Dict[str, Any]) -> Dict[str, Any]:
    p = parse_payload(card.get("desc", "") or "")
    return {
        "id": card.get("id"),
        "name": card.get("name", ""),
        "payload": p,
        "url": card.get("url", ""),
    }


def _parse_start_date(payload: dict) -> datetime:
    s = (payload.get("start_date") or "").strip()
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return datetime.max


def _sort_bookings(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        items,
        key=lambda b: (
            _parse_start_date(b.get("payload", {})),
            (b.get("payload", {}).get("client_name") or "").lower(),
        ),
    )

# =========================================================
# Pages
# =========================================================

@bookings_bp.get("/")
@login_required
def index():
    t = Trello()

    demandes = _sort_bookings([_as_booking(c) for c in t.list_cards(C.LIST_DEMANDES)])
    reserved = _sort_bookings([_as_booking(c) for c in t.list_cards(C.LIST_RESERVED)])
    ongoing = _sort_bookings([_as_booking(c) for c in t.list_cards(C.LIST_ONGOING)])
    done = _sort_bookings([_as_booking(c) for c in t.list_cards(C.LIST_DONE)])
    canceled = _sort_bookings([_as_booking(c) for c in t.list_cards(C.LIST_CANCELED)])

    stats = {
        "demandes": len(demandes),
        "reserved": len(reserved),
        "ongoing": len(ongoing),
        "done": len(done),
        "canceled": len(canceled),
    }

    return render_template(
        "bookings.html",
        demandes=demandes,
        reserved=reserved,
        ongoing=ongoing,
        done=done,
        canceled=canceled,
        stats=stats,
    )


@bookings_bp.get("/calendar")
@login_required
def calendar_page():
    return render_template("calendar.html")

# =========================================================
# API
# =========================================================

@bookings_bp.get("/api/calendar")
@login_required
def api_calendar():
    t = Trello()
    lists = [
        ("demandes", C.LIST_DEMANDES),
        ("reserved", C.LIST_RESERVED),
        ("ongoing", C.LIST_ONGOING),
    ]

    events = []

    for status, list_id in lists:
        for card in t.list_cards(list_id):
            p = parse_payload(card.get("desc", "") or "")
            if p.get("_type") != "booking":
                continue

            start = (p.get("start_date") or "").strip()
            end = (p.get("end_date") or "").strip()
            if not start:
                continue

            client = (p.get("client_name") or "").strip()
            vehicle = (p.get("vehicle_name") or p.get("vehicle_model") or "").strip()
            title = f"{client} — {vehicle}".strip(" —") or card.get("name", "")

            events.append({
                "id": card.get("id"),
                "title": title,
                "start": start,
                "end": end,
                "status": status,
            })

    return jsonify(events)


@bookings_bp.get("/api/card/<card_id>")
@login_required
def api_card(card_id: str):
    t = Trello()
    card = t.get_card(card_id)
    p = parse_payload(card.get("desc", "") or "")
    return jsonify({
        "id": card.get("id"),
        "name": card.get("name", ""),
        "url": card.get("url", ""),
        "payload": p,
    })

# =========================================================
# Actions
# =========================================================

@bookings_bp.post("/create")
@login_required
@admin_required
def create():
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
        "daily_price": request.form.get("daily_price", "").strip(),
        "deposit": request.form.get("deposit", "").strip(),
        "total_price": request.form.get("total_price", "").strip(),
        "km_out": request.form.get("km_out", "").strip(),
        "km_in": request.form.get("km_in", "").strip(),
        "fuel_out": request.form.get("fuel_out", "").strip(),
        "fuel_in": request.form.get("fuel_in", "").strip(),
        "options": {
            "gps": bool(request.form.get("opt_gps")),
            "chauffeur": bool(request.form.get("opt_driver")),
            "baby_seat": bool(request.form.get("opt_baby_seat")),
        },
    }

    role, name = current_user()
    audit_add(payload, role, name, "booking_create", {
        "client_name": client_name,
        "vehicle_name": vehicle_name,
    })

    title = f"{client_name} — {vehicle_name}".strip(" —") or "Nouvelle réservation"
    t.create_card(C.LIST_DEMANDES, title, dump_payload(payload))

    flash("Réservation créée ✅", "success")
    return redirect(url_for("bookings.index"))


@bookings_bp.post("/move/<card_id>/<action>")
@login_required
@admin_required
def move(card_id: str, action: str):
    mapping = {
        "demandes": C.LIST_DEMANDES,
        "reserved": C.LIST_RESERVED,
        "ongoing": C.LIST_ONGOING,
        "done": C.LIST_DONE,
        "canceled": C.LIST_CANCELED,
        "cancel": C.LIST_CANCELED,
    }

    target = mapping.get(action)
    if not target:
        flash("Action inconnue ❌", "error")
        return redirect(url_for("bookings.index"))

    t = Trello()
    t.move_card(card_id, target)

    flash("Carte déplacée ✅", "success")
    return redirect(url_for("bookings.index"))


@bookings_bp.post("/delete/<card_id>")
@login_required
@admin_required
def delete(card_id: str):
    t = Trello()
    try:
        t.archive_card(card_id)
        flash("Carte archivée ✅", "success")
    except Exception as e:
        flash(f"Erreur archive: {e}", "error")

    return redirect(url_for("bookings.index"))


@bookings_bp.post("/contract_and_move")
@login_required
@admin_required
def contract_and_move():
    card_id = request.form.get("card_id", "").strip()
    lang = _normalize_lang(request.form.get("lang"))

    if not card_id:
        flash("card_id manquant ❌", "error")
        return redirect(url_for("bookings.index"))

    t = Trello()
    card = t.get_card(card_id)
    payload = parse_payload(card.get("desc", "") or "")

    if payload.get("_type") != "booking":
        flash("Cette carte n'a pas de payload booking ❌", "error")
        return redirect(url_for("bookings.index"))

    payload["trello_card_id"] = card_id
    payload["trello_card_name"] = card.get("name", "")

    pdf_bytes = build_contract_pdf(payload, lang=lang)
    filename = f"contrat_{card_id}_{lang}.pdf"

    t.attach_file_to_card(card_id, filename, pdf_bytes)
    t.move_card(card_id, C.LIST_ONGOING)

    flash(f"Contrat {lang.upper()} généré + passé en location ✅", "success")
    return redirect(url_for("bookings.index"))

