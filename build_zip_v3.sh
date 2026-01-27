#!/usr/bin/env bash
set -e

mkdir -p app/templates app/static

cat > requirements.txt << 'REQ'
Flask==3.0.3
python-dotenv==1.0.1
requests==2.32.5
reportlab==4.2.5
gunicorn==22.0.0
REQ

cat > app/config.py << 'CFG'
import os

def env(name: str, default=None):
    v = os.getenv(name)
    return v if v not in (None, "") else default

SECRET_KEY = env("SECRET_KEY", "change-me")
ADMIN_PASSWORD = env("ADMIN_PASSWORD", "admin")
AGENT_PASSWORD = env("AGENT_PASSWORD", "agent")

TRELLO_KEY = env("TRELLO_KEY")
TRELLO_TOKEN = env("TRELLO_TOKEN")
BOARD_REF = env("BOARD_ID") or env("TRELLO_BOARD_ID")

# Lists names (tu peux les overrider via env)
LIST_DEMANDES = env("LIST_NAME_FILTER", "📥 DEMANDES")
LIST_RESERVED = env("RESERVED_LIST_NAME", "📅 RÉSERVÉES")
LIST_DONE     = env("TRELLO_CLOSED_LIST_NAME", "✅ TERMINÉES")

LIST_ONGOING  = env("LIST_ONGOING", "🔑 EN COURS")
LIST_CANCEL   = env("LIST_CANCELLED", "❌ ANNULÉES")
LIST_VEHICLES = env("LIST_VEHICLES", "🚗 VÉHICULES")
LIST_CLIENTS  = env("LIST_CLIENTS", "👤 CLIENTS")

LIST_INVOICES_OPEN = env("TRELLO_LIST_INVOICES_OPEN", "🧾 FACTURES - OUVERTES")
LIST_INVOICES_PAID = env("TRELLO_LIST_INVOICES_PAID", "💰 FACTURES - PAYÉES")
LIST_EXPENSES      = env("LIST_EXPENSES", "💸 DÉPENSES")

# Infos contrat
LOUEUR_NOM = env("LOUEUR_NOM", "LOUEUR")
LOUEUR_TEL = env("LOUEUR_TEL", "")
LOUEUR_ADRESSE = env("LOUEUR_ADRESSE", "")
CFG

cat > app/trello_schema.py << 'SCHEMA'
import json
from datetime import datetime

def parse_payload(desc: str) -> dict:
    desc = (desc or "").strip()
    if not desc:
        return {}
    try:
        return json.loads(desc)
    except Exception:
        return {}

def dump_payload(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)

def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def audit_add(payload: dict, by: str, action: str, meta: dict | None = None):
    payload.setdefault("audit", [])
    payload["audit"].append({
        "at": now_iso(),
        "by": by,
        "action": action,
        "meta": meta or {}
    })
SCHEMA

cat > app/trello_client.py << 'TRELLO'
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
TRELLO

cat > app/auth.py << 'AUTH'
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.config import ADMIN_PASSWORD, AGENT_PASSWORD

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def current_user():
    return session.get("user_role"), session.get("user_name","")

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_role"):
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("user_role") != "admin":
            return redirect(url_for("dashboard.index"))
        return fn(*args, **kwargs)
    return wrapper

@auth_bp.get("/login")
def login():
    return render_template("login.html")

@auth_bp.post("/login")
def login_post():
    role = request.form.get("role", "agent")
    password = request.form.get("password", "")
    name = request.form.get("name","").strip() or ("Admin" if role=="admin" else "Agent")

    if role == "admin" and password == ADMIN_PASSWORD:
        session["user_role"] = "admin"
        session["user_name"] = name
        return redirect(url_for("dashboard.index"))
    if role == "agent" and password == AGENT_PASSWORD:
        session["user_role"] = "agent"
        session["user_name"] = name
        return redirect(url_for("dashboard.index"))

    flash("Login incorrect", "error")
    return redirect(url_for("auth.login"))

@auth_bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
AUTH

cat > app/pdf_generator.py << 'PDF'
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from app.config import LOUEUR_NOM, LOUEUR_TEL, LOUEUR_ADRESSE

