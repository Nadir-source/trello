from flask import Blueprint, render_template, request, redirect, url_for, send_file
import io
from app.auth import login_required, current_user, admin_required
from app.trello_client import Trello
from app.trello_schema import parse_payload, dump_payload, audit_add
from app import config as C
from flask import Blueprint, render_template, request, redirect, url_for, send_file
from io import BytesIO

from app.pdf_generator import build_contract_pdf_fr_ar
from app.trello_client import get_card_by_id   # ou ta fonction équivalente


bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")

def _select_options(cards):
    opts=[]
    for c in cards:
        p=parse_payload(c.get("desc",""))
        opts.append({"id": c["id"], "name": c["name"], "p": p})
    return opts

@bookings_bp.get("")
@login_required
def index():
    t = Trello()
    demandes = t.list_cards(C.LIST_DEMANDES)
    reserved = t.list_cards(C.LIST_RESERVED)
    ongoing  = t.list_cards(C.LIST_ONGOING)
    done     = t.list_cards(C.LIST_DONE)

    vehicles = _select_options(t.list_cards(C.LIST_VEHICLES))
    clients  = _select_options(t.list_cards(C.LIST_CLIENTS))
    return render_template("bookings.html",
                           demandes=demandes, reserved=reserved, ongoing=ongoing, done=done,
                           vehicles=vehicles, clients=clients)

@bookings_bp.post("/create")
@login_required
def create():
    t = Trello()
    role, name = current_user()

    vehicle_card_id = request.form.get("vehicle_card_id","").strip()
    client_card_id  = request.form.get("client_card_id","").strip()

    payload = {
        "type": "booking",
        "booking_status": "DEMANDE",
        "vehicle_card_id": vehicle_card_id,
        "client_card_id": client_card_id,
        "start_date": request.form.get("start_date","").strip(),
        "end_date": request.form.get("end_date","").strip(),
        "price_per_day": float(request.form.get("price_per_day","0") or 0),
        "deposit": float(request.form.get("deposit","0") or 0),
        "paid_amount": float(request.form.get("paid_amount","0") or 0),
        "payment_method": request.form.get("payment_method","cash").strip(),
        "pickup_place": request.form.get("pickup_place","").strip(),
        "return_place": request.form.get("return_place","").strip(),
        "notes": request.form.get("notes","").strip(),
        "extras": {
            "driver": bool(request.form.get("extra_driver")),
            "gps": bool(request.form.get("extra_gps")),
            "child_seat": bool(request.form.get("extra_child_seat")),
        },
        "km_out": None,
        "fuel_out": "",
        "km_in": None,
        "fuel_in": "",
        "damage_notes": "",
        "created_by": name,
        "audit": []
    }
    audit_add(payload, name, "booking_create", {"status": "DEMANDE"})
    title = request.form.get("title","").strip() or "Réservation"
    t.create_card(C.LIST_DEMANDES, title, dump_payload(payload))
    return redirect(url_for("bookings.index"))

@bookings_bp.post("/move/<card_id>/<target>")
@login_required
def move(card_id, target):
    t = Trello()
    role, name = current_user()

    # map target -> list
    if target == "reserved":
        list_name = C.LIST_RESERVED
        new_status = "RESERVED"
    elif target == "ongoing":
        list_name = C.LIST_ONGOING
        new_status = "ONGOING"
    elif target == "done":
        list_name = C.LIST_DONE
        new_status = "DONE"
    elif target == "cancel":
        list_name = C.LIST_CANCEL
        new_status = "CANCELLED"
    else:
        return redirect(url_for("bookings.index"))

    card = t.get_card(card_id)
    payload = parse_payload(card.get("desc",""))
    payload["booking_status"] = new_status
    audit_add(payload, name, "booking_move", {"to": new_status})
    t.update_card(card_id, desc=dump_payload(payload))
    t.move_card(card_id, list_name)
    return redirect(url_for("bookings.index"))

