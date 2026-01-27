from flask import Blueprint, render_template, request, redirect, url_for, send_file
from io import BytesIO

from app.auth import admin_required
from app.trello_client import (
    get_cards_by_list_name,
    create_card,
    move_card_to_list,
    get_card_by_id,
)
from app.pdf_generator import build_contract_pdf_fr_ar
from app.config import (
    LIST_DEMANDES,
    LIST_RESERVED,
    LIST_DONE,
)

bookings_bp = Blueprint("bookings", __name__)


# -------------------------
# PAGE PRINCIPALE
# -------------------------
@bookings_bp.route("/bookings")
@admin_required
def bookings():
    demandes = get_cards_by_list_name(LIST_DEMANDES)
    reserved = get_cards_by_list_name(LIST_RESERVED)
    closed = get_cards_by_list_name(LIST_DONE)

    return render_template(
        "bookings.html",
        demandes=demandes,
        reserved=reserved,
        closed=closed,
    )


# -------------------------
# CRÉATION DEMANDE
# -------------------------
@bookings_bp.post("/bookings/create")
@admin_required
def create_booking():
    title = request.form.get("title", "Location véhicule")
    client = request.form.get("client", "")
    vehicle = request.form.get("vehicle", "")
    start = request.form.get("start", "")
    end = request.form.get("end", "")
    ppd = request.form.get("ppd", "")
    deposit = request.form.get("deposit", "")
    paid = request.form.get("paid", "")
    notes = request.form.get("notes", "")

    desc = f"""
CLIENT: {client}
VEHICLE: {vehicle}
START: {start}
END: {end}
PRICE/DAY: {ppd}
DEPOSIT: {deposit}
PAID: {paid}

{notes}
"""

    create_card(title=title, description=desc, list_name=LIST_DEMANDES)
    return redirect(url_for("bookings.bookings"))


# -------------------------
# MOUVEMENTS TRELLO
# -------------------------
@bookings_bp.post("/bookings/move/<card_id>/reserved")
@admin_required
def to_reserved(card_id):
    move_card_to_list(card_id, LIST_RESERVED)
    return redirect(url_for("bookings.bookings"))


@bookings_bp.post("/bookings/move/<card_id>/done")
@admin_required
def to_done(card_id):
    move_card_to_list(card_id, LIST_DONE)
    return redirect(url_for("bookings.bookings"))


# -------------------------
# CONTRAT PDF FR + AR
# -------------------------
@bookings_bp.get("/bookings/contract.pdf/<card_id>")
@admin_required
def contract_pdf(card_id):
    card = get_card_by_id(card_id)

    # --- Extraction simple depuis description Trello ---
    desc = card.get("desc", "")

    def extract(label):
        for line in desc.splitlines():
            if line.startswith(label):
                return line.split(":", 1)[1].strip()
        return ""

    data = {
        "booking_ref": card_id,
        "client": {
            "name": extract("CLIENT"),
            "document": "Carte nationale ou passeport",
        },
        "vehicle": {
            "name": extract("VEHICLE"),
        },
        "dates": {
            "start": extract("START"),
            "end": extract("END"),
        },
        "pricing": {
            "price_per_day": extract("PRICE/DAY"),
            "deposit": extract("DEPOSIT"),
            "paid": extract("PAID"),
            "currency": "DZD",
        },
        "company": {
            "name": "Zohir Location Auto",
        },
    }

    pdf_bytes = build_contract_pdf_fr_ar(data)

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"contrat_{card_id}.pdf",
    )

