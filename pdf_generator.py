import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from config import LOUEUR_NOM, LOUEUR_TEL, LOUEUR_ADRESSE

def build_simple_pdf(title: str, payload: dict) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, h-60, title)

    c.setFont("Helvetica", 10)
    c.drawString(40, h-90, f"Loueur: {LOUEUR_NOM} | {LOUEUR_TEL}")
    c.drawString(40, h-105, f"Adresse: {LOUEUR_ADRESSE}")

    y = h-140
    c.setFont("Helvetica", 11)
    for k, v in payload.items():
        c.drawString(40, y, f"{k}: {v}")
        y -= 16
        if y < 60:
            c.showPage()
            y = h-60

    c.showPage()
    c.save()
    return buf.getvalue()
