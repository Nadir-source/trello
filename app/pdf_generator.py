import io
import json
import re
import unicodedata
from datetime import datetime
from typing import Dict, Any, List

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm


# ============================================================
# Helpers
# ============================================================

def _safe_json(desc: str) -> Dict[str, Any]:
    try:
        obj = json.loads(desc or "{}")
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def _fmt_date(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    # accepte : 2026-01-29 / 2026-01-29T10:30 / 2026-01-29 10:30 / avec secondes
    candidates = [
        ("%Y-%m-%d", False),
        ("%Y-%m-%dT%H:%M", True),
        ("%Y-%m-%d %H:%M", True),
        ("%Y-%m-%dT%H:%M:%S", True),
        ("%Y-%m-%d %H:%M:%S", True),
    ]
    for fmt, has_time in candidates:
        try:
            dt = datetime.strptime(s[:19], fmt)
            return dt.strftime("%d/%m/%Y %H:%M") if has_time else dt.strftime("%d/%m/%Y")
        except Exception:
            pass
    return s


def _yesno(b: bool) -> str:
    return "Oui" if b else "Non"


def _wrap_text(text: str, max_chars: int = 95) -> List[str]:
    text = (text or "").strip()
    if not text:
        return ["-"]
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]


# ============================================================
# Booking data extraction from Trello card desc JSON
# ============================================================

def extract_booking_data(card: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attend que card["desc"] contienne un JSON avec:
      _type = "booking"
    """
    payload = _safe_json(card.get("desc", ""))

    if payload.get("_type") != "booking":
        return {}

    client = payload.get("client_name") or payload.get("client") or ""
    vehicle = payload.get("vehicle_name") or payload.get("vehicle") or ""
    start = _fmt_date(payload.get("start_date") or payload.get("start") or "")
    end = _fmt_date(payload.get("end_date") or payload.get("end") or "")

    options = payload.get("options") if isinstance(payload.get("options"), dict) else {}
    chauffeur = bool(options.get("chauffeur", False))
    gps = bool(options.get("gps", False))
    baby_seat = bool(options.get("baby_seat", False))

    return {
        "card_title": card.get("name", ""),
        "client": client,
        "vehicle": vehicle,
        "period": (f"{start} -> {end}").strip(" ->"),
        "pickup_location": payload.get("pickup_location") or "",
        "return_location": payload.get("return_location") or "",
        "doc_type": payload.get("doc_type") or "",
        "notes": payload.get("notes") or "",
        "options": {
            "chauffeur": chauffeur,
            "gps": gps,
            "baby_seat": baby_seat,
        },
    }


# ============================================================
# Contract PDF
# ============================================================

def generate_contract_pdf(card: Dict[str, Any], lang: str = "FR+AR") -> bytes:
    """
    PDF de contrat simple et lisible.
    lang: "FR", "AR", "FR+AR"
    NOTE: la partie AR est placeholder (pas de RTL/shaping).
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    data = extract_booking_data(card)

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(20 * mm, h - 25 * mm, "Contrat de location" + (" (draft)" if not data else ""))

    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, h - 32 * mm, f"Carte Trello: {card.get('name','')}")
    c.line(20 * mm, h - 35 * mm, w - 20 * mm, h - 35 * mm)

    y = h - 50 * mm

    # Si données absentes : message clair
    if not data:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, y, "Erreur: données réservation introuvables.")
        y -= 8 * mm

        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, "La description Trello doit contenir du JSON avec: _type = 'booking'.")
        y -= 6 * mm
        c.drawString(20 * mm, y, "Ex: {\"_type\":\"booking\",\"client_name\":\"...\",\"vehicle_name\":\"...\",\"start_date\":\"...\"}")
        c.showPage()
        c.save()
        return buf.getvalue()

    # Section FR
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "Informations (FR)")
    y -= 8 * mm

    c.setFont("Helvetica", 11)
    lines = [
        f"Client: {data['client'] or '-'}",
        f"Véhicule: {data['vehicle'] or '-'}",
        f"Période: {data['period'] or '-'}",
        f"Lieu remise: {data['pickup_location'] or '-'}",
        f"Lieu retour: {data['return_location'] or '-'}",
        f"Document: {data['doc_type'] or '-'}",
        f"Option chauffeur: {_yesno(data['options']['chauffeur'])}",
        f"Option GPS: {_yesno(data['options']['gps'])}",
        f"Option siège bébé: {_yesno(data['options']['baby_seat'])}",
    ]

    for line in lines:
        c.drawString(20 * mm, y, line)
        y -= 7 * mm

    # Notes
    y -= 2 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, y, "Notes:")
    y -= 6 * mm
    c.setFont("Helvetica", 10)

    for chunk in _wrap_text(data["notes"], max_chars=95):
        c.drawString(20 * mm, y, chunk)
        y -= 5 * mm

    # Section AR (placeholder)
    if "AR" in (lang or "").upper():
        y -= 10 * mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, y, "Arabic section (placeholder)")
        y -= 7 * mm
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, "Pour un rendu arabe correct (RTL), il faut shaping + bidi + police arabe.")
        y -= 5 * mm
        c.drawString(20 * mm, y, "Dis-moi si tu veux la version FR+AR parfaite (Noto Naskh + arabic_reshaper + bidi).")
        y -= 5 * mm

    c.showPage()
    c.save()
    return buf.getvalue()


# ============================================================
# Finance monthly report PDF (required by app/finance.py)
# ============================================================

def build_month_report_pdf(month: str, rows: List[Dict[str, Any]] | None = None) -> bytes:
    """
    Génère un PDF de rapport mensuel.
    Cette fonction est IMPORTANTE car app/finance.py l'importe.
    month: ex "2026-01" ou "Janvier 2026"
    rows: liste de dicts optionnelle
        ex: [{"date":"2026-01-10","label":"Paiement X","amount":12000}, ...]
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 18)
    c.drawString(20 * mm, h - 25 * mm, "Rapport mensuel (Facturation)")

    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, h - 35 * mm, f"Mois: {month}")

    y = h - 55 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, y, "Détails")
    y -= 8 * mm

    rows = rows or []

    if not rows:
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, "Aucune donnée disponible.")
        y -= 6 * mm
        c.showPage()
        c.save()
        return buf.getvalue()

    # En-tête
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Date")
    c.drawString(55 * mm, y, "Libellé")
    c.drawRightString(w - 20 * mm, y, "Montant")
    y -= 6 * mm
    c.line(20 * mm, y, w - 20 * mm, y)
    y -= 8 * mm

    c.setFont("Helvetica", 10)
    total = 0.0

    for r in rows:
        if y < 25 * mm:
            c.showPage()
            y = h - 25 * mm
            c.setFont("Helvetica", 10)

        date = str(r.get("date", ""))[:20]
        label = str(r.get("label", r.get("name", "")))[:70]

        amount = r.get("amount", r.get("price", 0)) or 0
        try:
            amount_f = float(amount)
        except Exception:
            amount_f = 0.0

        total += amount_f

        c.drawString(20 * mm, y, date)
        c.drawString(55 * mm, y, label)
        c.drawRightString(w - 20 * mm, y, f"{amount_f:,.2f}")
        y -= 6 * mm

    y -= 10 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(w - 20 * mm, y, f"Total: {total:,.2f}")

    c.showPage()
    c.save()
    return buf.getvalue()

