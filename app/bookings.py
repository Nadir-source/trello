# app/bookings.py
from __future__ import annotations

import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from app.auth import login_required, admin_required
from app.trello_client import Trello
import app.config as C
from app.pdf_generator import build_contract_pdf

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")


def parse_payload(desc: str) -> dict:
    s = (desc or "").strip()
    if not s:
        return {}
    try:
        return json.loads(s)
    except Exception:
        start = s.find("{")
        end = s.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(s[start:end + 1])
            except Exception:
                return {}
        return {}


def dump_payload(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _as_booking(card: dict) -> dict:
    p = parse_payload(card.get("desc", ""))
    return {
        "id": card["id"],
        "name": card.get("name", ""),
        "desc": card.get("desc", ""),
        "payload": p,
        "idList": card.get("idList", ""),
    }


def _normalize_lang(v: str | None) -> str:
    v = (v or "fr").lower().strip()
    return v if v in ("fr", "en", "ar") else "fr"


@bookings_bp.get("/")
@login_required
def index():
    t = Trello()

    demandes = [_as_booking(c) for c in t.list_cards(C.LIST_DEMANDES)]
    reserved = [_as_booking(c) for c in t.list_cards(C.LIST_RESERVED)]
    ongoing = [_as_booking(c) for c in t.list_cards(C.LIST_ONGOING)]
    done = [_as_booking(c) for c in t.list_cards(C.LIST_DONE)]
    canceled = [_as_booking(c) for c in t.list_cards(C.LIST_CANCELED)]

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


@bookings_bp.post("/create")
@login_required
@admin_required
def create():
    t = Trello()

    client_name = (request.form.get("client_name", "")).strip()
    vehicle_name = (request.form.get("vehicle_name", "")).strip()

    payload = {
        "_type": "booking",
        "client_name": client_name,
        "client_phone": (request.form.get("client_phone", "")).strip(),
        "client_address": (request.form.get("client_address", "")).strip(),
        "doc_id": (request.form.get("doc_id", "")).strip(),
        "driver_license": (request.form.get("driver_license", "")).strip(),
        "vehicle_name": vehicle_name,
        "vehicle_plate": (request.form.get("vehicle_plate", "")).strip(),
        "vehicle_model": (request.form.get("vehicle_model", "")).strip(),
        "vehicle_vin": (request.form.get("vehicle_vin", "")).strip(),
        "start_date": (request.form.get("start_date", "")).strip(),
        "end_date": (request.form.get("end_date", "")).strip(),
        "pickup_location": (request.form.get("pickup_location", "")).strip(),
        "return_location": (request.form.get("return_location", "")).strip(),
        "notes": (request.form.get("notes", "")).strip(),
        "options": {
            "gps": bool(request.form.get("opt_gps")),
            "chauffeur": bool(request.form.get("opt_driver")),
            "baby_seat": bool(request.form.get("opt_baby_seat")),
        },
    }

    title = f"{client_name} — {vehicle_name}".strip(" —") or "Nouvelle réservation"
    t.create_card(C.LIST_DEMANDES, title, dump_payload(payload))
    flash("Réservation créée dans DEMANDES ✅", "success")
    return redirect(url_for("bookings.index"))


@bookings_bp.post("/move/<card_id>/<action>")
@login_required
@admin_required
def move(card_id: str, action: str):
    t = Trello()
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

    t.move_card(card_id, target)
    flash("Carte déplacée ✅", "success")
    return redirect(url_for("bookings.index"))


@bookings_bp.post("/archive/<card_id>")
@login_required
@admin_required
def archive(card_id: str):
    t = Trello()
    t.archive_card(card_id)
    flash("Carte archivée ✅", "success")
    return redirect(url_for("bookings.index"))


@bookings_bp.post("/delete/<card_id>")
@login_required
@admin_required
def delete(card_id: str):
    t = Trello()
    t.delete_card(card_id)
    flash("Carte supprimée définitivement ✅", "success")
    return redirect(url_for("bookings.index"))


@bookings_bp.get("/api/card/<card_id>")
@login_required
def api_card(card_id: str):
    t = Trello()
    card = t.get_card(card_id)
    payload = parse_payload(card.get("desc", ""))

    return jsonify({
        "id": card_id,
        "name": card.get("name", ""),
        "url": card.get("url", ""),
        "payload": payload,
    })


@bookings_bp.post("/contract_and_move/<card_id>")
@login_required
@admin_required
def contract_and_move(card_id: str):
    """
    1) Génère le contrat PDF (lang au choix)
    2) Attache le PDF à la carte Trello
    3) Déplace vers EN COURS
    """
    lang = _normalize_lang(request.form.get("lang"))

    t = Trello()
    card = t.get_card(card_id)
    payload = parse_payload(card.get("desc", ""))

    if payload.get("_type") != "booking":
        flash("La carte n'a pas de JSON _type=booking.", "error")
        return redirect(url_for("bookings.index"))

    payload["trello_card_id"] = card_id
    payload["trello_card_name"] = card.get("name", "")

    pdf_bytes = build_contract_pdf(payload, lang=lang)

    filename = f"contrat_{card_id}_{lang}.pdf"
    t.attach_file_to_card(card_id, filename, pdf_bytes)

    t.move_card(card_id, C.LIST_ONGOING)

    flash(f"Contrat ({lang.upper()}) généré + attaché + passé en location ✅", "success")
    return redirect(url_for("bookings.index"))

