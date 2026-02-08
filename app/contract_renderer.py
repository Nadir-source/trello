# app/contract_renderer.py
from pathlib import Path
from flask import render_template
from weasyprint import HTML, CSS

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR.parent / "static" / "css"


def render_contract_pdf(payload: dict, lang: str = "fr") -> bytes:
    template_name = f"contracts/contract_{lang}.html"
    css_path = STATIC_DIR / f"contract_{lang}.css"

    context = _map_payload(payload)

    html = render_template(template_name, **context)

    stylesheets = []
    if css_path.exists():
        stylesheets.append(CSS(filename=str(css_path)))

    return HTML(string=html).write_pdf(stylesheets=stylesheets)


def _map_payload(p: dict) -> dict:
    return {
        "ref": p.get("trello_card_id", "—"),
        "now_date": p.get("now_date", "—"),

        "company": {
            "name": "ZOHIR LOCATION AUTO",
            "phone": "+213 6 00 00 00 00",
            "email": "contact@email.dz",
            "address": "Alger, Algérie",
        },

        "client": {
            "name": p.get("client_name") or "—",
            "phone": p.get("client_phone") or "—",
            "address": p.get("client_address") or "—",
            "doc_id": p.get("doc_id") or "—",
            "permit": p.get("driver_license") or "—",
        },

        "vehicle": {
            "name": p.get("vehicle_name") or "—",
            "model": p.get("vehicle_model") or "—",
            "plate": p.get("vehicle_plate") or "—",
            "vin": p.get("vehicle_vin") or "—",
        },

        "rental": {
            "from": p.get("start_date") or "—",
            "to": p.get("end_date") or "—",
            "pickup": p.get("pickup_location") or "—",
            "return": p.get("return_location") or "—",
        },

        "pricing": {
            "daily": p.get("daily_price") or "—",
            "deposit": p.get("deposit") or "—",
            "total": p.get("total_price") or "—",
            "currency": "DA",
        },

        "options": {
            "gps": p.get("options", {}).get("gps", False),
            "chauffeur": p.get("options", {}).get("chauffeur", False),
            "baby_seat": p.get("options", {}).get("baby_seat", False),
        },

        "mileage": {
            "out": p.get("km_out") or "—",
            "in": p.get("km_in") or "—",
        },

        "fuel": {
            "out": p.get("fuel_out") or "—",
            "in": p.get("fuel_in") or "—",
        },

        "notes": p.get("notes") or "—",

        "sign": {
            "place": "Alger",
            "date": p.get("now_date", "—"),
        },
    }

