# app/pdf_generator.py
from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

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

UNICODE_FONT_REGULAR = os.getenv("PDF_UNICODE_FONT_REGULAR", "DejaVuSans")
UNICODE_FONT_BOLD = os.getenv("PDF_UNICODE_FONT_BOLD", "DejaVuSans-Bold")


def _try_register_unicode_fonts() -> Tuple[str, str]:
    """
    Best-effort font registration for Unicode/Arabic.
    If not found, falls back to Helvetica.
    """
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
    """Best-effort Arabic shaping (optional libs)."""
    if not text:
        return ""
    try:
        import arabic_reshaper  # type: ignore
        from bidi.algorithm import get_display  # type: ignore

        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def _is_ar(lang: str) -> bool:
    return (lang or "").lower().strip() == "ar"


# ============================================================
# Company (env-driven)
# ============================================================

COMPANY = {
    "name": os.getenv("COMPANY_NAME", "Zohir Location Auto"),
    "tagline_fr": os.getenv("COMPANY_TAGLINE_FR", "Location de voitures (avec ou sans chauffeur)"),
    "tagline_en": os.getenv("COMPANY_TAGLINE_EN", "Car rental (with or without driver)"),
    "tagline_ar": os.getenv("COMPANY_TAGLINE_AR", "كراء السيارات (مع أو بدون سائق)"),
    "phone1": os.getenv("COMPANY_PHONE_1", "+213 ..."),
    "phone2": os.getenv("COMPANY_PHONE_2", ""),
    "address": os.getenv("COMPANY_ADDRESS", "Alger"),
    "email": os.getenv("COMPANY_EMAIL", "contact@..."),
}

# ============================================================
# Labels (FR / EN / AR)
# ============================================================

LABELS = {
    "fr": {
        "title": "CONTRAT DE LOCATION VÉHICULE",
        "ref": "Référence",
        "date": "Date",
        "company": "Société",
        "summary": "Résumé de la location",
        "client": "Le Locataire",
        "vehicle": "Véhicule",
        "rental": "Location",
        "denomination": "Nom / Prénom",
        "phone": "Téléphone",
        "address": "Adresse",
        "doc": "Document (CNI/Passeport)",
        "permit": "Permis",
        "model": "Modèle",
        "plate": "Immatriculation",
        "vin": "N° série (VIN)",
        "from": "Du",
        "to": "Au",
        "pickup_place": "Lieu de livraison",
        "return_place": "Lieu de restitution",
        "options": "Options",
        "gps": "GPS",
        "chauffeur": "Chauffeur",
        "baby": "Siège bébé",
        "notes": "Notes",
        "terms": "CONDITIONS GÉNÉRALES",
        "sign": "Signatures",
        "lessor": "Loueur",
        "lessee": "Locataire",
        "read_approved": "Lu et approuvé",
        "page": "Page",
        "trello": "Carte Trello",
        "open": "Ouvrir",
    },
    "en": {
        "title": "VEHICLE RENTAL CONTRACT",
        "ref": "Reference",
        "date": "Date",
        "company": "Company",
        "summary": "Rental summary",
        "client": "Renter",
        "vehicle": "Vehicle",
        "rental": "Rental",
        "denomination": "Full name",
        "phone": "Phone",
        "address": "Address",
        "doc": "Document (ID/Passport)",
        "permit": "Driving license",
        "model": "Model",
        "plate": "Plate",
        "vin": "Serial number (VIN)",
        "from": "From",
        "to": "To",
        "pickup_place": "Pickup place",
        "return_place": "Return place",
        "options": "Options",
        "gps": "GPS",
        "chauffeur": "Driver",
        "baby": "Baby seat",
        "notes": "Notes",
        "terms": "GENERAL TERMS",
        "sign": "Signatures",
        "lessor": "Owner",
        "lessee": "Renter",
        "read_approved": "Read and approved",
        "page": "Page",
        "trello": "Trello card",
        "open": "Open",
    },
    "ar": {
        "title": _maybe_ar("عقد كراء سيارة"),
        "ref": _maybe_ar("مرجع"),
        "date": _maybe_ar("التاريخ"),
        "company": _maybe_ar("الشركة"),
        "summary": _maybe_ar("ملخص الكراء"),
        "client": _maybe_ar("المستأجر"),
        "vehicle": _maybe_ar("السيارة"),
        "rental": _maybe_ar("الكراء"),
        "denomination": _maybe_ar("الاسم و اللقب"),
        "phone": _maybe_ar("الهاتف"),
        "address": _maybe_ar("العنوان"),
        "doc": _maybe_ar("وثيقة (بطاقة/جواز)"),
        "permit": _maybe_ar("رخصة السياقة"),
        "model": _maybe_ar("الطراز"),
        "plate": _maybe_ar("الترقيم"),
        "vin": _maybe_ar("الرقم التسلسلي"),
        "from": _maybe_ar("من"),
        "to": _maybe_ar("إلى"),
        "pickup_place": _maybe_ar("مكان التسليم"),
        "return_place": _maybe_ar("مكان الاسترجاع"),
        "options": _maybe_ar("الخيارات"),
        "gps": _maybe_ar("GPS"),
        "chauffeur": _maybe_ar("سائق"),
        "baby": _maybe_ar("مقعد طفل"),
        "notes": _maybe_ar("ملاحظات"),
        "terms": _maybe_ar("الشروط العامة"),
        "sign": _maybe_ar("الإمضاءات"),
        "lessor": _maybe_ar("المؤجر"),
        "lessee": _maybe_ar("المستأجر"),
        "read_approved": _maybe_ar("قرأت ووافقت"),
        "page": _maybe_ar("صفحة"),
        "trello": _maybe_ar("بطاقة Trello"),
        "open": _maybe_ar("فتح"),
    },
}

