# app/pdf_generator.py
from __future__ import annotations

import io
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


# ----------------------------
# Helpers formatting
# ----------------------------
def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _safe(s: Any) -> str:
    if s is None:
        return ""
    return str(s).strip()


def _parse_dt(dt_str: str) -> Tuple[str, str]:
    """
    Accept:
      - "2026-01-29T10:00" (datetime-local)
      - "2026-01-29 10:00"
      - "2026-01-29"
    Returns: (date_str_ddmmyyyy, time_str_hhmm)
    """
    s = _safe(dt_str)
    if not s:
        return ("", "")

    # Normalize
    s = s.replace(" ", "T")
    # Keep only YYYY-MM-DDTHH:MM
    m = re.match(r"^(\d{4}-\d{2}-\d{2})(?:T(\d{2}:\d{2}))?", s)
    if not m:
        return (s, "")

    d = m.group(1)
    t = m.group(2) or ""
    try:
        d_obj = datetime.strptime(d, "%Y-%m-%d")
        d_out = d_obj.strftime("%d/%m/%Y")
    except Exception:
        d_out = d

    return (d_out, t)


def _draw_kv(c: canvas.Canvas, x: float, y: float, key: str, val: str, key_w: float = 46 * mm) -> float:
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, y, key)
    c.setFont("Helvetica", 9)
    c.drawString(x + key_w, y, val)
    return y - 5.2 * mm


def _box(c: canvas.Canvas, x: float, y: float, w: float, h: float, title: str = ""):
    c.rect(x, y - h, w, h, stroke=1, fill=0)
    if title:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x + 3 * mm, y + 1.5 * mm, title)


