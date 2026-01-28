# app/contracts.py
from __future__ import annotations

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from io import BytesIO

from app.auth import login_required
from app.trello_client import Trello
import app.config as C

from app.storage_contracts import load_contract, save_contract

# PDF (ReportLab)
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

contracts_bp = Blueprint("contracts", __name__)

def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def _default_contract_model(booking: dict, client: dict, vehicle: dict) -> dict:
    """
    Modèle éditable (stocké en JSON).
    booking/client/vehicle sont des dicts déjà normalisés côté bookings.
    """
    title = booking.get("name") or "Contrat de location"
    return {
        "meta": {
            "booking_id": booking.get("id"),
            "generated_at": _now_str(),
            "version": 1,
        },
        "header": {
            "company_name": "Zohir Location Auto",
            "company_address": "Alger, Algérie",
            "company_phone": "+213 ....",
            "title_fr": "CONTRAT DE LOCATION DE VÉHICULE",
            "title_ar": "عقد كراء سيارة",
        },
        "booking": {
            "title": title,
            "start": booking.get("start", ""),
            "end": booking.get("end", ""),
            "pickup": booking.get("pickup", ""),
            "return_place": booking.get("return_place", ""),
            "ppd": booking.get("ppd", ""),
            "deposit": booking.get("deposit", ""),
            "paid": booking.get("paid", ""),
            "method": booking.get("method", ""),
            "doc": booking.get("doc", ""),
            "extras": booking.get("extras", []),
            "notes": booking.get("notes", ""),
        },
        "client": {
            "name": client.get("name", ""),
            "phone": client.get("phone", ""),
            "doc_id": client.get("doc_id", ""),
            "license": client.get("license", ""),
            "address": client.get("address", ""),
        },
        "vehicle": {
            "name": vehicle.get("name", ""),
            "plate": vehicle.get("plate", ""),
            "brand": vehicle.get("brand", ""),
            "model": vehicle.get("model", ""),
            "color": vehicle.get("color", ""),
        },
        # Texte éditable
        "body_fr": (
            "Le présent contrat définit les conditions de location du véhicule.\n"
            "Le locataire s'engage à respecter les conditions ci-dessous."
        ),
        "body_ar": (
            "يحدد هذا العقد شروط وأحكام كراء السيارة.\n"
            "يلتزم المستأجر باحترام الشروط أدناه."
        ),
        "clauses_fr": [
            "Le locataire est responsable des infractions, amendes et dommages durant la période de location.",
            "Le véhicule doit être rendu avec le même niveau de carburant qu’au départ.",
            "Interdiction de sous-location sans accord écrit du loueur.",
        ],
        "clauses_ar": [
            "المستأجر مسؤول عن المخالفات والغرامات والأضرار خلال مدة الكراء.",
            "يجب إرجاع السيارة بنفس مستوى الوقود عند الاستلام.",
            "يمنع التأجير من الباطن دون موافقة كتابية من المؤجر.",
        ],
        "signature": {
            "place": "Alger",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "lessor_name": "Zohir Location Auto",
            "lessee_name": client.get("name", ""),
        },
    }

def _get_booking_client_vehicle(t: Trello, booking_id: str):
    """
    À adapter selon ton format actuel :
    - booking = carte réservation
    - client_id + vehicle_id sont dans custom fields / description / labels selon ton implémentation
    Ici on suppose que ton Trello() sait déjà "build_booking_dict" ou similaire.
    Si tu as déjà une fonction util dans bookings.py, réutilise-la.
    """
    booking = t.get_booking(booking_id)  # <-- si tu n'as pas, remplace par ta fonction existante
    client = t.get_client(booking["client_id"])
    vehicle = t.get_vehicle(booking["vehicle_id"])
    return booking, client, vehicle

