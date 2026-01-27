#!/usr/bin/env bash
set -e
mkdir -p templates static

cat > requirements.txt << 'REQ'
Flask==3.0.3
python-dotenv==1.0.1
requests==2.32.3
reportlab==4.2.5
REQ

cat > config.py << 'CFG'
import os

def env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    return v if v not in (None, "") else default

SECRET_KEY = env("SECRET_KEY", "change-me")
ADMIN_PASSWORD = env("ADMIN_PASSWORD", "admin")
CLIENT_PASSWORD = env("CLIENT_PASSWORD", None)

# Trello
TRELLO_KEY = env("TRELLO_KEY")
TRELLO_TOKEN = env("TRELLO_TOKEN")
BOARD_ID = env("BOARD_ID") or env("TRELLO_BOARD_ID")  # compat si jamais

# Lists (tes noms)
LIST_DEMANDES = env("LIST_NAME_FILTER", "📥 Demandes")
LIST_RESERVED = env("RESERVED_LIST_NAME", "📅 Réservations")
LIST_CLOSED = env("TRELLO_CLOSED_LIST_NAME", "✅ Terminées")

LIST_INVOICES_OPEN = env("TRELLO_LIST_INVOICES_OPEN", "🧾 Invoices - Open")
LIST_INVOICES_PAID = env("TRELLO_LIST_INVOICES_PAID", "🧾 Invoices - Paid")

# Infos loueur (contrat)
LOUEUR_NOM = env("LOUEUR_NOM", "LOUEUR")
LOUEUR_TEL = env("LOUEUR_TEL", "")
LOUEUR_ADRESSE = env("LOUEUR_ADRESSE", "")
CFG

cat > trello_client.py << 'TRELLO'
import requests
from config import TRELLO_KEY, TRELLO_TOKEN, BOARD_ID

API = "https://api.trello.com/1"

def _check():
    if not (TRELLO_KEY and TRELLO_TOKEN and BOARD_ID):
        raise RuntimeError("Missing Trello config: TRELLO_KEY / TRELLO_TOKEN / BOARD_ID")

def _params(extra=None):
    p = {"key": TRELLO_KEY, "token": TRELLO_TOKEN}
    if extra:
        p.update(extra)
    return p

def board_lists():
    _check()
    r = requests.get(f"{API}/boards/{BOARD_ID}/lists", params=_params({"fields": "name"}), timeout=30)
    r.raise_for_status()
    return r.json()

def list_id_by_name(name: str) -> str:
    for lst in board_lists():
        if (lst.get("name") or "").strip() == name.strip():
            return lst["id"]
    raise RuntimeError(f"List not found on board: {name}")

def list_cards(list_name: str):
    lid = list_id_by_name(list_name)
    r = requests.get(f"{API}/lists/{lid}/cards",
                     params=_params({"fields": "name,desc,idList,closed,dateLastActivity"}),
                     timeout=30)
    r.raise_for_status()
    return r.json()

def get_card(card_id: str):
    r = requests.get(f"{API}/cards/{card_id}",
                     params=_params({"fields": "name,desc,idList,closed,dateLastActivity"}),
                     timeout=30)
    r.raise_for_status()
    return r.json()

def create_card(list_name: str, name: str, desc: str = ""):
    lid = list_id_by_name(list_name)
    r = requests.post(f"{API}/cards", params=_params({"idList": lid, "name": name, "desc": desc}), timeout=30)
    r.raise_for_status()
    return r.json()

def update_card(card_id: str, name: str = None, desc: str = None):
    data = {}
    if name is not None: data["name"] = name
    if desc is not None: data["desc"] = desc
    r = requests.put(f"{API}/cards/{card_id}", params=_params(data), timeout=30)
    r.raise_for_status()
    return r.json()

def move_card(card_id: str, target_list_name: str):
    lid = list_id_by_name(target_list_name)
    r = requests.put(f"{API}/cards/{card_id}", params=_params({"idList": lid}), timeout=30)
    r.raise_for_status()
    return r.json()
TRELLO

cat > trello_schema.py << 'SCHEMA'
import json

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
SCHEMA

