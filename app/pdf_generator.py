# app/pdf_generator.py
from __future__ import annotations

import io
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth


# ============================================================
# Helpers dessin
# ============================================================

def _box(c: canvas.Canvas, x, y, w, h, lw=1):
    c.setLineWidth(lw)
    c.rect(x, y, w, h, stroke=1, fill=0)

def _hline(c: canvas.Canvas, x1, y, x2, lw=1):
    c.setLineWidth(lw)
    c.line(x1, y, x2, y)

def _vline(c: canvas.Canvas, x, y1, y2, lw=1):
    c.setLineWidth(lw)
    c.line(x, y1, x, y2)

def _txt(c: canvas.Canvas, x, y, text, size=9, bold=False):
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawString(x, y, text or "")

def _ctxt(c: canvas.Canvas, x, y, text, size=9, bold=False):
    font = "Helvetica-Bold" if bold else "Helvetica"
    c.setFont(font, size)
    t = text or ""
    w = stringWidth(t, font, size)
    c.drawString(x - w / 2.0, y, t)

def _wrap_lines(text: str, max_chars: int) -> List[str]:
    text = (text or "").replace("\r", "")
    out: List[str] = []
    for para in text.split("\n"):
        p = para.strip()
        if not p:
            out.append("")
            continue
        line = ""
        for word in p.split():
            if len(line) + len(word) + 1 <= max_chars:
                line = (line + " " + word).strip()
            else:
                out.append(line)
                line = word
        if line:
            out.append(line)
    return out

def _safe_float(v, default=0.0) -> float:
    try:
        return float(v)
    except Exception:
        return float(default)

def _safe_str(v) -> str:
    return (v or "").strip()


# ============================================================
# Logo simple (tu m'as dit: "logo je te laisse")
# ============================================================

def _draw_simple_logo(c: canvas.Canvas, x, y, w, h, brand_text="KADID ZOUHIR"):
    _box(c, x, y, w, h, lw=1)
    _ctxt(c, x + w/2, y + h*0.62, brand_text, size=10, bold=True)
    _ctxt(c, x + w/2, y + h*0.30, "Location de voitures", size=8, bold=False)


# ============================================================
# Company defaults
# ============================================================

DEFAULT_COMPANY = {
    "name": "KADID ZOUHIR",
    "subtitle": "Location de Voitures (avec ou sans chauffeur)",
    "phones": ["0782 39 52 74", "0552 00 03 19"],
    "address": "ALGER",
    "email": "contact@example.com",
}


# ============================================================
# API PUBLIC
# ============================================================

def build_contract_pdf(booking: Dict[str, Any], company: Optional[Dict[str, Any]] = None) -> bytes:
    """
    Génère un contrat très proche du modèle “fiche rose”.
    - Page 1: Formulaire
    - Page 2: Conditions générales (1 -> 9)
    """
    company = {**DEFAULT_COMPANY, **(company or {})}

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    _contract_page_1(c, W, H, booking, company)
    c.showPage()

    _contract_page_2_conditions(c, W, H, company)
    c.showPage()

    c.save()
    return buf.getvalue()


