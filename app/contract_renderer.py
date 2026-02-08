# app/contract_renderer.py
from pathlib import Path
from flask import render_template
from weasyprint import HTML, CSS

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR.parent / "static" / "css"


def render_contract_pdf(payload: dict, lang: str = "fr") -> bytes:
    """
    Génère le PDF du contrat à partir du payload déjà prêt
    (payload construit dans contracts.py)
    """
    template_name = f"contracts/contract_{lang}.html"
    css_path = STATIC_DIR / f"contract_{lang}.css"

    html_str = render_template(template_name, **payload)
    html = HTML(string=html_str)

    if css_path.exists():
        stylesheet = CSS(filename=str(css_path))
        return html.write_pdf(stylesheets=[stylesheet])

    return html.write_pdf()

