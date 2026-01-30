# app/pdf_generator.py
from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ============================================================
# Fonts (Unicode / Arabic best-effort)
# ============================================================

_DEFAULT_FONT = "Helvetica"
_DEFAULT_FONT_BOLD = "Helvetica-Bold"

# Optional: if you add a ttf font (recommended) it will be used.
# Put a font here for better Arabic + accents:
#   app/static/fonts/DejaVuSans.ttf
#   app/static/fonts/DejaVuSans-Bold.ttf
UNICODE_FONT_REGULAR = os.getenv("PDF_UNICODE_FONT_REGULAR", "DejaVuSans")
UNICODE_FONT_BOLD = os.getenv("PDF_UNICODE_FONT_BOLD", "DejaVuSans-Bold")


def _try_register_unicode_fonts() -> Tuple[str, str]:
    """
    Try to register DejaVu fonts if present. Falls back to Helvetica.
    """
    # Common paths you may use in your repo
    candidates = [
        ("app/static/fonts/DejaVuSans.ttf", "app/static/fonts/DejaVuSans-Bold.ttf"),
        ("static/fonts/DejaVuSans.ttf", "static/fonts/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]

    for reg_path, bold_path in candidates:
        if os.path.exists(reg_path) and os.path.exists(bold_path):
            try:
                pdfmetrics.registerFont(TTFont(UNICODE_FONT_REGULAR, reg_path))
                pdfmetrics.registerFont(TTFont(UNICODE_FONT_BOLD, bold_path))
                return UNICODE_FONT_REGULAR, UNICODE_FONT_BOLD
            except Exception:
                pass

    return _DEFAULT_FONT, _DEFAULT_FONT_BOLD


FONT_REG, FONT_BOLD = _try_register_unicode_fonts()


def _maybe_ar(text: str) -> str:
    """
    Best-effort Arabic shaping (optional libs).
    If libs not installed, returns raw text (still works but may look disconnected).
    """
    if not text:
        return ""
    try:
        import arabic_reshaper  # type: ignore
        from bidi.algorithm import get_display  # type: ignore

        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


# ============================================================
# Language blocks (FR / EN / AR)
# ============================================================

COMPANY = {
    "name": "Zohir Location Auto",
    "tagline_fr": "Location de voitures (avec ou sans chauffeur)",
    "tagline_en": "Car rental (with or without driver)",
    "tagline_ar": "كراء السيارات (مع أو بدون سائق)",
    "phone1": os.getenv("COMPANY_PHONE_1", "+213 ..."),
    "phone2": os.getenv("COMPANY_PHONE_2", ""),
    "address": os.getenv("COMPANY_ADDRESS", "Alger"),
    "email": os.getenv("COMPANY_EMAIL", "contact@..."),
}

LABELS = {
    "fr": {
        "title": "CONTRAT DE LOCATION VÉHICULE",
        "enterprise": "Entreprise",
        "individual": "Particulier",
        "ref": "Référence de contrat",
        "tenant": "Le Locataire",
        "renter": "Le Loueur",
        "vehicle": "Objet de la location",
        "denomination": "Dénomination",
        "phone": "Téléphone",
        "address": "Adresse",
        "doc": "Document (CNI/Passeport)",
        "permit": "Permis",
        "driver1": "Conducteur habilité 01",
        "driver2": "Conducteur habilité 02",
        "name": "Nom / Prénom",
        "pickup_date": "Date de location",
        "from": "du",
        "to": "au",
        "pickup_time": "Heure de départ",
        "pickup_place": "Lieu de livraison",
        "return_place": "Lieu de restitution",
        "model": "Modèle",
        "plate": "Immatriculation",
        "vin": "N° série (VIN)",
        "state": "État du véhicule",
        "ok": "Aucun problèmes",
        "damaged": "Véhicule endommagé",
        "other_pb": "Autres problèmes",
        "dirt": "Salissures",
        "missing": "Équipement manquants",
        "burns": "Brûlures des sièges",
        "other": "Autres",
        "return_fill": "À remplir au retour",
        "km": "Nombre Km au Compteur",
        "fuel": "Niveau de Carburant",
        "sign_renter": "Signature du loueur",
        "sign_tenant": "Signature du locataire",
        "conditions": "CONDITIONS GÉNÉRALES",
        "page": "Page",
        "options": "Options",
        "gps": "GPS",
        "chauffeur": "Chauffeur",
        "baby": "Siège bébé",
        "notes": "Notes",
    },
    "en": {
        "title": "VEHICLE RENTAL CONTRACT",
        "enterprise": "Company",
        "individual": "Individual",
        "ref": "Contract reference",
        "tenant": "Renter",
        "renter": "Owner",
        "vehicle": "Vehicle details",
        "denomination": "Full name",
        "phone": "Phone",
        "address": "Address",
        "doc": "Document (ID/Passport)",
        "permit": "Driving license",
        "driver1": "Authorized driver 01",
        "driver2": "Authorized driver 02",
        "name": "Name",
        "pickup_date": "Rental period",
        "from": "from",
        "to": "to",
        "pickup_time": "Departure time",
        "pickup_place": "Pickup place",
        "return_place": "Return place",
        "model": "Model",
        "plate": "Plate",
        "vin": "Serial number (VIN)",
        "state": "Vehicle condition",
        "ok": "No issues",
        "damaged": "Damaged vehicle",
        "other_pb": "Other issues",
        "dirt": "Dirt",
        "missing": "Missing equipment",
        "burns": "Seat burns",
        "other": "Other",
        "return_fill": "To be filled on return",
        "km": "Odometer (Km)",
        "fuel": "Fuel level",
        "sign_renter": "Owner signature",
        "sign_tenant": "Renter signature",
        "conditions": "GENERAL TERMS",
        "page": "Page",
        "options": "Options",
        "gps": "GPS",
        "chauffeur": "Driver",
        "baby": "Baby seat",
        "notes": "Notes",
    },
    "ar": {
        "title": _maybe_ar("عقد كراء سيارة"),
        "enterprise": _maybe_ar("شركة"),
        "individual": _maybe_ar("شخص"),
        "ref": _maybe_ar("مرجع العقد"),
        "tenant": _maybe_ar("المستأجر"),
        "renter": _maybe_ar("المؤجر"),
        "vehicle": _maybe_ar("معلومات السيارة"),
        "denomination": _maybe_ar("الاسم و اللقب"),
        "phone": _maybe_ar("الهاتف"),
        "address": _maybe_ar("العنوان"),
        "doc": _maybe_ar("وثيقة (بطاقة/جواز)"),
        "permit": _maybe_ar("رخصة السياقة"),
        "driver1": _maybe_ar("السائق 01"),
        "driver2": _maybe_ar("السائق 02"),
        "name": _maybe_ar("الاسم"),
        "pickup_date": _maybe_ar("مدة الكراء"),
        "from": _maybe_ar("من"),
        "to": _maybe_ar("إلى"),
        "pickup_time": _maybe_ar("ساعة الانطلاق"),
        "pickup_place": _maybe_ar("مكان التسليم"),
        "return_place": _maybe_ar("مكان الاسترجاع"),
        "model": _maybe_ar("الطراز"),
        "plate": _maybe_ar("الترقيم"),
        "vin": _maybe_ar("الرقم التسلسلي"),
        "state": _maybe_ar("حالة السيارة"),
        "ok": _maybe_ar("لا مشاكل"),
        "damaged": _maybe_ar("السيارة متضررة"),
        "other_pb": _maybe_ar("مشاكل أخرى"),
        "dirt": _maybe_ar("اتساخ"),
        "missing": _maybe_ar("نقص في التجهيزات"),
        "burns": _maybe_ar("حروق المقاعد"),
        "other": _maybe_ar("أخرى"),
        "return_fill": _maybe_ar("يملأ عند الرجوع"),
        "km": _maybe_ar("عداد الكيلومترات"),
        "fuel": _maybe_ar("مستوى الوقود"),
        "sign_renter": _maybe_ar("إمضاء المؤجر"),
        "sign_tenant": _maybe_ar("إمضاء المستأجر"),
        "conditions": _maybe_ar("الشروط العامة"),
        "page": _maybe_ar("صفحة"),
        "options": _maybe_ar("الخيارات"),
        "gps": _maybe_ar("GPS"),
        "chauffeur": _maybe_ar("سائق"),
        "baby": _maybe_ar("مقعد طفل"),
        "notes": _maybe_ar("ملاحظات"),
    },
}


CONDITIONS_FR = [
    "1. Définitions : Le loueur met à disposition un véhicule au locataire selon les présentes conditions.",
    "2. Conditions du conducteur : Le conducteur doit présenter une pièce d’identité et un permis valides.",
    "3. État du véhicule : Le locataire reconnaît l’état du véhicule au départ (photos recommandées).",
    "4. Durée de location : La location est consentie pour la période indiquée au contrat. Tout dépassement peut être facturé.",
    "5. Accident / Incident : Tout accident doit être signalé immédiatement au loueur (photos + constat si possible).",
    "6. Vol : En cas de vol, le locataire doit déposer plainte et remettre le récépissé au loueur.",
    "7. Assurance : Les modalités d’assurance / franchise sont celles indiquées par le loueur. Exclusions possibles.",
    "8. Conditions financières : Le locataire s’engage à régler le montant convenu. Carburant, péages, amendes à sa charge.",
    "9. Restitution : Le véhicule doit être restitué à la date/heure prévues, avec le niveau carburant convenu.",
    "10. Litiges : En cas de litige, une solution amiable est privilégiée avant toute action.",
]

CONDITIONS_EN = [
    "1. Definitions: The owner rents a vehicle to the renter under these terms.",
    "2. Driver requirements: Valid ID and driving license are required.",
    "3. Vehicle condition: The renter acknowledges the vehicle condition at pickup (photos recommended).",
    "4. Rental period: The contract applies for the stated dates. Extensions may be billed.",
    "5. Accident/Incident: Any incident must be reported immediately (photos and report when applicable).",
    "6. Theft: In case of theft, a police report must be filed and provided to the owner.",
    "7. Insurance: Insurance/franchise terms apply as specified by the owner. Exclusions may apply.",
    "8. Financial terms: The renter pays the agreed amount. Fuel, tolls, fines are renter’s responsibility.",
    "9. Return: Vehicle must be returned on time, with agreed fuel level.",
    "10. Disputes: Parties shall seek an amicable solution before legal action.",
]

CONDITIONS_AR = [
    _maybe_ar("1. تعاريف: يقوم المؤجر بوضع السيارة تحت تصرف المستأجر وفق الشروط التالية."),
    _maybe_ar("2. شروط السائق: يجب تقديم بطاقة هوية ورخصة سياقة ساريتين."),
    _maybe_ar("3. حالة السيارة: يصرح المستأجر بأنه استلم السيارة في الحالة الموضحة عند التسليم."),
    _maybe_ar("4. مدة الكراء: الكراء محدد بالفترة المذكورة، وكل تمديد قد يكون مدفوعًا."),
    _maybe_ar("5. حادث/ضرر: يجب الإبلاغ فورًا عن أي حادث أو ضرر مع صور إن أمكن."),
    _maybe_ar("6. سرقة: في حالة السرقة يجب تقديم شكوى لدى الجهات المختصة."),
    _maybe_ar("7. التأمين: تطبق شروط التأمين/الفرانشيز حسب ما يحدده المؤجر."),
    _maybe_ar("8. الشروط المالية: الوقود، المخالفات والرسوم على عاتق المستأجر."),
    _maybe_ar("9. الاسترجاع: تُعاد السيارة في الوقت المحدد وبمستوى الوقود المتفق عليه."),
    _maybe_ar("10. النزاعات: يُفضل الحل الودي قبل اللجوء إلى القضاء."),
]


def _conditions_for_lang(lang: str) -> List[str]:
    if lang == "en":
        return CONDITIONS_EN
    if lang == "ar":
        return CONDITIONS_AR
    return CONDITIONS_FR


# ============================================================
# Helpers
# ============================================================

def _safe(s: Any) -> str:
    return ("" if s is None else str(s)).strip()


def _draw_checkbox(c: canvas.Canvas, x: float, y: float, size: float, checked: bool = False):
    c.rect(x, y, size, size, stroke=1, fill=0)
    if checked:
        c.setLineWidth(2)
        c.line(x + 2, y + size / 2, x + size / 2, y + 2)
        c.line(x + size / 2, y + 2, x + size - 2, y + size - 2)
        c.setLineWidth(1)


def _draw_title_box(c: canvas.Canvas, x: float, y: float, w: float, h: float, title: str):
    c.setFillColor(colors.whitesmoke)
    c.rect(x, y, w, h, stroke=1, fill=0)
    c.setFont(FONT_BOLD, 14)
    c.drawString(x + 8, y + h - 18, title)


def _draw_company_box(c: canvas.Canvas, x: float, y: float, w: float, h: float, lang: str):
    c.rect(x, y, w, h, stroke=1, fill=0)
    c.setFont(FONT_BOLD, 11)
    c.drawString(x + 8, y + h - 16, COMPANY["name"])

    c.setFont(FONT_REG, 8.5)
    tagline = COMPANY["tagline_fr"] if lang == "fr" else COMPANY["tagline_en"] if lang == "en" else COMPANY["tagline_ar"]
    c.drawString(x + 8, y + h - 30, _safe(tagline))

    c.setFont(FONT_REG, 8.5)
    c.drawString(x + 8, y + h - 44, f"☎ {COMPANY['phone1']}".strip())
    if COMPANY["phone2"]:
        c.drawString(x + 8, y + h - 56, f"☎ {COMPANY['phone2']}".strip())
        line_y = y + h - 68
    else:
        line_y = y + h - 56

    c.drawString(x + 8, line_y, f"📍 {COMPANY['address']}".strip())
    c.drawString(x + 8, line_y - 12, f"✉ {COMPANY['email']}".strip())


def _draw_kv(c: canvas.Canvas, x: float, y: float, label: str, value: str, w: float, h: float):
    c.rect(x, y, w, h, stroke=1, fill=0)
    c.setFont(FONT_REG, 8)
    c.drawString(x + 6, y + h - 11, label)
    c.setFont(FONT_BOLD, 9.5)
    c.drawString(x + 6, y + 6, value[:60])


def _draw_multiline(c: canvas.Canvas, x: float, y: float, w: float, h: float, label: str, lines: List[str]):
    c.rect(x, y, w, h, stroke=1, fill=0)
    c.setFont(FONT_REG, 8)
    c.drawString(x + 6, y + h - 11, label)
    c.setFont(FONT_REG, 9)
    yy = y + h - 24
    for ln in lines[:6]:
        c.drawString(x + 6, yy, ln[:90])
        yy -= 12


def _fmt_dt_local(dt_str: str) -> str:
    """
    Accepts "2026-01-29T10:00" and returns "2026-01-29 10:00"
    """
    s = _safe(dt_str)
    if "T" in s:
        return s.replace("T", " ")
    return s


def _contract_ref(payload: Dict[str, Any]) -> str:
    # Prefer an explicit field if you add one later.
    ref = _safe(payload.get("contract_ref"))
    if ref:
        return ref
    # fallback: use Trello card id (short) + date
    cid = _safe(payload.get("trello_card_id"))
    short = cid[-6:] if len(cid) >= 6 else cid
    return f"{datetime.now().strftime('%Y%m%d')}-{short}".strip("-")


# ============================================================
# Main: Contract PDF (2 pages)
# ============================================================

def build_contract_pdf(payload: Dict[str, Any], lang: str = "fr") -> bytes:
    lang = (lang or "fr").lower().strip()
    if lang not in ("fr", "en", "ar"):
        lang = "fr"

    L = LABELS[lang]
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    # Page 1: Form layout (similar to your photo)
    _draw_contract_page_1(c, payload, lang, L, W, H)

    c.showPage()

    # Page 2: Conditions générales
    _draw_contract_page_2_conditions(c, lang, L, W, H)

    c.save()
    return buf.getvalue()


def _draw_contract_page_1(c: canvas.Canvas, payload: Dict[str, Any], lang: str, L: Dict[str, str], W: float, H: float):
    margin = 12 * mm
    top = H - margin

    c.setStrokeColor(colors.white)
    c.setFillColor(colors.white)

    # Outer frame
    c.setLineWidth(1)
    c.rect(margin, margin, W - 2 * margin, H - 2 * margin, stroke=1, fill=0)

    # Header boxes
    company_w = (W - 2 * margin) * 0.34
    title_w = (W - 2 * margin) - company_w - 6
    header_h = 38 * mm

    x0 = margin
    y0 = top - header_h

    _draw_company_box(c, x0, y0, company_w, header_h, lang)

    # Title box
    c.rect(x0 + company_w + 6, y0, title_w, header_h, stroke=1, fill=0)
    c.setFont(FONT_BOLD, 13)
    c.drawString(x0 + company_w + 14, y0 + header_h - 18, L["title"])

    # Enterprise/Individual checkboxes + reference
    cb_size = 10
    c.setFont(FONT_REG, 9)

    # Checkboxes row
    cx = x0 + company_w + 14
    cy = y0 + header_h - 34
    _draw_checkbox(c, cx, cy, cb_size, checked=False)
    c.drawString(cx + cb_size + 6, cy + 2, L["enterprise"])

    cx2 = cx + 120
    _draw_checkbox(c, cx2, cy, cb_size, checked=True)  # default: individual checked
    c.drawString(cx2 + cb_size + 6, cy + 2, L["individual"])

    # Contract ref field
    ref_y = y0 + 8
    c.setFont(FONT_REG, 9)
    c.drawString(x0 + company_w + 14, ref_y + 16, f"{L['ref']} :")
    c.setFont(FONT_BOLD, 10.5)
    c.drawString(x0 + company_w + 120, ref_y + 16, _contract_ref(payload))

    # Body: two big panels (left renter, right vehicle)
    body_top = y0 - 8
    body_h = 112 * mm
    left_w = (W - 2 * margin) * 0.52
    right_w = (W - 2 * margin) - left_w - 6

    left_x = margin
    right_x = margin + left_w + 6
    body_y = body_top - body_h

    # Panel titles
    c.setFont(FONT_BOLD, 11)
    c.rect(left_x, body_y, left_w, body_h, stroke=1, fill=0)
    c.drawString(left_x + 8, body_y + body_h - 16, L["tenant"])

    c.rect(right_x, body_y, right_w, body_h, stroke=1, fill=0)
    c.drawString(right_x + 8, body_y + body_h - 16, L["vehicle"])

    # Left panel fields
    p_client = _safe(payload.get("client_name"))
    p_phone = _safe(payload.get("client_phone"))
    p_addr = _safe(payload.get("client_address"))
    p_doc = _safe(payload.get("doc_id"))
    p_permit = _safe(payload.get("driver_license"))

    # rental period / places
    p_start = _fmt_dt_local(_safe(payload.get("start_date")))
    p_end = _fmt_dt_local(_safe(payload.get("end_date")))
    p_pick = _safe(payload.get("pickup_location"))
    p_ret = _safe(payload.get("return_location"))

    # Small grid inside left panel
    grid_x = left_x + 6
    grid_top = body_y + body_h - 26
    row_h = 14 * mm

    _draw_kv(c, grid_x, grid_top - row_h, left_w - 12, row_h, L["denomination"], p_client, w=left_w - 12, h=row_h)
    _draw_kv(c, grid_x, grid_top - 2 * row_h, (left_w - 12) * 0.52, row_h, L["phone"], p_phone, w=(left_w - 12) * 0.52, h=row_h)
    _draw_kv(c, grid_x + (left_w - 12) * 0.52 + 6, grid_top - 2 * row_h, (left_w - 12) * 0.48 - 6, row_h, L["doc"], p_doc, w=(left_w - 12) * 0.48 - 6, h=row_h)

    _draw_kv(c, grid_x, grid_top - 3 * row_h, left_w - 12, row_h, L["address"], p_addr, w=left_w - 12, h=row_h)
    _draw_kv(c, grid_x, grid_top - 4 * row_h, left_w - 12, row_h, L["permit"], p_permit, w=left_w - 12, h=row_h)

    # Dates
    date_box_h = 16 * mm
    _draw_multiline(
        c,
        grid_x,
        grid_top - 5 * row_h - 2,
        left_w - 12,
        date_box_h,
        L["pickup_date"],
        [f"{L['from']} {p_start}", f"{L['to']} {p_end}"],
    )

    # Places
    place_box_h = 22 * mm
    _draw_multiline(
        c,
        grid_x,
        body_y + 18 * mm,
        left_w - 12,
        place_box_h,
        "",
        [f"{L['pickup_place']}: {p_pick}", f"{L['return_place']}: {p_ret}"],
    )

    # Right panel fields (vehicle)
    v_name = _safe(payload.get("vehicle_name"))
    v_plate = _safe(payload.get("vehicle_plate"))
    v_model = _safe(payload.get("vehicle_model")) or v_name
    v_vin = _safe(payload.get("vehicle_vin"))

    rx = right_x + 6
    rt = body_y + body_h - 26

    _draw_kv(c, rx, rt - row_h, right_w - 12, row_h, L["model"], v_model, w=right_w - 12, h=row_h)
    _draw_kv(c, rx, rt - 2 * row_h, right_w - 12, row_h, L["plate"], v_plate, w=right_w - 12, h=row_h)
    _draw_kv(c, rx, rt - 3 * row_h, right_w - 12, row_h, L["vin"], v_vin, w=right_w - 12, h=row_h)

    # Condition checkboxes
    c.setFont(FONT_BOLD, 10)
    c.drawString(rx, rt - 3 * row_h - 16, L["state"])
    c.setFont(FONT_REG, 9)

    opt_y = rt - 3 * row_h - 34
    cb = 10
    _draw_checkbox(c, rx, opt_y, cb, checked=True)
    c.drawString(rx + cb + 6, opt_y + 2, L["ok"])

    opt_y -= 14
    _draw_checkbox(c, rx, opt_y, cb, checked=False)
    c.drawString(rx + cb + 6, opt_y + 2, L["damaged"])

    opt_y -= 14
    _draw_checkbox(c, rx, opt_y, cb, checked=False)
    c.drawString(rx + cb + 6, opt_y + 2, L["other_pb"])

    # sub items
    subx = rx + 18
    opt_y -= 14
    _draw_checkbox(c, subx, opt_y, cb, checked=False)
    c.drawString(subx + cb + 6, opt_y + 2, L["dirt"])

    opt_y -= 14
    _draw_checkbox(c, subx, opt_y, cb, checked=False)
    c.drawString(subx + cb + 6, opt_y + 2, L["missing"])

    opt_y -= 14
    _draw_checkbox(c, subx, opt_y, cb, checked=False)
    c.drawString(subx + cb + 6, opt_y + 2, L["burns"])

    opt_y -= 14
    _draw_checkbox(c, subx, opt_y, cb, checked=False)
    c.drawString(subx + cb + 6, opt_y + 2, L["other"])

    # Options box + notes
    options = payload.get("options") or {}
    gps = bool(options.get("gps"))
    chauffeur = bool(options.get("chauffeur"))
    baby = bool(options.get("baby_seat"))

    c.setFont(FONT_BOLD, 10)
    c.drawString(rx, body_y + 52, L["options"])
    c.setFont(FONT_REG, 9)
    oy = body_y + 38
    _draw_checkbox(c, rx, oy, cb, checked=gps)
    c.drawString(rx + cb + 6, oy + 2, L["gps"])
    _draw_checkbox(c, rx + 90, oy, cb, checked=chauffeur)
    c.drawString(rx + 90 + cb + 6, oy + 2, L["chauffeur"])
    _draw_checkbox(c, rx, oy - 14, cb, checked=baby)
    c.drawString(rx + cb + 6, oy - 12, L["baby"])

    notes = _safe(payload.get("notes"))
    _draw_multiline(c, rx, body_y + 6, right_w - 12, 26 * mm, L["notes"], [notes])

    # Bottom area: return fill + signatures
    bottom_top = body_y - 8
    bottom_h = (bottom_top - margin) - 10
    bottom_y = margin + 10

    # Return fill section
    c.rect(margin, bottom_y + 38 * mm, W - 2 * margin, 30 * mm, stroke=1, fill=0)
    c.setFont(FONT_BOLD, 10.5)
    c.drawString(margin + 8, bottom_y + 38 * mm + 30 * mm - 14, L["return_fill"])

    # Odometer/fuel boxes
    bx = margin + 8
    by = bottom_y + 42 * mm
    bw = (W - 2 * margin - 24) / 2
    bh = 18 * mm

    _draw_kv(c, bx, by, bw, bh, L["km"], "", w=bw, h=bh)
    _draw_kv(c, bx + bw + 8, by, bw, bh, L["fuel"], "", w=bw, h=bh)

    # Signatures
    sig_y = bottom_y
    sig_h = 34 * mm
    sig_w = (W - 2 * margin - 10) / 2

    c.rect(margin, sig_y, sig_w, sig_h, stroke=1, fill=0)
    c.rect(margin + sig_w + 10, sig_y, sig_w, sig_h, stroke=1, fill=0)

    c.setFont(FONT_REG, 9)
    c.drawString(margin + 8, sig_y + sig_h - 14, L["sign_renter"])
    c.drawString(margin + sig_w + 18, sig_y + sig_h - 14, L["sign_tenant"])

    # Small footer
    c.setFont(FONT_REG, 7.5)
    c.setFillColor(colors.grey)
    c.drawRightString(W - margin, margin - 2, f"{L['page']} 1/2")
    c.setFillColor(colors.white)


def _draw_contract_page_2_conditions(c: canvas.Canvas, lang: str, L: Dict[str, str], W: float, H: float):
    margin = 14 * mm
    c.setStrokeColor(colors.white)
    c.setFillColor(colors.white)

    # Title
    c.setFont(FONT_BOLD, 15)
    c.drawString(margin, H - margin - 10, L["conditions"])

    # Two-column conditions like your photo
    items = _conditions_for_lang(lang)
    col_gap = 10 * mm
    col_w = (W - 2 * margin - col_gap) / 2
    top_y = H - margin - 30
    bottom_y = margin + 14

    c.setFont(FONT_REG, 10)
    line_h = 12

    # split items roughly in half
    mid = (len(items) + 1) // 2
    cols = [items[:mid], items[mid:]]

    for ci in range(2):
        x = margin + ci * (col_w + col_gap)
        y = top_y
        for paragraph in cols[ci]:
            lines = _wrap_text(paragraph, max_chars=78 if ci == 0 else 78)
            for ln in lines:
                if y < bottom_y:
                    break
                c.drawString(x, y, ln)
                y -= line_h
            y -= 6  # paragraph spacing

    # Signature line at bottom like “Empreintes et Signature”
    c.setFont(FONT_REG, 9)
    c.setFillColor(colors.grey)
    c.drawString(margin, margin + 6, "Empreintes et Signature / Signatures")
    c.setFillColor(colors.white)

    c.setFont(FONT_REG, 7.5)
    c.setFillColor(colors.grey)
    c.drawRightString(W - margin, margin - 2, f"{L['page']} 2/2")
    c.setFillColor(colors.white)


def _wrap_text(text: str, max_chars: int = 80) -> List[str]:
    """
    Simple word wrap (avoids reportlab Paragraph for full-canvas approach).
    """
    s = _safe(text)
    if not s:
        return [""]
    words = s.split()
    lines = []
    cur = ""
    for w in words:
        if len(cur) + len(w) + 1 <= max_chars:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ============================================================
# Finance PDF (for your finance.py import)
# ============================================================

def build_month_report_pdf(title: str, lines: List[str]) -> bytes:
    """
    Simple PDF report for finance.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    margin = 18 * mm
    y = H - margin

    c.setFont(FONT_BOLD, 16)
    c.drawString(margin, y, _safe(title))
    y -= 22

    c.setFont(FONT_REG, 11)
    for ln in lines:
        if y < margin:
            c.showPage()
            y = H - margin
            c.setFont(FONT_REG, 11)
        c.drawString(margin, y, _safe(ln))
        y -= 14

    c.save()
    return buf.getvalue()


# Alias (if older code referenced another name)
def build_month_report_pdf_bytes(title: str, lines: List[str]) -> bytes:
    return build_month_report_pdf(title, lines)

