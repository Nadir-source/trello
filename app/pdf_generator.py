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
        "denomination": "Nom / Prénom",
        "phone": "Téléphone",
        "address": "Adresse",
        "doc": "Document (CNI/Passeport)",
        "permit": "Permis",
        "driver1": "Conducteur habilité 01",
        "driver2": "Conducteur habilité 02",
        "name": "Nom / Prénom",
        "pickup_date": "Période de location",
        "from": "du",
        "to": "au",
        "pickup_time": "Heure de départ",
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
# CONDITIONS (MAX / COMPLET)
# NOTE: ceci n'est pas un avis juridique, adapte selon ton activité.
# ============================================================

CONDITIONS_FR = [
    "1. Objet : Le présent contrat encadre la mise à disposition d’un véhicule par le Loueur au Locataire, selon les informations indiquées sur la page 1.",
    "2. Identité & documents : Le Locataire et tout conducteur habilité doivent présenter une pièce d’identité et un permis valides. Le Loueur peut refuser la remise des clés en cas de doute ou documents incomplets.",
    "3. Conducteurs autorisés : Seules les personnes mentionnées au contrat sont autorisées à conduire. Le prêt du volant à un tiers non déclaré engage la responsabilité du Locataire.",
    "4. Usage du véhicule : Le véhicule est utilisé en « bon père de famille ». Sont interdits : conduite dangereuse, courses, transport illégal, surcharge, sous-location, apprentissage de conduite, usage hors route non adapté.",
    "5. Territoire : Le véhicule ne peut sortir du territoire autorisé par le Loueur sans accord écrit (ex : wilayas spécifiques / frontières).",
    "6. État du véhicule au départ : Le Locataire reconnaît l’état du véhicule au départ. Des photos/vidéos datées au départ sont recommandées (intérieur/extérieur).",
    "7. Carburant : Le véhicule est remis avec un niveau de carburant. Il doit être restitué au même niveau (sauf accord contraire) ; à défaut, la différence est facturée.",
    "8. Kilométrage : Le kilométrage et/ou le forfait (si applicable) est celui indiqué. Tout dépassement peut être facturé.",
    "9. Durée & retards : La location est consentie pour la période indiquée. Tout retard non validé par le Loueur peut entraîner facturation supplémentaire.",
    "10. Paiement : Le Locataire s’engage à régler le montant convenu, ainsi que les frais additionnels (prolongation, nettoyage, carburant, livraison/restitution, options).",
    "11. Dépôt de garantie / caution : Si une caution est exigée, elle couvre les dommages, pertes, carburant, amendes, nettoyage, accessoires manquants. Elle peut être conservée partiellement ou totalement selon constat.",
    "12. Amendes & infractions : Le Locataire est seul responsable des amendes, PV, frais de stationnement, fourrière, péages pendant la location.",
    "13. Entretien & alertes : Le Locataire doit surveiller voyants (huile, température, pneus). En cas d’alerte, arrêter le véhicule et prévenir immédiatement le Loueur.",
    "14. Interdiction de réparation : Aucune réparation, modification ou intervention (pneus, batterie, pièces) sans accord du Loueur, sauf urgence sécuritaire.",
    "15. Panne : En cas de panne, le Locataire doit prévenir le Loueur. La prise en charge dépend de l’origine (usure normale vs mauvaise utilisation).",
    "16. Accident / incident : Tout accident doit être déclaré immédiatement au Loueur avec photos, lieu, circonstances, coordonnées des tiers. Un constat/rapport est requis si possible.",
    "17. Vol : En cas de vol ou tentative de vol, le Locataire doit déposer plainte immédiatement et fournir le récépissé au Loueur. Les clés/documents doivent être remis si disponibles.",
    "18. Responsabilité : Le Locataire est responsable des dommages causés par sa faute, négligence, ou violation des règles du contrat, y compris accessoires manquants et dégâts intérieur.",
    "19. Assurance : Les garanties et franchises appliquées sont celles communiquées par le Loueur. Certaines situations peuvent être exclues (alcool, drogue, vitesse excessive, conducteur non autorisé).",
    "20. Nettoyage : Le véhicule doit être restitué dans un état correct. Un nettoyage peut être facturé (salissures importantes, odeurs, poils, sable, taches).",
    "21. Objets personnels : Le Loueur n’est pas responsable des objets oubliés dans le véhicule.",
    "22. Restitution : La restitution se fait au lieu/date/heure convenus. Le Loueur effectue un contrôle (extérieur/intérieur).",
    "23. Perte de clés/papiers : Toute perte de clés, carte grise, accessoires (triangle, cric, roue de secours, câble) est facturée au Locataire.",
    "24. Résiliation : Le Loueur peut reprendre le véhicule en cas de non-paiement, non-respect des conditions, suspicion de fraude ou usage interdit.",
    "25. Données : Les informations fournies servent à la gestion de la location. Elles peuvent être conservées pour preuve/gestion (contrat, incidents, facturation).",
    "26. Litiges : En cas de litige, les parties privilégient une solution amiable. À défaut, la juridiction compétente est celle indiquée par le Loueur (à adapter).",
]

CONDITIONS_EN = [
    "1. Purpose: This contract governs the rental of a vehicle from the Owner to the Renter, based on the details on page 1.",
    "2. Identity & documents: Valid ID and driving license are required for the renter and any authorized driver. The Owner may refuse delivery if documents are incomplete.",
    "3. Authorized drivers: Only drivers listed in the contract may drive. Any unauthorized driver makes the renter fully liable.",
    "4. Vehicle use: Proper and careful use is required. Forbidden: racing, illegal transport, overloading, sub-rental, driving lessons, off-road misuse.",
    "5. Territory: The vehicle may not leave the authorized area without written approval.",
    "6. Condition at pickup: The renter acknowledges the vehicle condition at pickup. Dated photos/videos are recommended.",
    "7. Fuel: Vehicle must be returned with the same fuel level unless otherwise agreed; differences may be charged.",
    "8. Mileage: Mileage limit/package (if any) applies as stated; excess mileage may be charged.",
    "9. Duration & delays: Rental applies for the agreed period. Unapproved delays may incur extra charges.",
    "10. Payment: The renter shall pay the agreed price and any additional costs (extension, cleaning, fuel, delivery/return, options).",
    "11. Deposit: If required, the deposit covers damages, fuel, fines, cleaning, missing accessories. It may be partially/fully retained after inspection.",
    "12. Fines: The renter is responsible for fines, tickets, parking, tolls, impound fees during the rental.",
    "13. Maintenance alerts: The renter must monitor warning lights (oil, temperature, tires). In case of alert, stop and contact the owner immediately.",
    "14. No repairs: No repairs/modifications without owner approval, except for safety emergencies.",
    "15. Breakdown: In case of breakdown, renter must contact owner. Coverage depends on cause (normal wear vs misuse).",
    "16. Accident/incident: Must be reported immediately with photos, location, circumstances, third-party details. A police report/statement is required when possible.",
    "17. Theft: In case of theft, renter must file a police report immediately and provide proof. Keys/documents must be returned if available.",
    "18. Liability: Renter is liable for damages caused by negligence, misuse, contract breach, missing accessories, interior damage.",
    "19. Insurance: Insurance/franchise terms apply as specified by the owner. Exclusions may apply (alcohol/drugs, excessive speed, unauthorized driver).",
    "20. Cleaning: Vehicle must be returned reasonably clean. Excess cleaning may be charged (sand, stains, odors, pet hair).",
    "21. Personal items: Owner is not responsible for items left in the vehicle.",
    "22. Return: Vehicle must be returned at agreed place/time. Owner performs inspection (inside/outside).",
    "23. Lost keys/docs: Loss of keys, documents, accessories (triangle, jack, spare wheel, cable) will be charged.",
    "24. Termination: Owner may repossess the vehicle in case of non-payment, breach, fraud suspicion, or forbidden use.",
    "25. Data: Information is used for rental management and may be retained for records (contract, incidents, billing).",
    "26. Disputes: Parties seek an amicable solution first. Otherwise, competent jurisdiction applies (to be adapted).",
]

CONDITIONS_AR = [
    _maybe_ar("1. الهدف: يحدد هذا العقد شروط كراء السيارة بين المؤجر والمستأجر حسب المعلومات في الصفحة الأولى."),
    _maybe_ar("2. الهوية والوثائق: يجب تقديم بطاقة هوية ورخصة سياقة ساريتين. يمكن للمؤجر رفض تسليم السيارة إذا كانت الوثائق ناقصة."),
    _maybe_ar("3. السائقون المصرح لهم: لا يحق القيادة إلا للأشخاص المذكورين في العقد. أي سائق غير مصرح به يجعل المستأجر مسؤولاً بالكامل."),
    _maybe_ar("4. استعمال السيارة: الاستعمال يجب أن يكون بحسن نية. يمنع: السباق، النقل غير القانوني، الحمولة الزائدة، التأجير من الباطن، تعليم السياقة، الاستعمال خارج الطريق بشكل غير مناسب."),
    _maybe_ar("5. النطاق الجغرافي: لا يجوز إخراج السيارة من المنطقة المسموح بها دون موافقة كتابية من المؤجر."),
    _maybe_ar("6. حالة السيارة عند التسليم: يقر المستأجر بحالة السيارة عند التسليم. ينصح بالصور/الفيديو بتاريخ التسليم."),
    _maybe_ar("7. الوقود: يجب إرجاع السيارة بنفس مستوى الوقود المتفق عليه، وإلا يتم احتساب الفرق."),
    _maybe_ar("8. الكيلومترات: يطبق الحد/الباقة المذكورة، وأي تجاوز قد يتم احتسابه."),
    _maybe_ar("9. المدة والتأخير: أي تأخير غير مصرح به قد يؤدي إلى رسوم إضافية."),
    _maybe_ar("10. الدفع: يلتزم المستأجر بدفع المبلغ المتفق عليه وكل الرسوم الإضافية (تمديد، تنظيف، وقود، تسليم/استرجاع، خيارات)."),
    _maybe_ar("11. الضمان/الكفالة: إذا تم طلب كفالة فهي تغطي الأضرار، الوقود، المخالفات، التنظيف، المعدات الناقصة، وقد يتم اقتطاعها حسب المعاينة."),
    _maybe_ar("12. المخالفات: المستأجر مسؤول عن جميع المخالفات والغرامات والرسوم خلال مدة الكراء."),
    _maybe_ar("13. التنبيهات والصيانة: يجب مراقبة أضواء التحذير (زيت، حرارة، إطارات). عند ظهور إنذار يجب التوقف وإبلاغ المؤجر فوراً."),
    _maybe_ar("14. منع الإصلاح: يمنع إجراء أي إصلاح أو تعديل دون موافقة المؤجر إلا في حالات السلامة القصوى."),
    _maybe_ar("15. العطب: في حالة العطل يجب إبلاغ المؤجر. تتحمل التكاليف حسب سبب العطل (استعمال عادي أو سوء استعمال)."),
    _maybe_ar("16. حادث/واقعة: يجب الإبلاغ فوراً مع صور ومكان الحادث وتفاصيل الأطراف. يفضل تقرير أو محضر عند الإمكان."),
    _maybe_ar("17. السرقة: في حالة السرقة يجب تقديم شكوى فورية لدى الشرطة وتقديم الإثبات للمؤجر."),
    _maybe_ar("18. المسؤولية: المستأجر مسؤول عن الأضرار الناتجة عن الإهمال أو سوء الاستعمال أو مخالفة شروط العقد."),
    _maybe_ar("19. التأمين: تطبق شروط التأمين والفرانشيز حسب ما يحدده المؤجر، وقد توجد استثناءات (كحول/مخدرات/سرعة مفرطة/سائق غير مصرح)."),
    _maybe_ar("20. التنظيف: يجب إرجاع السيارة بحالة نظافة مقبولة، والتنظيف الزائد (رمل/بقع/روائح/شعر) قد يتم احتسابه."),
    _maybe_ar("21. الأغراض الشخصية: المؤجر غير مسؤول عن الأغراض المتروكة داخل السيارة."),
    _maybe_ar("22. الاسترجاع: يتم الاسترجاع في المكان والوقت المتفق عليهما مع معاينة داخلية وخارجية."),
    _maybe_ar("23. ضياع المفاتيح/الوثائق: أي ضياع للمفاتيح أو الوثائق أو المعدات يتم احتسابه على المستأجر."),
    _maybe_ar("24. إنهاء العقد: يمكن للمؤجر استرجاع السيارة في حالة عدم الدفع أو مخالفة الشروط أو الاشتباه في الاحتيال أو الاستعمال الممنوع."),
    _maybe_ar("25. البيانات: تستخدم المعلومات لإدارة الكراء ويمكن حفظها لأغراض الإثبات (عقد/حوادث/فواتير)."),
    _maybe_ar("26. النزاعات: يُفضل الحل الودي أولاً، وإلا يتم اللجوء إلى الجهة القضائية المختصة (يُعدل حسب الحالة)."),
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


def _draw_kv(c: canvas.Canvas, x: float, y: float, label: str, value: str, w: float, h: float):
    c.rect(x, y, w, h, stroke=1, fill=0)
    c.setFont(FONT_REG, 8)
    c.drawString(x + 6, y + h - 11, label)
    c.setFont(FONT_BOLD, 9.5)
    c.drawString(x + 6, y + 6, _safe(value)[:60])


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
        c.drawString(x + 6, yy, _safe(ln)[:95])
        yy -= 12


def _fmt_dt_local(dt_str: str) -> str:
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

    # Body: two big panels
    body_top = y0 - 8
    body_h = 112 * mm
    left_w = (W - 2 * margin) * 0.52
    right_w = (W - 2 * margin) - left_w - 6

    left_x = margin
    right_x = margin + left_w + 6
    body_y = body_top - body_h

    c.setFont(FONT_BOLD, 11)
    c.rect(left_x, body_y, left_w, body_h, stroke=1, fill=0)
    c.drawString(left_x + 8, body_y + body_h - 16, L["tenant"])

    c.rect(right_x, body_y, right_w, body_h, stroke=1, fill=0)
    c.drawString(right_x + 8, body_y + body_h - 16, L["vehicle"])

    # Left fields
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

    # ✅ FIX _draw_kv calls (no duplicate w/h)
    _draw_kv(c, grid_x, grid_top - row_h, L["denomination"], p_client, left_w - 12, row_h)
    _draw_kv(c, grid_x, grid_top - 2 * row_h, L["phone"], p_phone, (left_w - 12) * 0.52, row_h)
    _draw_kv(
        c,
        grid_x + (left_w - 12) * 0.52 + 6,
        grid_top - 2 * row_h,
        L["doc"],
        p_doc,
        (left_w - 12) * 0.48 - 6,
        row_h,
    )
    _draw_kv(c, grid_x, grid_top - 3 * row_h, L["address"], p_addr, left_w - 12, row_h)
    _draw_kv(c, grid_x, grid_top - 4 * row_h, L["permit"], p_permit, left_w - 12, row_h)

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

    # Right panel fields
    v_name = _safe(payload.get("vehicle_name"))
    v_plate = _safe(payload.get("vehicle_plate"))
    v_model = _safe(payload.get("vehicle_model")) or v_name
    v_vin = _safe(payload.get("vehicle_vin"))

    rx = right_x + 6
    rt = body_y + body_h - 26

    # ✅ FIX _draw_kv calls (no duplicate w/h)
    _draw_kv(c, rx, rt - row_h, L["model"], v_model, right_w - 12, row_h)
    _draw_kv(c, rx, rt - 2 * row_h, L["plate"], v_plate, right_w - 12, row_h)
    _draw_kv(c, rx, rt - 3 * row_h, L["vin"], v_vin, right_w - 12, row_h)

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
    bottom_y = margin + 10

    c.rect(margin, bottom_y + 38 * mm, W - 2 * margin, 30 * mm, stroke=1, fill=0)
    c.setFont(FONT_BOLD, 10.5)
    c.drawString(margin + 8, bottom_y + 38 * mm + 30 * mm - 14, L["return_fill"])

    bx = margin + 8
    by = bottom_y + 42 * mm
    bw = (W - 2 * margin - 24) / 2
    bh = 18 * mm

    # ✅ FIX _draw_kv calls for km/fuel
    _draw_kv(c, bx, by, L["km"], "", bw, bh)
    _draw_kv(c, bx + bw + 8, by, L["fuel"], "", bw, bh)

    sig_y = bottom_y
    sig_h = 34 * mm
    sig_w = (W - 2 * margin - 10) / 2

    c.rect(margin, sig_y, sig_w, sig_h, stroke=1, fill=0)
    c.rect(margin + sig_w + 10, sig_y, sig_w, sig_h, stroke=1, fill=0)

    c.setFont(FONT_REG, 9)
    c.drawString(margin + 8, sig_y + sig_h - 14, L["sign_renter"])
    c.drawString(margin + sig_w + 18, sig_y + sig_h - 14, L["sign_tenant"])

    c.setFont(FONT_REG, 7.5)
    c.setFillColor(colors.grey)
    c.drawRightString(W - margin, margin - 2, f"{L['page']} 1/2")
    c.setFillColor(colors.white)


def _draw_contract_page_2_conditions(c: canvas.Canvas, lang: str, L: Dict[str, str], W: float, H: float):
    margin = 14 * mm
    c.setStrokeColor(colors.white)
    c.setFillColor(colors.white)

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
    c.setFillColor(colors.white)

    c.setFont(FONT_REG, 7.5)
    c.setFillColor(colors.grey)
    c.drawRightString(W - margin, margin - 2, f"{L['page']} 2/2")
    c.setFillColor(colors.white)


def _wrap_text(text: str, max_chars: int = 80) -> List[str]:
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

