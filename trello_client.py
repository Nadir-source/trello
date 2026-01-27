import requests
from config import TRELLO_KEY, TRELLO_TOKEN, BOARD_ID

API = "https://api.trello.com/1"

def _check():
    if not (TRELLO_KEY and TRELLO_TOKEN and BOARD_ID):
        raise RuntimeError("Missing Trello config: TRELLO_KEY / TRELLO_TOKEN / BOARD_ID")

def _params(extra=None):
    p = {"key": TRELLO_KEY, "token": TRELLO_TOKEN}
    if extra:
        p.update(extra)
    return p

def board_lists():
    _check()
    r = requests.get(f"{API}/boards/{BOARD_ID}/lists", params=_params({"fields": "name"}), timeout=30)
    r.raise_for_status()
    return r.json()

def list_id_by_name(name: str) -> str:
    for lst in board_lists():
        if (lst.get("name") or "").strip() == name.strip():
            return lst["id"]
    raise RuntimeError(f"List not found on board: {name}")

def list_cards(list_name: str):
    lid = list_id_by_name(list_name)
    r = requests.get(f"{API}/lists/{lid}/cards",
                     params=_params({"fields": "name,desc,idList,closed,dateLastActivity"}),
                     timeout=30)
    r.raise_for_status()
    return r.json()

def get_card(card_id: str):
    r = requests.get(f"{API}/cards/{card_id}",
                     params=_params({"fields": "name,desc,idList,closed,dateLastActivity"}),
                     timeout=30)
    r.raise_for_status()
    return r.json()

def create_card(list_name: str, name: str, desc: str = ""):
    lid = list_id_by_name(list_name)
    r = requests.post(f"{API}/cards", params=_params({"idList": lid, "name": name, "desc": desc}), timeout=30)
    r.raise_for_status()
    return r.json()

def update_card(card_id: str, name: str = None, desc: str = None):
    data = {}
    if name is not None: data["name"] = name
    if desc is not None: data["desc"] = desc
    r = requests.put(f"{API}/cards/{card_id}", params=_params(data), timeout=30)
    r.raise_for_status()
    return r.json()

def move_card(card_id: str, target_list_name: str):
    lid = list_id_by_name(target_list_name)
    r = requests.put(f"{API}/cards/{card_id}", params=_params({"idList": lid}), timeout=30)
    r.raise_for_status()
    return r.json()
