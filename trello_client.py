import os
import requests

# ---- ENV ----
TRELLO_KEY = os.getenv("TRELLO_KEY") or os.getenv("TRELLO_API_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")

# Board: tu peux passer BOARD_ID ou TRELLO_BOARD_ID
BOARD_REF = os.getenv("BOARD_ID") or os.getenv("TRELLO_BOARD_ID")

# List names (tu peux overrider via env)
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
    """
    BOARD_REF peut être:
    - un id board (8+ chars)
    - une URL trello (https://trello.com/b/XXXX/...)
    - ou vide => erreur
    """
    if not BOARD_REF:
        raise RuntimeError("Missing BOARD_ID / TRELLO_BOARD_ID env var")

    ref = BOARD_REF.strip()

    # URL => /b/{shortLink}/...
    if "trello.com" in ref and "/b/" in ref:
        try:
            short = ref.split("/b/")[1].split("/")[0]
            b = _get(f"/boards/{short}")
            return b["id"]
        except Exception:
            pass

    # assume direct id or shortLink
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
    # fields min pour ton UI
    return _get(f"/lists/{list_id}/cards", params={"fields": "name,desc,idList"})


def create_card(list_id: str, title: str, desc: str):
    return _post("/cards", data={"idList": list_id, "name": title, "desc": desc})


def move_card_to_list(card_id: str, list_id: str):
    return _put(f"/cards/{card_id}", data={"idList": list_id})


def get_card_by_id(card_id: str):
    return _get(f"/cards/{card_id}", params={"fields": "name,desc,idList"})


def ensure_default_lists(board_id: str):
    """
    Optionnel: crée les listes si elles n’existent pas.
    """
    existing = {l["name"] for l in get_lists(board_id)}
    wanted = [LIST_DEMANDES, LIST_RESERVED, LIST_ONGOING, LIST_DONE, LIST_CANCEL]
    for name in wanted:
        if name and name not in existing:
            _post("/lists", data={"idBoard": board_id, "name": name})