# ============================================================
# Conditions – FR/EN/AR
# (tu peux éditer ces textes plus tard)
# ============================================================

CONDITIONS_FR = [
    "1. Objet : le loueur met à disposition le véhicule identifié au contrat.",
    "2. Documents : pièce d’identité + permis valides requis (originaux).",
    "3. Conducteurs : seuls les conducteurs déclarés sont autorisés à conduire.",
    "4. Usage : interdiction off-road, course, remorquage sans accord, usage illégal.",
    "5. Zone : sortie de wilaya/pays uniquement avec accord écrit.",
    "6. Carburant : restitution au niveau convenu ; sinon facturation du complément.",
    "7. Kilométrage : forfait/limite selon accord ; dépassement facturable.",
    "8. Durée : retard/extension facturés (heures/jours supplémentaires).",
    "9. Dépôt : restitué après contrôle (dommages, amendes, carburant, nettoyage).",
    "10. Accident/incident : déclaration immédiate (photos + constat si possible).",
    "11. Amendes / péages / stationnement : à la charge du locataire.",
    "12. Restitution : véhicule + clés + équipements (gilet, triangle, etc.).",
    "13. Litiges : priorité à l’amiable ; tribunal compétent selon lieu du loueur.",
]

CONDITIONS_EN = [
    "1. Purpose: the owner provides the vehicle identified in the contract.",
    "2. Documents: valid ID + driving license required (originals).",
    "3. Drivers: only authorized drivers may operate the vehicle.",
    "4. Use: no off-road, racing, towing without consent, or unlawful use.",
    "5. Area: leaving authorized area/city/country requires written approval.",
    "6. Fuel: return with agreed fuel level; otherwise fuel difference is charged.",
    "7. Mileage: package/limit per agreement; extra mileage may be billed.",
    "8. Duration: late return/extensions may be billed (extra hours/days).",
    "9. Deposit: refunded after inspection (damages, fines, fuel, cleaning).",
    "10. Accident/incident: must be reported immediately (photos + report if possible).",
    "11. Fines/tolls/parking: renter is responsible.",
    "12. Return: vehicle + keys + mandatory equipment (safety kit, etc.).",
    "13. Disputes: amicable solution first; jurisdiction per owner location.",
]

