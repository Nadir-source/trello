from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from io import BytesIO
import json

import app.config as C
from app.auth import login_required
from app.trello_client import Trello

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")


def _parse_desc(desc: str) -> dict:
    if not desc:
        return {}
    desc = desc.strip()
    try:
        return json.loads(desc)
    except Exception:
        return {}


def _decorate_booking(card: dict) -> dict:
    payload = _parse_desc(card.get("desc", ""))
    return {
        "id": card.get("id"),
        "name": card.get("name", ""),
        "client": payload.get("client_name") or payload.get("client") or "—",
        "vehicle": payload.get("vehicle_name") or payload.get("vehicle") or "—",
        "start": payload.get("start") or "—",
        "end": payload.get("end") or "—",
        "raw": payload,
    }


@bookings_bp.get("/")
@login_required
def index():
    t = Trello()

    demandes = [_decorate_booking(c) for c in t.list_cards(C.LIST_DEMANDES)]
    reserved = [_decorate_booking(c) for c in t.list_cards(C.LIST_RESERVED)]
    ongoing = [_decorate_booking(c) for c in t.list_cards(C.LIST_ONGOING)]
    done = [_decorate_booking(c) for c in t.list_cards(C.LIST_DONE)]

    clients = t.list_cards(C.LIST_CLIENTS)
    vehicles = t.list_cards(C.LIST_VEHICLES)

    stats = {
        "demandes": len(demandes),
        "reserved": len(reserved),
        "ongoing": len(ongoing),
        "done": len(done),
    }

    # adapt clients/vehicles to template needs: id + name
    clients_ui = [{"id": c["id"], "name": c.get("name", "")} for c in clients]
    vehicles_ui = [{"id": v["id"], "name": v.get("name", "")} for v in vehicles]

    return render_template(
        "bookings.html",
        title="Réservations",
        stats=stats,
        demandes=demandes,
        reserved=reserved,
        ongoing=ongoing,
        done=done,
        clients=clients_ui,
        vehicles=vehicles_ui,
        board=t.board,
    )


@bookings_bp.post("/create")
@login_required
def create():
    t = Trello()

    # Get selected names from trello card IDs (client/vehicle)
    client_id = (request.form.get("client_id") or "").strip()
    vehicle_id = (request.form.get("vehicle_id") or "").strip()

    client_name = ""
    vehicle_name = ""

    if client_id:
        try:
            client_name = t.get_card(client_id).get("name", "")
        except Exception:
            client_name = ""

    if vehicle_id:
        try:
            vehicle_name = t.get_card(vehicle_id).get("name", "")
        except Exception:
            vehicle_name = ""

    data = {
        "title": (request.form.get("title") or "").strip(),
        "client_id": client_id,
        "client_name": client_name,
        "vehicle_id": vehicle_id,
        "vehicle_name": vehicle_name,
        "start": (request.form.get("start") or "").strip(),
        "end": (request.form.get("end") or "").strip(),
        "ppd": (request.form.get("ppd") or "").strip(),
        "deposit": (request.form.get("deposit") or "").strip(),
        "paid": (request.form.get("paid") or "").strip(),
        "method": (request.form.get("method") or "").strip(),
        "doc": (request.form.get("doc") or "").strip(),
        "pickup": (request.form.get("pickup") or "").strip(),
        "return_place": (request.form.get("return_place") or "").strip(),
        "extra_driver": bool(request.form.get("extra_driver")),
        "extra_gps": bool(request.form.get("extra_gps")),
        "extra_baby": bool(request.form.get("extra_baby")),
        "notes": (request.form.get("notes") or "").strip(),
    }

    try:
        t.create_booking_card(data)
        flash("Demande créée dans Trello.", "success")
    except Exception as e:
        flash(f"Erreur création demande: {e}", "error")

    return redirect(url_for("bookings.index"))


@bookings_bp.post("/move/<card_id>/<target>")
@login_required
def move(card_id: str, target: str):
    t = Trello()

    targets = {
        "reserved": C.LIST_RESERVED,
        "ongoing": C.LIST_ONGOING,
        "done": C.LIST_DONE,
        "cancel": C.LIST_CANCEL,
    }

    if target not in targets:
        flash("Action inconnue.", "error")
        return redirect(url_for("bookings.index"))

    try:
        t.move_card(card_id, targets[target])
        flash("Carte déplacée.", "success")
    except Exception as e:
        flash(f"Erreur déplacement: {e}", "error")

    return redirect(url_for("bookings.index"))


@bookings_bp.get("/contract.pdf/<card_id>")
@login_required
def contract_pdf(card_id: str):
    """
    Compatible: si tu as déjà un générateur PDF ailleurs, on l'utilise.
    Sinon, on renvoie un PDF minimal (pour ne jamais casser).
    """
    t = Trello()
    card = t.get_card(card_id)
    payload = _parse_desc(card.get("desc", ""))

    # Try your existing generator (if you have one)
    try:
        from app.contract_pdf import build_contract_pdf_bytes  # optional module
        pdf_bytes = build_contract_pdf_bytes(card, payload)
        return send_file(
            BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"contrat_{card_id}.pdf",
        )
    except Exception:
        # fallback minimal PDF
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4

            buf = BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, 800, "Contrat de location (draft)")
            c.setFont("Helvetica", 10)
            c.drawString(50, 780, f"Carte Trello: {card.get('name','')}")
            c.drawString(50, 765, f"Client: {payload.get('client_name','')}")
            c.drawString(50, 750, f"Vehicule: {payload.get('vehicle_name','')}")
            c.drawString(50, 735, f"Periode: {payload.get('start','')} -> {payload.get('end','')}")
            c.showPage()
            c.save()
            buf.seek(0)

            return send_file(
                buf,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=f"contrat_{card_id}.pdf",
            )
        except Exception as e:
            flash(f"Erreur PDF: {e}", "error")
            return redirect(url_for("bookings.index"))

