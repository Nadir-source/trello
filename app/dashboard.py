from flask import Blueprint, render_template, session
import app.config as C
from app.auth import login_required
from app.trello_client import Trello

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.get("")
@dashboard_bp.get("/")
@login_required
def index():
    t = Trello()

    demandes = t.list_cards(C.LIST_DEMANDES)
    reserved = t.list_cards(C.LIST_RESERVED)
    ongoing = t.list_cards(C.LIST_ONGOING)
    done = t.list_cards(C.LIST_DONE)

    clients = t.list_cards(C.LIST_CLIENTS)
    vehicles = t.list_cards(C.LIST_VEHICLES)

    stats = {
        "demandes": len(demandes),
        "reserved": len(reserved),
        "ongoing": len(ongoing),
        "done": len(done),
        "clients": len(clients),
        "vehicles": len(vehicles),
    }

    role = session.get("role", "admin")
    name = session.get("name", "Admin")

    return render_template(
        "dashboard.html",
        title="Dashboard",
        role=role,
        name=name,
        stats=stats,
        board=t.board,
        demandes=demandes,
        reserved=reserved,
        ongoing=ongoing,
        done=done,
        clients=clients,
        vehicles=vehicles,
    )

