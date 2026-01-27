import os
import requests

TRELLO_KEY = os.getenv("TRELLO_KEY") or os.getenv("TRELLO_API_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
BOARD_REF = os.getenv("BOARD_ID") or os.getenv("TRELLO_BOARD_ID")

LIST_DEMANDES = os.getenv("LIST_NAME_FILTER", "📥 DEMANDES")
LIST_RESERVED = os.getenv("RESERVED_LIST_NAME", "📅 RÉSERVÉES")
LIST_DONE     = os.getenv("TRELLO_CLOSED_LIST_NAME", "✅ TERMINÉES")
LIST_ONGOING  = os.getenv("LIST_ONGOING", "🔑 EN COURS")
LIST_CANCEL   = os.getenv("LIST_CANCELLED", "❌ ANNULÉES")

BASE = "https://api.trello.com/1"


def _check():
    if not TRELLO_KEY or not TRELLO_TOKEN:
        raise RuntimeError("Missing TRELLO_KEY/TRELLO_TOKEN env vars")


def _params(extra=None):
    p = {"key": TRELLO_KEY, "token": TRELLO_TOKEN}
    if extra:
        p.update(extra)
    return p


def _get(path, params=None):
    _check()
    r = requests.get(BASE + path, params=_params(params))
    r.raise_for_status()
    return r.json()


def _post(path, data=None):
    _check()
    r = requests.post(BASE + path, params=_params(), data=data or {})
    r.raise_for_status()
    return r.json()


def _put(path, data=None):
    _check()
    r = requests.put(BASE + path, params=_params(), data=data or {})
    r.raise_for_status()
    return r.json()


def resolve_board_id():
    if not BOARD_REF:
        raise RuntimeError("Missing BOARD_ID / TRELLO_BOARD_ID env var")

    ref = BOARD_REF.strip()

    if "trello.com" in ref and "/b/" in ref:
        short = ref.split("/b/")[1].split("/")[0]
        b = _get(f"/boards/{short}")
        return b["id"]

    b = _get(f"/boards/{ref}")
    return b["id"]


def get_lists(board_id: str):
    return _get(f"/boards/{board_id}/lists", params={"fields": "name"})


def get_list_id_by_name(board_id: str, list_name: str):
    lists = get_lists(board_id)
    for l in lists:
        if l.get("name") == list_name:
            return l["id"]
    raise RuntimeError(f'List "{list_name}" not found on board')


def get_cards_by_list_id(list_id: str):
    return _get(f"/lists/{list_id}/cards", params={"fields": "name,desc,idList"})


def create_card(list_id: str, title: str, desc: str):
    return _post("/cards", data={"idList": list_id, "name": title, "desc": desc})


def move_card_to_list(card_id: str, list_id: str):
    return _put(f"/cards/{card_id}", data={"idList": list_id})


def get_card_by_id(card_id: str):
    return _get(f"/cards/{card_id}", params={"fields": "name,desc,idList"})

# ---------------------------------------------------------
# Compatibility layer: keep old code working (dashboard, etc.)
# ---------------------------------------------------------
# ---------------------------------------------------------
# Compatibility layer: keep old code working (dashboard, clients, etc.)
# ---------------------------------------------------------
class Trello:
    def __init__(self):
        self.board_id = resolve_board_id()
    # keep old code compatibility: dashboard expects t.board
        try:
            self.board = _get(f"/boards/{self.board_id}", params={"fields": "name,url,shortUrl"})
        except Exception:
        # fallback minimal
            self.board = {"id": self.board_id, "name": "Trello Board", "url": ""}

    # -------- Lists --------
    def get_lists(self):
        return get_lists(self.board_id)

    def get_list_id_by_name(self, name: str):
        return get_list_id_by_name(self.board_id, name)

    # old name expected by some files
    def list_cards(self, list_name: str):
        """Return cards for a list by its name (old API)."""
        list_id = get_list_id_by_name(self.board_id, list_name)
        return get_cards_by_list_id(list_id)

    # aliases (just in case different modules use different names)
    def get_cards_by_list_name(self, list_name: str):
        return self.list_cards(list_name)

    def cards(self, list_name: str):
        return self.list_cards(list_name)

    # -------- Cards --------
    def get_card(self, card_id: str):
        return get_card_by_id(card_id)

    def get_card_by_id(self, card_id: str):
        return get_card_by_id(card_id)

    def create_card(self, list_name: str, title: str, desc: str):
        list_id = get_list_id_by_name(self.board_id, list_name)
        return create_card(list_id, title, desc)

    def move_card(self, card_id: str, list_name: str):
        list_id = get_list_id_by_name(self.board_id, list_name)
        return move_card_to_list(card_id, list_id)

    # old naming
    def move(self, card_id: str, list_name: str):
        return self.move_card(card_id, list_name)

