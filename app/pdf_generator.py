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

UNICODE_FONT_REGULAR = os.getenv("PDF_UNICODE_FONT_REGULAR", "DejaVuSans")
UNICODE_FONT_BOLD = os.getenv("PDF_UNICODE_FONT_BOLD", "DejaVuSans-Bold")


def _try_register_unicode_fonts() -> Tuple[str, str]:
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


# ============================================================
# Company
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
        "enterprise": "Entreprise",
        "individual": "Particulier",
        "ref": "Référence de contrat",
        "tenant": "Le Locataire",
        "vehicle": "Informations véhicule",
        "denomination": "Nom / Prénom",
        "phone": "Téléphone",
        "address": "Adresse",
        "doc": "Document (CNI/Passeport)",
        "permit": "Permis",
        "pickup_date": "Durée de location",
        "from": "du",
        "to": "au",
        "pickup_place": "Lieu de livraison",
        "return_place": "Lieu de restitution",
        "model": "Modèle",
        "plate": "Immatriculation",
        "vin": "N° série (VIN)",
        "state": "État du véhicule",
        "ok": "Aucun problème",
        "damaged": "Véhicule endommagé",
        "other_pb": "Autres problèmes",
        "dirt": "Salissures",
        "missing": "Équipement manquant",
        "burns": "Brûlures des sièges",
        "other": "Autres",
        "return_fill": "À remplir au retour",
        "km": "Km compteur",
        "fuel": "Niveau carburant",
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
        "vehicle": "Vehicle details",
        "denomination": "Full name",
        "phone": "Phone",
        "address": "Address",
        "doc": "Document (ID/Passport)",
        "permit": "Driving license",
        "pickup_date": "Rental period",
        "from": "from",
        "to": "to",
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
        "vehicle": _maybe_ar("معلومات السيارة"),
        "denomination": _maybe_ar("الاسم و اللقب"),
        "phone": _maybe_ar("الهاتف"),
        "address": _maybe_ar("العنوان"),
        "doc": _maybe_ar("وثيقة (بطاقة/جواز)"),
        "permit": _maybe_ar("رخصة السياقة"),
        "pickup_date": _maybe_ar("مدة الكراء"),
        "from": _maybe_ar("من"),
        "to": _maybe_ar("إلى"),
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

# ============================================================
# Conditions (MAX) – FR/EN/AR
# ============================================================

CONDITIONS_FR = [
    "1. Objet : le loueur met à disposition le véhicule identifié au contrat.",
    "2. Documents : pièce d’identité + permis valides requis (originaux).",
    "3. Conducteurs : seuls les conducteurs déclarés sont autorisés à conduire.",
    "4. Éligibilité : le loueur peut refuser une location (âge, permis, situation).",
    "5. État du véhicule : le locataire reconnaît l’état au départ (photos conseillées).",
    "6. Usage : interdiction off-road, course, remorquage sans accord, usage illégal.",
    "7. Zone d’utilisation : sortie de wilaya/pays uniquement avec accord écrit.",
    "8. Carburant : restitution au niveau convenu ; sinon facturation du complément.",
    "9. Kilométrage : forfait/limite selon accord ; dépassement facturable.",
    "10. Durée : retard/extension facturés (heures/jours supplémentaires).",
    "11. Paiement : montant convenu + options + dépôt de garantie si demandé.",
    "12. Dépôt : restitué après contrôle (dommages, amendes, carburant, nettoyage).",
    "13. Amendes / péages / stationnement : à la charge du locataire.",
    "14. Accident / incident : déclaration immédiate (photos + constat si possible).",
    "15. Interdiction de continuer si danger : le locataire doit prévenir le loueur.",
    "16. Vol : plainte obligatoire + remise du récépissé ; clés à restituer si possible.",
    "17. Assurance : conditions/franchise selon loueur ; exclusions possibles.",
    "18. Dommages : non couverts par assurance ou faute → charge du locataire.",
    "19. Entretien : le locataire veille aux niveaux/alertes ; stop si alerte critique.",
    "20. Restitution : véhicule + clés + équipements (gilet, triangle, etc.).",
    "21. Données : les informations peuvent être conservées pour gestion du contrat.",
    "22. Litiges : priorité à l’amiable ; tribunal compétent selon lieu du loueur.",
]

