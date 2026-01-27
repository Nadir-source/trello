from flask import Blueprint, render_template, request, redirect, url_for, send_file
import io
from datetime import datetime
from app.auth import login_required, admin_required, current_user
from app.trello_client import Trello
from app.trello_schema import parse_payload, dump_payload, audit_add
from app.pdf_generator import build_month_report_pdf
from app import config as C

finance_bp = Blueprint("finance", __name__, url_prefix="/finance")

def _month_key(dt: datetime):
    return dt.strftime("%Y-%m")

@finance_bp.get("")
@login_required
@admin_required
def index():
    t = Trello()
    inv_open = t.list_cards(C.LIST_INVOICES_OPEN)
    inv_paid = t.list_cards(C.LIST_INVOICES_PAID)
    expenses = t.list_cards(C.LIST_EXPENSES)

    def sum_amount(cards, field):
        total = 0
        for c in cards:
            p = parse_payload(c.get("desc",""))
            v = p.get(field, 0) or 0
            try:
                total += float(v)
            except Exception:
                pass
        return total

    totals = {
        "paid": sum_amount(inv_paid, "paid_amount") or sum_amount(inv_paid, "total"),
        "open": sum_amount(inv_open, "total"),
        "expenses": sum_amount(expenses, "amount")
    }
    totals["profit_est"] = totals["paid"] - totals["expenses"]
    return render_template("finance.html", inv_open=inv_open, inv_paid=inv_paid, expenses=expenses, totals=totals)

@finance_bp.post("/expense/create")
@login_required
@admin_required
def create_expense():
    t = Trello()
    date = request.form.get("date","").strip()
    category = request.form.get("category","fuel").strip()
    amount = request.form.get("amount","0").strip()
    notes = request.form.get("notes","").strip()

    payload = {"type":"expense","date":date,"category":category,"amount":float(amount or 0),"payment_method":"cash","notes":notes,"linked_vehicle_card_id":""}
    role, name = current_user()
    audit_add(payload, name, "expense_create", {"amount": amount, "category": category})
    title = f"{date} — {category} — {amount}"
    t.create_card(C.LIST_EXPENSES, title, dump_payload(payload))
    return redirect(url_for("finance.index"))

@finance_bp.get("/month_report.pdf")
@login_required
@admin_required
def month_report_pdf():
    t = Trello()
    inv_open = t.list_cards(C.LIST_INVOICES_OPEN)
    inv_paid = t.list_cards(C.LIST_INVOICES_PAID)
    expenses = t.list_cards(C.LIST_EXPENSES)

    paid = 0.0
    open_total = 0.0
    exp_total = 0.0

    def _sum(cards, key, fallback=None):
        s = 0.0
        for c in cards:
            p = parse_payload(c.get("desc",""))
            v = p.get(key, None)
            if v is None and fallback:
                v = p.get(fallback, 0)
            try:
                s += float(v or 0)
            except Exception:
                pass
        return s

    paid = _sum(inv_paid, "paid_amount", "total")
    open_total = _sum(inv_open, "total")
    exp_total = _sum(expenses, "amount")
    profit = paid - exp_total

    now = datetime.now()
    title = f"Rapport Fin de Mois — {_month_key(now)}"
    lines = [
        f"Encaissements (payés): {paid:.2f}",
        f"A encaisser (ouverts): {open_total:.2f}",
        f"Dépenses: {exp_total:.2f}",
        f"Bénéfice estimé: {profit:.2f}",
        "",
        "Notes:",
        "- Ce rapport est basé sur les cartes Trello (Factures Payées/Ouvertes + Dépenses)."
    ]

    pdf_bytes = build_month_report_pdf(title, lines)
    return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf", as_attachment=True, download_name="rapport_fin_de_mois.pdf")
