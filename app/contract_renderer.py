# app/contract_renderer.py
from __future__ import annotations

import os
from typing import Any, Dict

from flask import render_template
from weasyprint import HTML, CSS


def render_contract_pdf(payload: Dict[str, Any], lang: str) -> bytes:
    lang = (lang or "fr").lower().strip()
    if lang not in ("fr", "en", "ar"):
        lang = "fr"

    template_map = {
        "fr": "contract_fr.html",
        "en": "contract_en.html",
        "ar": "contract_ar.html",
    }

    # Render HTML (requires Flask app context)
    html_str = render_template(template_map[lang], payload=payload)

    # Load CSS
    css_path = os.path.join(os.path.dirname(__file__), "static", "css", "contract.css")
    stylesheets = [CSS(filename=css_path)] if os.path.exists(css_path) else []

    # base_url needed for local assets if you add fonts/images later
    base_url = os.path.abspath(os.path.dirname(__file__))

    return HTML(string=html_str, base_url=base_url).write_pdf(stylesheets=stylesheets)

