# app/dashboard.py
from flask import Blueprint, render_template, session
from app.auth import login_required
from app.trello_client import Trello
import app.config as C

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.get("/dashboard")
@login_required
def index():
    role = session.get("role", "user")
    name = session.get("name", "user")

    t = Trello()

    # KPIs simples
    demandes = t.list_cards(C.LIST_DEMANDES)
    reserved = t.list_cards(C.LIST_RESERVED)
    ongoing = t.list_cards(C.LIST_ONGOING)
    done = t.list_cards(C.LIST_DONE)

    clients = t.list_cards(C.LIST_CLIENTS)
    vehicles = t.list_cards(C.LIST_VEHICLES)

    # Finance (si tu as ces listes)
    invoices_open = []
    invoices_paid = []
    expenses = []
    try:
        invoices_open = t.list_cards(C.LIST_INVOICES_OPEN)
        invoices_paid = t.list_cards(C.LIST_INVOICES_PAID)
        expenses = t.list_cards(C.LIST_EXPENSES)
    except Exception:
        pass

    stats = {
        "demandes": len(demandes),
        "reserved": len(reserved),
        "ongoing": len(ongoing),
        "done": len(done),
        "clients": len(clients),
        "vehicles": len(vehicles),
        "invoices_open": len(invoices_open),
        "invoices_paid": len(invoices_paid),
        "expenses": len(expenses),
    }

    # IMPORTANT : on passe tout au template
    return render_template(
        "dashboard.html",
        title="Dashboard",
        role=role,
        name=name,
        stats=stats,
        board=getattr(t, "board", None),
        demandes=demandes[:5],
        reserved_cards=reserved[:5],
        ongoing_cards=ongoing[:5],
        done_cards=done[:5],
    )

