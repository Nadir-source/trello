import json
from datetime import datetime

def parse_payload(desc: str) -> dict:
    desc = (desc or "").strip()
    if not desc:
        return {}
    try:
        return json.loads(desc)
    except Exception:
        return {}

def dump_payload(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)

def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def audit_add(payload: dict, by: str, action: str, meta: dict | None = None):
    payload.setdefault("audit", [])
    payload["audit"].append({
        "at": now_iso(),
        "by": by,
        "action": action,
        "meta": meta or {}
    })
