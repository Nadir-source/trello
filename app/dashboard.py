# app/dashboard.py
from flask import Blueprint, render_template, session
from app.auth import login_required
from app.trello_client import Trello
import app.config as C

dashboard_bp = Blueprint("dashboard", __name__)

def _safe_list_cards(t: Trello, list_name: str):
    """
    Evite de casser le dashboard si une liste n'existe pas.
    Retourne toujours une liste.
    """
    try:
        return t.list_cards(list_name) or []
    except Exception:
        return []

@dashboard_bp.route("/")
@login_required
def root():
    # redirige vers le dashboard
    return index()

@dashboard_bp.route("/dashboard")
@login_required
def index():
    role = session.get("role", "user")
    name = session.get("name", "Utilisateur")

    t = Trello()

    # Récupérer cartes par liste (safe)
    demandes = _safe_list_cards(t, C.LIST_DEMANDES)
    reserved = _safe_list_cards(t, C.LIST_RESERVED)
    ongoing  = _safe_list_cards(t, getattr(C, "LIST_ONGOING", "🔑 EN COURS"))
    done     = _safe_list_cards(t, getattr(C, "LIST_DONE", "✅ TERMINÉES"))
    cancel   = _safe_list_cards(t, getattr(C, "LIST_CANCEL", "❌ ANNULÉES"))

    # Si tu as des listes invoices dans config, on les calcule, sinon 0
    invoices_open = 0
    invoices_paid = 0
    if hasattr(C, "LIST_INVOICES_OPEN"):
        invoices_open = len(_safe_list_cards(t, C.LIST_INVOICES_OPEN))
    if hasattr(C, "LIST_INVOICES_PAID"):
        invoices_paid = len(_safe_list_cards(t, C.LIST_INVOICES_PAID))

    stats = {
        "demandes": len(demandes),
        "reserved": len(reserved),
        "ongoing": len(ongoing),
        "done": len(done),
        "cancel": len(cancel),
        "invoices_open": invoices_open,
        "invoices_paid": invoices_paid,
    }

    # board (optionnel) : ton template peut l'afficher
    board = getattr(t, "board", None)

    return render_template(
        "dashboard.html",
        role=role,
        name=name,
        stats=stats,
        board=board,
        demandes=demandes,
        reserved=reserved,
        ongoing=ongoing,
        done=done,
        cancel=cancel,
    )

