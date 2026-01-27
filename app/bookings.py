from flask import Blueprint, render_template, request, redirect, url_for, send_file
from io import BytesIO

from app.auth import admin_required

# ⚠️ ON UTILISE TES FONCTIONS EXISTANTES
from app.trello_client import (
    get_demandes_cards,
    get_closed_cards,
    get_card,
    move_card,
    TRELLO_LIST_NAME,
    TRELLO_CLOSED_LIST_NAME,
)

from app.pdf_generator import build_contract_pdf_fr_ar

bookings_bp = Blueprint("bookings", __name__)


# -------------------------
# PAGE BOOKINGS
# -------------------------
@bookings_bp.route("/bookings")
@admin_required
def bookings():
    demandes = get_demandes_cards()
    closed = get_closed_cards()

    # les réservées = celles qui ne sont ni fermées ni nouvelles
    reserved = [
        c for c in demandes
        if c.get("idList") != TRELLO_LIST_NAME
    ]

    return render_template(
        "bookings.html",
        demandes=demandes,
        reserved=reserved,
        closed=closed,
    )


# -------------------------
# CREATE DEMANDE
# -------------------------
@bookings_bp.post("/bookings/create")
@admin_required
def create_booking():
    title = request.form.get("title", "Location véhicule")

    desc = f"""
CLIENT: {request.form.get("client", "")}
VEHICLE: {request.form.get("vehicle", "")}
START: {request.form.get("start", "")}
END: {request.form.get("end", "")}
PRICE/DAY: {request.form.get("ppd", "")}
DEPOSIT: {request.form.get("deposit", "")}
PAID: {request.form.get("paid", "")}

{request.form.get("notes", "")}
"""

    from app.trello_client import create_card
    create_card(title, desc)

    return redirect(url_for("bookings.bookings"))


# -------------------------
# MOVE CARD → RESERVED
# -------------------------
@bookings_bp.post("/bookings/move/<card_id>/reserved")
@admin_required
def move_reserved(card_id):
    move_card(card_id)
    return redirect(url_for("bookings.bookings"))


# -------------------------
# MOVE CARD → DONE
# -------------------------
@bookings_bp.post("/bookings/move/<card_id>/done")
@admin_required
def move_done(card_id):
    move_card(card_id, TRELLO_CLOSED_LIST_NAME)
    return redirect(url_for("bookings.bookings"))


# -------------------------
# CONTRACT PDF FR + AR
# -------------------------
@bookings_bp.get("/bookings/contract.pdf/<card_id>")
@admin_required
def contract_pdf(card_id):
    card = get_card(card_id)
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