@bookings_bp.get("/contract.pdf/<card_id>")
@login_required
def contract_pdf(card_id):
    t = Trello()
    card = t.get_card(card_id)
    booking = parse_payload(card.get("desc",""))

    client = {}
    vehicle = {}
    if booking.get("client_card_id"):
        c = t.get_card(booking["client_card_id"])
        client = parse_payload(c.get("desc",""))
        client.setdefault("full_name", c.get("name",""))
    if booking.get("vehicle_card_id"):
        v = t.get_card(booking["vehicle_card_id"])
        vehicle = parse_payload(v.get("desc",""))
        vehicle.setdefault("plate", v.get("name",""))

    pdf_bytes = build_contract_pdf(booking, client, vehicle)
    return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf", as_attachment=True, download_name="contrat_location.pdf")

@bookings_bp.post("/invoice/mark_paid/<booking_card_id>")
@login_required
@admin_required
def mark_invoice_paid(booking_card_id):
    # simple: crée une invoice OPEN puis la move PAID si payé_amount>=total
    t = Trello()
    role, name = current_user()

    booking_card = t.get_card(booking_card_id)
    booking = parse_payload(booking_card.get("desc",""))
    total = 0.0

    # estimation total = days*ppd (si tu veux améliorer après)
    # ici on laisse l'admin saisir le total via form
    total = float(request.form.get("total","0") or 0)
    paid_amount = float(request.form.get("paid_amount","0") or 0)
    status = "PAID" if paid_amount >= total and total > 0 else "OPEN"

    invoice_payload = {
        "type": "invoice",
        "booking_card_id": booking_card_id,
        "status": status,
        "total": total,
        "paid_amount": paid_amount,
        "payment_method": request.form.get("payment_method","cash"),
        "notes": request.form.get("notes","")
    }
    audit_add(invoice_payload, name, "invoice_create", {"status": status, "total": total, "paid": paid_amount})

    title = f"Invoice — {booking_card.get('name','booking')} — {status}"
    inv_card = t.create_card(C.LIST_INVOICES_OPEN, title, dump_payload(invoice_payload))

    if status == "PAID":
        t.move_card(inv_card["id"], C.LIST_INVOICES_PAID)

    # also update booking paid amount
    booking["paid_amount"] = paid_amount
    audit_add(booking, name, "booking_paid_update", {"paid_amount": paid_amount, "total": total})
    t.update_card(booking_card_id, desc=dump_payload(booking))
    return redirect(url_for("finance.index"))


@bookings_bp.route("/bookings/<card_id>/contract")
def booking_contract(card_id):
    # 1️⃣ Récupérer la carte Trello
    card = get_card_by_id(card_id)

    if not card:
        return "Réservation introuvable", 404

    # 2️⃣ Construire les données pour le contrat
    data = {
        "booking_ref": card.get("idShort") or card.get("id"),

        # Client
        "client_name": card.get("client_name"),
        "client_id": card.get("client_id"),          # CNI ou Passeport
        "client_phone": card.get("client_phone"),
        "client_address": card.get("client_address"),

        # Véhicule
        "vehicle_name": card.get("vehicle_name"),
        "vehicle_plate": card.get("vehicle_plate"),

        # Dates
        "start_date": card.get("start_date"),
        "end_date": card.get("end_date"),
        "days": card.get("days"),

        # Finance
        "price_per_day": card.get("price_per_day"),
        "deposit": card.get("deposit"),
        "advance": card.get("advance"),
        "total": card.get("total"),

        # Lieux
        "pickup_place": card.get("pickup_place"),
        "return_place": card.get("return_place"),
    }

    # 3️⃣ Générer le PDF
    pdf_bytes = build_contract_pdf_fr_ar(data)

    # 4️⃣ Retourner le PDF
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"contrat_{data['booking_ref']}.pdf"
    )

