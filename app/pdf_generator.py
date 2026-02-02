# app/pdf_generator.py
from __future__ import annotations

from typing import Any, Dict

from app.contract_renderer import render_contract_pdf

def build_month_report_pdf(payload: dict) -> bytes:
    """
    Compatibilité: certaines routes (finance.py) importent build_month_report_pdf.
    Si tu n'utilises pas ce report pour le moment, on renvoie un PDF simple.
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

