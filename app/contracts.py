# app/contracts.py
from __future__ import annotations

import json
import io
from flask import Blueprint, send_file, request
from datetime import datetime

from app.auth import login_required
from app.trello_client import Trello
from app.pdf_generator import build_contract_pdf

contracts_bp = Blueprint("contracts", __name__, url_prefix="/contracts")

def _parse_desc_json(desc: str) -> dict:
    s = (desc or "").strip()
    if not s:
        return {}
    try:
        return json.loads(s)
    except Exception:
        start = s.find("{")
        end = s.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(s[start : end + 1])
            except Exception:
                return {}
        return {}

def _normalize_lang(v: str | None) -> str:
    v = (v or "fr").lower().strip()
    return v if v in ("fr", "en", "ar") else "fr"

@contracts_bp.get("/<card_id>.pdf")
@login_required
def contract_pdf(card_id: str):
    lang = _normalize_lang(request.args.get("lang"))

    t = Trello()
    card = t.get_card(card_id)
    desc = card.get("desc", "")
    data = _parse_desc_json(desc)

    # Données enrichies pour le template
    payload = {
        "ref": card.get("idShort", "—"),
        "now_date": datetime.now().strftime("%d/%m/%Y"),
        "client": {
            "name": data.get("client_name", ""),
            "phone": data.get("client_phone", ""),
            "address": data.get("client_address", ""),
            "doc_id": data.get("doc_id", ""),
            "permit": data.get("driver_license", ""),
        },
        "vehicle": {
            "name": data.get("vehicle_name", ""),
            "model": data.get("vehicle_model", ""),
            "plate": data.get("vehicle_plate", ""),
            "vin": data.get("vehicle_vin", ""),
        },
        "rental": {
            "from": data.get("start_date", ""),
            "to": data.get("end_date", ""),
            "pickup": data.get("pickup_location", ""),
            "return": data.get("return_location", ""),
        },
        "pricing": {
            "daily_price": data.get("daily_price", ""),
            "deposit": data.get("deposit", ""),
            "total": data.get("total_price", ""),
            "currency": data.get("currency", "DA"),
        },
        "options": {
            "gps": data.get("options", {}).get("gps", False),
            "chauffeur": data.get("options", {}).get("chauffeur", False),
            "baby_seat": data.get("options", {}).get("baby_seat", False),
        },
        "mileage": {
            "km_out": data.get("km_out", ""),
            "km_in": data.get("km_in", ""),
        },
        "fuel": {
            "out": data.get("fuel_out", ""),
            "in": data.get("fuel_in", ""),
        },
        "notes": data.get("notes", ""),
        "sign": {
            "place": data.get("sign_place", ""),
            "date": data.get("sign_date", datetime.now().strftime("%d/%m/%Y")),
        },
        "company": {
            "name": "ZOHIR LOCATION AUTO",
            "phone1": "+213 5xx xxx xxx",
            "phone2": "+213 6xx xxx xxx",
            "email": "contact@email.dz",
            "address": "Alger, Algérie",
        },
    }

    pdf_bytes = build_contract_pdf(payload, lang=lang)
    filename = f"contrat_{card_id}_{lang}.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )

