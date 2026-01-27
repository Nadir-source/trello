# app/pdf_generator.py
import os
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Arabic shaping (RTL)
import arabic_reshaper
from bidi.algorithm import get_display


# -----------------------
# Helpers
# -----------------------
def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip() or default


def _fmt_money_dzd(value) -> str:
    try:
        v = float(value)
    except Exception:
        return f"{value} DZD"
    # format 1234567.00 -> 1 234 567 DZD
    s = f"{v:,.0f}".replace(",", " ")
    return f"{s} DZD"


def _fmt_date(value) -> str:
    """
    Accepts:
      - 'YYYY-MM-DD'
      - 'YYYY-MM-DDTHH:MM:SS'
      - datetime
      - already formatted string
    """
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return ""
        try:
            if "T" in v:
                dt = datetime.fromisoformat(v.replace("Z", ""))
                return dt.strftime("%d/%m/%Y")
            if len(v) >= 10 and v[4] == "-" and v[7] == "-":
                dt = datetime.strptime(v[:10], "%Y-%m-%d")
                return dt.strftime("%d/%m/%Y")
        except Exception:
            return v
        return v
    return str(value)


def _rtl(ar_text: str) -> str:
    """Shape + bidi for Arabic rendering in reportlab"""
    if not ar_text:
        return ""
    reshaped = arabic_reshaper.reshape(ar_text)
    return get_display(reshaped)


def _safe(v, default=""):
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


