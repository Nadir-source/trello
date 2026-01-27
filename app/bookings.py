from flask import Blueprint, render_template, request, redirect, url_for, send_file
from io import BytesIO

from app.auth import admin_required
from app.pdf_generator import build_contract_pdf_fr_ar

from app.trello_client import (
    resolve_board_id,
    get_list_id_by_name,
    get_cards_by_list_id,
    create_card,
    move_card_to_list,
    get_card_by_id,
    LIST_DEMANDES,
    LIST_RESERVED,
    LIST_DONE,
    LIST_ONGOING,
    LIST_CANCEL,
)

bookings_bp = Blueprint("bookings", __name__)


def _board_and_lists():
    board_id = resolve_board_id()
    ids = {
        "demandes": get_list_id_by_name(board_id, LIST_DEMANDES),
        "reserved": get_list_id_by_name(board_id, LIST_RESERVED),
        "ongoing":  get_list_id_by_name(board_id, LIST_ONGOING),
        "done":     get_list_id_by_name(board_id, LIST_DONE),
        "cancel":   get_list_id_by_name(board_id, LIST_CANCEL),
    }
    return board_id, ids


@bookings_bp.get("/bookings")
@admin_required
def bookings():
    _, ids = _board_and_lists()

    demandes = get_cards_by_list_id(ids["demandes"])
    reserved = get_cards_by_list_id(ids["reserved"])
    ongoing  = get_cards_by_list_id(ids["ongoing"])
    done     = get_cards_by_list_id(ids["done"])
    cancel   = get_cards_by_list_id(ids["cancel"])

    return render_template(
        "bookings.html",
        demandes=demandes,
        reserved=reserved,
        ongoing=ongoing,
        closed=done,
        cancelled=cancel,
    )


@bookings_bp.post("/bookings/create")
@admin_required
def create_booking():
    _, ids = _board_and_lists()

    title = request.form.get("title", "Location véhicule")

    desc = "\n".join([
        f"CLIENT: {request.form.get('client','')}",
        f"VEHICLE: {request.form.get('vehicle','')}",
        f"START: {request.form.get('start','')}",
        f"END: {request.form.get('end','')}",
        f"PRICE/DAY: {request.form.get('ppd','')}",
        f"DEPOSIT: {request.form.get('deposit','')}",
        f"PAID: {request.form.get('paid','')}",
        f"DOC: {request.form.get('doc','')}",
        "",
        request.form.get("notes",""),
    ])

    create_card(ids["demandes"], title, desc)
    return redirect(url_for("bookings.bookings"))


@bookings_bp.post("/bookings/move/<card_id>/<target>")
@admin_required
def move(card_id, target):
    _, ids = _board_and_lists()

    if target == "reserved":
        move_card_to_list(card_id, ids["reserved"])
    elif target == "ongoing":
        move_card_to_list(card_id, ids["ongoing"])
    elif target == "done":
        move_card_to_list(card_id, ids["done"])
    elif target == "cancel":
        move_card_to_list(card_id, ids["cancel"])
    else:
        # fallback demandes
        move_card_to_list(card_id, ids["demandes"])

    return redirect(url_for("bookings.bookings"))


@bookings_bp.get("/bookings/contract.pdf/<card_id>")
@admin_required
def contract_pdf(card_id):
    card = get_card_by_id(card_id)
    desc = card.get("desc", "")

    def extract(label):
        for line in desc.splitlines():
            if line.startswith(label + ":"):
                return line.split(":", 1)[1].strip()
        return ""

    data = {
        "booking_ref": card_id,
        "client": {
            "name": extract("CLIENT"),
            "document": extract("DOC") or "Carte nationale ou passeport",
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
        "company": {"name": "Zohir Location Auto"},
    }

    pdf_bytes = build_contract_pdf_fr_ar(data)

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"contrat_{card_id}.pdf",
    )