CONDITIONS_AR = [
    _maybe_ar("1. الغرض: يضع المؤجر السيارة المحددة في العقد تحت تصرف المستأجر."),
    _maybe_ar("2. الوثائق: بطاقة هوية + رخصة سياقة ساريتان (الأصول)."),
    _maybe_ar("3. السائقون: لا يقود السيارة إلا السائقون المصرح بهم."),
    _maybe_ar("4. الاستعمال: يمنع الطرق الوعرة، السباق، السحب دون موافقة، أو استعمال غير قانوني."),
    _maybe_ar("5. المجال: الخروج من المنطقة/الولاية/البلد يتطلب موافقة كتابية."),
    _maybe_ar("6. الوقود: ترجع السيارة بمستوى الوقود المتفق عليه وإلا تُحسب التكلفة."),
    _maybe_ar("7. الكيلومترات: حسب الاتفاق، والزيادة قد تُفوتر."),
    _maybe_ar("8. المدة: التأخير/التمديد قد يُحسب (ساعات/أيام إضافية)."),
    _maybe_ar("9. الضمان: يُسترجع بعد المعاينة (أضرار، مخالفات، وقود، تنظيف)."),
    _maybe_ar("10. حادث/واقعة: يجب الإبلاغ فورًا (صور + محضر إن أمكن)."),
    _maybe_ar("11. المخالفات/الرسوم/التوقف: على عاتق المستأجر."),
    _maybe_ar("12. الاسترجاع: السيارة + المفاتيح + التجهيزات الإلزامية."),
    _maybe_ar("13. النزاعات: يُفضل الحل الودي أولاً والاختصاص حسب مقر المؤجر."),
]


def _conditions_for_lang(lang: str) -> List[str]:
    if lang == "en":
        return CONDITIONS_EN
    if lang == "ar":
        return CONDITIONS_AR
    return CONDITIONS_FR


# ============================================================
# Small helpers
# ============================================================

def _safe(v: Any) -> str:
    return ("" if v is None else str(v)).strip()


def _fmt_dt_local(dt_str: str) -> str:
    s = _safe(dt_str)
    return s.replace("T", " ") if "T" in s else s


def _contract_ref(payload: Dict[str, Any]) -> str:
    ref = _safe(payload.get("contract_ref"))
    if ref:
        return ref
    cid = _safe(payload.get("trello_card_id"))
    short = cid[-6:] if len(cid) >= 6 else cid
    return f"{datetime.now().strftime('%Y%m%d')}-{short}".strip("-")


def _sw(text: str, font: str, size: float) -> float:
    return pdfmetrics.stringWidth(text or "", font, size)


def _truncate(text: str, font: str, size: float, max_w: float) -> str:
    t = _safe(text)
    if not t:
        return ""
    if _sw(t, font, size) <= max_w:
        return t
    ell = "…"
    while t and _sw(t + ell, font, size) > max_w:
        t = t[:-1]
    return (t + ell) if t else ell


def _wrap(text: str, font: str, size: float, max_w: float) -> List[str]:
    s = _safe(text)
    if not s:
        return [""]
    words = s.split()
    lines: List[str] = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        if _sw(test, font, size) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _set_fill_stroke(c: canvas.Canvas, fill=colors.black, stroke=colors.black):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)


def _draw_text(c: canvas.Canvas, x: float, y: float, txt: str, font: str, size: float, rtl: bool = False):
    c.setFont(font, size)
    if rtl:
        c.drawRightString(x, y, txt)
    else:
        c.drawString(x, y, txt)


def _draw_pill(c: canvas.Canvas, x: float, y: float, w: float, h: float, txt: str, rtl: bool = False):
    # pill background
    c.roundRect(x, y, w, h, 6, stroke=0, fill=1)
    # text
    _set_fill_stroke(c, colors.white, colors.white)
    c.setFont(FONT_BOLD, 9)
    if rtl:
        c.drawRightString(x + w - 8, y + (h - 9) / 2 + 1, txt)
    else:
        c.drawString(x + 8, y + (h - 9) / 2 + 1, txt)


