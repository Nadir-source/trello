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


def _normalize_lang(v: str | None) -> str:
    v = (v or "fr").lower().strip()
    return v if v in ("fr", "en", "ar") else "fr"


@contracts_bp.get("/<card_id>.pdf")
@login_required
def contract_pdf(card_id: str):
    lang = _normalize_lang(request.args.get("lang"))

    t = Trello()
    card = t.get_card(card_id)
    payload = _parse_desc_json(card.get("desc", ""))

    # Sécurité si carte mal formée
    if payload.get("_type") != "booking":
        payload = {}

    # ==========================
    # 🔴 DONNÉES CONTRAT STANDARD
    # ==========================
    payload.update({
        "company": {
            "name": "Zohir Location Auto",
            "name_ar": "زهير لوكيشن أوتو",
            "city": "Alger",
            "city_ar": "الجزائر",
            "phone": "+213 555 00 00 00",
            "email": "contact@zohirauto.dz",
        },
        "ref": card.get("shortLink", card_id),
        "lang": lang,
        "trello_card_id": card_id,
        "trello_card_name": card.get("name", ""),
    })

    pdf_bytes = build_contract_pdf(payload, lang=lang)

    filename = f"contrat_{card_id}_{lang}.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )

