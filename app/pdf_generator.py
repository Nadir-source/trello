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
# Put fonts here for better Arabic + accents:
#   app/static/fonts/DejaVuSans.ttf
#   app/static/fonts/DejaVuSans-Bold.ttf
UNICODE_FONT_REGULAR = os.getenv("PDF_UNICODE_FONT_REGULAR", "DejaVuSans")
UNICODE_FONT_BOLD = os.getenv("PDF_UNICODE_FONT_BOLD", "DejaVuSans-Bold")


def _try_register_unicode_fonts() -> Tuple[str, str]:
    """
    Try to register DejaVu fonts if present. Falls back to Helvetica.
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

# ============================================================
# Conditions (max / plus complet)
# ============================================================

CONDITIONS_FR = [
    "1. Objet : Le loueur met à disposition du locataire le véhicule identifié au présent contrat.",
    "2. Documents : Le locataire/ conducteur présente une pièce d’identité, un permis valide et, si demandé, un justificatif de domicile.",
    "3. Conducteurs : Seuls les conducteurs déclarés et autorisés peuvent conduire le véhicule. Toute conduite par un tiers engage la responsabilité du locataire.",
    "4. Âge/Expérience : Le loueur peut refuser la location si l’âge, l’expérience de conduite ou la situation du conducteur ne le permettent pas.",
    "5. État du véhicule au départ : Le locataire reconnaît l’état du véhicule au départ (photos recommandées). Toute réserve doit être indiquée avant départ.",
    "6. Usage : Interdiction d’usage hors route, compétition, remorquage (sauf accord), transport de marchandises illicites ou usage contraire à la loi.",
    "7. Zone de circulation : Toute sortie de zone/ville/pays (si applicable) doit être validée par le loueur.",
    "8. Carburant : Le véhicule est remis avec un niveau de carburant convenu et doit être restitué selon le même niveau, sauf accord contraire.",
    "9. Kilométrage : Le kilométrage inclus et l’éventuel surplus sont facturables selon le tarif défini par le loueur.",
    "10. Durée : La location est consentie pour la période indiquée. Tout dépassement peut être facturé (heures/jours supplémentaires).",
    "11. Paiement : Le locataire s’engage à régler le montant convenu (location + options). Un dépôt/ caution peut être exigé.",
    "12. Amendes/Péages : Amendes, infractions, péages, stationnement et frais liés à la conduite sont à la charge du locataire.",
    "13. Accident/Incident : Tout accident/incident doit être signalé immédiatement au loueur (photos, coordonnées, constat si possible).",
    "14. Vol : En cas de vol, le locataire doit déposer plainte sans délai et remettre le récépissé au loueur.",
    "15. Assurance : L’assurance et/ou franchise appliquées sont celles indiquées par le loueur. Certaines exclusions peuvent s’appliquer.",
    "16. Dommages : Les dommages non couverts par l’assurance, ou dus à une négligence (ex: clés perdues, mauvaise utilisation), restent à la charge du locataire.",
    "17. Entretien : Le locataire s’engage à un usage raisonnable. Toute alerte mécanique doit être signalée (ne pas continuer à rouler si risque).",
    "18. Restitution : Le véhicule doit être restitué au lieu/date/heure prévus, avec les documents/équipements remis (clé, triangle, gilet, etc.).",
    "19. Nettoyage : Des frais de nettoyage peuvent être appliqués si le véhicule est rendu très sale (intérieur/extérieur).",
    "20. Résiliation : En cas de non-respect des conditions, le loueur peut exiger la restitution immédiate du véhicule.",
    "21. Données/Confidentialité : Les informations du locataire peuvent être conservées pour la gestion du contrat et des factures.",
    "22. Litiges : En cas de litige, une solution amiable est privilégiée avant toute action.",
]

CONDITIONS_EN = [
    "1. Purpose: The owner provides the vehicle identified in this contract to the renter.",
    "2. Documents: Valid ID and driving license are required; proof of address may be requested.",
    "3. Drivers: Only declared/authorized drivers may operate the vehicle. Any third-party driving is under renter’s responsibility.",
    "4. Eligibility: The owner may refuse rental based on age/experience or driver situation.",
    "5. Vehicle condition at pickup: The renter acknowledges the vehicle condition (photos recommended). Any remarks must be stated before departure.",
    "6. Use: No off-road, racing, towing (unless agreed), illegal transport, or unlawful use.",
    "7. Area of use: Leaving the authorized area/city/country (if applicable) must be approved by the owner.",
    "8. Fuel: Vehicle is provided with an agreed fuel level and must be returned with the same level unless otherwise agreed.",
    "9. Mileage: Included mileage and any excess mileage may be billed according to the owner’s rates.",
    "10. Duration: Rental applies for stated dates/time. Overruns may be billed (extra hours/days).",
    "11. Payment: The renter pays the agreed amount (rental + options). A deposit may be required.",
    "12. Fines/Tolls: Fines, violations, tolls, parking fees are at renter’s expense.",
    "13. Accident/Incident: Any accident/incident must be reported immediately (photos, details, report when applicable).",
    "14. Theft: In case of theft, renter must file a police report promptly and provide proof to the owner.",
    "15. Insurance: Insurance/franchise terms apply as specified by the owner; exclusions may apply.",
    "16. Damages: Damages not covered by insurance or due to negligence (e.g., lost keys) remain renter’s responsibility.",
    "17. Care: Renter must use the vehicle reasonably and report any mechanical warning (do not continue driving if unsafe).",
    "18. Return: Vehicle must be returned at agreed time/place with all provided items (keys, safety kit, etc.).",
    "19. Cleaning: Cleaning fees may apply if the vehicle is returned excessively dirty.",
    "20. Termination: If terms are breached, owner may demand immediate return of the vehicle.",
    "21. Data: Renter information may be stored for contract and billing purposes.",
    "22. Disputes: Parties should seek an amicable solution before legal action.",
]

CONDITIONS_AR = [
    _maybe_ar("1. الموضوع: يضع المؤجر السيارة المذكورة في هذا العقد تحت تصرف المستأجر."),
    _maybe_ar("2. الوثائق: يجب تقديم بطاقة هوية ورخصة سياقة ساريتين، وقد يُطلب إثبات عنوان."),
    _maybe_ar("3. السائقون: يمنع قيادة السيارة إلا من طرف السائقين المصرح بهم. أي قيادة من طرف شخص آخر تكون على مسؤولية المستأجر."),
    _maybe_ar("4. الأهلية: يمكن للمؤجر رفض الكراء حسب السن/الخبرة أو وضعية السائق."),
    _maybe_ar("5. حالة السيارة عند التسليم: يقر المستأجر بحالة السيارة عند التسليم (ينصح بالصور). يجب تسجيل أي ملاحظة قبل الانطلاق."),
    _maybe_ar("6. الاستعمال: يمنع الاستعمال خارج الطريق، السباقات، القطر (إلا باتفاق)، أو أي استعمال غير قانوني."),
    _maybe_ar("7. مجال الاستعمال: الخروج من المجال/المدينة/البلد (إن وجد) يتطلب موافقة المؤجر."),
    _maybe_ar("8. الوقود: تُسلم السيارة بمستوى وقود متفق عليه وتُعاد بنفس المستوى إلا باتفاق آخر."),
    _maybe_ar("9. الكيلومترات: قد يتم احتساب فائض الكيلومترات حسب تسعيرة المؤجر."),
    _maybe_ar("10. المدة: الكراء محدد بالمدة المذكورة وأي تجاوز قد يُدفع عنه."),
    _maybe_ar("11. الدفع: يلتزم المستأجر بدفع المبلغ المتفق عليه (الكراء + الخيارات). وقد تُطلب كفالة."),
    _maybe_ar("12. المخالفات والرسوم: المخالفات، الرسوم، مواقف السيارات والطرقات على عاتق المستأجر."),
    _maybe_ar("13. حادث/ضرر: يجب الإبلاغ فورًا عن أي حادث أو ضرر مع صور ومعلومات إن أمكن."),
    _maybe_ar("14. سرقة: في حالة السرقة يجب تقديم شكوى لدى الجهات المختصة وتسليم وصل الشكوى للمؤجر."),
    _maybe_ar("15. التأمين: تطبق شروط التأمين/الفرانشيز حسب ما يحدده المؤجر مع احتمال وجود استثناءات."),
    _maybe_ar("16. الأضرار: الأضرار غير المغطاة أو الناتجة عن الإهمال (مثل ضياع المفاتيح) تكون على عاتق المستأجر."),
    _maybe_ar("17. العناية: يجب استعمال السيارة بشكل معقول والإبلاغ عن أي عطل وعدم مواصلة القيادة إن كان ذلك خطرًا."),
    _maybe_ar("18. الاسترجاع: تُعاد السيارة في المكان/الوقت المتفق عليه مع كل التجهيزات والوثائق."),
    _maybe_ar("19. التنظيف: قد تُفرض رسوم تنظيف إذا أُعيدت السيارة متسخة جدًا."),
    _maybe_ar("20. الإنهاء: في حالة مخالفة الشروط يمكن للمؤجر طلب إرجاع السيارة فورًا."),
    _maybe_ar("21. البيانات: يمكن الاحتفاظ ببيانات المستأجر لأغراض العقد والفوترة."),
    _maybe_ar("22. النزاعات: يُفضل الحل الودي قبل اللجوء إلى القضاء."),
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


def _draw_kv(c: canvas.Canvas, x: float, y: float, w: float, h: float, label: str, value: str):
    """
    Simple key/value rectangle.
    """
    c.rect(x, y, w, h, stroke=1, fill=0)
    c.setFont(FONT_REG, 8)
    c.drawString(x + 6, y + h - 11, label)
    c.setFont(FONT_BOLD, 9.5)
    c.drawString(x + 6, y + 6, (value or "")[:60])


def _draw_multiline(c: canvas.Canvas, x: float, y: float, w: float, h: float, label: str, lines: List[str]):
    c.rect(x, y, w, h, stroke=1, fill=0)
    if label:
        c.setFont(FONT_REG, 8)
        c.drawString(x + 6, y + h - 11, label)
        yy = y + h - 24
    else:
        yy = y + h - 14

    c.setFont(FONT_REG, 9)
    for ln in lines[:6]:
        c.drawString(x + 6, yy, (ln or "")[:90])
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
    ref = _safe(payload.get("contract_ref"))
    if ref:
        return ref
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

    _draw_contract_page_1(c, payload, lang, L, W, H)
    c.showPage()
    _draw_contract_page_2_conditions(c, lang, L, W, H)

    c.save()
    return buf.getvalue()


def _draw_contract_page_1(c: canvas.Canvas, payload: Dict[str, Any], lang: str, L: Dict[str, str], W: float, H: float):
    margin = 12 * mm
    top = H - margin

    # ✅ IMPORTANT: black text (not white)
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.black)

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

    cx = x0 + company_w + 14
    cy = y0 + header_h - 34
    _draw_checkbox(c, cx, cy, cb_size, checked=False)
    c.drawString(cx + cb_size + 6, cy + 2, L["enterprise"])

    cx2 = cx + 120
    _draw_checkbox(c, cx2, cy, cb_size, checked=True)
    c.drawString(cx2 + cb_size + 6, cy + 2, L["individual"])

    ref_y = y0 + 8
    c.setFont(FONT_REG, 9)
    c.drawString(x0 + company_w + 14, ref_y + 16, f"{L['ref']} :")
    c.setFont(FONT_BOLD, 10.5)
    c.drawString(x0 + company_w + 120, ref_y + 16, _contract_ref(payload))

    # Body panels
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

    p_start = _fmt_dt_local(_safe(payload.get("start_date")))
    p_end = _fmt_dt_local(_safe(payload.get("end_date")))
    p_pick = _safe(payload.get("pickup_location"))
    p_ret = _safe(payload.get("return_location"))

    grid_x = left_x + 6
    grid_top = body_y + body_h - 26
    row_h = 14 * mm

    # ✅ FIX: correct _draw_kv signature (no duplicated w/h)
    _draw_kv(c, grid_x, grid_top - row_h, left_w - 12, row_h, L["denomination"], p_client)

    w1 = (left_w - 12) * 0.52
    w2 = (left_w - 12) * 0.48 - 6
    _draw_kv(c, grid_x, grid_top - 2 * row_h, w1, row_h, L["phone"], p_phone)
    _draw_kv(c, grid_x + w1 + 6, grid_top - 2 * row_h, w2, row_h, L["doc"], p_doc)

    _draw_kv(c, grid_x, grid_top - 3 * row_h, left_w - 12, row_h, L["address"], p_addr)
    _draw_kv(c, grid_x, grid_top - 4 * row_h, left_w - 12, row_h, L["permit"], p_permit)

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

    _draw_kv(c, rx, rt - row_h, right_w - 12, row_h, L["model"], v_model)
    _draw_kv(c, rx, rt - 2 * row_h, right_w - 12, row_h, L["plate"], v_plate)
    _draw_kv(c, rx, rt - 3 * row_h, right_w - 12, row_h, L["vin"], v_vin)

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

    # Options + notes
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

    # Bottom: return fill + signatures
    bottom_top = body_y - 8
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

    _draw_kv(c, bx, by, bw, bh, L["km"], "")
    _draw_kv(c, bx + bw + 8, by, bw, bh, L["fuel"], "")

    # Signatures
    sig_y = bottom_y
    sig_h = 34 * mm
    sig_w = (W - 2 * margin - 10) / 2

    c.rect(margin, sig_y, sig_w, sig_h, stroke=1, fill=0)
    c.rect(margin + sig_w + 10, sig_y, sig_w, sig_h, stroke=1, fill=0)

    c.setFont(FONT_REG, 9)
    c.drawString(margin + 8, sig_y + sig_h - 14, L["sign_renter"])
    c.drawString(margin + sig_w + 18, sig_y + sig_h - 14, L["sign_tenant"])

    # Footer
    c.setFont(FONT_REG, 7.5)
    c.setFillColor(colors.grey)
    c.drawRightString(W - margin, margin - 2, f"{L['page']} 1/2")
    c.setFillColor(colors.black)


def _draw_contract_page_2_conditions(c: canvas.Canvas, lang: str, L: Dict[str, str], W: float, H: float):
    margin = 14 * mm

    # ✅ IMPORTANT: black text (not white)
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.black)

    c.setFont(FONT_BOLD, 15)
    c.drawString(margin, H - margin - 10, L["conditions"])

    items = _conditions_for_lang(lang)
    col_gap = 10 * mm
    col_w = (W - 2 * margin - col_gap) / 2
    top_y = H - margin - 30
    bottom_y = margin + 14

    c.setFont(FONT_REG, 10)
    line_h = 12

    mid = (len(items) + 1) // 2
    cols = [items[:mid], items[mid:]]

    for ci in range(2):
        x = margin + ci * (col_w + col_gap)
        y = top_y
        for paragraph in cols[ci]:
            lines = _wrap_text(paragraph, max_chars=78)
            for ln in lines:
                if y < bottom_y:
                    break
                c.drawString(x, y, ln)
                y -= line_h
            y -= 6

    c.setFont(FONT_REG, 9)
    c.setFillColor(colors.grey)
    c.drawString(margin, margin + 6, "Empreintes et Signature / Signatures")
    c.setFillColor(colors.black)

    c.setFont(FONT_REG, 7.5)
    c.setFillColor(colors.grey)
    c.drawRightString(W - margin, margin - 2, f"{L['page']} 2/2")
    c.setFillColor(colors.black)


def _wrap_text(text: str, max_chars: int = 80) -> List[str]:
    s = _safe(text)
    if not s:
        return [""]
    words = s.split()
    lines: List[str] = []
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


def build_month_report_pdf_bytes(title: str, lines: List[str]) -> bytes:
    return build_month_report_pdf(title, lines)