def build_month_report_pdf(title: str, lines: List[str]) -> bytes:
    """
    Utilisé par finance.py (ton import build_month_report_pdf).
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    margin = 18 * mm
    x = margin
    y = H - margin

    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, title)
    y -= 12 * mm

    c.setFont("Helvetica", 10)
    for ln in lines:
        if y < margin + 10 * mm:
            c.showPage()
            y = H - margin
            c.setFont("Helvetica", 10)
        c.drawString(x, y, ln or "")
        y -= 6 * mm

    c.save()
    return buf.getvalue()


# ============================================================
# PAGE 1: CONTRAT (FORMULAIRE)
# ============================================================

def _contract_page_1(c: canvas.Canvas, W, H, booking: Dict[str, Any], company: Dict[str, Any]):
    margin = 10 * mm
    left = margin
    right = W - margin
    bottom = margin
    top = H - margin

    # Cadre global
    _box(c, left, bottom, right - left, top - bottom, lw=1)

    # =========================
    # HEADER (logo + titre)
    # =========================
    header_h = 34 * mm
    header_y = top - header_h
    _box(c, left, header_y, right - left, header_h, lw=1)

    mid = left + (right - left) * 0.34
    _vline(c, mid, header_y, top, lw=1)

    # gauche: logo + info
    _draw_simple_logo(c, left + 3*mm, top - 28*mm, 34*mm, 20*mm, brand_text=company["name"])

    _txt(c, left + 40*mm, top - 8*mm, company["name"], size=12, bold=True)
    _txt(c, left + 40*mm, top - 13*mm, company["subtitle"], size=8)
    y = top - 19*mm
    for ph in company.get("phones", []):
        _txt(c, left + 40*mm, y, f"Tél: {ph}", size=8)
        y -= 4*mm
    _txt(c, left + 40*mm, y, f"Adresse: {company.get('address','')}", size=7); y -= 4*mm
    _txt(c, left + 40*mm, y, f"Email: {company.get('email','')}", size=7)

    # droite: titre + cases
    _ctxt(c, mid + (right-mid)/2, top - 9*mm, "CONTRAT DE LOCATION VÉHICULE", size=12, bold=True)

    x0 = mid + 4*mm
    cb_y = top - 18*mm
    _txt(c, x0, cb_y, "☐ Entreprise", size=9)
    _txt(c, x0 + 42*mm, cb_y, "☐ Particulier", size=9)

    ref = _safe_str(booking.get("contract_ref")) or _safe_str(booking.get("trello_card_id")) or "____"
    _txt(c, x0, cb_y - 7*mm, "Référence de contrat :", size=9)
    _box(c, x0 + 42*mm, cb_y - 10*mm, 48*mm, 7*mm, lw=1)
    _txt(c, x0 + 44*mm, cb_y - 8.5*mm, ref, size=10, bold=True)

    # =========================
    # 2 colonnes: Locataire / Objet location
    # =========================
    y_cursor = header_y - 4*mm
    section_h = 78 * mm
    y1 = y_cursor - section_h
    _box(c, left, y1, right-left, section_h, lw=1)

    split = left + (right-left)*0.56
    _vline(c, split, y1, y_cursor, lw=1)

    _ctxt(c, left + (split-left)/2, y_cursor - 5*mm, "Le Locataire", size=10, bold=True)
    _ctxt(c, split + (right-split)/2, y_cursor - 5*mm, "Objet de la location", size=10, bold=True)

    client_name = _safe_str(booking.get("client_name"))
    client_phone = _safe_str(booking.get("client_phone"))
    client_addr = _safe_str(booking.get("client_address"))
    client_doc_id = _safe_str(booking.get("doc_id")) or _safe_str(booking.get("client_doc_id"))
    driver_license = _safe_str(booking.get("driver_license"))

    vehicle_model = _safe_str(booking.get("vehicle_model")) or _safe_str(booking.get("vehicle_name"))
    vehicle_plate = _safe_str(booking.get("vehicle_plate"))
    vehicle_vin = _safe_str(booking.get("vehicle_vin"))

    start_date = _safe_str(booking.get("start_date"))
    end_date = _safe_str(booking.get("end_date"))
    heure_dep = _safe_str(booking.get("start_hour")) or (start_date[11:16] if "T" in start_date else "")
    heure_ret = _safe_str(booking.get("end_hour")) or (end_date[11:16] if "T" in end_date else "")
    d1 = start_date[:10] if len(start_date) >= 10 else ""
    d2 = end_date[:10] if len(end_date) >= 10 else ""

    pickup = _safe_str(booking.get("pickup_location"))
    retloc = _safe_str(booking.get("return_location"))

    # Locataire (haut)
    loc_x = left + 4*mm
    loc_y = y_cursor - 13*mm
    _txt(c, loc_x, loc_y, "Dénomination :", bold=True); _txt(c, loc_x + 28*mm, loc_y, client_name)
    loc_y -= 7*mm
    _txt(c, loc_x, loc_y, "Bon de Commande :", bold=True); _txt(c, loc_x + 35*mm, loc_y, ref)
    loc_y -= 7*mm
    _txt(c, loc_x, loc_y, "Registre de Commerce :", bold=True); _txt(c, loc_x + 40*mm, loc_y, "—")

    # Conducteurs
    loc_y -= 9*mm
    _txt(c, loc_x, loc_y, "Conducteur habilité 01", bold=True)
    _txt(c, loc_x + 64*mm, loc_y, "Conducteur habilité 02", bold=True)
    loc_y -= 6*mm
    _hline(c, left + 3*mm, loc_y, split - 3*mm, lw=0.6)

    yb = loc_y - 6*mm
    _txt(c, loc_x, yb, "Nom :", bold=True); _txt(c, loc_x+14*mm, yb, client_name); yb -= 6*mm
    _txt(c, loc_x, yb, "Adresse :", bold=True); _txt(c, loc_x+18*mm, yb, client_addr[:60]); yb -= 6*mm
    _txt(c, loc_x, yb, "P/conduire N° :", bold=True); _txt(c, loc_x+28*mm, yb, driver_license); yb -= 6*mm
    _txt(c, loc_x, yb, "N° Doc :", bold=True); _txt(c, loc_x+16*mm, yb, client_doc_id); yb -= 6*mm
    _txt(c, loc_x, yb, "N° Tél :", bold=True); _txt(c, loc_x+16*mm, yb, client_phone)

    # Date location (bas)
    dd_y = y1 + 22*mm
    _txt(c, loc_x, dd_y, "Date de location :", bold=True); _txt(c, loc_x+28*mm, dd_y, f"du {d1} au {d2}")
    dd_y -= 6*mm
    _txt(c, loc_x, dd_y, "Heure de départ :", bold=True); _txt(c, loc_x+28*mm, dd_y, heure_dep)
    _txt(c, loc_x+52*mm, dd_y, "Lieu de livraison :", bold=True); _txt(c, loc_x+82*mm, dd_y, pickup[:22])
    dd_y -= 6*mm
    _txt(c, loc_x, dd_y, "Heure retour :", bold=True); _txt(c, loc_x+28*mm, dd_y, heure_ret)
    _txt(c, loc_x+52*mm, dd_y, "Lieu restitution :", bold=True); _txt(c, loc_x+82*mm, dd_y, retloc[:22])

    # Objet location (droite)
    veh_x = split + 4*mm
    veh_y = y_cursor - 13*mm
    _txt(c, veh_x, veh_y, "Modèle :", bold=True); _txt(c, veh_x+18*mm, veh_y, vehicle_model[:30]); veh_y -= 7*mm
    _txt(c, veh_x, veh_y, "Immatriculation :", bold=True); _txt(c, veh_x+32*mm, veh_y, vehicle_plate); veh_y -= 7*mm
    _txt(c, veh_x, veh_y, "N° série :", bold=True); _txt(c, veh_x+18*mm, veh_y, vehicle_vin[:28])

    pb_y = y_cursor - 35*mm
    _txt(c, veh_x, pb_y, "☐ Aucun problèmes", size=9); pb_y -= 6*mm
    _txt(c, veh_x, pb_y, "☐ Véhicule endommagé", size=9); pb_y -= 6*mm
    _txt(c, veh_x, pb_y, "☐ Autre Problèmes :", size=9); pb_y -= 7*mm
    _txt(c, veh_x + 4*mm, pb_y, "○ Salissures", size=9); pb_y -= 6*mm
    _txt(c, veh_x + 4*mm, pb_y, "○ Equipement Manquants", size=9); pb_y -= 6*mm
    _txt(c, veh_x + 4*mm, pb_y, "○ Brûlures des sièges", size=9); pb_y -= 6*mm
    _txt(c, veh_x + 4*mm, pb_y, "○ Autres", size=9)

    # =========================
    # Bloc retour + compteur
    # =========================
    y2_top = y1 - 4*mm
    block_h = 48 * mm
    y2 = y2_top - block_h
    _box(c, left, y2, right-left, block_h, lw=1)

    col1 = left + (right-left)*0.38
    col2 = left + (right-left)*0.68
    _vline(c, col1, y2, y2_top, lw=1)
    _vline(c, col2, y2, y2_top, lw=1)

    _ctxt(c, left + (col1-left)/2, y2_top - 5*mm, "A remplir au retour", size=10, bold=True)

    bx = left + 4*mm
    by = y2_top - 15*mm
    _txt(c, bx, by, "Date:", bold=True); _txt(c, bx+14*mm, by, "__________")
    _txt(c, bx+45*mm, by, "Heur:", bold=True); _txt(c, bx+58*mm, by, "_____")
    by -= 8*mm
    _txt(c, bx, by, "Nbre Km:", bold=True); _txt(c, bx+18*mm, by, "__________")
    by -= 8*mm
    _txt(c, bx, by, "Niveau carburant", bold=True)

    _ctxt(c, col1 + (col2-col1)/2, y2_top - 22*mm, "SCHÉMA VÉHICULE", size=9, bold=True)
    _box(c, col1 + 10*mm, y2 + 10*mm, (col2-col1) - 20*mm, block_h - 28*mm, lw=1)

    _ctxt(c, col2 + (right-col2)/2, y2_top - 10*mm, "Nombre Km au Compteur", size=10, bold=True)
    _txt(c, col2 + 10*mm, y2_top - 18*mm, "Km: ____________________", size=9)
    _txt(c, col2 + 10*mm, y2_top - 26*mm, "Niveau de Carburant", size=9, bold=True)

    # =========================
    # Signatures
    # =========================
    y3_top = y2 - 4*mm
    sig_h = 35 * mm
    y3 = y3_top - sig_h
    _box(c, left, y3, right-left, sig_h, lw=1)

    mid2 = left + (right-left)/2
    _vline(c, mid2, y3, y3_top, lw=1)

    _ctxt(c, left + (mid2-left)/2, y3_top - 7*mm, "Signature du loueur", bold=True)
    _ctxt(c, mid2 + (right-mid2)/2, y3_top - 7*mm, "Signature du locataire", bold=True)

    # “Cachet” (rond) simulé
    stamp_x = left + 12*mm
    stamp_y = y3 + 6*mm
    c.setLineWidth(1)
    c.circle(stamp_x + 16*mm, stamp_y + 10*mm, 12*mm, stroke=1, fill=0)
    _ctxt(c, stamp_x + 16*mm, stamp_y + 10*mm, company["name"], size=7, bold=True)
    _ctxt(c, stamp_x + 16*mm, stamp_y + 6*mm, "Location", size=6, bold=False)

    _txt(c, left, bottom - 6*mm, f"Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')}", size=7)


# ============================================================
# PAGE 2: CONDITIONS GENERALES (1 -> 9) — proche du modèle
# ============================================================

def _contract_page_2_conditions(c: canvas.Canvas, W, H, company: Dict[str, Any]):
    margin = 10 * mm
    left, right = margin, W - margin
    top, bottom = H - margin, margin

    _box(c, left, bottom, right-left, top-bottom, lw=1)
    _ctxt(c, W/2, top - 10*mm, "CONDITIONS GENERALES", size=16, bold=True)

    conditions = """
