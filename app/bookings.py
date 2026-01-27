from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from io import BytesIO
from datetime import datetime

from app.auth import login_required
from app.trello_client import Trello
import app.config as C

# PDF
from app.pdf_generator import build_contract_pdf_fr_ar


bookings_bp = Blueprint("bookings", __name__)


# -----------------------------
# Helpers: desc format & parsing
# -----------------------------
DESC_KEYS = ["CLIENT", "VEHICLE", "START", "END", "PPD", "DEPOSIT", "PAID", "DOC", "NOTES"]


def build_desc(form: dict) -> str:
    """
    Standardize Trello card desc so data is always recoverable.
    """
    def g(k):  # safe get
        return (form.get(k) or "").strip()

    # DOC: CNI or PASSPORT
    doc = g("doc").upper().replace("É", "E")
    if doc not in ("CNI", "PASSPORT", ""):
        doc = ""

    # keep consistent keys
    data = {
        "CLIENT": g("client"),
        "VEHICLE": g("vehicle"),
        "START": g("start"),
        "END": g("end"),
        "PPD": g("ppd"),
        "DEPOSIT": g("deposit"),
        "PAID": g("paid"),
        "DOC": doc,
        "NOTES": g("notes"),
    }

    lines = [f"{k}: {data.get(k,'')}" for k in DESC_KEYS]
    return "\n".join(lines).strip() + "\n"


def parse_desc(desc: str) -> dict:
    """
    Parse standardized desc. Works even if some lines are missing.
    """
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


def card_to_viewmodel(card: dict) -> dict:
    """
    Make a safe object for templates: id, name + parsed fields
    """
    desc = card.get("desc", "") if isinstance(card, dict) else ""
    meta = parse_desc(desc)
    vm = {
        "id": card.get("id"),
        "name": card.get("name", ""),
        "desc": desc,
        "client": meta["CLIENT"],
        "vehicle": meta["VEHICLE"],
        "start": meta["START"],
        "end": meta["END"],
        "ppd": meta["PPD"],
        "deposit": meta["DEPOSIT"],
        "paid": meta["PAID"],
        "doc": meta["DOC"],
        "notes": meta["NOTES"],
    }
    return vm


def safe_len(x):
    try:
        return len(x)
    except Exception:
        return 0


# -----------------------------
# Routes
# -----------------------------
@bookings_bp.get("/bookings")
@login_required
def index():
    t = Trello()

    demandes = [card_to_viewmodel(c) for c in t.list_cards(C.LIST_DEMANDES)]
    reserved = [card_to_viewmodel(c) for c in t.list_cards(C.LIST_RESERVED)]
    ongoing = [card_to_viewmodel(c) for c in t.list_cards(C.LIST_ONGOING)]
    done = [card_to_viewmodel(c) for c in t.list_cards(C.LIST_DONE)]
    cancel = [card_to_viewmodel(c) for c in t.list_cards(C.LIST_CANCEL)]

    stats = {
        "demandes": safe_len(demandes),
        "reserved": safe_len(reserved),
        "ongoing": safe_len(ongoing),
        "done": safe_len(done),
        "cancel": safe_len(cancel),
    }

    return render_template(
        "bookings.html",
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

    title = (request.form.get("title") or "").strip() or "Nouvelle réservation"
    desc = build_desc(request.form)

    # create in DEMANDES
    t.create_card(C.LIST_DEMANDES, title, desc)
    flash("✅ Demande créée dans Trello.", "ok")
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
    flash(f"✅ Déplacé vers {mapping[stage]}", "ok")
    return redirect(url_for("bookings.index"))


@bookings_bp.get("/bookings/contract.pdf/<card_id>")
@login_required
def contract_pdf(card_id: str):
    """
    Generate FR+AR contract from Trello card desc.
    """
    t = Trello()
    card = t.get_card(card_id)  # dict: name, desc, ...
    meta = parse_desc(card.get("desc", ""))

    # data object for PDF generator
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
        "doc_type": meta["DOC"],  # CNI / PASSPORT
        "notes": meta["NOTES"],
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

