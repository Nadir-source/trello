import requests
from app.config import TRELLO_KEY, TRELLO_TOKEN, BOARD_REF

API = "https://api.trello.com/1"

def _check():
    if not (TRELLO_KEY and TRELLO_TOKEN and BOARD_REF):
        raise RuntimeError("Missing Trello env: TRELLO_KEY/TRELLO_TOKEN/BOARD_ID")

def _params(extra=None):
    p = {"key": TRELLO_KEY, "token": TRELLO_TOKEN}
    if extra:
        p.update(extra)
    return p

def _get(path, extra=None):
    r = requests.get(f"{API}{path}", params=_params(extra), timeout=30)
    r.raise_for_status()
    return r.json()

def _post(path, extra=None):
    r = requests.post(f"{API}{path}", params=_params(extra), timeout=30)
    r.raise_for_status()
    return r.json()

def _put(path, extra=None):
    r = requests.put(f"{API}{path}", params=_params(extra), timeout=30)
    r.raise_for_status()
    return r.json()

def resolve_board_id(board_ref: str) -> dict:
    ref = (board_ref or "").strip()
    if "trello.com/b/" in ref:
        ref = ref.split("trello.com/b/")[1].split("/")[0].strip()
    board = _get(f"/boards/{ref}", {"fields": "id,name,url,shortLink"})
    return board  # has id (long)

class Trello:
    def __init__(self):
        _check()
        self.board = resolve_board_id(BOARD_REF)
        self.board_id = self.board["id"]
        self._lists_cache = None  # name->id

    def lists(self):
        lst = _get(f"/boards/{self.board_id}/lists", {"filter": "all", "fields": "name"})
        self._lists_cache = { (x.get("name") or "").strip(): x["id"] for x in lst }
        return self._lists_cache

    def list_id(self, name: str) -> str:
        if not self._lists_cache:
            self.lists()
        if name not in self._lists_cache:
            # refresh once
            self.lists()
        if name not in self._lists_cache:
            raise RuntimeError(f"List not found: {name}")
        return self._lists_cache[name]

    def list_cards(self, list_name: str):
        lid = self.list_id(list_name)
        return _get(f"/lists/{lid}/cards", {"fields": "name,desc,idList,closed,dateLastActivity"})

    def get_card(self, card_id: str):
        return _get(f"/cards/{card_id}", {"fields": "name,desc,idList,closed,dateLastActivity"})

    def create_card(self, list_name: str, name: str, desc: str = ""):
        lid = self.list_id(list_name)
        return _post("/cards", {"idList": lid, "name": name, "desc": desc})

    def update_card(self, card_id: str, name: str | None = None, desc: str | None = None):
        data = {}
        if name is not None: data["name"] = name
        if desc is not None: data["desc"] = desc
        return _put(f"/cards/{card_id}", data)

    def move_card(self, card_id: str, target_list_name: str):
        lid = self.list_id(target_list_name)
        return _put(f"/cards/{card_id}", {"idList": lid})

    def add_comment(self, card_id: str, text: str):
        return _post(f"/cards/{card_id}/actions/comments", {"text": text})