1- Définition :
Les présentes conditions générales régissent la location du véhicule (VP) mis à disposition par le loueur. Le locataire reconnaît avoir pris connaissance de ces conditions et les accepte.

2- Condition de location d’un véhicule :
• Le locataire doit présenter une pièce d’identité valide et un permis de conduire en cours de validité.
• Le locataire s’engage à fournir des informations exactes (nom, adresse, téléphone, document, permis, etc.).
• Le véhicule est remis au locataire après constat (état du véhicule, accessoires, niveaux, kilométrage).

3- Véhicule (état – utilisation – obligations) :
• Le locataire s’engage à utiliser le véhicule conformément au Code de la route et à en prendre soin.
• Il est interdit de sous-louer le véhicule, de l’utiliser pour des fins illicites, de transport non autorisé ou en compétition.
• Le locataire ne doit pas confier le véhicule à un conducteur non déclaré / non autorisé.
• Le locataire supporte les amendes, contraventions et frais liés à son usage.

4- Durée de la location :
• La durée figure sur le contrat. Tout dépassement non autorisé peut entraîner une facturation supplémentaire.
• Toute prolongation nécessite l’accord préalable du loueur.
• En cas de retard de restitution, le loueur peut appliquer des pénalités (heure/jour supplémentaire).

5- Accident :
• En cas d’accident, le locataire doit prévenir immédiatement le loueur et établir un constat amiable (ou PV).
• Le locataire ne doit pas abandonner le véhicule sans instructions du loueur.
• Les frais de remise en état et/ou la franchise d’assurance peuvent rester à la charge du locataire selon responsabilité.

