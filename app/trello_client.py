import os
import requests

BASE = "https://api.trello.com/1"

TRELLO_KEY = os.getenv("TRELLO_KEY", "")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN", "")
TRELLO_BOARD = os.getenv("TRELLO_BOARD", "")  # peut être id ou shortLink

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
    ref = TRELLO_BOARD.strip()
    if not ref:
        raise RuntimeError("Missing TRELLO_BOARD env var (board id or shortLink).")

    # si déjà un id 24 chars, on le garde
    if len(ref) >= 24:
        return ref[:24]

    # sinon shortLink -> GET /boards/{shortLink}
    b = _get(f"/boards/{ref}")
    return b["id"]


def get_card_by_id(card_id: str):
    c = _get(f"/cards/{card_id}", {"customFieldItems": "true"})
    return c


def get_list_id_by_name(board_id: str, list_name: str):
    lists = _get(f"/boards/{board_id}/lists", {"fields": "name"})
    for l in lists:
        if l.get("name", "").strip().lower() == list_name.strip().lower():
            return l["id"]
    raise RuntimeError(f"List not found on board: {list_name}")


class Trello:
    def __init__(self):
        self.board_id = resolve_board_id()
        self.board = _get(f"/boards/{self.board_id}", {"fields": "name,url"})

    # ---------- Lists / Cards ----------
    def list_cards(self, list_id: str):
        cards = _get(f"/lists/{list_id}/cards", {"fields": "name,desc,idList"})
        out = []
        for c in cards:
            out.append({
                "id": c["id"],
                "name": c.get("name", ""),
                "desc": c.get("desc", ""),
                "idList": c.get("idList", ""),
            })
        return out

    def create_card(self, list_id: str, name: str, desc: str = ""):
        return _post("/cards", {"idList": list_id, "name": name, "desc": desc})

    def move_card(self, card_id: str, target_list_id: str):
        return _put(f"/cards/{card_id}", {"idList": target_list_id})

    def delete_card(self, card_id: str):
        _check()
        r = requests.delete(BASE + f"/cards/{card_id}", params=_params(), timeout=TIMEOUT)
        r.raise_for_status()
        return True

    def get_card(self, card_id: str):
        return get_card_by_id(card_id)

    # ---------- Helpers ----------
    def get_list_id(self, list_name: str):
        return get_list_id_by_name(self.board_id, list_name)