CONDITIONS_EN = [
    "1. Purpose: the owner provides the vehicle identified in the contract.",
    "2. Documents: valid ID + driving license required (originals).",
    "3. Drivers: only declared/authorized drivers may operate the vehicle.",
    "4. Eligibility: the owner may refuse rental (age, license, situation).",
    "5. Condition at pickup: renter acknowledges condition (photos recommended).",
    "6. Use: no off-road, racing, towing without consent, or unlawful use.",
    "7. Area of use: leaving the authorized area/city/country requires written approval.",
    "8. Fuel: return with agreed fuel level; otherwise fuel difference is charged.",
    "9. Mileage: package/limit per agreement; extra mileage may be billed.",
    "10. Duration: late return/extensions may be billed (extra hours/days).",
    "11. Payment: agreed price + options + security deposit if required.",
    "12. Deposit: refunded after inspection (damages, fines, fuel, cleaning).",
    "13. Fines/tolls/parking: renter is responsible.",
    "14. Accident/incident: must be reported immediately (photos + report when applicable).",
    "15. Safety: do not keep driving if unsafe; inform owner immediately.",
    "16. Theft: police report required + provide proof; return keys when possible.",
    "17. Insurance: terms/excess per owner; exclusions may apply.",
    "18. Damages: not covered by insurance or renter fault → renter bears the cost.",
    "19. Maintenance: renter monitors alerts/levels; stop if critical warning appears.",
    "20. Return: vehicle + keys + mandatory equipment (safety kit, etc.).",
    "21. Data: information may be stored for contract management/legal purposes.",
    "22. Disputes: parties seek amicable solution first; jurisdiction as per owner location.",
]