6- Vol de véhicule :
• En cas de vol, le locataire doit déposer plainte immédiatement et informer le loueur sans délai.
• Les clés et documents du véhicule doivent être remis au loueur.
• Les pertes, dommages et frais liés au vol peuvent être imputés au locataire selon les conditions du contrat/assurance.

7- Assurances :
• Le véhicule peut être couvert par une assurance selon les conditions du loueur.
• Exclusions possibles (conduite non autorisée, alcool/stupéfiants, usage illicite, négligence, non-respect des obligations).
• Le locataire reste responsable de toute somme non prise en charge par l’assurance (franchise/exclusions).

8- Conditions financières :
• Le tarif comprend la location pour la période convenue.
• Frais supplémentaires possibles : carburant manquant, dépassement kilométrique, nettoyage, dégradations, retard.
• Le dépôt de garantie/caution peut être retenu en tout ou partie en cas de dommages, manquants ou impayés.

9- Disposition (restitution – dépôt – litiges) :
• Le véhicule doit être restitué à la date/heure et au lieu convenus, dans le même état qu’au départ (hors usure normale).
• Un état des lieux est réalisé au retour (carrosserie, accessoires, niveaux, kilométrage, propreté).
• En cas de litige, un règlement amiable est privilégié ; à défaut, la juridiction compétente est celle du ressort du loueur.

Empreintes et Signature :
Le locataire reconnaît avoir lu et accepté les présentes conditions générales.
""".strip()

    lines = _wrap_lines(conditions, max_chars=105)

    y = top - 22*mm
    c.setFont("Helvetica", 9)

    for ln in lines:
        if y < bottom + 18*mm:
            c.showPage()
            _box(c, left, bottom, right-left, top-bottom, lw=1)
            _ctxt(c, W/2, top - 10*mm, "CONDITIONS GENERALES (suite)", size=16, bold=True)
            y = top - 22*mm
            c.setFont("Helvetica", 9)

        c.drawString(left + 6*mm, y, ln)
        y -= 4.6*mm

    # Bas: ligne signature
    _hline(c, left + 6*mm, bottom + 22*mm, right - 6*mm, lw=0.8)
    _ctxt(c, W/2, bottom + 14*mm, "Empreintes et Signature", size=11, bold=True)

