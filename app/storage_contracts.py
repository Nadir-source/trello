# app/storage_contracts.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "contracts"   # app/data/contracts
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _safe_id(s: str) -> str:
    # On garde uniquement des chars safe (id trello)
    return "".join(ch for ch in s if ch.isalnum())

def contract_path(booking_id: str) -> Path:
    bid = _safe_id(booking_id)
    return DATA_DIR / f"{bid}.json"

def load_contract(booking_id: str) -> Optional[Dict[str, Any]]:
    p = contract_path(booking_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

def save_contract(booking_id: str, payload: Dict[str, Any]) -> None:
    p = contract_path(booking_id)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

