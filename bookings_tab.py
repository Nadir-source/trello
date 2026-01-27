from flask import Blueprint, render_template, request, redirect, url_for, send_file
import io
from admin_auth import admin_required
from trello_client import list_cards, create_card, get_card, move_card, update_card
from trello_schema import parse_payload, dump_payload
from config import LIST_DEMANDES, LIST_RESERVED, LIST_CLOSED
from pdf_generator import build_simple_pdf

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")

@bookings_bp.get("")
@admin_required
def index():
    demandes = list_cards(LIST_DEMANDES)
    reserved = list_cards(LIST_RESERVED)
    closed = list_cards(LIST_CLOSED)
    return render_template("bookings.html", demandes=demandes, reserved=reserved, closed=closed)

@bookings_bp.post("/create")
@admin_required
def create():
    title = request.form.get("title", "Nouvelle réservation").strip()
    payload = {
        "client": request.form.get("client", "").strip(),
        "vehicle": request.form.get("vehicle", "").strip(),
        "start": request.form.get("start", "").strip(),
        "end": request.form.get("end", "").strip(),
        "price_per_day": request.form.get("ppd", "").strip(),
        "deposit": request.form.get("deposit", "").strip(),
        "paid": request.form.get("paid", "").strip(),
        "notes": request.form.get("notes", "").strip(),
    }
    create_card(LIST_DEMANDES, title, dump_payload(payload))
    return redirect(url_for("bookings.index"))

@bookings_bp.post("/to_reserved/<card_id>")
@admin_required
def to_reserved(card_id):
    move_card(card_id, LIST_RESERVED)
    return redirect(url_for("bookings.index"))

@bookings_bp.post("/to_closed/<card_id>")
@admin_required
def to_closed(card_id):
    move_card(card_id, LIST_CLOSED)
    return redirect(url_for("bookings.index"))

@bookings_bp.get("/pdf/<card_id>")
@admin_required
def pdf(card_id):
    c = get_card(card_id)
    payload = parse_payload(c.get("desc",""))
    pdf_bytes = build_simple_pdf("Contrat (Simple)", payload)
    return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf", as_attachment=True, download_name="contrat.pdf")

@bookings_bp.post("/update/<card_id>")
@admin_required
def update(card_id):
    c = get_card(card_id)
    payload = parse_payload(c.get("desc",""))
    for k in ["client","vehicle","start","end","price_per_day","deposit","paid","notes"]:
        if k in request.form:
            payload[k] = request.form.get(k, "").strip()
    update_card(card_id, desc=dump_payload(payload))
    return redirect(url_for("bookings.index"))