cat > admin_auth.py << 'AUTH'
from functools import wraps
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from config import ADMIN_PASSWORD

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin.login"))
        return fn(*args, **kwargs)
    return wrapper

@admin_bp.get("/login")
def login():
    return render_template("login.html")

@admin_bp.post("/login")
def login_post():
    if request.form.get("password", "") == ADMIN_PASSWORD:
        session["is_admin"] = True
        return redirect(url_for("dashboard.index"))
    flash("Mot de passe incorrect", "error")
    return redirect(url_for("admin.login"))

@admin_bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin.login"))
AUTH

cat > pdf_generator.py << 'PDF'
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from config import LOUEUR_NOM, LOUEUR_TEL, LOUEUR_ADRESSE

def build_simple_pdf(title: str, payload: dict) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, h-60, title)

    c.setFont("Helvetica", 10)
    c.drawString(40, h-90, f"Loueur: {LOUEUR_NOM} | {LOUEUR_TEL}")
    c.drawString(40, h-105, f"Adresse: {LOUEUR_ADRESSE}")

    y = h-140
    c.setFont("Helvetica", 11)
    for k, v in payload.items():
        c.drawString(40, y, f"{k}: {v}")
        y -= 16
        if y < 60:
            c.showPage()
            y = h-60

    c.showPage()
    c.save()
    return buf.getvalue()
PDF

cat > dashboard.py << 'DASH'
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
DASH

cat > bookings_tab.py << 'BOOK'
from flask import Blueprint, render_template, request, redirect, url_for, send_file
import io
from admin_auth import admin_required
from trello_client import list_cards, create_card, get_card, move_card, update_card
from trello_schema import parse_payload, dump_payload
from config import LIST_DEMANDES, LIST_RESERVED, LIST_CLOSED
from pdf_generator import build_simple_pdf

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")

@bookings_bp.get("")
@admin_required
def index():
    demandes = list_cards(LIST_DEMANDES)
    reserved = list_cards(LIST_RESERVED)
    closed = list_cards(LIST_CLOSED)
    return render_template("bookings.html", demandes=demandes, reserved=reserved, closed=closed)

@bookings_bp.post("/create")
@admin_required
def create():
    title = request.form.get("title", "Nouvelle réservation").strip()
    payload = {
        "client": request.form.get("client", "").strip(),
        "vehicle": request.form.get("vehicle", "").strip(),
        "start": request.form.get("start", "").strip(),
        "end": request.form.get("end", "").strip(),
        "price_per_day": request.form.get("ppd", "").strip(),
        "deposit": request.form.get("deposit", "").strip(),
        "paid": request.form.get("paid", "").strip(),
        "notes": request.form.get("notes", "").strip(),
    }
    create_card(LIST_DEMANDES, title, dump_payload(payload))
    return redirect(url_for("bookings.index"))

@bookings_bp.post("/to_reserved/<card_id>")
@admin_required
def to_reserved(card_id):
    move_card(card_id, LIST_RESERVED)
    return redirect(url_for("bookings.index"))

@bookings_bp.post("/to_closed/<card_id>")
@admin_required
def to_closed(card_id):
    move_card(card_id, LIST_CLOSED)
    return redirect(url_for("bookings.index"))

@bookings_bp.get("/pdf/<card_id>")
@admin_required
def pdf(card_id):
    c = get_card(card_id)
    payload = parse_payload(c.get("desc",""))
    pdf_bytes = build_simple_pdf("Contrat (Simple)", payload)
    return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf", as_attachment=True, download_name="contrat.pdf")

@bookings_bp.post("/update/<card_id>")
@admin_required
def update(card_id):
    c = get_card(card_id)
    payload = parse_payload(c.get("desc",""))
    for k in ["client","vehicle","start","end","price_per_day","deposit","paid","notes"]:
        if k in request.form:
            payload[k] = request.form.get(k, "").strip()
    update_card(card_id, desc=dump_payload(payload))
    return redirect(url_for("bookings.index"))
BOOK

