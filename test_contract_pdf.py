from flask import Flask
from app.pdf_generator import build_contract_pdf

def create_pdf_app() -> Flask:
    app = Flask(__name__)
    # IMPORTANT : on pointe templates/static sur ceux de ton dossier app/
    app.template_folder = "app/templates"
    app.static_folder = "app/static"

    # Optionnel: pour éviter certains problèmes si tu utilises url_for (normalement on ne l'utilise plus)
    app.config["SERVER_NAME"] = "localhost"
    app.config["PREFERRED_URL_SCHEME"] = "http"
    return app

payload = {
  "agency_name": "Zohir Location Auto",
  "agency_city": "Alger",
  "agency_phone": "+213 555 00 00 00",
  "agency_email": "contact@zohirlocation.dz",
  "agency_name_ar": "زهير لوكيشن أوتو",
  "agency_city_ar": "الجزائر",

  "contract_ref": "ALG-0007-20260131",
  "contract_date": "2026-01-31",

  "client_first_name": "Nadir",
  "client_last_name": "Boudoua",
  "client_phone": "+213 555 12 34 56",
  "client_address": "Hydra, Alger",
  "doc_id": "CNI 1234567890",
  "driver_license": "DZ-987654",

  "vehicle_name": "Renault Clio 5",
  "vehicle_model": "2022 • Diesel • Auto",
  "vehicle_plate": "123-456-16",
  "vehicle_vin": "VF1ABCDE123456789",

  "start_date": "2026-02-01 10:00",
  "end_date": "2026-02-05 18:00",
  "pickup_location": "Aéroport",
  "return_location": "Hydra (Agence)",

  "options": {"gps": True, "chauffeur": False, "baby_seat": True},
  "pricing": {"currency": "DZD", "daily_price": "4500", "deposit": "20000", "total": "18000"},
  "mileage": {"km_out": "120000", "km_in": ""},
  "fuel": {"out": "3/4", "in": ""},
  "notes": "Interdiction de fumer."
}

app = create_pdf_app()

with app.app_context():
    open("contract_fr.pdf", "wb").write(build_contract_pdf(payload, "fr"))
    open("contract_en.pdf", "wb").write(build_contract_pdf(payload, "en"))
    open("contract_ar.pdf", "wb").write(build_contract_pdf(payload, "ar"))

print("OK: contract_fr.pdf / contract_en.pdf / contract_ar.pdf")