def _kv_box(
    c: canvas.Canvas,
    x: float, y: float, w: float, h: float,
    label: str, value: str,
    rtl: bool = False,
    accent: Optional[colors.Color] = None,
):
    # border + subtle fill
    c.setLineWidth(1)
    c.setStrokeColor(colors.Color(0, 0, 0, alpha=0.12))
    c.setFillColor(colors.Color(0, 0, 0, alpha=0.03))
    c.roundRect(x, y, w, h, 10, stroke=1, fill=1)

    # accent bar
    if accent is not None:
        c.setFillColor(accent)
        c.roundRect(x, y, 4, h, 2, stroke=0, fill=1)

    # label
    _set_fill_stroke(c, colors.Color(0, 0, 0, alpha=0.65), colors.black)
    c.setFont(FONT_REG, 8)
    lbl = label
    val = value
    if rtl:
        lbl = _maybe_ar(lbl)
        val = _maybe_ar(val) if any("\u0600" <= ch <= "\u06FF" for ch in val) else val
        c.drawRightString(x + w - 10, y + h - 14, _truncate(lbl, FONT_REG, 8, w - 20))
        c.setFont(FONT_BOLD, 10.5)
        _set_fill_stroke(c, colors.black, colors.black)
        c.drawRightString(x + w - 10, y + 12, _truncate(val, FONT_BOLD, 10.5, w - 20))
    else:
        c.drawString(x + 10, y + h - 14, _truncate(lbl, FONT_REG, 8, w - 20))
        c.setFont(FONT_BOLD, 10.5)
        _set_fill_stroke(c, colors.black, colors.black)
        c.drawString(x + 10, y + 12, _truncate(val, FONT_BOLD, 10.5, w - 20))


def _section_title(c: canvas.Canvas, x: float, y: float, txt: str, rtl: bool = False):
    c.setLineWidth(0)
    c.setFillColor(colors.Color(0, 0, 0, alpha=0.08))
    c.roundRect(x, y - 2, 120 * mm, 10 * mm, 8, stroke=0, fill=1)
    _set_fill_stroke(c, colors.black, colors.black)
    c.setFont(FONT_BOLD, 11)
    if rtl:
        c.drawRightString(x + 120 * mm - 10, y + 2, txt)
    else:
        c.drawString(x + 10, y + 2, txt)


def _draw_footer(c: canvas.Canvas, page_num: int, rtl: bool, L: Dict[str, str], W: float, margin: float):
    c.setLineWidth(1)
    c.setStrokeColor(colors.Color(0, 0, 0, alpha=0.10))
    c.line(margin, 18 * mm, W - margin, 18 * mm)

    c.setFont(FONT_REG, 8)
    c.setFillColor(colors.Color(0, 0, 0, alpha=0.65))
    left = f"{COMPANY['name']} • {COMPANY['phone1']} • {COMPANY['email']}".strip(" •")
    right = f"{L['page']} {page_num}"
    if rtl:
        c.drawRightString(W - margin, 8 * mm, _maybe_ar(left))
        c.drawString(margin, 8 * mm, _maybe_ar(right))
    else:
        c.drawString(margin, 8 * mm, left)
        c.drawRightString(W - margin, 8 * mm, right)


# ============================================================
# Main public function
# ============================================================

def build_contract_pdf(payload: Dict[str, Any], lang: str = "fr") -> bytes:
    lang = (lang or "fr").lower().strip()
    if lang not in ("fr", "en", "ar"):
        lang = "fr"
    rtl = _is_ar(lang)
    L = LABELS[lang]

    # -------- extract data
    client_name = _safe(payload.get("client_name"))
    client_phone = _safe(payload.get("client_phone"))
    client_address = _safe(payload.get("client_address"))
    doc_id = _safe(payload.get("doc_id"))
    driver_license = _safe(payload.get("driver_license"))

    vehicle_name = _safe(payload.get("vehicle_name")) or _safe(payload.get("vehicle_model"))
    vehicle_model = _safe(payload.get("vehicle_model"))
    vehicle_plate = _safe(payload.get("vehicle_plate"))
    vehicle_vin = _safe(payload.get("vehicle_vin"))

    start_date = _fmt_dt_local(_safe(payload.get("start_date")))
    end_date = _fmt_dt_local(_safe(payload.get("end_date")))
    pickup_location = _safe(payload.get("pickup_location"))
    return_location = _safe(payload.get("return_location"))

    notes = _safe(payload.get("notes"))
    options = payload.get("options") or {}
    opt_gps = bool(options.get("gps"))
    opt_driver = bool(options.get("chauffeur"))
    opt_baby = bool(options.get("baby_seat"))

    trello_url = _safe(payload.get("trello_card_url") or payload.get("trello_url") or payload.get("card_url") or "")

    ref = _contract_ref(payload)
    today_str = datetime.now().strftime("%Y-%m-%d")

    # -------- pdf init
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    margin = 14 * mm
    x0 = margin
    x1 = W - margin
    y_top = H - margin

    # Theme colors (soft pro)
    ACCENT = colors.HexColor("#2563EB")  # blue
    ACCENT2 = colors.HexColor("#7C3AED")  # violet
    ACCENT3 = colors.HexColor("#14B8A6")  # teal

