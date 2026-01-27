from flask import Blueprint, render_template
from app.auth import login_required, current_user
from app.trello_client import Trello
from app import config as C

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@dashboard_bp.get("")
@login_required
def index():
    t = Trello()
    role, name = current_user()
    stats = {
        "demandes": len(t.list_cards(C.LIST_DEMANDES)),
        "reserved": len(t.list_cards(C.LIST_RESERVED)),
        "ongoing": len(t.list_cards(C.LIST_ONGOING)),
        "done": len(t.list_cards(C.LIST_DONE)),
        "cancel": len(t.list_cards(C.LIST_CANCEL)),
        "vehicles": len(t.list_cards(C.LIST_VEHICLES)),
        "clients": len(t.list_cards(C.LIST_CLIENTS)),
        "inv_open": len(t.list_cards(C.LIST_INVOICES_OPEN)),
        "inv_paid": len(t.list_cards(C.LIST_INVOICES_PAID)),
        "expenses": len(t.list_cards(C.LIST_EXPENSES)),
    }
    return render_template("dashboard.html", role=role, name=name, stats=stats, board=t.board)
