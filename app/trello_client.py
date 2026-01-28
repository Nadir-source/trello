import os
import re
import requests

BASE = "https://api.trello.com/1"

TRELLO_KEY = os.getenv("TRELLO_KEY", "")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN", "")
TRELLO_BOARD = os.getenv("TRELLO_BOARD", "")  # id, shortLink, ou vide

TIMEOUT = 30


def _check():
    if not TRELLO_KEY or not TRELLO_TOKEN:
        raise RuntimeError("Missing TRELLO_KEY or TRELLO_TOKEN env vars")


def _params(extra=None):
    p = {"key": TRELLO_KEY, "token": TRELLO_TOKEN}
    if extra:
        p.update(extra)
    return p


def _get(path, params=None):
    _check()
    r = requests.get(BASE + path, params=_params(params), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _post(path, params=None, json=None):
    _check()
    r = requests.post(BASE + path, params=_params(params), json=json, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _put(path, params=None, json=None):
    _check()
    r = requests.put(BASE + path, params=_params(params), json=json, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def resolve_board_id():
    """
    Résout le board :
    1) TRELLO_BOARD = id -> OK
    2) TRELLO_BOARD = shortLink -> GET /boards/{shortLink}
    3) TRELLO_BOARD vide -> prend le 1er board du compte
    """
    ref = (TRELLO_BOARD or "").strip()

    if not ref:
        boards = _get("/members/me/boards", {"fields": "name,url", "filter": "open"})
        if not boards:
            raise RuntimeError("No Trello boards found for this token.")
        return boards[0]["id"]

    # id
    if len(ref) >= 24:
        return ref[:24]

    # shortLink
    b = _get(f"/boards/{ref}")
    return b["id"]


def get_card_by_id(card_id: str):
    return _get(f"/cards/{card_id}", {"fields": "name,desc,idList"})


def get_list_id_by_name(board_id: str, list_name: str):
    lists = _get(f"/boards/{board_id}/lists", {"fields": "name"})
    wanted = (list_name or "").strip().lower()
    for l in lists:
        if (l.get("name") or "").strip().lower() == wanted:
            return l["id"]
    raise RuntimeError(f"List not found on board: {list_name}")


def _looks_like_list_id(x: str) -> bool:
    """
    Trello list ids are typically 24 hex chars, but we keep this permissive.
    """
    if not x:
        return False
    s = x.strip()
    return bool(re.fullmatch(r"[a-zA-Z0-9]{20,}", s))


class Trello:
    def __init__(self):
        self.board_id = resolve_board_id()
        self.board = _get(f"/boards/{self.board_id}", {"fields": "name,url"})

    def get_list_id(self, list_name: str):
        return get_list_id_by_name(self.board_id, list_name)

    def list_cards(self, list_id_or_name: str):
        """
        Accepts either:
        - list id (recommended)
        - OR list name like "📥 DEMANDES"
        """
        target = (list_id_or_name or "").strip()
        if not target:
            return []

        if _looks_like_list_id(target):
            list_id = target
        else:
            list_id = self.get_list_id(target)

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

    def create_card(self, list_id_or_name: str, name: str, desc: str = ""):
        target = (list_id_or_name or "").strip()
        if _looks_like_list_id(target):
            list_id = target
        else:
            list_id = self.get_list_id(target)
        return _post("/cards", {"idList": list_id, "name": name, "desc": desc})

    def move_card(self, card_id: str, target_list_id_or_name: str):
        target = (target_list_id_or_name or "").strip()
        if _looks_like_list_id(target):
            target_list_id = target
        else:
            target_list_id = self.get_list_id(target)
        return _put(f"/cards/{card_id}", {"idList": target_list_id})

    def delete_card(self, card_id: str):
        _check()
        r = requests.delete(BASE + f"/cards/{card_id}", params=_params(), timeout=TIMEOUT)
        r.raise_for_status()
        return True

    def get_card(self, card_id: str):
        return get_card_by_id(card_id)

