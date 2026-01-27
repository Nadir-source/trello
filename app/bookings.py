from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from io import BytesIO
from datetime import datetime

from app.auth import login_required
from app.trello_client import Trello
import app.config as C

from app.pdf_generator import build_contract_pdf_fr_ar

bookings_bp = Blueprint("bookings", __name__)

DESC_KEYS = ["CLIENT", "VEHICLE", "START", "END", "PPD", "DEPOSIT", "PAID", "DOC", "NOTES", "METHOD", "PICKUP", "RETURN", "EXTRA_DRIVER", "EXTRA_GPS", "EXTRA_BABY"]


def _g(form, k):
    return (form.get(k) or "").strip()


def build_desc(data: dict) -> str:
    out = {k: "" for k in DESC_KEYS}
    out.update({k: (data.get(k) or "").strip() for k in DESC_KEYS})

    # normalise doc
    doc = out["DOC"].upper().replace("É", "E")
    if doc not in ("CNI", "PASSPORT", ""):
        doc = ""
    out["DOC"] = doc

    # normalise extras
    for k in ["EXTRA_DRIVER", "EXTRA_GPS", "EXTRA_BABY"]:
        out[k] = "YES" if out.get(k) in ("on", "true", "1", "YES") else "NO"

    lines = [f"{k}: {out.get(k,'')}" for k in DESC_KEYS]
    return "\n".join(lines).strip() + "\n"


def parse_desc(desc: str) -> dict:
    out = {k: "" for k in DESC_KEYS}
    if not desc:
        return out
    for line in desc.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip().upper()
        if k in out:
            out[k] = v.strip()
    return out


def card_to_vm(card: dict) -> dict:
    meta = parse_desc(card.get("desc", ""))
    return {
        "id": card.get("id"),
        "name": card.get("name", ""),
        "client": meta["CLIENT"],
        "vehicle": meta["VEHICLE"],
        "start": meta["START"],
        "end": meta["END"],
        "ppd": meta["PPD"],
        "deposit": meta["DEPOSIT"],
        "paid": meta["PAID"],
        "doc": meta["DOC"],
        "notes": meta["NOTES"],
        "method": meta["METHOD"],
        "pickup": meta["PICKUP"],
        "return_place": meta["RETURN"],
        "extra_driver": meta["EXTRA_DRIVER"],
        "extra_gps": meta["EXTRA_GPS"],
        "extra_baby": meta["EXTRA_BABY"],
    }


@bookings_bp.get("/bookings")
@login_required
def index():
    t = Trello()

    # ✅ listes pour remplir les SELECT
    clients_cards = t.list_cards(C.LIST_CLIENTS)
    vehicles_cards = t.list_cards(C.LIST_VEHICLES)

    clients = [{"id": c["id"], "name": c.get("name", "")} for c in clients_cards]
    vehicles = [{"id": c["id"], "name": c.get("name", "")} for c in vehicles_cards]

    demandes = [card_to_vm(c) for c in t.list_cards(C.LIST_DEMANDES)]
    reserved = [card_to_vm(c) for c in t.list_cards(C.LIST_RESERVED)]
    ongoing = [card_to_vm(c) for c in t.list_cards(C.LIST_ONGOING)]
    done = [card_to_vm(c) for c in t.list_cards(C.LIST_DONE)]
    cancel = [card_to_vm(c) for c in t.list_cards(C.LIST_CANCEL)]

    stats = {
        "demandes": len(demandes),
        "reserved": len(reserved),
        "ongoing": len(ongoing),
        "done": len(done),
        "cancel": len(cancel),
    }

    return render_template(
        "bookings.html",
        clients=clients,
        vehicles=vehicles,
        demandes=demandes,
        reserved=reserved,
        ongoing=ongoing,
        done=done,
        cancel=cancel,
        stats=stats,
    )


@bookings_bp.post("/bookings/create")
@login_required
def create_booking():
    t = Trello()

    title = _g(request.form, "title") or "Nouvelle réservation"

    # ✅ select envoie des IDs -> on récupère les noms depuis Trello
    client_id = _g(request.form, "client_id")
    vehicle_id = _g(request.form, "vehicle_id")

    client_name = ""
    vehicle_name = ""

    if client_id:
        c = t.get_card(client_id)
        client_name = c.get("name", "")

    if vehicle_id:
        v = t.get_card(vehicle_id)
        vehicle_name = v.get("name", "")

    desc = build_desc({
        "CLIENT": client_name or _g(request.form, "client_free"),
        "VEHICLE": vehicle_name or _g(request.form, "vehicle_free"),
        "START": _g(request.form, "start"),
        "END": _g(request.form, "end"),
        "PPD": _g(request.form, "ppd"),
        "DEPOSIT": _g(request.form, "deposit"),
        "PAID": _g(request.form, "paid"),
        "DOC": _g(request.form, "doc"),
        "NOTES": _g(request.form, "notes"),
        "METHOD": _g(request.form, "method"),
        "PICKUP": _g(request.form, "pickup"),
        "RETURN": _g(request.form, "return_place"),
        "EXTRA_DRIVER": request.form.get("extra_driver", ""),
        "EXTRA_GPS": request.form.get("extra_gps", ""),
        "EXTRA_BABY": request.form.get("extra_baby", ""),
    })

    t.create_card(C.LIST_DEMANDES, title, desc)
    flash("✅ Demande créée.", "ok")
    return redirect(url_for("bookings.index"))


@bookings_bp.post("/bookings/move/<card_id>/<stage>")
@login_required
def move(card_id: str, stage: str):
    t = Trello()
    stage = stage.lower().strip()

    mapping = {
        "demandes": C.LIST_DEMANDES,
        "reserved": C.LIST_RESERVED,
        "ongoing": C.LIST_ONGOING,
        "done": C.LIST_DONE,
        "cancel": C.LIST_CANCEL,
    }

    if stage not in mapping:
        flash("❌ Stage inconnu.", "err")
        return redirect(url_for("bookings.index"))

    t.move_card(card_id, mapping[stage])
    flash("✅ Déplacé.", "ok")
    return redirect(url_for("bookings.index"))


@bookings_bp.get("/bookings/contract.pdf/<card_id>")
@login_required
def contract_pdf(card_id: str):
    t = Trello()
    card = t.get_card(card_id)
    meta = parse_desc(card.get("desc", ""))

    data = {
        "booking_ref": card_id[:8],
        "title": card.get("name", ""),
        "client_name": meta["CLIENT"],
        "vehicle": meta["VEHICLE"],
        "start": meta["START"],
        "end": meta["END"],
        "ppd": meta["PPD"],
        "deposit": meta["DEPOSIT"],
        "paid": meta["PAID"],
        "doc_type": meta["DOC"],
        "notes": meta["NOTES"],
        "method": meta["METHOD"],
        "pickup": meta["PICKUP"],
        "return_place": meta["RETURN"],
        "extras": {
            "driver": meta["EXTRA_DRIVER"],
            "gps": meta["EXTRA_GPS"],
            "baby": meta["EXTRA_BABY"],
        },
        "company_name": "Zohir Location Auto",
        "currency": "DZD",
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }

    pdf_bytes = build_contract_pdf_fr_ar(data)
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"contrat_{data['booking_ref']}.pdf",
    )