CONDITIONS_AR = [
    _maybe_ar("1. الغرض: يضع المؤجر السيارة المحددة في العقد تحت تصرف المستأجر."),
    _maybe_ar("2. الوثائق: بطاقة هوية + رخصة سياقة ساريتان (الأصول)."),
    _maybe_ar("3. السائقون: لا يقود السيارة إلا السائقون المصرح بهم."),
    _maybe_ar("4. الأهلية: يمكن للمؤجر رفض الكراء حسب الحالة/السن/الرخصة."),
    _maybe_ar("5. حالة السيارة عند التسليم: يقر المستأجر بالحالة (صور مستحسنة)."),
    _maybe_ar("6. الاستعمال: يمنع الطرق الوعرة، السباق، السحب دون موافقة، أو استعمال غير قانوني."),
    _maybe_ar("7. مجال الاستعمال: الخروج من المنطقة/الولاية/البلد يتطلب موافقة كتابية."),
    _maybe_ar("8. الوقود: ترجع السيارة بمستوى الوقود المتفق عليه وإلا تُحسب التكلفة."),
    _maybe_ar("9. الكيلومترات: حسب الاتفاق، والزيادة قد تُفوتر."),
    _maybe_ar("10. المدة: التأخير/التمديد قد يُحسب (ساعات/أيام إضافية)."),
    _maybe_ar("11. الدفع: المبلغ المتفق عليه + الخيارات + تأمين/ضمان عند الطلب."),
    _maybe_ar("12. الضمان: يُسترجع بعد المعاينة (أضرار، مخالفات، وقود، تنظيف)."),
    _maybe_ar("13. المخالفات/الرسوم/التوقف: على عاتق المستأجر."),
    _maybe_ar("14. حادث/واقعة: يجب الإبلاغ فورًا (صور + محضر إن أمكن)."),
    _maybe_ar("15. السلامة: يمنع مواصلة القيادة إن كانت خطرة ويجب إبلاغ المؤجر."),
    _maybe_ar("16. السرقة: شكوى إلزامية وتقديم الإثبات وإرجاع المفاتيح إن أمكن."),
    _maybe_ar("17. التأمين: حسب شروط المؤجر والفرانشيز، وقد توجد استثناءات."),
    _maybe_ar("18. الأضرار: غير المغطاة أو بسبب خطأ المستأجر على عاتقه."),
    _maybe_ar("19. الصيانة: مراقبة التنبيهات/السوائل والتوقف عند إنذار خطير."),
    _maybe_ar("20. الاسترجاع: السيارة + المفاتيح + التجهيزات الإلزامية."),
    _maybe_ar("21. البيانات: قد تُحفظ المعلومات لتسيير العقد ولأسباب قانونية."),
    _maybe_ar("22. النزاعات: يُفضل الحل الودي أولاً والاختصاص حسب مقر المؤجر."),
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


def _is_ar(lang: str) -> bool:
    return (lang or "").lower().strip() == "ar"


def _set_text_color(c: canvas.Canvas):
    c.setFillColor(colors.black)
    c.setStrokeColor(colors.black)


def _truncate_to_width(text: str, font: str, size: float, max_w: float) -> str:
    t = _safe(text)
    if not t:
        return ""
    if pdfmetrics.stringWidth(t, font, size) <= max_w:
        return t
    ell = "…"
    # shrink until fits
    while t and pdfmetrics.stringWidth(t + ell, font, size) > max_w:
        t = t[:-1]
    return (t + ell) if t else ell


def _wrap_to_width(text: str, font: str, size: float, max_w: float) -> List[str]:
    s = _safe(text)
    if not s:
        return [""]
    words = s.split()
    lines: List[str] = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        if pdfmetrics.stringWidth(test, font, size) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _draw_checkbox(c: canvas.Canvas, x: float, y: float, size: float, checked: bool = False):
    c.rect(x, y, size, size, stroke=1, fill=0)
    if checked:
        c.setLineWidth(2)
        c.line(x + 2, y + size / 2, x + size / 2, y + 2)
        c.line(x + size / 2, y + 2, x + size - 2, y + size - 2)
        c.setLineWidth(1)


def _draw_kv(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    value: str,
    lang: str,
):
    # box
    c.rect(x, y, w, h, stroke=1, fill=0)

    # label
    c.setFont(FONT_REG, 8)
    _set_text_color(c)

    lbl = label or ""
    val = value or ""
    if _is_ar(lang):
        lbl = _maybe_ar(lbl)
        # label right aligned
        c.drawRightString(x + w - 6, y + h - 11, _truncate_to_width(lbl, FONT_REG, 8, w - 12))
        c.setFont(FONT_BOLD, 10)
        c.drawRightString(x + w - 6, y + 6, _truncate_to_width(_maybe_ar(val) if any("\u0600" <= ch <= "\u06FF" for ch in val) else val, FONT_BOLD, 10, w - 12))
    else:
        c.drawString(x + 6, y + h - 11, _truncate_to_width(lbl, FONT_REG, 8, w - 12))
        c.setFont(FONT_BOLD, 10)
        c.drawString(x + 6, y + 6, _truncate_to_width(val, FONT_BOLD, 10, w - 12))


def _draw_multiline(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    lines: List[str],
    lang: str,
):
    c.rect(x, y, w, h, stroke=1, fill=0)
    _set_text_color(c)

    c.setFont(FONT_REG, 8)
    if label:
        if _is_ar(lang):
            c.drawRightString(x + w - 6, y + h - 11, _truncate_to_width(_maybe_ar(label), FONT_REG, 8, w - 12))
        else:
            c.drawString(x + 6, y + h - 11, _truncate_to_width(label, FONT_REG, 8, w - 12))

    c.setFont(FONT_REG, 9)
    yy = y + h - 24
    for raw in lines[:10]:
        for ln in _wrap_to_width(raw, FONT_REG, 9, w - 12):
            if yy < y + 8:
                break
            if _is_ar(lang):
                c.drawRightString(x + w - 6, yy, _maybe_ar(ln))
            else:
                c.drawString(x + 6, yy, ln)
            yy -= 12


# ============================================================
# Main PDF
# ============================================================

def build_contract_pdf(payload: Dict[str, Any], lang: str = "fr") -> bytes:
    lang = (lang or "fr").lower().strip()
    if lang not in ("fr", "en", "ar"):
        lang = "fr"

    L = LABELS[lang]
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    _draw_contract_page_1(c, payload, lang, L, W, H)
    c.showPage()
    _draw_contract_page_2_conditions(c, lang, L, W, H)

    c.save()
    return buf.getvalue()


def _draw_contract_page_1(c: canvas.Canvas, payload: Dict[str, Any], lang: str, L: Dict[str, str], W: float, H: float):
    margin = 12 * mm
    top = H - margin

    _set_text_color(c)
    c.setLineWidth(1)

    # Outer frame
    c.rect(margin, margin, W - 2 * margin, H - 2 * margin, stroke=1, fill=0)

    # Header
    header_h = 38 * mm
    company_w = (W - 2 * margin) * 0.34
    title_w = (W - 2 * margin) - company_w - 6

    x0 = margin
    y0 = top - header_h

    # company box
    c.rect(x0, y0, company_w, header_h, stroke=1, fill=0)
    c.setFont(FONT_BOLD, 12)
    c.drawString(x0 + 8, y0 + header_h - 18, COMPANY["name"])

    c.setFont(FONT_REG, 9)
    tagline = COMPANY["tagline_fr"] if lang == "fr" else COMPANY["tagline_en"] if lang == "en" else COMPANY["tagline_ar"]
    c.drawString(x0 + 8, y0 + header_h - 32, _safe(tagline))

    c.setFont(FONT_REG, 9)
    c.drawString(x0 + 8, y0 + header_h - 46, f"☎ {COMPANY['phone1']}".strip())
    yy = y0 + header_h - 60
    if COMPANY["phone2"]:
        c.drawString(x0 + 8, yy, f"☎ {COMPANY['phone2']}".strip())
        yy -= 14
    c.drawString(x0 + 8, yy, f"📍 {COMPANY['address']}".strip())
    c.drawString(x0 + 8, yy - 14, f"✉ {COMPANY['email']}".strip())

    # title box
    tx = x0 + company_w + 6
    c.rect(tx, y0, title_w, header_h, stroke=1, fill=0)

    c.setFont(FONT_BOLD, 14)
    if _is_ar(lang):
        c.drawRightString(tx + title_w - 10, y0 + header_h - 18, L["title"])
    else:
        c.drawString(tx + 10, y0 + header_h - 18, L["title"])

    # checkboxes + ref
    cb_size = 10
    c.setFont(FONT_REG, 10)

    # row
    cy = y0 + header_h - 34
    if _is_ar(lang):
        # right side
        cx2 = tx + title_w - 150
        _draw_checkbox(c, cx2, cy, cb_size, checked=True)
        c.drawRightString(cx2 - 6, cy + 2, L["individual"])

        cx1 = cx2 - 120
        _draw_checkbox(c, cx1, cy, cb_size, checked=False)
        c.drawRightString(cx1 - 6, cy + 2, L["enterprise"])
    else:
        cx = tx + 10
        _draw_checkbox(c, cx, cy, cb_size, checked=False)
        c.drawString(cx + cb_size + 6, cy + 2, L["enterprise"])

        cx2 = cx + 130
        _draw_checkbox(c, cx2, cy, cb_size, checked=True)
        c.drawString(cx2 + cb_size + 6, cy + 2, L["individual"])

    # ref line
    ref = _contract_ref(payload)
    c.setFont(FONT_REG, 10)
    if _is_ar(lang):
        c.drawRightString(tx + title_w - 10, y0 + 14, f"{L['ref']} : {ref}")
    else:
        c.drawString(tx + 10, y0 + 14, f"{L['ref']} : {ref}")

    # Body panels
    body_top = y0 - 8
    body_h = 112 * mm
    left_w = (W - 2 * margin) * 0.52
    right_w = (W - 2 * margin) - left_w - 6

    left_x = margin
    right_x = margin + left_w + 6
    body_y = body_top - body_h

    c.setFont(FONT_BOLD, 11)
    c.rect(left_x, body_y, left_w, body_h, stroke=1, fill=0)
    c.rect(right_x, body_y, right_w, body_h, stroke=1, fill=0)

    if _is_ar(lang):
        c.drawRightString(left_x + left_w - 8, body_y + body_h - 16, L["tenant"])
        c.drawRightString(right_x + right_w - 8, body_y + body_h - 16, L["vehicle"])
    else:
        c.drawString(left_x + 8, body_y + body_h - 16, L["tenant"])
        c.drawString(right_x + 8, body_y + body_h - 16, L["vehicle"])

    # payload fields
    p_client = _safe(payload.get("client_name"))
    p_phone = _safe(payload.get("client_phone"))
    p_addr = _safe(payload.get("client_address"))
    p_doc = _safe(payload.get("doc_id"))
    p_permit = _safe(payload.get("driver_license"))

    p_start = _fmt_dt_local(_safe(payload.get("start_date")))
    p_end = _fmt_dt_local(_safe(payload.get("end_date")))
    p_pick = _safe(payload.get("pickup_location"))
    p_ret = _safe(payload.get("return_location"))

    v_plate = _safe(payload.get("vehicle_plate"))
    v_model = _safe(payload.get("vehicle_model")) or _safe(payload.get("vehicle_name"))
    v_vin = _safe(payload.get("vehicle_vin"))

    row_h = 14 * mm

    # left grid
    grid_x = left_x + 6
    grid_top = body_y + body_h - 26

    _draw_kv(c, grid_x, grid_top - row_h, left_w - 12, row_h, L["denomination"], p_client, lang)

    w1 = (left_w - 12) * 0.52
    w2 = (left_w - 12) - w1 - 6
    _draw_kv(c, grid_x, grid_top - 2 * row_h, w1, row_h, L["phone"], p_phone, lang)
    _draw_kv(c, grid_x + w1 + 6, grid_top - 2 * row_h, w2, row_h, L["doc"], p_doc, lang)

    _draw_kv(c, grid_x, grid_top - 3 * row_h, left_w - 12, row_h, L["address"], p_addr, lang)
    _draw_kv(c, grid_x, grid_top - 4 * row_h, left_w - 12, row_h, L["permit"], p_permit, lang)

    _draw_multiline(
        c,
        grid_x,
        grid_top - 5 * row_h - 2,
        left_w - 12,
        16 * mm,
        L["pickup_date"],
        [f"{L['from']} {p_start}", f"{L['to']} {p_end}"],
        lang,
    )

    _draw_multiline(
        c,
        grid_x,
        body_y + 18 * mm,
        left_w - 12,
        22 * mm,
        "",
        [f"{L['pickup_place']}: {p_pick}", f"{L['return_place']}: {p_ret}"],
        lang,
    )

    # right grid
    rx = right_x + 6
    rt = body_y + body_h - 26

    _draw_kv(c, rx, rt - row_h, right_w - 12, row_h, L["model"], v_model, lang)
    _draw_kv(c, rx, rt - 2 * row_h, right_w - 12, row_h, L["plate"], v_plate, lang)
    _draw_kv(c, rx, rt - 3 * row_h, right_w - 12, row_h, L["vin"], v_vin, lang)

    # vehicle condition
    c.setFont(FONT_BOLD, 10)
    if _is_ar(lang):
        c.drawRightString(rx + right_w - 12, rt - 3 * row_h - 16, L["state"])
    else:
        c.drawString(rx, rt - 3 * row_h - 16, L["state"])

    c.setFont(FONT_REG, 9)
    cb = 10
    opt_y = rt - 3 * row_h - 34

    def _row(label: str, checked: bool):
        nonlocal opt_y
        if _is_ar(lang):
            # checkbox on right
            bx = rx + (right_w - 12) - cb
            _draw_checkbox(c, bx, opt_y, cb, checked=checked)
            c.drawRightString(bx - 6, opt_y + 2, label)
        else:
            _draw_checkbox(c, rx, opt_y, cb, checked=checked)
            c.drawString(rx + cb + 6, opt_y + 2, label)
        opt_y -= 14

    _row(L["ok"], True)
    _row(L["damaged"], False)
    _row(L["other_pb"], False)

    # sub items
    sub_labels = [L["dirt"], L["missing"], L["burns"], L["other"]]
    for s in sub_labels:
        _row("  - " + s if not _is_ar(lang) else s, False)

    # options
    options = payload.get("options") or {}
    gps = bool(options.get("gps"))
    chauffeur = bool(options.get("chauffeur"))
    baby = bool(options.get("baby_seat"))

    c.setFont(FONT_BOLD, 10)
    if _is_ar(lang):
        c.drawRightString(rx + right_w - 12, body_y + 52, L["options"])
    else:
        c.drawString(rx, body_y + 52, L["options"])

    c.setFont(FONT_REG, 9)
    oy = body_y + 38

    if _is_ar(lang):
        # align right, checkboxes on right
        bx = rx + (right_w - 12) - cb
        _draw_checkbox(c, bx, oy, cb, checked=gps)
        c.drawRightString(bx - 6, oy + 2, L["gps"])

        bx2 = bx - 90
        _draw_checkbox(c, bx2, oy, cb, checked=chauffeur)
        c.drawRightString(bx2 - 6, oy + 2, L["chauffeur"])

        _draw_checkbox(c, bx, oy - 14, cb, checked=baby)
        c.drawRightString(bx - 6, oy - 12, L["baby"])
    else:
        _draw_checkbox(c, rx, oy, cb, checked=gps)
        c.drawString(rx + cb + 6, oy + 2, L["gps"])
        _draw_checkbox(c, rx + 90, oy, cb, checked=chauffeur)
        c.drawString(rx + 90 + cb + 6, oy + 2, L["chauffeur"])
        _draw_checkbox(c, rx, oy - 14, cb, checked=baby)
        c.drawString(rx + cb + 6, oy - 12, L["baby"])

    notes = _safe(payload.get("notes"))
    _draw_multiline(c, rx, body_y + 6, right_w - 12, 26 * mm, L["notes"], [notes], lang)

    # bottom: return fill + signatures
    bottom_y = margin + 10

    c.rect(margin, bottom_y + 38 * mm, W - 2 * margin, 30 * mm, stroke=1, fill=0)
    c.setFont(FONT_BOLD, 10.5)
    if _is_ar(lang):
        c.drawRightString(W - margin - 8, bottom_y + 38 * mm + 30 * mm - 14, L["return_fill"])
    else:
        c.drawString(margin + 8, bottom_y + 38 * mm + 30 * mm - 14, L["return_fill"])

    bx = margin + 8
    by = bottom_y + 42 * mm
    bw = (W - 2 * margin - 24) / 2
    bh = 18 * mm
    _draw_kv(c, bx, by, bw, bh, L["km"], "", lang)
    _draw_kv(c, bx + bw + 8, by, bw, bh, L["fuel"], "", lang)

    # signatures
    sig_y = bottom_y
    sig_h = 34 * mm
    sig_w = (W - 2 * margin - 10) / 2

    c.rect(margin, sig_y, sig_w, sig_h, stroke=1, fill=0)
    c.rect(margin + sig_w + 10, sig_y, sig_w, sig_h, stroke=1, fill=0)

    c.setFont(FONT_REG, 9)
    if _is_ar(lang):
        c.drawRightString(margin + sig_w - 8, sig_y + sig_h - 14, L["sign_renter"])
        c.drawRightString(margin + sig_w + 10 + sig_w - 8, sig_y + sig_h - 14, L["sign_tenant"])
    else:
        c.drawString(margin + 8, sig_y + sig_h - 14, L["sign_renter"])
        c.drawString(margin + sig_w + 18, sig_y + sig_h - 14, L["sign_tenant"])

    # footer
    c.setFont(FONT_REG, 8)
    c.setFillColor(colors.grey)
    c.drawRightString(W - margin, margin - 2, f"{L['page']} 1/2")
    c.setFillColor(colors.black)


def _draw_contract_page_2_conditions(c: canvas.Canvas, lang: str, L: Dict[str, str], W: float, H: float):
    margin = 14 * mm
    _set_text_color(c)

    c.setFont(FONT_BOLD, 16)
    if _is_ar(lang):
        c.drawRightString(W - margin, H - margin - 10, L["conditions"])
    else:
        c.drawString(margin, H - margin - 10, L["conditions"])

    items = _conditions_for_lang(lang)

    # For AR: keep it simple (1 column, right aligned) to avoid ugly overlap
    if _is_ar(lang):
        x = W - margin
        y = H - margin - 35
        line_h = 13
        c.setFont(FONT_REG, 11)
        max_w = W - 2 * margin
        for p in items:
            lines = _wrap_to_width(_maybe_ar(p), FONT_REG, 11, max_w)
            for ln in lines:
                if y < margin + 20:
                    c.showPage()
                    _set_text_color(c)
                    c.setFont(FONT_BOLD, 16)
                    c.drawRightString(W - margin, H - margin - 10, L["conditions"])
                    c.setFont(FONT_REG, 11)
                    y = H - margin - 35
                c.drawRightString(x, y, ln)
                y -= line_h
            y -= 6
    else:
        # Two columns FR/EN
        col_gap = 10 * mm
        col_w = (W - 2 * margin - col_gap) / 2
        top_y = H - margin - 35
        bottom_y = margin + 18
        line_h = 12.5

        mid = (len(items) + 1) // 2
        cols = [items[:mid], items[mid:]]

        c.setFont(FONT_REG, 10.5)

        for ci in range(2):
            x = margin + ci * (col_w + col_gap)
            y = top_y
            max_w = col_w
            for paragraph in cols[ci]:
                # wrap by width, not max chars
                wrapped = _wrap_to_width(paragraph, FONT_REG, 10.5, max_w)
                for ln in wrapped:
                    if y < bottom_y:
                        break
                    c.drawString(x, y, ln)
                    y -= line_h
                y -= 6

    c.setFont(FONT_REG, 8)
    c.setFillColor(colors.grey)
    c.drawRightString(W - margin, margin - 2, f"{L['page']} 2/2")
    c.setFillColor(colors.black)


# ============================================================
# Finance PDF (kept for compatibility)
# ============================================================

def build_month_report_pdf(title: str, lines: List[str]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    margin = 18 * mm
    y = H - margin

    c.setFont(FONT_BOLD, 16)
    c.setFillColor(colors.black)
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


def build_month_report_pdf_bytes(title: str, lines: List[str]) -> bytes:
    return build_month_report_pdf(title, lines)

