# app/trello_client.py
import os
import re
import json
import requests

BASE = "https://api.trello.com/1"


def _check_env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


def _params(extra: dict | None = None) -> dict:
    p = {
        "key": _check_env("TRELLO_KEY"),
        "token": _check_env("TRELLO_TOKEN"),
    }
    if extra:
        p.update(extra)
    return p


def _get(path: str, params: dict | None = None):
    r = requests.get(BASE + path, params=_params(params), timeout=30)
    r.raise_for_status()
    return r.json()


def _post(path: str, data: dict | None = None, params: dict | None = None):
    r = requests.post(BASE + path, params=_params(params), json=data or {}, timeout=30)
    r.raise_for_status()
    return r.json()


def _put(path: str, data: dict | None = None, params: dict | None = None):
    r = requests.put(BASE + path, params=_params(params), json=data or {}, timeout=30)
    r.raise_for_status()
    return r.json()


def _looks_like_list_id(x: str) -> bool:
    s = (x or "").strip()
    return bool(re.fullmatch(r"[a-f0-9]{24}", s, flags=re.IGNORECASE))


def resolve_board_id() -> str:
    ref = os.getenv("TRELLO_BOARD", "").strip()
    if not ref:
        raise RuntimeError("Missing TRELLO_BOARD env var (board id or shortLink).")

    if bool(re.fullmatch(r"[a-f0-9]{24}", ref, flags=re.IGNORECASE)):
        return ref

    b = _get(f"/boards/{ref}", {"fields": "id"})
    board_id = (b.get("id") or "").strip()
    if not board_id:
        raise RuntimeError(f"Unable to resolve board id from TRELLO_BOARD={ref!r}")
    return board_id


def get_list_id_by_name(board_id: str, list_name: str) -> str:
    wanted = (list_name or "").strip()
    if not wanted:
        raise RuntimeError("Empty list_name")

    lists = _get(f"/boards/{board_id}/lists", {"fields": "name"})

    # exact
    for l in lists:
        if (l.get("name") or "").strip() == wanted:
            return l["id"]

    # case-insensitive
    w2 = wanted.casefold()
    for l in lists:
        if (l.get("name") or "").strip().casefold() == w2:
            return l["id"]

    # relaxed spaces
    def norm(s: str) -> str:
        return re.sub(r"\s+", " ", (s or "").strip()).casefold()

    w3 = norm(wanted)
    for l in lists:
        if norm(l.get("name") or "") == w3:
            return l["id"]

    available = ", ".join([(l.get("name") or "").strip() for l in lists if l.get("name")])
    raise RuntimeError(f"List not found on board: {wanted!r}. Available: {available}")


class Trello:
    def __init__(self):
        self.board_id = resolve_board_id()
        self.board = _get(f"/boards/{self.board_id}", {"fields": "name,url"})

    def get_list_id(self, list_name: str) -> str:
        return get_list_id_by_name(self.board_id, list_name)

    def list_cards(self, list_id_or_name: str):
        target = (list_id_or_name or "").strip()
        if not target:
            return []

        list_id = target if _looks_like_list_id(target) else self.get_list_id(target)
        cards = _get(f"/lists/{list_id}/cards", {"fields": "name,desc,idList"})

        return [
            {
                "id": c["id"],
                "name": c.get("name", ""),
                "desc": c.get("desc", ""),
                "idList": c.get("idList", ""),
            }
            for c in cards
        ]

    def get_card(self, card_id: str):
        return _get(f"/cards/{card_id}", {"fields": "name,desc,idList,url"})

    def create_card(self, list_id_or_name: str, name: str, desc: str = ""):
        target = (list_id_or_name or "").strip()
        list_id = target if _looks_like_list_id(target) else self.get_list_id(target)
        return _post("/cards", {"idList": list_id, "name": name, "desc": desc})

    def move_card(self, card_id: str, target_list_id_or_name: str):
        target = (target_list_id_or_name or "").strip()
        target_list_id = target if _looks_like_list_id(target) else self.get_list_id(target)
        return _put(f"/cards/{card_id}", params={"idList": target_list_id})

    def archive_card(self, card_id: str):
        return _put(f"/cards/{card_id}", params={"closed": "true"})

    # bookings helper
    def create_booking_card(self, data: dict):
        import app.config as C

        title = (data.get("title") or "").strip() or "Nouvelle réservation"
        payload = dict(data)
        payload["_type"] = "booking"
        desc = json.dumps(payload, ensure_ascii=False, indent=2)

        return self.create_card(C.LIST_DEMANDES, title, desc)

    # ✅ NEW: attach file to Trello card
    def attach_file_to_card(self, card_id: str, filename: str, file_bytes: bytes):
        """
        Upload un fichier en pièce jointe sur la carte Trello.
        """
        url = f"{BASE}/cards/{card_id}/attachments"
        params = _params({})
        files = {"file": (filename, file_bytes, "application/pdf")}
        r = requests.post(url, params=params, files=files, timeout=60)
        r.raise_for_status()
        return r.json()

