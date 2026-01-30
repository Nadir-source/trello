# app/contracts.py
from __future__ import annotations

import io
import json
from typing import Any, Dict

from flask import Blueprint, send_file, flash, redirect, url_for

from app.auth import login_required, admin_required, current_user
from app.trello_client import Trello
from app.pdf_generator import build_contract_pdf

contracts_bp = Blueprint("contracts", __name__, url_prefix="/contracts")


def _parse_desc_json(desc: str) -> Dict[str, Any]:
    """
    Desc Trello = JSON (idéalement).
    Tolère du texte autour → tente de trouver un bloc {...}.
    """
    s = (desc or "").strip()
    if not s:
        return {}

    # 1) direct JSON
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        pass

    # 2) fallback: bloc JSON entre { ... }
    start = s.find("{")
    end = s.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(s[start : end + 1])
            return obj if isinstance(obj, dict) else {}
        except Exception:
            return {}

    return {}


def _ensure_booking_payload(card: Dict[str, Any]) -> Dict[str, Any]:
    """
    Garantit un payload minimal exploitable pour le PDF.
    On essaie de récupérer le max depuis la carte.
    """
    payload = _parse_desc_json(card.get("desc", ""))

    # si pas bon type, on tente quand même d'avoir des champs
    if payload.get("_type") != "booking":
        payload = dict(payload) if isinstance(payload, dict) else {}
        payload["_type"] = "booking"

        # si la carte s'appelle "Client — Voiture" on split
        name = (card.get("name") or "").strip()
        if "—" in name:
            a, b = [x.strip() for x in name.split("—", 1)]
            payload.setdefault("client_name", a)
            payload.setdefault("vehicle_name", b)
        else:
            payload.setdefault("client_name", payload.get("client_name", ""))
            payload.setdefault("vehicle_name", payload.get("vehicle_name", ""))

        # champs standards
        payload.setdefault("start_date", "")
        payload.setdefault("end_date", "")
        payload.setdefault("pickup_location", "")
        payload.setdefault("return_location", "")
        payload.setdefault("notes", "")
        payload.setdefault("options", {})

    payload["trello_card_id"] = card.get("id") or payload.get("trello_card_id")
    payload["trello_card_name"] = card.get("name", "")

    return payload


@contracts_bp.get("/<card_id>.pdf")
@login_required
def contract_pdf(card_id: str):
    """
    Télécharge le PDF du contrat (sans attacher sur Trello).
    """
    t = Trello()
    card = t.get_card(card_id)
    # on ajoute id dans la structure pour _ensure_booking_payload
    card["id"] = card_id

    payload = _ensure_booking_payload(card)
    pdf_bytes = build_contract_pdf(payload)

    filename = f"contrat_{card_id}.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@contracts_bp.post("/<card_id>/attach")
@login_required
@admin_required
def attach_contract(card_id: str):
    """
    Génère le PDF et l'attache sur la carte Trello (pièce jointe),
    puis redirige vers Réservations.
    """
    t = Trello()
    card = t.get_card(card_id)
    card["id"] = card_id

    payload = _ensure_booking_payload(card)
    pdf_bytes = build_contract_pdf(payload)

    filename = f"contrat_{card_id}.pdf"
    t.attach_file_to_card(card_id, filename, pdf_bytes)

    role, name = current_user()
    flash(f"Contrat attaché à la carte Trello ✅ ({name})", "success")
    return redirect(url_for("bookings.index"))

