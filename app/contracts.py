# app/contracts.py
from __future__ import annotations

import json
import io
from flask import Blueprint, send_file, request

from app.auth import login_required
from app.trello_client import Trello
from app.pdf_generator import build_contract_pdf

contracts_bp = Blueprint("contracts", __name__, url_prefix="/contracts")


def _parse_desc_json(desc: str) -> dict:
    """
    Desc Trello = JSON. Tolère texte autour mais tente JSON direct d'abord.
    """
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


def _normalize_lang(x: str | None) -> str:
    v = (x or "fr").lower().strip()
    if v in ("fr", "en", "ar"):
        return v
    return "fr"


@contracts_bp.get("/<card_id>.pdf")
@login_required
def contract_pdf(card_id: str):
    # ✅ /contracts/<id>.pdf?lang=fr|en|ar
    lang = _normalize_lang(request.args.get("lang"))

    t = Trello()
    card = t.get_card(card_id)
    desc = card.get("desc", "")
    payload = _parse_desc_json(desc)

    # fallback si pas un booking JSON
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