def _register_fonts():
    """
    Register Arabic font shipped in repo: app/static/fonts/NotoNaskhArabic-Regular.ttf
    Falls back to Helvetica if missing (Arabic will look broken).
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "static", "fonts")

    reg = os.path.join(fonts_dir, "NotoNaskhArabic-Regular.ttf")
    bold = os.path.join(fonts_dir, "NotoNaskhArabic-Bold.ttf")

    if os.path.exists(reg):
        pdfmetrics.registerFont(TTFont("AR", reg))
    else:
        # still register a name so code doesn't crash
        # Arabic rendering won't be correct without a real Arabic TTF
        pass

    if os.path.exists(bold):
        pdfmetrics.registerFont(TTFont("AR-B", bold))
    else:
        # if no bold, we reuse AR
        pass


def build_contract_pdf_fr_ar(data: dict) -> bytes:
    """
    Generates a 2-page PDF:
      Page 1: French
      Page 2: Arabic (RTL)
    data keys expected (best effort):
      - booking_ref
      - client_name, client_id, client_phone, client_address
      - vehicle_name, vehicle_plate, vehicle_vin
      - start_date, end_date, days
      - price_per_day, deposit, advance, total
      - pickup_place, return_place
    """
    _register_fonts()

    # Loueur info
    loueur_nom = _env("LOUEUR_NOM", "Zohir Location Auto")
    loueur_tel = _env("LOUEUR_TEL", "")
    loueur_addr = _env("LOUEUR_ADRESSE", "")

    # Booking info
    booking_ref = _safe(data.get("booking_ref") or data.get("ref") or data.get("id"), "—")

    client_name = _safe(data.get("client_name") or data.get("nom_client"))
    client_id = _safe(data.get("client_id") or data.get("cin") or data.get("passport") or data.get("id_doc"))
    client_phone = _safe(data.get("client_phone") or data.get("tel") or data.get("telephone"))
    client_address = _safe(data.get("client_address") or data.get("adresse"))

    vehicle_name = _safe(data.get("vehicle_name") or data.get("vehicule") or data.get("car_name"))
    vehicle_plate = _safe(data.get("vehicle_plate") or data.get("plate") or data.get("immatriculation"))
    vehicle_vin = _safe(data.get("vehicle_vin") or data.get("vin"))

    start_date = _fmt_date(data.get("start_date") or data.get("date_debut"))
    end_date = _fmt_date(data.get("end_date") or data.get("date_fin"))
    days = _safe(data.get("days") or data.get("nb_jours"), "—")

    price_per_day = _fmt_money_dzd(data.get("price_per_day") or data.get("prix_jour") or data.get("daily_price") or 0)
    deposit = _fmt_money_dzd(data.get("deposit") or data.get("caution") or 0)
    advance = _fmt_money_dzd(data.get("advance") or data.get("avance") or 0)
    total = _fmt_money_dzd(data.get("total") or data.get("montant_total") or 0)

    pickup_place = _safe(data.get("pickup_place") or data.get("lieu_depart"), "—")
    return_place = _safe(data.get("return_place") or data.get("lieu_retour"), "—")

    # PDF setup
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    def hr(y):
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(0.6)
        c.line(20 * mm, y, (w - 20 * mm), y)

    def box(x, y, bw, bh):
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(0.8)
        c.roundRect(x, y, bw, bh, 6, stroke=1, fill=0)

    def label_value(x, y, label, value, font="Helvetica", fsize=10, vsize=10):
        c.setFont(font, fsize)
        c.setFillColor(colors.grey)
        c.drawString(x, y, label)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", vsize)
        c.drawString(x, y - 12, value)

    # -----------------------
    # PAGE 1 - FR
    # -----------------------
    margin = 18 * mm
    y = h - margin

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin, y, "CONTRAT DE LOCATION DE VÉHICULE")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.grey)
    c.drawString(margin, y - 16, f"Référence: {booking_ref}  |  Devise: DZD")
    c.setFillColor(colors.black)

    y -= 26
    hr(y)
    y -= 18

    # Parties
    box(margin, y - 90, w - 2 * margin, 80)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin + 10, y - 20, "1) Parties")
    c.setFont("Helvetica", 10)
    c.drawString(margin + 10, y - 40, f"Loueur : {loueur_nom}")
    if loueur_tel:
        c.drawString(margin + 10, y - 55, f"Tél : {loueur_tel}")
    if loueur_addr:
        c.drawString(margin + 10, y - 70, f"Adresse : {loueur_addr}")

    c.drawString(margin + 280, y - 40, f"Locataire : {client_name}")
    c.drawString(margin + 280, y - 55, f"CNI/Passeport : {client_id}")
    c.drawString(margin + 280, y - 70, f"Tél : {client_phone}")

    y -= 110

    # Véhicule
    box(margin, y - 90, w - 2 * margin, 80)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin + 10, y - 20, "2) Véhicule")
    c.setFont("Helvetica", 10)
    c.drawString(margin + 10, y - 40, f"Modèle : {vehicle_name}")
    c.drawString(margin + 10, y - 55, f"Immatriculation : {vehicle_plate}")
    if vehicle_vin and vehicle_vin != "—":
        c.drawString(margin + 10, y - 70, f"VIN : {vehicle_vin}")

    y -= 110

    # Période / lieux
    box(margin, y - 100, w - 2 * margin, 90)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin + 10, y - 20, "3) Période & lieux")
    c.setFont("Helvetica", 10)
    c.drawString(margin + 10, y - 40, f"Début : {start_date}   |   Fin : {end_date}   |   Jours : {days}")
    c.drawString(margin + 10, y - 58, f"Lieu de départ : {pickup_place}")
    c.drawString(margin + 10, y - 76, f"Lieu de retour : {return_place}")

    y -= 120

    # Tarifs
    box(margin, y - 105, w - 2 * margin, 95)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin + 10, y - 20, "4) Tarification (DZD)")
    c.setFont("Helvetica", 10)
    c.drawString(margin + 10, y - 42, f"Prix / jour : {price_per_day}")
    c.drawString(margin + 10, y - 60, f"Caution : {deposit}")
    c.drawString(margin + 10, y - 78, f"Avance : {advance}")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin + 280, y - 60, f"TOTAL : {total}")

    y -= 125

    # Conditions (courtes) + renvoi
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "5) Conditions essentielles")
    y -= 16
    c.setFont("Helvetica", 9)

    bullets = [
        "Le véhicule est remis en bon état. Toute dégradation est à la charge du locataire.",
        "Interdiction de sous-location ou prêt du véhicule sans accord écrit du loueur.",
        "Le locataire s’engage à respecter le Code de la route. Les amendes restent à sa charge.",
        "En cas d’accident/vol : déclaration immédiate + dépôt du PV/constat sous 24h.",
        "Retard : facturation journalière + pénalités possibles. Le loueur peut reprendre le véhicule.",
        "Carburant : le véhicule doit être restitué avec le même niveau qu’au départ.",
        "La caution peut être retenue (partiellement ou totalement) en cas de dommages, retard, impayés.",
    ]
    for b in bullets:
        c.drawString(margin + 8, y, f"• {b}")
        y -= 12

    y -= 4
    c.setFont("Helvetica-Oblique", 8.5)
    c.setFillColor(colors.grey)
    c.drawString(margin, y, "La page 2 contient la version arabe et fait partie intégrante du contrat.")
    c.setFillColor(colors.black)

    # Signatures
    y -= 20
    box(margin, y - 65, (w - 2 * margin) / 2 - 6, 55)
    box(margin + (w - 2 * margin) / 2 + 6, y - 65, (w - 2 * margin) / 2 - 6, 55)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin + 10, y - 20, "Signature Loueur")
    c.drawString(margin + (w - 2 * margin) / 2 + 16, y - 20, "Signature Locataire")
    c.setFont("Helvetica", 9)
    c.drawString(margin + 10, y - 40, f"{loueur_nom}")
    c.drawString(margin + (w - 2 * margin) / 2 + 16, y - 40, f"{client_name}")

    c.showPage()

    # -----------------------
    # PAGE 2 - AR (RTL)
    # -----------------------
    # Choose Arabic font if available
    arabic_font = "AR" if "AR" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
    arabic_bold = "AR-B" if "AR-B" in pdfmetrics.getRegisteredFontNames() else arabic_font

    y = h - margin
    c.setFont(arabic_bold, 18)
    c.drawRightString(w - margin, y, _rtl("عقد كراء مركبة"))
    c.setFont(arabic_font, 10)
    c.setFillColor(colors.grey)
    c.drawRightString(w - margin, y - 16, _rtl(f"المرجع: {booking_ref}   |   العملة: دينار جزائري"))
    c.setFillColor(colors.black)

    y -= 26
    hr(y)
    y -= 18

    # Parties
    box(margin, y - 90, w - 2 * margin, 80)
    c.setFont(arabic_bold, 12)
    c.drawRightString(w - margin - 10, y - 20, _rtl("1) الأطراف"))
    c.setFont(arabic_font, 10)
    c.drawRightString(w - margin - 10, y - 40, _rtl(f"المؤجر: {loueur_nom}"))
    if loueur_tel:
        c.drawRightString(w - margin - 10, y - 55, _rtl(f"الهاتف: {loueur_tel}"))
    if loueur_addr:
        c.drawRightString(w - margin - 10, y - 70, _rtl(f"العنوان: {loueur_addr}"))

    c.drawString(margin + 10, y - 40, _rtl(f"المستأجر: {client_name}"))
    c.drawString(margin + 10, y - 55, _rtl(f"بطاقة/جواز: {client_id}"))
    c.drawString(margin + 10, y - 70, _rtl(f"الهاتف: {client_phone}"))

    y -= 110

    # Vehicle
    box(margin, y - 90, w - 2 * margin, 80)
    c.setFont(arabic_bold, 12)
    c.drawRightString(w - margin - 10, y - 20, _rtl("2) المركبة"))
    c.setFont(arabic_font, 10)
    c.drawRightString(w - margin - 10, y - 40, _rtl(f"الطراز: {vehicle_name}"))
    c.drawRightString(w - margin - 10, y - 55, _rtl(f"رقم التسجيل: {vehicle_plate}"))
    if vehicle_vin and vehicle_vin != "—":
        c.drawRightString(w - margin - 10, y - 70, _rtl(f"رقم الهيكل (VIN): {vehicle_vin}"))

    y -= 110

    # Period / places
    box(margin, y - 100, w - 2 * margin, 90)
    c.setFont(arabic_bold, 12)
    c.drawRightString(w - margin - 10, y - 20, _rtl("3) المدة والأماكن"))
    c.setFont(arabic_font, 10)
    c.drawRightString(w - margin - 10, y - 40, _rtl(f"البداية: {start_date}   |   النهاية: {end_date}   |   الأيام: {days}"))
    c.drawRightString(w - margin - 10, y - 58, _rtl(f"مكان الانطلاق: {pickup_place}"))
    c.drawRightString(w - margin - 10, y - 76, _rtl(f"مكان الإرجاع: {return_place}"))

    y -= 120

    # Pricing
    box(margin, y - 105, w - 2 * margin, 95)
    c.setFont(arabic_bold, 12)
    c.drawRightString(w - margin - 10, y - 20, _rtl("4) السعر (دينار جزائري)"))
    c.setFont(arabic_font, 10)
    c.drawRightString(w - margin - 10, y - 42, _rtl(f"السعر لليوم: {price_per_day}"))
    c.drawRightString(w - margin - 10, y - 60, _rtl(f"الضمان (الكفالة): {deposit}"))
    c.drawRightString(w - margin - 10, y - 78, _rtl(f"الدفعة المسبقة: {advance}"))
    c.setFont(arabic_bold, 11)
    c.drawString(margin + 10, y - 60, _rtl(f"المجموع: {total}"))

    y -= 125

    # Arabic conditions
    c.setFont(arabic_bold, 12)
    c.drawRightString(w - margin, y, _rtl("5) شروط أساسية"))
    y -= 16
    c.setFont(arabic_font, 9)

    ar_bullets = [
        "تُسلم المركبة بحالة جيدة، وأي ضرر يتحمله المستأجر.",
        "يمنع منعًا باتًا تأجيرها من الباطن أو إعارتها دون موافقة كتابية من المؤجر.",
        "يلتزم المستأجر باحترام قانون المرور، والغرامات على عاتقه.",
        "في حالة حادث/سرقة: إشعار فوري + إحضار محضر/معاينة خلال 24 ساعة.",
        "التأخير: يُحسب يوم إضافي وقد تُطبق غرامات، ويحق للمؤجر استرجاع المركبة.",
        "الوقود: تُعاد المركبة بنفس مستوى الوقود عند التسليم.",
        "يمكن حجز الضمان كليًا/جزئيًا عند وجود أضرار أو تأخير أو مبالغ غير مدفوعة.",
    ]
    for b in ar_bullets:
        c.drawRightString(w - margin, y, _rtl(f"• {b}"))
        y -= 12

    # Signatures
    y -= 18
    box(margin, y - 65, (w - 2 * margin) / 2 - 6, 55)
    box(margin + (w - 2 * margin) / 2 + 6, y - 65, (w - 2 * margin) / 2 - 6, 55)
    c.setFont(arabic_bold, 10)
    c.drawRightString(margin + (w - 2 * margin) / 2 - 20, y - 20, _rtl("توقيع المؤجر"))
    c.drawRightString(w - margin - 10, y - 20, _rtl("توقيع المستأجر"))
    c.setFont(arabic_font, 9)
    c.drawRightString(margin + (w - 2 * margin) / 2 - 20, y - 40, _rtl(loueur_nom))
    c.drawRightString(w - margin - 10, y - 40, _rtl(client_name))

    c.showPage()
    c.save()

    return buf.getvalue()

def build_month_report_pdf(report_data: dict) -> bytes:
    """
    Temporary month report PDF generator (placeholder).
    Keeps the app running. We'll replace it with the real monthly report (Step D).
    """
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, h - 60, "Rapport mensuel (placeholder)")

    c.setFont("Helvetica", 11)
    c.drawString(40, h - 90, "Le générateur du rapport mensuel sera finalisé (étape D).")

    # Print a few totals if present
    y = h - 130
    for k in ["month", "year", "total_income", "total_expenses", "net"]:
        if k in report_data:
            c.drawString(40, y, f"{k}: {report_data.get(k)}")
            y -= 18

    c.showPage()
    c.save()
    return buf.getvalue()

