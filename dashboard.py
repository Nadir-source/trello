from flask import Blueprint, render_template
from admin_auth import admin_required
from trello_client import list_cards
from config import LIST_DEMANDES, LIST_RESERVED, LIST_CLOSED, LIST_INVOICES_OPEN, LIST_INVOICES_PAID

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@dashboard_bp.get("")
@admin_required
def index():
    stats = {
        "demandes": len(list_cards(LIST_DEMANDES)),
        "reserved": len(list_cards(LIST_RESERVED)),
        "closed": len(list_cards(LIST_CLOSED)),
        "invoices_open": len(list_cards(LIST_INVOICES_OPEN)),
        "invoices_paid": len(list_cards(LIST_INVOICES_PAID)),
    }
    return render_template("dashboard.html", stats=stats)