def build_contract_pdf(booking: dict, client: dict, vehicle: dict) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w,h = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, h-60, "CONTRAT DE LOCATION (Simple)")

    c.setFont("Helvetica", 10)
    c.drawString(40, h-85, f"Loueur: {LOUEUR_NOM} | {LOUEUR_TEL}")
    c.drawString(40, h-100, f"Adresse: {LOUEUR_ADRESSE}")

    y = h-135
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Client")
    y -= 18
    c.setFont("Helvetica", 11)
    for k in ["full_name","phone","doc_id","driver_license","address"]:
        v = client.get(k,"")
        if v:
            c.drawString(40, y, f"{k}: {v}")
            y -= 16

    y -= 8
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Véhicule")
    y -= 18
    c.setFont("Helvetica", 11)
    for k in ["plate","brand","model","year","color","km","status"]:
        v = vehicle.get(k,"")
        if v != "":
            c.drawString(40, y, f"{k}: {v}")
            y -= 16

    y -= 8
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Location")
    y -= 18
    c.setFont("Helvetica", 11)
    for k in ["start_date","end_date","price_per_day","deposit","paid_amount","payment_method","pickup_place","return_place","notes"]:
        v = booking.get(k,"")
        if v != "":
            c.drawString(40, y, f"{k}: {v}")
            y -= 16

    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Conditions (résumé)")
    y -= 16
    c.setFont("Helvetica", 10)
    lines = [
        "- Le véhicule doit être rendu dans le même état.",
        "- Toute infraction/amende est à la charge du locataire.",
        "- En cas de dommages, la franchise/dépôt peut être retenu.",
        "- Paiement restant dû à la restitution si non réglé."
    ]
    for ln in lines:
        c.drawString(45, y, ln); y -= 14

    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, h-60, "Signature")
    c.setFont("Helvetica", 11)
    c.drawString(40, h-95, "Client: _______________________")
    c.drawString(40, h-125, "Loueur: _______________________")

    c.save()
    return buf.getvalue()

def build_month_report_pdf(title: str, lines: list[str]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w,h = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, h-60, title)
    y = h-100
    c.setFont("Helvetica", 11)
    for ln in lines:
        c.drawString(40, y, ln)
        y -= 16
        if y < 60:
            c.showPage()
            y = h-60
            c.setFont("Helvetica", 11)
    c.save()
    return buf.getvalue()
PDF

cat > app/dashboard.py << 'DASH'
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
DASH

cat > app/vehicles.py << 'VEH'
from flask import Blueprint, render_template, request, redirect, url_for
from app.auth import login_required, admin_required, current_user
from app.trello_client import Trello
from app.trello_schema import parse_payload, dump_payload, audit_add

vehicles_bp = Blueprint("vehicles", __name__, url_prefix="/vehicles")

@vehicles_bp.get("")
@login_required
def index():
    t = Trello()
    cards = t.list_cards(__import__("app.config").config.LIST_VEHICLES)
    vehicles = []
    for c in cards:
        p = parse_payload(c.get("desc",""))
        vehicles.append({"id": c["id"], "title": c["name"], **p})
    return render_template("vehicles.html", vehicles=vehicles)

@vehicles_bp.post("/create")
@login_required
@admin_required
def create():
    t = Trello()
    plate = request.form.get("plate","").strip()
    brand = request.form.get("brand","").strip()
    model = request.form.get("model","").strip()
    year = request.form.get("year","").strip()
    color = request.form.get("color","").strip()
    km = request.form.get("km","0").strip()

    payload = {
        "type": "vehicle",
        "plate": plate,
        "brand": brand,
        "model": model,
        "year": int(year) if year.isdigit() else None,
        "color": color,
        "km": int(km) if km.isdigit() else 0,
        "status": "AVAILABLE",
        "insurance_expiry": "",
        "technical_control_expiry": "",
        "notes": ""
    }
    role, name = current_user()
    audit_add(payload, name, "vehicle_create", {"plate": plate})
    title = f"{plate} — {brand} {model}".strip()
    t.create_card(__import__("app.config").config.LIST_VEHICLES, title, dump_payload(payload))
    return redirect(url_for("vehicles.index"))
