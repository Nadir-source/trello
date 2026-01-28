from flask import Blueprint, render_template, request, redirect, send_file
from io import BytesIO

from app.auth import login_required
from app.trello_client import Trello
import app.config as C
from app.pdf_generator import build_contract_pdf_fr_ar

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")


@bookings_bp.route("/", methods=["GET"])
@login_required
def index():
    t = Trello()

    demandes = t.list_cards(C.LIST_DEMANDES)
    reserved = t.list_cards(C.LIST_RESERVED)
    ongoing = t.list_cards(C.LIST_ONGOING)
    done = t.list_cards(C.LIST_DONE)

    clients = t.list_cards(C.LIST_CLIENTS)
    vehicles = t.list_cards(C.LIST_VEHICLES)

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
        clients=clients,
        vehicles=vehicles,
    )


@bookings_bp.route("/create", methods=["POST"])
@login_required
def create():
    t = Trello()

    data = {
        "title": request.form.get("title"),
        "client_id": request.form.get("client_id"),
        "vehicle_id": request.form.get("vehicle_id"),
        "start": request.form.get("start"),
        "end": request.form.get("end"),
        "ppd": request.form.get("ppd"),
        "deposit": request.form.get("deposit"),
        "paid": request.form.get("paid"),
        "method": request.form.get("method"),
        "pickup": request.form.get("pickup"),
        "return_place": request.form.get("return_place"),
        "notes": request.form.get("notes"),
        "extra_driver": bool(request.form.get("extra_driver")),
        "extra_gps": bool(request.form.get("extra_gps")),
        "extra_baby": bool(request.form.get("extra_baby")),
    }

    t.create_booking_card(data)
    return redirect("/bookings")


@bookings_bp.route("/move/<card_id>/<target>", methods=["POST"])
@login_required
def move(card_id, target):
    t = Trello()

    target_map = {
        "reserved": C.LIST_RESERVED,
        "ongoing": C.LIST_ONGOING,
        "done": C.LIST_DONE,
        "cancel": C.LIST_CANCELLED,
    }

    if target in target_map:
        t.move_card(card_id, target_map[target])

    return redirect("/bookings")


@bookings_bp.route("/contract.pdf/<card_id>", methods=["GET"])
@login_required
def contract(card_id):
    t = Trello()
    card = t.get_card_by_id(card_id)

    pdf_bytes = build_contract_pdf_fr_ar(card)

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"contrat_{card_id}.pdf",
    )

