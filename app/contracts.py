from flask import Blueprint, send_file, abort
from app.auth import admin_required
from app.trello_client import Trello
from app.pdf_generator import generate_contract_pdf
import io

contracts_bp = Blueprint("contracts", __name__, url_prefix="/contracts")


@contracts_bp.get("/<card_id>/fr")
@admin_required
def contract_fr(card_id: str):
    t = Trello()
    card = t.get_card(card_id)
    pdf_bytes = generate_contract_pdf(card, lang="FR")
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"contrat_{card_id}_FR.pdf",
    )


@contracts_bp.get("/<card_id>/ar")
@admin_required
def contract_ar(card_id: str):
    t = Trello()
    card = t.get_card(card_id)
    pdf_bytes = generate_contract_pdf(card, lang="AR")
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"contrat_{card_id}_AR.pdf",
    )


@contracts_bp.get("/<card_id>/frar")
@admin_required
def contract_frar(card_id: str):
    t = Trello()
    card = t.get_card(card_id)
    pdf_bytes = generate_contract_pdf(card, lang="FR+AR")
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"contrat_{card_id}_FR_AR.pdf",
    )