VEH

cat > app/clients.py << 'CLI'
from flask import Blueprint, render_template, request, redirect, url_for
from app.auth import login_required, admin_required, current_user
from app.trello_client import Trello
from app.trello_schema import parse_payload, dump_payload, audit_add

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")

@clients_bp.get("")
@login_required
def index():
    t = Trello()
    cards = t.list_cards(__import__("app.config").config.LIST_CLIENTS)
    clients = []
    for c in cards:
        p = parse_payload(c.get("desc",""))
        clients.append({"id": c["id"], "title": c["name"], **p})
    return render_template("clients.html", clients=clients)

@clients_bp.post("/create")
@login_required
def create():
    # Agent peut créer un client (utile)
    t = Trello()
    full_name = request.form.get("full_name","").strip()
    phone = request.form.get("phone","").strip()
    doc_id = request.form.get("doc_id","").strip()
    driver_license = request.form.get("driver_license","").strip()
    address = request.form.get("address","").strip()

    payload = {
        "type": "client",
        "full_name": full_name,
        "phone": phone,
        "doc_id": doc_id,
        "driver_license": driver_license,
        "address": address,
        "notes": "",
        "blacklisted": False
    }
    role, name = current_user()
    audit_add(payload, name, "client_create", {"full_name": full_name})
    t.create_card(__import__("app.config").config.LIST_CLIENTS, full_name, dump_payload(payload))
    return redirect(url_for("clients.index"))
CLI

cat > app/finance.py << 'FIN'
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
FIN

cat > app/bookings.py << 'BOOK'
from flask import Blueprint, render_template, request, redirect, url_for, send_file
import io
from app.auth import login_required, current_user, admin_required
from app.trello_client import Trello
from app.trello_schema import parse_payload, dump_payload, audit_add
from app.pdf_generator import build_contract_pdf
from app import config as C

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")

def _select_options(cards):
    opts=[]
    for c in cards:
        p=parse_payload(c.get("desc",""))
        opts.append({"id": c["id"], "name": c["name"], "p": p})
    return opts

@bookings_bp.get("")
@login_required
def index():
    t = Trello()
    demandes = t.list_cards(C.LIST_DEMANDES)
    reserved = t.list_cards(C.LIST_RESERVED)
    ongoing  = t.list_cards(C.LIST_ONGOING)
    done     = t.list_cards(C.LIST_DONE)

    vehicles = _select_options(t.list_cards(C.LIST_VEHICLES))
    clients  = _select_options(t.list_cards(C.LIST_CLIENTS))
    return render_template("bookings.html",
                           demandes=demandes, reserved=reserved, ongoing=ongoing, done=done,
                           vehicles=vehicles, clients=clients)

@bookings_bp.post("/create")
@login_required
def create():
    t = Trello()
    role, name = current_user()

    vehicle_card_id = request.form.get("vehicle_card_id","").strip()
    client_card_id  = request.form.get("client_card_id","").strip()

    payload = {
        "type": "booking",
        "booking_status": "DEMANDE",
        "vehicle_card_id": vehicle_card_id,
        "client_card_id": client_card_id,
        "start_date": request.form.get("start_date","").strip(),
        "end_date": request.form.get("end_date","").strip(),
        "price_per_day": float(request.form.get("price_per_day","0") or 0),
        "deposit": float(request.form.get("deposit","0") or 0),
        "paid_amount": float(request.form.get("paid_amount","0") or 0),
        "payment_method": request.form.get("payment_method","cash").strip(),
        "pickup_place": request.form.get("pickup_place","").strip(),
        "return_place": request.form.get("return_place","").strip(),
        "notes": request.form.get("notes","").strip(),
        "extras": {
            "driver": bool(request.form.get("extra_driver")),
            "gps": bool(request.form.get("extra_gps")),
            "child_seat": bool(request.form.get("extra_child_seat")),
        },
        "km_out": None,
        "fuel_out": "",
        "km_in": None,
        "fuel_in": "",
        "damage_notes": "",
        "created_by": name,
        "audit": []
    }
    audit_add(payload, name, "booking_create", {"status": "DEMANDE"})
    title = request.form.get("title","").strip() or "Réservation"
    t.create_card(C.LIST_DEMANDES, title, dump_payload(payload))
    return redirect(url_for("bookings.index"))

