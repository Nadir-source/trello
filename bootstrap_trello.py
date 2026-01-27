import os
import json
import requests

API = "https://api.trello.com/1"

KEY = os.getenv("TRELLO_KEY")
TOKEN = os.getenv("TRELLO_TOKEN")
BOARD_REF = os.getenv("BOARD_ID") or os.getenv("TRELLO_BOARD_ID")  # peut être shortLink ou id long

if not (KEY and TOKEN and BOARD_REF):
    raise SystemExit("❌ Missing env: TRELLO_KEY, TRELLO_TOKEN, BOARD_ID (or TRELLO_BOARD_ID)")

def params(extra=None):
    p = {"key": KEY, "token": TOKEN}
    if extra:
        p.update(extra)
    return p

def trello_get(path, extra=None):
    r = requests.get(f"{API}{path}", params=params(extra), timeout=30)
    if not r.ok:
        print("❌ Trello GET failed:", r.status_code, path)
        try:
            print("Response:", r.json())
        except Exception:
            print("Response text:", r.text[:800])
        r.raise_for_status()
    return r.json()

def trello_post(path, extra=None):
    r = requests.post(f"{API}{path}", params=params(extra), timeout=30)
    if not r.ok:
        print("❌ Trello POST failed:", r.status_code, path)
        print("Sent:", extra)
        try:
            print("Response:", r.json())
        except Exception:
            print("Response text:", r.text[:800])
        r.raise_for_status()
    return r.json()

# Couleurs valides Trello
VALID_LABEL_COLORS = {
    "green", "yellow", "orange", "red", "purple",
    "blue", "sky", "lime", "pink", "black", "none"
}

def resolve_board_id(board_ref: str) -> tuple[str, dict]:
    """
    board_ref peut être:
    - shortLink (ex: E7RiQWGZ)
    - id long (ex: 5abbe4b7ddc1b351ef961414)
    - URL (ex: https://trello.com/b/E7RiQWGZ/xxx)
    """
    ref = board_ref.strip()

    # Si on reçoit une URL, extraire le shortLink
    if "trello.com/b/" in ref:
        ref = ref.split("trello.com/b/")[1].split("/")[0].strip()

    board = trello_get(f"/boards/{ref}", {"fields": "id,name,url,shortLink"})
    board_id_long = board["id"]  # ✅ celui-ci marche pour /labels, /lists, etc.
    return board_id_long, board

def ensure_label(board_id_long, name, color):
    if color not in VALID_LABEL_COLORS:
        print(f"⚠️ Invalid label color '{color}', fallback => 'blue'")
        color = "blue"

    labels = trello_get(f"/boards/{board_id_long}/labels", {"limit": 1000})
    for lb in labels:
        if (lb.get("name") or "").strip() == name.strip():
            return lb["id"]

    # /labels exige idBoard = id long
    lb = trello_post("/labels", {"idBoard": board_id_long, "name": name, "color": color})
    return lb["id"]

def ensure_list(board_id_long, name, pos="bottom"):
    lists = trello_get(f"/boards/{board_id_long}/lists", {"filter": "all"})
    for lst in lists:
        if (lst.get("name") or "").strip() == name.strip():
            return lst["id"]
    lst = trello_post("/lists", {"idBoard": board_id_long, "name": name, "pos": pos})
    return lst["id"]

def create_card(list_id, name, desc="", labels=None):
    card = trello_post("/cards", {"idList": list_id, "name": name, "desc": desc})
    if labels:
        for label_id in labels:
            trello_post(f"/cards/{card['id']}/idLabels", {"value": label_id})
    return card["id"]

def add_checklist(card_id, title, items):
    cl = trello_post("/checklists", {"idCard": card_id, "name": title})
    checklist_id = cl["id"]
    for it in items:
        trello_post(f"/checklists/{checklist_id}/checkItems", {"name": it, "checked": "false"})
    return checklist_id

# ===== Payload templates (stockés dans desc JSON) =====

def booking_template_payload():
    return {
        "type": "booking",
        "booking_status": "DEMANDE",  # DEMANDE/RESERVED/ONGOING/DONE/CANCELLED
        "client_card_id": "",
        "vehicle_card_id": "",
        "start_date": "",
        "end_date": "",
        "price_per_day": 0,
        "deposit": 0,
        "paid_amount": 0,
        "payment_method": "cash",  # cash/transfer/card
        "extras": {"driver": False, "gps": False, "child_seat": False},
        "pickup_place": "",
        "return_place": "",
        "km_out": None,
        "fuel_out": "",
        "km_in": None,
        "fuel_in": "",
        "damage_notes": "",
        "created_by": "",
        "audit": []
    }

def vehicle_template_payload():
    return {
        "type": "vehicle",
        "plate": "",
        "brand": "",
        "model": "",
        "year": None,
        "color": "",
        "km": 0,
        "status": "AVAILABLE",  # AVAILABLE/RENTED/MAINTENANCE
        "insurance_expiry": "",
        "technical_control_expiry": "",
        "notes": ""
    }

def client_template_payload():
    return {
        "type": "client",
        "full_name": "",
        "phone": "",
        "doc_id": "",
        "driver_license": "",
        "address": "",
        "notes": "",
        "blacklisted": False
    }

def expense_template_payload():
    return {
        "type": "expense",
        "date": "",
        "category": "fuel",  # fuel/maintenance/wash/fine/other
        "amount": 0,
        "payment_method": "cash",
        "notes": "",
        "linked_vehicle_card_id": ""
    }

def invoice_template_payload():
    return {
        "type": "invoice",
        "booking_card_id": "",
        "status": "OPEN",  # OPEN/PAID
        "total": 0,
        "paid_amount": 0,
        "payment_method": "cash",
        "notes": ""
    }

def main():
    # 0) Resolve board id (shortLink -> long id)
    board_id_long, board = resolve_board_id(BOARD_REF)
    print("✅ Board:", board.get("name"), "|", board.get("url"))
    print("✅ Board shortLink:", board.get("shortLink"), "| Board long id:", board_id_long)

    # ===== Lists names (compat Render) =====
    LIST_DEMANDES = os.getenv("LIST_NAME_FILTER", "📥 DEMANDES")
    LIST_RESERVED = os.getenv("RESERVED_LIST_NAME", "📅 RÉSERVÉES")
    LIST_DONE     = os.getenv("TRELLO_CLOSED_LIST_NAME", "✅ TERMINÉES")

    LIST_ONGOING  = "🔑 EN COURS"
    LIST_CANCEL   = "❌ ANNULÉES"
    LIST_VEHICLES = "🚗 VÉHICULES"
    LIST_CLIENTS  = "👤 CLIENTS"
    LIST_EXPENSES = "💸 DÉPENSES"

    LIST_INVOICES_OPEN = os.getenv("TRELLO_LIST_INVOICES_OPEN", "🧾 FACTURES - OUVERTES")
    LIST_INVOICES_PAID = os.getenv("TRELLO_LIST_INVOICES_PAID", "💰 FACTURES - PAYÉES")

    # ===== 1) Labels =====
    lb_demande  = ensure_label(board_id_long, "DEMANDE", "yellow")
    lb_reserve  = ensure_label(board_id_long, "RESERVE", "sky")
    lb_ongoing  = ensure_label(board_id_long, "EN_COURS", "orange")
    lb_done     = ensure_label(board_id_long, "TERMINE", "green")
    lb_cancel   = ensure_label(board_id_long, "ANNULE", "red")

    lb_cash     = ensure_label(board_id_long, "PAIEMENT_CASH", "lime")
    lb_transfer = ensure_label(board_id_long, "PAIEMENT_VIREMENT", "blue")
    lb_card     = ensure_label(board_id_long, "PAIEMENT_CARTE", "purple")

    # ===== 2) Lists =====
    lid_demandes = ensure_list(board_id_long, LIST_DEMANDES, "top")
    lid_reserved = ensure_list(board_id_long, LIST_RESERVED, "bottom")
    lid_ongoing  = ensure_list(board_id_long, LIST_ONGOING, "bottom")
    lid_done     = ensure_list(board_id_long, LIST_DONE, "bottom")
    lid_cancel   = ensure_list(board_id_long, LIST_CANCEL, "bottom")

    lid_vehicles = ensure_list(board_id_long, LIST_VEHICLES, "bottom")
    lid_clients  = ensure_list(board_id_long, LIST_CLIENTS, "bottom")

    lid_inv_open = ensure_list(board_id_long, LIST_INVOICES_OPEN, "bottom")
    lid_inv_paid = ensure_list(board_id_long, LIST_INVOICES_PAID, "bottom")
    lid_expenses = ensure_list(board_id_long, LIST_EXPENSES, "bottom")

    # ===== 3) Templates cards =====
    booking_desc = json.dumps(booking_template_payload(), ensure_ascii=False, indent=2)
    booking_card_id = create_card(
        lid_demandes,
        "🧩 TEMPLATE - Booking (NE PAS TOUCHER)",
        booking_desc,
        labels=[lb_demande]
    )
    add_checklist(booking_card_id, "État des lieux - Départ", [
        "Carburant noté",
        "KM noté",
        "Photos (avant)",
        "Rayures/impacts notés",
        "Papiers remis",
        "Dépôt encaissé",
    ])
    add_checklist(booking_card_id, "État des lieux - Retour", [
        "Carburant noté",
        "KM noté",
        "Photos (après)",
        "Dégâts notés",
        "Solde encaissé",
        "Clés récupérées",
    ])

    vehicle_desc = json.dumps(vehicle_template_payload(), ensure_ascii=False, indent=2)
    create_card(lid_vehicles, "🧩 TEMPLATE - Vehicle (NE PAS TOUCHER)", vehicle_desc)

    client_desc = json.dumps(client_template_payload(), ensure_ascii=False, indent=2)
    create_card(lid_clients, "🧩 TEMPLATE - Client (NE PAS TOUCHER)", client_desc)

    inv_desc = json.dumps(invoice_template_payload(), ensure_ascii=False, indent=2)
    create_card(lid_inv_open, "🧩 TEMPLATE - Invoice (NE PAS TOUCHER)", inv_desc)

    exp_desc = json.dumps(expense_template_payload(), ensure_ascii=False, indent=2)
    create_card(lid_expenses, "🧩 TEMPLATE - Expense (NE PAS TOUCHER)", exp_desc)

    # ===== 4) Examples =====
    sample_vehicle = vehicle_template_payload()
    sample_vehicle.update({"plate": "000-TEST-16", "brand": "Renault", "model": "Clio", "year": 2021, "km": 120000})
    create_card(lid_vehicles, "000-TEST-16 — Renault Clio", json.dumps(sample_vehicle, ensure_ascii=False, indent=2))

    sample_client = client_template_payload()
    sample_client.update({"full_name": "Client Test", "phone": "+213000000000"})
    create_card(lid_clients, "Client Test", json.dumps(sample_client, ensure_ascii=False, indent=2))

    print("\n✅ Trello bootstrap terminé.")
    print("📌 Lists créées/validées :")
    for n in [
        LIST_DEMANDES, LIST_RESERVED, LIST_ONGOING, LIST_DONE, LIST_CANCEL,
        LIST_VEHICLES, LIST_CLIENTS, LIST_INVOICES_OPEN, LIST_INVOICES_PAID, LIST_EXPENSES
    ]:
        print(" -", n)

if __name__ == "__main__":
    main()

