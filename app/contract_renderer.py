# app/contract_renderer.py
from pathlib import Path
from flask import render_template
from weasyprint import HTML, CSS
from app.trello_client import get_company_config

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates/contracts"
STATIC_DIR = BASE_DIR.parent / "static/css"


def render_contract_pdf(payload: dict, lang: str = "fr") -> bytes:
    from weasyprint import HTML, CSS
    from flask import render_template
    from pathlib import Path

    template_name = f"contracts/contract_{lang}.html"
    css_path = Path("static/css") / f"contract_{lang}.css"

    context = {
        "payload": _map_payload(payload),
        "company": get_company_config(),
    }

    html_str = render_template(template_name, **context)
    html = HTML(string=html_str)
    stylesheet = CSS(filename=str(css_path))
    return html.write_pdf(stylesheets=[stylesheet])




def _map_payload(p: dict) -> dict:
    return {
        "ref": p.get("trello_card_id", "—"),
        "now_date": p.get("now_date", "—"),
        "company": {
            "name": "ZOHIR LOCATION AUTO",
            "phone1": "+213 6 00 00 00 00",
            "phone2": None,
            "email": "contact@email.dz",
            "address": "Alger, Algérie"
        },
        "client": {
            "name": p.get("client_name"),
            "phone": p.get("client_phone"),
            "address": p.get("client_address"),
            "doc_id": p.get("doc_id"),
            "permit": p.get("driver_license")
        },
        "vehicle": {
            "name": p.get("vehicle_name"),
            "plate": p.get("vehicle_plate"),
            "model": p.get("vehicle_model"),
            "vin": p.get("vehicle_vin"),
        },
        "rental": {
            "from": p.get("start_date"),
            "to": p.get("end_date"),
            "pickup": p.get("pickup_location"),
            "return": p.get("return_location"),
        },
        "pricing": {
            "daily_price": p.get("daily_price"),
            "deposit": p.get("deposit"),
            "total": p.get("total_price"),
            "currency": "DA"
        },
        "options": {
            "gps": p.get("options", {}).get("gps", False),
            "chauffeur": p.get("options", {}).get("chauffeur", False),
            "baby_seat": p.get("options", {}).get("baby_seat", False)
        },
        "mileage": {
            "km_out": p.get("km_out"),
            "km_in": p.get("km_in"),
        },
        "fuel": {
            "out": p.get("fuel_out"),
            "in": p.get("fuel_in"),
        },
        "notes": p.get("notes"),
        "sign": {
            "place": "Alger",
            "date": p.get("now_date", "—"),
        }
    }