@bookings_bp.post("/move/<card_id>/<target>")
@login_required
def move(card_id, target):
    t = Trello()
    role, name = current_user()

    # map target -> list
    if target == "reserved":
        list_name = C.LIST_RESERVED
        new_status = "RESERVED"
    elif target == "ongoing":
        list_name = C.LIST_ONGOING
        new_status = "ONGOING"
    elif target == "done":
        list_name = C.LIST_DONE
        new_status = "DONE"
    elif target == "cancel":
        list_name = C.LIST_CANCEL
        new_status = "CANCELLED"
    else:
        return redirect(url_for("bookings.index"))

    card = t.get_card(card_id)
    payload = parse_payload(card.get("desc",""))
    payload["booking_status"] = new_status
    audit_add(payload, name, "booking_move", {"to": new_status})
    t.update_card(card_id, desc=dump_payload(payload))
    t.move_card(card_id, list_name)
    return redirect(url_for("bookings.index"))

@bookings_bp.get("/contract.pdf/<card_id>")
@login_required
def contract_pdf(card_id):
    t = Trello()
    card = t.get_card(card_id)
    booking = parse_payload(card.get("desc",""))

    client = {}
    vehicle = {}
    if booking.get("client_card_id"):
        c = t.get_card(booking["client_card_id"])
        client = parse_payload(c.get("desc",""))
        client.setdefault("full_name", c.get("name",""))
    if booking.get("vehicle_card_id"):
        v = t.get_card(booking["vehicle_card_id"])
        vehicle = parse_payload(v.get("desc",""))
        vehicle.setdefault("plate", v.get("name",""))

    pdf_bytes = build_contract_pdf(booking, client, vehicle)
    return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf", as_attachment=True, download_name="contrat_location.pdf")

@bookings_bp.post("/invoice/mark_paid/<booking_card_id>")
@login_required
@admin_required
def mark_invoice_paid(booking_card_id):
    # simple: crée une invoice OPEN puis la move PAID si payé_amount>=total
    t = Trello()
    role, name = current_user()

    booking_card = t.get_card(booking_card_id)
    booking = parse_payload(booking_card.get("desc",""))
    total = 0.0

    # estimation total = days*ppd (si tu veux améliorer après)
    # ici on laisse l'admin saisir le total via form
    total = float(request.form.get("total","0") or 0)
    paid_amount = float(request.form.get("paid_amount","0") or 0)
    status = "PAID" if paid_amount >= total and total > 0 else "OPEN"

    invoice_payload = {
        "type": "invoice",
        "booking_card_id": booking_card_id,
        "status": status,
        "total": total,
        "paid_amount": paid_amount,
        "payment_method": request.form.get("payment_method","cash"),
        "notes": request.form.get("notes","")
    }
    audit_add(invoice_payload, name, "invoice_create", {"status": status, "total": total, "paid": paid_amount})

    title = f"Invoice — {booking_card.get('name','booking')} — {status}"
    inv_card = t.create_card(C.LIST_INVOICES_OPEN, title, dump_payload(invoice_payload))

    if status == "PAID":
        t.move_card(inv_card["id"], C.LIST_INVOICES_PAID)

    # also update booking paid amount
    booking["paid_amount"] = paid_amount
    audit_add(booking, name, "booking_paid_update", {"paid_amount": paid_amount, "total": total})
    t.update_card(booking_card_id, desc=dump_payload(booking))
    return redirect(url_for("finance.index"))
BOOK

cat > app/__init__.py << 'INIT'
# empty init
INIT

cat > app/app.py << 'APP'
from flask import Flask, redirect, url_for
from dotenv import load_dotenv
from app.config import SECRET_KEY

from app.auth import auth_bp
from app.dashboard import dashboard_bp
from app.vehicles import vehicles_bp
from app.clients import clients_bp
from app.bookings import bookings_bp
from app.finance import finance_bp

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(finance_bp)

    @app.get("/")
    def home():
        return redirect(url_for("dashboard.index"))

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
APP

