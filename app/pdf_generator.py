# app/pdf_generator.py
from __future__ import annotations

from typing import Any, Dict
from datetime import datetime

from app.contract_renderer import render_contract_pdf


def build_contract_pdf(payload: dict, lang: str = "fr") -> bytes:
    """
    Génère le PDF du contrat de location avec données enrichies.
    """
    payload = payload.copy()
    payload["now_date"] = datetime.now().strftime("%Y-%m-%d")

    # Ajoute d'autres enrichissements ici si nécessaire
    return render_contract_pdf(payload, lang=lang)


def build_month_report_pdf(payload: dict) -> bytes:
    """
    Compatibilité avec les rapports mensuels.
    """
    from reportlab.pdfgen import canvas
    from io import BytesIO

    buf = BytesIO()
    c = canvas.Canvas(buf)
    c.setFont("Helvetica", 14)
    c.drawString(50, 800, "Monthly Report (Demo)")
    c.setFont("Helvetica", 10)
    y = 770
    for k, v in (payload or {}).items():
        c.drawString(50, y, f"{k}: {v}")
        y -= 14
        if y < 50:
            c.showPage()
            y = 800
    c.showPage()
    c.save()
    return buf.getvalue()

