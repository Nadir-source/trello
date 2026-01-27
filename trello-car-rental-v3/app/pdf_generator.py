import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from app.config import LOUEUR_NOM, LOUEUR_TEL, LOUEUR_ADRESSE

def build_contract_pdf(booking: dict, client: dict, vehicle: dict) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w,h = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, h-60, "CONTRAT DE LOCATION (Simple)")

    c.setFont("Helvetica", 10)
    c.drawString(40, h-85, f"Loueur: {LOUEUR_NOM} | {LOUEUR_TEL}")
    c.drawString(40, h-100, f"Adresse: {LOUEUR_ADRESSE}")

    y = h-135
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Client")
    y -= 18
    c.setFont("Helvetica", 11)
    for k in ["full_name","phone","doc_id","driver_license","address"]:
        v = client.get(k,"")
        if v:
            c.drawString(40, y, f"{k}: {v}")
            y -= 16

    y -= 8
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Véhicule")
    y -= 18
    c.setFont("Helvetica", 11)
    for k in ["plate","brand","model","year","color","km","status"]:
        v = vehicle.get(k,"")
        if v != "":
            c.drawString(40, y, f"{k}: {v}")
            y -= 16

    y -= 8
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Location")
    y -= 18
    c.setFont("Helvetica", 11)
    for k in ["start_date","end_date","price_per_day","deposit","paid_amount","payment_method","pickup_place","return_place","notes"]:
        v = booking.get(k,"")
        if v != "":
            c.drawString(40, y, f"{k}: {v}")
            y -= 16

    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Conditions (résumé)")
    y -= 16
    c.setFont("Helvetica", 10)
    lines = [
        "- Le véhicule doit être rendu dans le même état.",
        "- Toute infraction/amende est à la charge du locataire.",
        "- En cas de dommages, la franchise/dépôt peut être retenu.",
        "- Paiement restant dû à la restitution si non réglé."
    ]
    for ln in lines:
        c.drawString(45, y, ln); y -= 14

    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, h-60, "Signature")
    c.setFont("Helvetica", 11)
    c.drawString(40, h-95, "Client: _______________________")
    c.drawString(40, h-125, "Loueur: _______________________")

    c.save()
    return buf.getvalue()

def build_month_report_pdf(title: str, lines: list[str]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w,h = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, h-60, title)
    y = h-100
    c.setFont("Helvetica", 11)
    for ln in lines:
        c.drawString(40, y, ln)
        y -= 16
        if y < 60:
            c.showPage()
            y = h-60
            c.setFont("Helvetica", 11)
    c.save()
    return buf.getvalue()
