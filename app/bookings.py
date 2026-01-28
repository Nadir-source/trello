from flask import Blueprint, render_template, request, redirect, send_file
from io import BytesIO

from app.auth import login_required
from app.trello_client import Trello
import app.config as C
from app.pdf_generator import build_contract_pdf_fr_ar

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")


def _get_name_by_id(items, _id):
    for it in items:
        if it["id"] == _id:
            return it["name"]
    return ""


def _build_desc(data, client_name, vehicle_name):
    # Description lisible dans Trello
    lines = []
    lines.append(f"CLIENT: {client_name}")
    lines.append(f"VEHICLE: {vehicle_name}")
    lines.append(f"START: {data.get('start','')}")
    lines.append(f"END: {data.get('end','')}")
    lines.append(f"PPD_DZD: {data.get('ppd','')}")
    lines.append(f"DEPOSIT_DZD: {data.get('deposit','')}")
    lines.append(f"PAID_DZD: {data.get('paid','')}")
    lines.append(f"METHOD: {data.get('method','')}")
    lines.append(f"PICKUP: {data.get('pickup','')}")
    lines.append(f"RETURN: {data.get('return_place','')}")
    extras = []
    if data.get("extra_driver"):
        extras.append("CHAUFFEUR")
    if data.get("extra_gps"):
        extras.append("GPS")
    if data.get("extra_baby"):
        extras.append("SIEGE_BEBE")
    lines.append(f"EXTRAS: {', '.join(extras) if extras else '-'}")
    notes = (data.get("notes") or "").strip()
    if notes:
        lines.append("")
        lines.append("NOTES:")
        lines.append(notes)
    return "\n".join(lines)


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
        board=t.board,
    )


@bookings_bp.route("/create", methods=["POST"])
@login_required
def create():
    t = Trello()

    data = {
        "title": (request.form.get("title") or "").strip() or "Nouvelle réservation",
        "client_id": (request.form.get("client_id") or "").strip(),
        "vehicle_id": (request.form.get("vehicle_id") or "").strip(),
        "start": (request.form.get("start") or "").strip(),
        "end": (request.form.get("end") or "").strip(),
        "ppd": (request.form.get("ppd") or "").strip(),
        "deposit": (request.form.get("deposit") or "").strip(),
        "paid": (request.form.get("paid") or "").strip(),
        "method": (request.form.get("method") or "Cash").strip(),
        "pickup": (request.form.get("pickup") or "").strip(),
        "return_place": (request.form.get("return_place") or "").strip(),
        "notes": (request.form.get("notes") or "").strip(),
        "extra_driver": bool(request.form.get("extra_driver")),
        "extra_gps": bool(request.form.get("extra_gps")),
        "extra_baby": bool(request.form.get("extra_baby")),
    }

    clients = t.list_cards(C.LIST_CLIENTS)
    vehicles = t.list_cards(C.LIST_VEHICLES)

    client_name = _get_name_by_id(clients, data["client_id"]) if data["client_id"] else ""
    vehicle_name = _get_name_by_id(vehicles, data["vehicle_id"]) if data["vehicle_id"] else ""

    desc = _build_desc(data, client_name, vehicle_name)

    # crée dans la liste DEMANDES
    t.create_card(C.LIST_DEMANDES, data["title"], desc)

    return redirect("/bookings/")


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

    return redirect("/bookings/")


@bookings_bp.route("/contract.pdf/<card_id>", methods=["GET"])
@login_required
def contract(card_id):
    t = Trello()
    card = t.get_card(card_id)

    pdf_bytes = build_contract_pdf_fr_ar(card)

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"contrat_{card_id}.pdf",
    )