# ----------------------------
# Contract PDF
# ----------------------------
def build_contract_pdf(payload: Dict[str, Any]) -> bytes:
    """
    payload expected:
      _type=booking
      client_name, client_phone, client_address, doc_id, driver_license
      vehicle_name, vehicle_plate, vehicle_model, vehicle_vin
      start_date, end_date, pickup_location, return_location
      notes
      options: {gps, chauffeur, baby_seat}
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    # margins
    left = 14 * mm
    right = 14 * mm
    top = H - 12 * mm
    width = W - left - right

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(left, top, "KADID ZOUHIR")
    c.setFont("Helvetica", 10)
    c.drawString(left, top - 6 * mm, "Location de Voitures (avec ou sans chauffeur)")
    c.drawString(left, top - 11.5 * mm, "Tél: 0782 39 52 74   |   Tél: 0552 00 03 19")
    c.drawString(left, top - 17 * mm, "Adresse: ALGER")
    c.drawString(left, top - 22.5 * mm, "Email: contact@example.com")

    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(left + width, top, "CONTRAT DE LOCATION VÉHICULE")

    ref = _safe(payload.get("trello_card_id") or payload.get("reference") or "")
    if not ref:
        ref = _safe(payload.get("id") or "")
    c.setFont("Helvetica", 9)
    c.drawRightString(left + width, top - 7 * mm, f"Référence: {ref}")

    y = top - 30 * mm

    # 2 columns blocks
    col_gap = 6 * mm
    col_w = (width - col_gap) / 2
    box_h = 52 * mm

    # Left box: Locataire
    _box(c, left, y, col_w, box_h, "Le Locataire")
    yy = y - 8 * mm
    yy = _draw_kv(c, left + 3 * mm, yy, "Nom / Prénom :", _safe(payload.get("client_name")), 36 * mm)
    yy = _draw_kv(c, left + 3 * mm, yy, "Adresse :", _safe(payload.get("client_address")), 36 * mm)
    yy = _draw_kv(c, left + 3 * mm, yy, "N° Tél :", _safe(payload.get("client_phone")), 36 * mm)
    yy = _draw_kv(c, left + 3 * mm, yy, "N° Doc :", _safe(payload.get("doc_id")), 36 * mm)
    yy = _draw_kv(c, left + 3 * mm, yy, "Permis N° :", _safe(payload.get("driver_license")), 36 * mm)

    # Right box: Objet location
    _box(c, left + col_w + col_gap, y, col_w, box_h, "Objet de la location")
    yy2 = y - 8 * mm
    yy2 = _draw_kv(c, left + col_w + col_gap + 3 * mm, yy2, "Modèle :", _safe(payload.get("vehicle_name") or payload.get("vehicle_model")), 30 * mm)
    yy2 = _draw_kv(c, left + col_w + col_gap + 3 * mm, yy2, "Immatriculation :", _safe(payload.get("vehicle_plate")), 30 * mm)
    yy2 = _draw_kv(c, left + col_w + col_gap + 3 * mm, yy2, "N° Série (VIN) :", _safe(payload.get("vehicle_vin")), 30 * mm)

    sd, st = _parse_dt(_safe(payload.get("start_date")))
    ed, et = _parse_dt(_safe(payload.get("end_date")))

    yy2 = _draw_kv(c, left + col_w + col_gap + 3 * mm, yy2, "Date location :", f"du {sd} au {ed}", 30 * mm)
    yy2 = _draw_kv(c, left + col_w + col_gap + 3 * mm, yy2, "Heure départ :", st or "--:--", 30 * mm)
    yy2 = _draw_kv(c, left + col_w + col_gap + 3 * mm, yy2, "Heure retour :", et or "--:--", 30 * mm)
    yy2 = _draw_kv(c, left + col_w + col_gap + 3 * mm, yy2, "Lieu livraison :", _safe(payload.get("pickup_location")), 30 * mm)
    yy2 = _draw_kv(c, left + col_w + col_gap + 3 * mm, yy2, "Lieu restitution :", _safe(payload.get("return_location")), 30 * mm)

    y = y - box_h - 8 * mm

    # Options + notes
    _box(c, left, y, width, 22 * mm, "Options / Notes")
    opt = payload.get("options") or {}
    gps = "Oui" if opt.get("gps") else "Non"
    chf = "Oui" if opt.get("chauffeur") else "Non"
    bby = "Oui" if opt.get("baby_seat") else "Non"
    c.setFont("Helvetica", 10)
    c.drawString(left + 3 * mm, y - 8 * mm, f"GPS: {gps}   |   Chauffeur: {chf}   |   Siège bébé: {bby}")
    c.setFont("Helvetica", 9)
    notes = _safe(payload.get("notes"))
    if not notes:
        notes = "—"
    c.drawString(left + 3 * mm, y - 14 * mm, f"Notes: {notes[:120]}")

    y = y - 28 * mm

    # Etat véhicule (simple)
    _box(c, left, y, width, 36 * mm, "État du véhicule (départ / retour)")
    c.setFont("Helvetica", 9)
    c.drawString(left + 3 * mm, y - 9 * mm, "Départ : ☐ OK   ☐ Endommagé   ☐ Salissures   ☐ Équipement manquant   ☐ Autre : __________")
    c.drawString(left + 3 * mm, y - 16 * mm, "Retour : ☐ OK   ☐ Endommagé   ☐ Salissures   ☐ Équipement manquant   ☐ Autre : __________")
    c.drawString(left + 3 * mm, y - 24 * mm, "Km départ: __________   Km retour: __________   Carburant départ: ____   Carburant retour: ____")

    y = y - 44 * mm

    # Signatures
    _box(c, left, y, width, 22 * mm, "Signatures")
    c.setFont("Helvetica", 10)
    c.drawString(left + 3 * mm, y - 12 * mm, "Signature du loueur: ____________________")
    c.drawRightString(left + width - 3 * mm, y - 12 * mm, "Signature du locataire: ____________________")

    # Footer
    c.setFont("Helvetica", 8)
    c.drawRightString(left + width, 10 * mm, f"Généré le {_now_str()}")

    c.showPage()

    # Page 2+: Conditions générales (propre)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(left, H - 18 * mm, "CONDITIONS GÉNÉRALES")
    c.setFont("Helvetica", 9)

    text = c.beginText(left, H - 26 * mm)
    text.setLeading(12)

    conditions = [
        "1) Le locataire doit présenter une pièce d’identité valide et un permis en cours de validité.",
        "2) Le véhicule est remis après constat (état, accessoires, niveaux, kilométrage).",
        "3) Le locataire s’engage à utiliser le véhicule conformément au Code de la route.",
        "4) Il est interdit de sous-louer, d’utiliser à des fins illicites ou de confier à un conducteur non autorisé.",
        "5) En cas d’accident, prévenir immédiatement le loueur et établir un constat/PV.",
        "6) En cas de vol, déposer plainte immédiatement et informer le loueur sans délai.",
        "7) Le locataire supporte amendes, contraventions, frais liés à l’usage.",
        "8) Des frais supplémentaires peuvent s’appliquer: carburant manquant, dépassement, nettoyage, dégâts, retard.",
        "9) Restitution à la date/heure/lieu convenus, dans le même état (hors usure normale).",
        "10) En cas de litige, règlement amiable puis juridiction compétente du ressort du loueur.",
        "",
        "Le locataire reconnaît avoir lu et accepté les présentes conditions générales.",
        "",
        "Empreinte et signature du locataire: ________________________________",
    ]
    for line in conditions:
        text.textLine(line)

    c.drawText(text)
    c.showPage()
    c.save()

    return buf.getvalue()


# ----------------------------
# Month report PDF (Finance)
# ----------------------------
def build_month_report_pdf(title: str, lines: List[str]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    left = 16 * mm
    top = H - 18 * mm

    c.setFont("Helvetica-Bold", 16)
    c.drawString(left, top, title)

    c.setFont("Helvetica", 10)
    y = top - 12 * mm
    for line in lines:
        c.drawString(left, y, str(line))
        y -= 6 * mm
        if y < 20 * mm:
            c.showPage()
            y = H - 20 * mm

    c.setFont("Helvetica", 8)
    c.drawRightString(W - 12 * mm, 10 * mm, f"Généré le {_now_str()}")
    c.showPage()
    c.save()
    return buf.getvalue()

