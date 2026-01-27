import json

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