def build_month_report_pdf(totals: Dict[str, Any], items: List[Dict[str, Any]] | None = None, lang: str = "fr") -> bytes:
    """
    PDF simple et propre pour le rapport mensuel Finance.
    - totals: dict avec keys possibles: paid, open, expenses, profit_est
    - items: liste optionnelle de lignes (factures/dépenses) si tu veux plus tard
    """
    lang = (lang or "fr").lower().strip()
    if lang not in ("fr", "en", "ar"):
        lang = "fr"
    rtl = _is_ar(lang)

    title = "Rapport mensuel" if lang == "fr" else ("Monthly report" if lang == "en" else _maybe_ar("تقرير شهري"))

    paid = _safe(totals.get("paid"))
    open_ = _safe(totals.get("open"))
    expenses = _safe(totals.get("expenses"))
    profit = _safe(totals.get("profit_est"))

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    margin = 16 * mm

    # background
    c.setFillColor(colors.white)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # header band
    ACCENT = colors.HexColor("#2563EB")
    c.setFillColor(colors.Color(0, 0, 0, alpha=0.02))
    c.roundRect(margin, H - margin - 30 * mm, W - 2 * margin, 30 * mm, 12, stroke=0, fill=1)
    c.setFillColor(ACCENT)
    c.roundRect(margin, H - margin - 30 * mm, 6, 30 * mm, 3, stroke=0, fill=1)

    c.setFillColor(colors.black)
    c.setFont(FONT_BOLD, 16)
    if rtl:
        c.drawRightString(W - margin - 10, H - margin - 16, _maybe_ar(title))
    else:
        c.drawString(margin + 14, H - margin - 16, title)

    c.setFont(FONT_REG, 9)
    sub = f"{COMPANY['name']} • {datetime.now().strftime('%Y-%m-%d')}"
    if rtl:
        c.setFillColor(colors.Color(0, 0, 0, alpha=0.7))
        c.drawRightString(W - margin - 10, H - margin - 28, _maybe_ar(sub))
    else:
        c.setFillColor(colors.Color(0, 0, 0, alpha=0.7))
        c.drawString(margin + 14, H - margin - 28, sub)

    # totals cards
    y = H - margin - 46 * mm
    card_h = 22 * mm
    gap = 8 * mm
    card_w = (W - 2 * margin - 3 * gap) / 4

    def card(ix: int, label: str, value: str):
        x = margin + ix * (card_w + gap)
        c.setStrokeColor(colors.Color(0, 0, 0, alpha=0.12))
        c.setFillColor(colors.Color(0, 0, 0, alpha=0.03))
        c.roundRect(x, y - card_h, card_w, card_h, 10, stroke=1, fill=1)
        c.setFillColor(colors.Color(0, 0, 0, alpha=0.65))
        c.setFont(FONT_REG, 8)
        if rtl:
            c.drawRightString(x + card_w - 10, y - 12, _maybe_ar(label))
            c.setFillColor(colors.black)
            c.setFont(FONT_BOLD, 12)
            c.drawRightString(x + card_w - 10, y - card_h + 9, _maybe_ar(value))
        else:
            c.drawString(x + 10, y - 12, label)
            c.setFillColor(colors.black)
            c.setFont(FONT_BOLD, 12)
            c.drawString(x + 10, y - card_h + 9, value)

    if lang == "fr":
        card(0, "Payé", paid or "0")
        card(1, "Ouvert", open_ or "0")
        card(2, "Dépenses", expenses or "0")
        card(3, "Profit estimé", profit or "0")
    elif lang == "en":
        card(0, "Paid", paid or "0")
        card(1, "Open", open_ or "0")
        card(2, "Expenses", expenses or "0")
        card(3, "Estimated profit", profit or "0")
    else:
        card(0, "مدفوع", paid or "0")
        card(1, "مفتوح", open_ or "0")
        card(2, "مصاريف", expenses or "0")
        card(3, "ربح تقديري", profit or "0")

    # footer
    c.setStrokeColor(colors.Color(0, 0, 0, alpha=0.10))
    c.line(margin, 18 * mm, W - margin, 18 * mm)
    c.setFont(FONT_REG, 8)
    c.setFillColor(colors.Color(0, 0, 0, alpha=0.65))
    foot = f"{COMPANY['name']} • {COMPANY['phone1']} • {COMPANY['email']}".strip(" •")
    if rtl:
        c.drawRightString(W - margin, 8 * mm, _maybe_ar(foot))
    else:
        c.drawString(margin, 8 * mm, foot)

    c.showPage()
    c.save()
    return buf.getvalue()


    def new_page(page_num: int):
        # background subtle
        c.setFillColor(colors.white)
        c.rect(0, 0, W, H, stroke=0, fill=1)
        _draw_footer(c, page_num, rtl, L, W, margin)

    # ============================================================
    # PAGE 1
    # ============================================================
    page = 1
    new_page(page)

    # Header block
    header_h = 34 * mm
    c.setFillColor(colors.Color(0, 0, 0, alpha=0.02))
    c.roundRect(x0, y_top - header_h, x1 - x0, header_h, 14, stroke=0, fill=1)

    # Accent bar
    c.setFillColor(ACCENT)
    c.roundRect(x0, y_top - header_h, 6, header_h, 3, stroke=0, fill=1)

    # Company name + contacts
    c.setFillColor(colors.black)
    c.setFont(FONT_BOLD, 14)
    company_name = COMPANY["name"]
    tagline = COMPANY["tagline_ar"] if rtl else (COMPANY["tagline_en"] if lang == "en" else COMPANY["tagline_fr"])
    tagline = _maybe_ar(tagline) if rtl else tagline

    left_x = x0 + 14
    right_x = x1 - 12

    if rtl:
        c.drawRightString(right_x, y_top - 16, _maybe_ar(company_name))
        c.setFont(FONT_REG, 9)
        c.setFillColor(colors.Color(0, 0, 0, alpha=0.75))
        c.drawRightString(right_x, y_top - 30, tagline)
    else:
        c.drawString(left_x, y_top - 16, company_name)
        c.setFont(FONT_REG, 9)
        c.setFillColor(colors.Color(0, 0, 0, alpha=0.75))
        c.drawString(left_x, y_top - 30, tagline)

    # Title + ref/date on the right
    title = L["title"]
    if rtl:
        title = _maybe_ar(title)

    c.setFont(FONT_BOLD, 15)
    c.setFillColor(colors.black)

    if rtl:
        c.drawString(x0 + 14, y_top - 18, title)
    else:
        c.drawRightString(x1 - 12, y_top - 18, title)

    # Pills: ref and date
    c.setFillColor(ACCENT2)
    pill_w = 62 * mm
    pill_h = 10 * mm
    pill_y = y_top - header_h + 10

    ref_txt = f"{L['ref']}: {ref}"
    date_txt = f"{L['date']}: {today_str}"
    if rtl:
        ref_txt = _maybe_ar(f"{L['ref']}: {ref}")
        date_txt = _maybe_ar(f"{L['date']}: {today_str}")

    _draw_pill(c, x0 + 14, pill_y, pill_w, pill_h, ref_txt, rtl=False)
    c.setFillColor(ACCENT3)
    _draw_pill(c, x0 + 14 + pill_w + 8, pill_y, pill_w, pill_h, date_txt, rtl=False)

    # Contacts bottom in header
    c.setFont(FONT_REG, 9)
    c.setFillColor(colors.Color(0, 0, 0, alpha=0.65))
    contacts = " • ".join([x for x in [COMPANY["phone1"], COMPANY["phone2"], COMPANY["email"], COMPANY["address"]] if x]).strip(" •")
    if rtl:
        c.drawRightString(right_x, y_top - header_h + 12, _maybe_ar(contacts))
    else:
        c.drawString(left_x, y_top - header_h + 12, contacts)

    # Layout positions
    y = y_top - header_h - 10 * mm

    # Summary section
    _section_title(c, x0, y - 6, L["summary"], rtl=rtl)
    y -= 16 * mm

    # Summary boxes (3 columns)
    box_h = 18 * mm
    gap = 8 * mm
    col_w = (x1 - x0 - 2 * gap) / 3

    _kv_box(c, x0, y - box_h, col_w, box_h, L["from"], start_date, rtl=rtl, accent=ACCENT)
    _kv_box(c, x0 + col_w + gap, y - box_h, col_w, box_h, L["to"], end_date, rtl=rtl, accent=ACCENT2)

    # options quick text
    opt_txt = []
    if opt_gps: opt_txt.append(L["gps"])
    if opt_driver: opt_txt.append(L["chauffeur"])
    if opt_baby: opt_txt.append(L["baby"])
    opt_value = ", ".join(opt_txt) if opt_txt else ("-" if not rtl else _maybe_ar("-"))
    _kv_box(c, x0 + 2 * (col_w + gap), y - box_h, col_w, box_h, L["options"], opt_value, rtl=rtl, accent=ACCENT3)

    y -= box_h + 10 * mm

    # Two columns: Client / Vehicle
    col2_gap = 10 * mm
    col2_w = (x1 - x0 - col2_gap) / 2
    left_col_x = x0
    right_col_x = x0 + col2_w + col2_gap

    _section_title(c, left_col_x, y - 6, L["client"], rtl=rtl)
    _section_title(c, right_col_x, y - 6, L["vehicle"], rtl=rtl)
    y -= 16 * mm

    # Client fields (stack)
    field_h = 16 * mm
    _kv_box(c, left_col_x, y - field_h, col2_w, field_h, L["denomination"], client_name, rtl=rtl, accent=ACCENT)
    y1c = y - field_h - 6 * mm
    _kv_box(c, left_col_x, y1c - field_h, col2_w, field_h, L["phone"], client_phone, rtl=rtl)
    y1c2 = y1c - field_h - 6 * mm
    _kv_box(c, left_col_x, y1c2 - field_h, col2_w, field_h, L["doc"], doc_id, rtl=rtl)
    y1c3 = y1c2 - field_h - 6 * mm
    _kv_box(c, left_col_x, y1c3 - field_h, col2_w, field_h, L["permit"], driver_license, rtl=rtl)

    # Address bigger
    addr_h = 22 * mm
    _kv_box(c, left_col_x, y1c3 - field_h - 6 * mm - addr_h, col2_w, addr_h, L["address"], client_address, rtl=rtl)

    # Vehicle fields (stack)
    yv = y
    _kv_box(c, right_col_x, yv - field_h, col2_w, field_h, L["model"], vehicle_model or vehicle_name, rtl=rtl, accent=ACCENT2)
    yv1 = yv - field_h - 6 * mm
    _kv_box(c, right_col_x, yv1 - field_h, col2_w, field_h, L["plate"], vehicle_plate, rtl=rtl)
    yv2 = yv1 - field_h - 6 * mm
    _kv_box(c, right_col_x, yv2 - field_h, col2_w, field_h, L["vin"], vehicle_vin, rtl=rtl)

    # Rental info boxes under vehicle
    place_h = 18 * mm
    yv3 = yv2 - field_h - 8 * mm
    _kv_box(c, right_col_x, yv3 - place_h, col2_w, place_h, L["pickup_place"], pickup_location, rtl=rtl, accent=ACCENT3)
    yv4 = yv3 - place_h - 6 * mm
    _kv_box(c, right_col_x, yv4 - place_h, col2_w, place_h, L["return_place"], return_location, rtl=rtl)

    # Notes (full width)
    y_notes = (y1c3 - field_h - 6 * mm - addr_h) - 12 * mm
    notes_h = 22 * mm
    if y_notes - notes_h < 45 * mm:
        # not enough space => push to next page
        c.showPage()
        page += 1
        new_page(page)
        y_notes = H - margin - 18 * mm

    _section_title(c, x0, y_notes - 6, L["notes"], rtl=rtl)
    y_notes -= 16 * mm
    _kv_box(c, x0, y_notes - notes_h, x1 - x0, notes_h, L["notes"], notes or "-", rtl=rtl)

    # ============================================================
    # PAGE 2+ : Terms
    # ============================================================
    c.showPage()
    page += 1
    new_page(page)

    y = H - margin - 10 * mm
    _section_title(c, x0, y - 6, L["terms"], rtl=rtl)
    y -= 18 * mm

    terms = _conditions_for_lang(lang)

    c.setFont(FONT_REG, 10)
    c.setFillColor(colors.black)

    line_h = 5.2 * mm
    max_w = (x1 - x0)

    def draw_term_line(line: str, y: float) -> float:
        nonlocal c
        # wrap
        parts = _wrap(line, FONT_REG, 10, max_w)
        for p in parts:
            if y < 35 * mm:
                # next page
                c.showPage()
                nonlocal_page_inc()
                y = H - margin - 10 * mm
                _section_title(c, x0, y - 6, L["terms"], rtl=rtl)
                y -= 18 * mm
                c.setFont(FONT_REG, 10)
                c.setFillColor(colors.black)

            if rtl:
                c.drawRightString(x1, y, p)
            else:
                c.drawString(x0, y, p)
            y -= line_h
        y -= 1.5 * mm
        return y

    def nonlocal_page_inc():
        nonlocal page
        page += 1
        new_page(page)

    for t in terms:
        t = t if not rtl else _maybe_ar(t)
        y = draw_term_line(t, y)

    # ============================================================
    # Signatures page (same page if place)
    # ============================================================
    if y < 95 * mm:
        c.showPage()
        page += 1
        new_page(page)
        y = H - margin - 10 * mm

    _section_title(c, x0, y - 6, L["sign"], rtl=rtl)
    y -= 18 * mm

    sig_h = 38 * mm
    sig_w = (x1 - x0 - 10 * mm) / 2

    # boxes
    c.setStrokeColor(colors.Color(0, 0, 0, alpha=0.12))
    c.setFillColor(colors.Color(0, 0, 0, alpha=0.02))
    c.roundRect(x0, y - sig_h, sig_w, sig_h, 12, stroke=1, fill=1)
    c.roundRect(x0 + sig_w + 10 * mm, y - sig_h, sig_w, sig_h, 12, stroke=1, fill=1)

    c.setFillColor(colors.black)
    c.setFont(FONT_BOLD, 11)
    if rtl:
        c.drawRightString(x0 + sig_w - 10, y - 14, _maybe_ar(L["lessor"]))
        c.drawRightString(x0 + sig_w + 10 * mm + sig_w - 10, y - 14, _maybe_ar(L["lessee"]))
    else:
        c.drawString(x0 + 10, y - 14, L["lessor"])
        c.drawString(x0 + sig_w + 10 * mm + 10, y - 14, L["lessee"])

    c.setFont(FONT_REG, 9)
    c.setFillColor(colors.Color(0, 0, 0, alpha=0.65))
    ra = L["read_approved"]
    if rtl:
        ra = _maybe_ar(ra)
        c.drawRightString(x0 + sig_w - 10, y - 28, ra)
        c.drawRightString(x0 + sig_w + 10 * mm + sig_w - 10, y - 28, ra)
    else:
        c.drawString(x0 + 10, y - 28, ra)
        c.drawString(x0 + sig_w + 10 * mm + 10, y - 28, ra)

    # signature lines
    c.setStrokeColor(colors.Color(0, 0, 0, alpha=0.25))
    c.setLineWidth(1)
    c.line(x0 + 12, y - sig_h + 12, x0 + sig_w - 12, y - sig_h + 12)
    c.line(x0 + sig_w + 10 * mm + 12, y - sig_h + 12, x0 + sig_w + 10 * mm + sig_w - 12, y - sig_h + 12)

    # finalize
    c.showPage()
    c.save()
    return buf.getvalue()

