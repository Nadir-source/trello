# app/contracts.py
from __future__ import annotations

import io
import json
from flask import Blueprint, send_file, request

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
                return json.loads(s[start:end + 1])
            except Exception:
                return {}
        return {}


@contracts_bp.get("/<card_id>.pdf")
@login_required
def contract_pdf(card_id: str):
    # ✅ langue via query string
    lang = (request.args.get("lang", "fr") or "fr").lower().strip()
    if lang not in ("fr", "en", "ar"):
        lang = "fr"

    t = Trello()
    card = t.get_card(card_id)
    payload = _parse_desc_json(card.get("desc", ""))

    # fallback si pas booking
    if payload.get("_type") != "booking":
        payload = {
            "_type": "booking",
            "client_name": "",
            "vehicle_name": "",
            "start_date": "",
            "end_date": "",
            "pickup_location": "",
            "return_location": "",
            "notes": "",
            "options": {},
        }

    payload["trello_card_id"] = card_id
    payload["trello_card_name"] = card.get("name", "")

    pdf_bytes = build_contract_pdf(payload, lang=lang)

    filename = f"contrat_{card_id}_{lang}.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )

