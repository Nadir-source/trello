from flask import Blueprint, render_template
from app.auth import login_required
from app.trello_client import Trello
from app.trello_schema import parse_payload
from app import config as C

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

def sum_amount(cards, field, fallback=None):
    total = 0
    for c in cards:
        p = parse_payload(c.get("desc", ""))
        v = p.get(field, None)
        if v is None and fallback:
            v = p.get(fallback, 0)
        try:
            total += float(v or 0)
        except Exception:
            continue
    return total

@dashboard_bp.route("/")
@login_required
def dashboard():
    t = Trello()

    demandes = t.list_cards(C.LIST_DEMANDES)
    reserved = t.list_cards(C.LIST_RESERVED)
    ongoing = t.list_cards(C.LIST_ONGOING)
    done = t.list_cards(C.LIST_DONE)
    canceled = t.list_cards(C.LIST_CANCELED)
    clients = t.list_cards(C.LIST_CLIENTS)
    vehicles = t.list_cards(C.LIST_VEHICLES)
    inv_paid = t.list_cards(C.LIST_INVOICES_PAID)
    inv_open = t.list_cards(C.LIST_INVOICES_OPEN)
    expenses = t.list_cards(C.LIST_EXPENSES)

    paid = sum_amount(inv_paid, "paid_amount", fallback="total")
    open_total = sum_amount(inv_open, "total")
    expense_total = sum_amount(expenses, "amount")
    profit = paid - expense_total

    stats = {
        "demandes": len(demandes),
        "reserved": len(reserved),
        "ongoing": len(ongoing),
        "done": len(done),
        "canceled": len(canceled),
        "clients": len(clients),
        "vehicles": len(vehicles),
        "invoices_paid": len(inv_paid),
        "invoices_open": len(inv_open),
        "revenue_paid": paid,
        "revenue_open": open_total,
        "expenses": expense_total,
        "estimated_profit": profit,
    }

    return render_template(
        "dashboard.html",
        stats=stats,
        demandes=[{"id": d["id"], "name": d["name"]} for d in demandes],
        reserved_cards=[{"id": r["id"], "name": r["name"]} for r in reserved],
        ongoing_cards=[{"id": o["id"], "name": o["name"]} for o in ongoing],
    )