def _pdf_from_contract_model(model: dict) -> bytes:
    """
    PDF simple & robuste (on améliore le design ensuite).
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    x = 40
    y = height - 50

    header = model.get("header", {})
    booking = model.get("booking", {})
    client = model.get("client", {})
    vehicle = model.get("vehicle", {})
    sig = model.get("signature", {})

    def line(txt: str, dy=16, font="Helvetica", size=11):
        nonlocal y
        c.setFont(font, size)
        c.drawString(x, y, txt[:110])
        y -= dy
        if y < 80:
            c.showPage()
            y = height - 50

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, header.get("company_name", ""))
    y -= 22
    c.setFont("Helvetica", 10)
    c.drawString(x, y, header.get("company_address", ""))
    y -= 14
    c.drawString(x, y, header.get("company_phone", ""))
    y -= 22

    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, header.get("title_fr", "CONTRAT"))
    y -= 26

    # Infos
    line("=== Location ===", font="Helvetica-Bold")
    line(f"Réservation: {booking.get('title','')}")
    line(f"Période: {booking.get('start','')} -> {booking.get('end','')}")
    line(f"Remise: {booking.get('pickup','')} | Retour: {booking.get('return_place','')}")
    line(f"Prix/jour: {booking.get('ppd','')} DZD | Dépôt: {booking.get('deposit','')} DZD | Payé: {booking.get('paid','')} DZD")
    line(f"Méthode: {booking.get('method','')} | Document: {booking.get('doc','')}")
    extras = booking.get("extras", [])
    if extras:
        line("Options: " + ", ".join(extras))

    y -= 10
    line("=== Client ===", font="Helvetica-Bold")
    line(f"Nom: {client.get('name','')}")
    if client.get("phone"):
        line(f"Téléphone: {client.get('phone','')}")
    if client.get("doc_id"):
        line(f"CNI/Passeport: {client.get('doc_id','')}")
    if client.get("license"):
        line(f"Permis: {client.get('license','')}")
    if client.get("address"):
        line(f"Adresse: {client.get('address','')[:90]}")

    y -= 10
    line("=== Véhicule ===", font="Helvetica-Bold")
    line(f"Nom: {vehicle.get('name','')}")
    if vehicle.get("plate"):
        line(f"Immatriculation: {vehicle.get('plate','')}")
    if vehicle.get("brand") or vehicle.get("model"):
        line(f"Marque/Modèle: {vehicle.get('brand','')} {vehicle.get('model','')}")
    if vehicle.get("color"):
        line(f"Couleur: {vehicle.get('color','')}")

    y -= 10
    line("=== Texte (FR) ===", font="Helvetica-Bold")
    for part in (model.get("body_fr", "")).splitlines():
        if part.strip():
            line(part.strip(), size=10)

    y -= 6
    line("=== Conditions (FR) ===", font="Helvetica-Bold")
    for idx, clause in enumerate(model.get("clauses_fr", []), start=1):
        line(f"{idx}. {clause}", size=10)

    y -= 10
    line("=== Signature ===", font="Helvetica-Bold")
    line(f"Lieu: {sig.get('place','')} | Date: {sig.get('date','')}")
    line(f"Le Loueur: {sig.get('lessor_name','')}")
    line(f"Le Locataire: {sig.get('lessee_name','')}")

    c.showPage()
    c.save()
    return buf.getvalue()

@contracts_bp.get("/bookings/contract/edit/<booking_id>")
@login_required
def contract_edit(booking_id: str):
    # Charge version modifiée si existe, sinon génère depuis Trello
    model = load_contract(booking_id)
    if model is None:
        t = Trello()
        # IMPORTANT: adapte ces 3 fonctions à ton code réel
        booking, client, vehicle = _get_booking_client_vehicle(t, booking_id)
        model = _default_contract_model(booking, client, vehicle)
        save_contract(booking_id, model)

    return render_template("contract_edit.html", title="Contrat", model=model)

@contracts_bp.post("/bookings/contract/save/<booking_id>")
@login_required
def contract_save(booking_id: str):
    # On reconstruit un model depuis form
    model = load_contract(booking_id) or {"meta": {"booking_id": booking_id, "version": 1}}

    # champs simples
    model.setdefault("header", {})
    model["header"]["company_name"] = request.form.get("company_name", "").strip()
    model["header"]["company_address"] = request.form.get("company_address", "").strip()
    model["header"]["company_phone"] = request.form.get("company_phone", "").strip()
    model["header"]["title_fr"] = request.form.get("title_fr", "").strip()
    model["header"]["title_ar"] = request.form.get("title_ar", "").strip()

    model.setdefault("body_fr", "")
    model.setdefault("body_ar", "")
    model["body_fr"] = request.form.get("body_fr", "")
    model["body_ar"] = request.form.get("body_ar", "")

    # clauses en textarea multi-lignes
    clauses_fr = request.form.get("clauses_fr", "")
    clauses_ar = request.form.get("clauses_ar", "")
    model["clauses_fr"] = [l.strip() for l in clauses_fr.splitlines() if l.strip()]
    model["clauses_ar"] = [l.strip() for l in clauses_ar.splitlines() if l.strip()]

    model.setdefault("signature", {})
    model["signature"]["place"] = request.form.get("sig_place", "").strip()
    model["signature"]["date"] = request.form.get("sig_date", "").strip()
    model["signature"]["lessor_name"] = request.form.get("sig_lessor", "").strip()
    model["signature"]["lessee_name"] = request.form.get("sig_lessee", "").strip()

    model.setdefault("meta", {})
    model["meta"]["generated_at"] = _now_str()

    save_contract(booking_id, model)
    flash("✅ Contrat enregistré.", "ok")
    return redirect(url_for("contracts.contract_edit", booking_id=booking_id))

@contracts_bp.get("/bookings/contract/pdf/<booking_id>")
@login_required
def contract_pdf(booking_id: str):
    model = load_contract(booking_id)
    if model is None:
        return redirect(url_for("contracts.contract_edit", booking_id=booking_id))

    pdf_bytes = _pdf_from_contract_model(model)
    filename = f"contrat_{booking_id}.pdf"

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=False,
        download_name=filename,
    )

