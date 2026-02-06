# app/contract_renderer.py
from __future__ import annotations

import os
from typing import Any, Dict

from flask import render_template
from weasyprint import HTML, CSS


def render_contract_pdf(payload, lang="fr"):
    base_url = os.path.abspath("app/static")

    template_name = f"contracts/contract_{lang}.html"
    css_path = f"static/css/contract_{lang}.css"

    html_str = render_template(template_name, **payload)
    stylesheet = CSS(filename=css_path)

    return HTML(string=html_str, base_url=base_url).write_pdf(stylesheets=[stylesheet])



    # Render HTML (requires Flask app context)
    html_str = render_template(template_map[lang], payload=payload)

    # Load CSS
    css_path = os.path.join(os.path.dirname(__file__), "static", "css", "contract.css")
    stylesheets = [CSS(filename=css_path)] if os.path.exists(css_path) else []

    # base_url needed for local assets if you add fonts/images later
    base_url = os.path.abspath(os.path.dirname(__file__))

    return HTML(string=html_str, base_url=base_url).write_pdf(stylesheets=stylesheets)