cat > gunicorn.conf.py << 'GUNI'
bind = "0.0.0.0:8000"
workers = 2
timeout = 120
GUNI

cat > templates_not_used.txt << 'NOTE'
Templates are inside app/templates
NOTE

# ===== Templates =====
cat > app/templates/layout.html << 'LAY'
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8"/>
  <title>Car Rental (Trello)</title>
  <style>
    body{font-family:Arial;margin:18px;background:#fafafa}
    .top{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
    .top a{padding:6px 10px;background:#fff;border:1px solid #ddd;border-radius:10px;text-decoration:none;color:#111}
    .box{background:#fff;border:1px solid #ddd;border-radius:14px;padding:12px;margin:10px 0}
    .grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
    .grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
    input,select,textarea{width:100%;padding:8px;border:1px solid #ddd;border-radius:10px;margin:4px 0}
    button{padding:8px 12px;border-radius:10px;border:1px solid #111;background:#111;color:#fff;cursor:pointer}
    .muted{color:#666;font-size:12px}
    .card{border:1px solid #eee;border-radius:12px;padding:10px;margin:8px 0;background:#fff}
    .row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
    .row button{background:#222}
    .badge{display:inline-block;padding:3px 8px;border:1px solid #ddd;border-radius:999px;font-size:12px;background:#f7f7f7}
  </style>
</head>
<body>
  <div class="top">
    <a href="/dashboard">Dashboard</a>
    <a href="/bookings">Réservations</a>
    <a href="/clients">Clients</a>
    <a href="/vehicles">Véhicules</a>
    <a href="/finance">Finance (Admin)</a>
    <a href="/auth/logout">Logout</a>
  </div>
  <hr>
  {% block content %}{% endblock %}
</body>
</html>
LAY

cat > app/templates/login.html << 'LOG'
<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><title>Login</title></head>
<body style="font-family:Arial;margin:30px">
  <h2>Connexion</h2>
  <form method="post" action="/auth/login">
    <label>Role</label>
    <select name="role">
      <option value="agent">Agent</option>
      <option value="admin">Admin</option>
    </select>
    <label>Nom (pour l'audit)</label>
    <input name="name" placeholder="Ex: Nadir / Mohamed">
    <label>Mot de passe</label>
    <input type="password" name="password" placeholder="AGENT_PASSWORD ou ADMIN_PASSWORD">
    <button type="submit">Login</button>
  </form>
  <p style="color:#666">Astuce: mets AGENT_PASSWORD pour ton ami, ADMIN_PASSWORD pour toi.</p>
</body>
</html>
LOG

cat > app/templates/dashboard.html << 'DB'
{% extends "layout.html" %}
{% block content %}
<div class="box">
  <div class="row">
    <h2 style="margin:0">Dashboard</h2>
    <span class="badge">Connecté: {{name}} ({{role}})</span>
  </div>
  <div class="muted">Board: {{board.name}} — {{board.url}}</div>
</div>

<div class="grid3">
  <div class="box"><b>Demandes</b><div style="font-size:26px">{{stats.demandes}}</div></div>
  <div class="box"><b>Réservées</b><div style="font-size:26px">{{stats.reserved}}</div></div>
  <div class="box"><b>En cours</b><div style="font-size:26px">{{stats.ongoing}}</div></div>
  <div class="box"><b>Terminées</b><div style="font-size:26px">{{stats.done}}</div></div>
  <div class="box"><b>Véhicules</b><div style="font-size:26px">{{stats.vehicles}}</div></div>
  <div class="box"><b>Clients</b><div style="font-size:26px">{{stats.clients}}</div></div>
</div>

<div class="box">
  <b>Finance</b>
  <div class="muted">Ouvertes: {{stats.inv_open}} | Payées: {{stats.inv_paid}} | Dépenses: {{stats.expenses}}</div>
</div>
{% endblock %}
DB

cat > app/templates/vehicles.html << 'VE'
{% extends "layout.html" %}
{% block content %}
<h2>Véhicules</h2>
<div class="box">
  <div class="muted">Création réservée à Admin (toi).</div>
  <form method="post" action="/vehicles/create">
    <div class="grid">
      <div><input name="plate" placeholder="Immat"></div>
      <div><input name="brand" placeholder="Marque"></div>
      <div><input name="model" placeholder="Modèle"></div>
      <div><input name="year" placeholder="Année"></div>
      <div><input name="color" placeholder="Couleur"></div>
      <div><input name="km" placeholder="KM"></div>
    </div>
    <button>Ajouter véhicule</button>
  </form>
</div>

<div class="box">
  {% for v in vehicles %}
    <div class="card">
      <b>{{v.title}}</b>
      <div class="muted">status: {{v.status}} | km: {{v.km}}</div>
    </div>
  {% endfor %}
</div>
{% endblock %}
VE

cat > app/templates/clients.html << 'CL'
{% extends "layout.html" %}
{% block content %}
<h2>Clients</h2>
<div class="box">
  <form method="post" action="/clients/create">
    <div class="grid">
      <div><input name="full_name" placeholder="Nom complet"></div>
      <div><input name="phone" placeholder="Téléphone"></div>
      <div><input name="doc_id" placeholder="CNI/Passeport"></div>
      <div><input name="driver_license" placeholder="Permis"></div>
    </div>
    <textarea name="address" placeholder="Adresse"></textarea>
    <button>Ajouter client</button>
  </form>
</div>

<div class="box">
  {% for c in clients %}
    <div class="card">
      <b>{{c.title}}</b>
      <div class="muted">{{c.phone}} | {{c.doc_id}}</div>
    </div>
  {% endfor %}
</div>
{% endblock %}
CL

cat > app/templates/bookings.html << 'BK'
{% extends "layout.html" %}
{% block content %}
<h2>Réservations</h2>

<div class="box">
  <h3>Créer une demande</h3>
  <form method="post" action="/bookings/create">
    <input name="title" placeholder="Titre (ex: Location Clio 10-12)" />
    <div class="grid">
      <div>
        <label>Client</label>
        <select name="client_card_id">
          <option value="">-- choisir --</option>
          {% for c in clients %}
            <option value="{{c.id}}">{{c.name}}</option>
          {% endfor %}
        </select>
      </div>
      <div>
        <label>Véhicule</label>
        <select name="vehicle_card_id">
          <option value="">-- choisir --</option>
          {% for v in vehicles %}
            <option value="{{v.id}}">{{v.name}}</option>
          {% endfor %}
        </select>
      </div>
      <div><input name="start_date" placeholder="Début (YYYY-MM-DD)"></div>
      <div><input name="end_date" placeholder="Fin (YYYY-MM-DD)"></div>
      <div><input name="price_per_day" placeholder="Prix/jour"></div>
      <div><input name="deposit" placeholder="Dépôt"></div>
      <div><input name="paid_amount" placeholder="Déjà payé"></div>
      <div>
        <label>Méthode</label>
        <select name="payment_method">
          <option value="cash">Cash</option>
          <option value="transfer">Virement</option>
          <option value="card">Carte</option>
        </select>
      </div>
    </div>

    <div class="grid">
      <div><input name="pickup_place" placeholder="Lieu remise"></div>
      <div><input name="return_place" placeholder="Lieu retour"></div>
    </div>

    <div class="row">
      <label><input type="checkbox" name="extra_driver"> Chauffeur</label>
      <label><input type="checkbox" name="extra_gps"> GPS</label>
      <label><input type="checkbox" name="extra_child_seat"> Siège bébé</label>
    </div>

    <textarea name="notes" placeholder="Notes"></textarea>
    <button>Créer demande</button>
  </form>
</div>

<div class="grid3">
  <div class="box">
    <h3>📥 Demandes</h3>
    {% for c in demandes %}
      <div class="card">
        <b>{{c.name}}</b>
        <div class="row">
          <form method="post" action="/bookings/move/{{c.id}}/reserved"><button>➡️ Réserver</button></form>
          <form method="post" action="/bookings/move/{{c.id}}/cancel"><button>❌ Annuler</button></form>
        </div>
      </div>
    {% endfor %}
  </div>

  <div class="box">
    <h3>📅 Réservées</h3>
    {% for c in reserved %}
      <div class="card">
        <b>{{c.name}}</b>
        <div class="row">
          <a href="/bookings/contract.pdf/{{c.id}}">📄 Contrat PDF</a>
        </div>
        <div class="row">
          <form method="post" action="/bookings/move/{{c.id}}/ongoing"><button>🔑 Remise</button></form>
          <form method="post" action="/bookings/move/{{c.id}}/cancel"><button>❌ Annuler</button></form>
        </div>
      </div>
    {% endfor %}
  </div>

  <div class="box">
    <h3>🔑 En cours</h3>
    {% for c in ongoing %}
      <div class="card">
        <b>{{c.name}}</b>
        <div class="row">
          <a href="/bookings/contract.pdf/{{c.id}}">📄 Contrat PDF</a>
        </div>
        <div class="row">
          <form method="post" action="/bookings/move/{{c.id}}/done"><button>✅ Retour</button></form>
          <form method="post" action="/bookings/move/{{c.id}}/cancel"><button>❌ Annuler</button></form>
        </div>
      </div>
    {% endfor %}
  </div>
</div>

<div class="box">
  <h3>✅ Terminées</h3>
  {% for c in done %}
    <div class="card">
      <b>{{c.name}}</b> — <a href="/bookings/contract.pdf/{{c.id}}">📄 PDF</a>
    </div>
  {% endfor %}
</div>

{% endblock %}
BK

cat > app/templates/finance.html << 'FI'
{% extends "layout.html" %}
{% block content %}
<h2>Finance (Admin)</h2>

<div class="box">
  <b>Totaux</b>
  <div class="muted">Payé: {{totals.paid}} | Ouvert: {{totals.open}} | Dépenses: {{totals.expenses}} | Profit estimé: {{totals.profit_est}}</div>
  <div class="row">
    <a href="/finance/month_report.pdf">📄 Rapport Fin de Mois PDF</a>
  </div>
</div>

<div class="box">
  <h3>Créer dépense</h3>
  <form method="post" action="/finance/expense/create">
    <div class="grid">
      <div><input name="date" placeholder="Date (YYYY-MM-DD)"></div>
      <div>
        <select name="category">
          <option value="fuel">Carburant</option>
          <option value="maintenance">Maintenance</option>
          <option value="wash">Lavage</option>
          <option value="fine">Amende</option>
          <option value="other">Autre</option>
        </select>
      </div>
      <div><input name="amount" placeholder="Montant"></div>
    </div>
    <textarea name="notes" placeholder="Notes"></textarea>
    <button>Ajouter dépense</button>
  </form>
</div>

<div class="grid">
  <div class="box">
    <h3>Factures ouvertes</h3>
    {% for c in inv_open %}
      <div class="card"><b>{{c.name}}</b></div>
    {% endfor %}
  </div>
  <div class="box">
    <h3>Factures payées</h3>
    {% for c in inv_paid %}
      <div class="card"><b>{{c.name}}</b></div>
    {% endfor %}
  </div>
</div>

<div class="box">
  <h3>Dépenses</h3>
  {% for c in expenses %}
    <div class="card"><b>{{c.name}}</b></div>
  {% endfor %}
</div>

<div class="box">
  <h3>Créer une facture (depuis une réservation)</h3>
  <div class="muted">Depuis l’admin, tu peux “marquer payé” une réservation en créant une invoice.</div>
  <div class="muted">Pour le moment, utilise l’URL: /bookings puis bouton contrat + workflow, ensuite tu peux créer l’invoice via l’endpoint.</div>
  <div class="muted">(Je peux ajouter un écran dédié invoice par réservation si tu veux.)</div>
</div>
{% endblock %}
FI

# ===== Entrypoint =====
cat > run.sh << 'RUN'
#!/usr/bin/env bash
set -e
export PYTHONPATH=.
gunicorn -c gunicorn.conf.py app.app:app
RUN
chmod +x run.sh

zip -r trello-car-rental-v3.zip . >/dev/null
echo "✅ ZIP créé: trello-car-rental-v3.zip"
