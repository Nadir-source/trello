# app/pdf_generator.py
from __future__ import annotations

from typing import Any, Dict

from app.contract_renderer import render_contract_pdf


def build_contract_pdf(payload: Dict[str, Any], lang: str = "fr") -> bytes:
    """
    Returns a SINGLE PDF (2 pages max):
      - page 1: contract data
      - page 2: conditions + signatures
    Language: fr | en | ar
    """
    return render_contract_pdf(payload, lang)