cat > app.py << 'APP'
from flask import Flask, redirect, url_for
from dotenv import load_dotenv
from config import SECRET_KEY

from admin_auth import admin_bp
from dashboard import dashboard_bp
from bookings_tab import bookings_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.register_blueprint(admin_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(bookings_bp)

@app.get("/")
def home():
    return redirect(url_for("dashboard.index"))

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(debug=True)
APP

cat > templates/layout.html << 'LAY'
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8"/>
  <title>Trello Car Rental</title>
  <style>
    body{font-family:Arial;margin:20px}
    .top a{margin-right:10px}
    .card{border:1px solid #ddd;border-radius:8px;padding:10px;margin:8px 0}
    .col{width:32%;display:inline-block;vertical-align:top}
    input,textarea{width:100%;padding:8px;margin:4px 0}
    button{padding:8px 12px}
  </style>
</head>
<body>
  <div class="top">
    <a href="/dashboard">Dashboard</a>
    <a href="/bookings">Réservations</a>
    <a href="/admin/logout">Logout</a>
  </div>
  <hr>
  {% block content %}{% endblock %}
</body>
</html>
LAY

cat > templates/login.html << 'LOG'
<!doctype html>
<html><body style="font-family:Arial;margin:30px">
<h2>Admin Login</h2>
<form method="post">
  <input type="password" name="password" placeholder="ADMIN_PASSWORD" />
  <button type="submit">Login</button>
</form>
</body></html>
LOG

cat > templates/dashboard.html << 'DB'
{% extends "layout.html" %}
{% block content %}
<h2>Dashboard</h2>
<ul>
  <li>Demandes: {{stats.demandes}}</li>
  <li>Réservations: {{stats.reserved}}</li>
  <li>Terminées: {{stats.closed}}</li>
  <li>Factures ouvertes: {{stats.invoices_open}}</li>
  <li>Factures payées: {{stats.invoices_paid}}</li>
</ul>
{% endblock %}
DB

cat > templates/bookings.html << 'BHTML'
{% extends "layout.html" %}
{% block content %}
<h2>Réservations (Trello)</h2>

<h3>Créer une demande</h3>
<form method="post" action="/bookings/create">
  <input name="title" placeholder="Titre (ex: Location Clio 10-12 Jan)" />
  <input name="client" placeholder="Client (nom/tel)" />
  <input name="vehicle" placeholder="Véhicule (immat/modèle)" />
  <input name="start" placeholder="Date début (YYYY-MM-DD)" />
  <input name="end" placeholder="Date fin (YYYY-MM-DD)" />
  <input name="ppd" placeholder="Prix/jour" />
  <input name="deposit" placeholder="Dépôt" />
  <input name="paid" placeholder="Payé" />
  <textarea name="notes" placeholder="Notes"></textarea>
  <button>Créer</button>
</form>

<hr>

<div class="col">
  <h3>📥 Demandes</h3>
  {% for c in demandes %}
    <div class="card">
      <b>{{c.name}}</b><br>
      <small>{{c.id}}</small><br><br>
      <form method="post" action="/bookings/to_reserved/{{c.id}}">
        <button>➡️ Confirmer (move to RESERVED)</button>
      </form>
    </div>
  {% endfor %}
</div>

<div class="col">
  <h3>📅 Réservations</h3>
  {% for c in reserved %}
    <div class="card">
      <b>{{c.name}}</b><br>
      <a href="/bookings/pdf/{{c.id}}">📄 PDF</a><br><br>
      <form method="post" action="/bookings/to_closed/{{c.id}}">
        <button>✅ Terminer (move to CLOSED)</button>
      </form>
    </div>
  {% endfor %}
</div>

<div class="col">
  <h3>✅ Terminées</h3>
  {% for c in closed %}
    <div class="card">
      <b>{{c.name}}</b><br>
      <a href="/bookings/pdf/{{c.id}}">📄 PDF</a>
    </div>
  {% endfor %}
</div>

{% endblock %}
BHTML

zip -r trello-car-rental-v2.zip . >/dev/null
echo "✅ ZIP créé: trello-car-rental-v2.zip"
