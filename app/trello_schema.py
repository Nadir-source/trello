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

def audit_add(payload: dict, role: str, name: str, action: str = "event", meta: dict | None = None):
    meta = meta or {}
    payload.setdefault("_audit", [])
    payload["_audit"].append({
        "ts": datetime.utcnow().isoformat(),
        "role": role,
        "name": name,
        "action": action,
        "meta": meta,
    })

