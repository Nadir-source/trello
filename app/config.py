import os
import secrets

def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()

# ==================================================
# Flask
# ==================================================
# IMPORTANT : mets SECRET_KEY dans Render (recommandé)
SECRET_KEY = _env("SECRET_KEY") or secrets.token_urlsafe(32)

# ==================================================
# Auth
# ==================================================
ADMIN_PASSWORD = _env("ADMIN_PASSWORD", "")
AGENT_PASSWORD = _env("AGENT_PASSWORD", "")

# ==================================================
# Trello (Render Environment)
# ==================================================
# TRELLO_BOARD = ID (24 hex) OU shortLink
TRELLO_BOARD = _env("TRELLO_BOARD", "")
TRELLO_KEY   = _env("TRELLO_KEY", "")
TRELLO_TOKEN = _env("TRELLO_TOKEN", "")

# ==================================================
# Trello Lists (NOMS ou IDs)
# ==================================================
# ⚠️ Conseil PRO : mets les IDs Trello en env vars si possible
# Sinon, les noms fonctionneront grâce au matching souple (emoji/accents)

# --- Bookings workflow ---
LIST_DEMANDES = _env("LIST_DEMANDES", "📥 DEMANDES")

LIST_RESERVED = _env("LIST_RESERVED", "📅 RÉSERVÉES")

LIST_ONGOING  = _env("LIST_ONGOING", "🔑 EN COURS")

# Terminées / clôturées
LIST_DONE     = _env("LIST_DONE", "✅ TERMINÉES")

# Annulées
LIST_CANCELED = _env("LIST_CANCELED", "❌ ANNULÉES")

# ==================================================
# ALIAS COMPATIBILITÉ (ANTI-BUGS)
# ==================================================
# Certains fichiers utilisent d'autres noms → on mappe tout ici

# dashboard.py / legacy
LIST_CLOSED = _env("LIST_CLOSED", LIST_DONE)

# bookings.py utilise LIST_CANCEL
LIST_CANCEL = _env("LIST_CANCEL", LIST_CANCELED)

# ==================================================
# Entities
# ==================================================
LIST_VEHICLES = _env("LIST_VEHICLES", "🚗 VÉHICULES")
LIST_CLIENTS  = _env("LIST_CLIENTS", "👤 CLIENTS")

# ==================================================
# Finance / Facturation
# ==================================================
LIST_INVOICES_OPEN = _env("LIST_INVOICES_OPEN", "🧾 FACTURES - OUVERTES")
LIST_INVOICES_PAID = _env("LIST_INVOICES_PAID", "💰 FACTURES - PAYÉES")
LIST_EXPENSES      = _env("LIST_EXPENSES", "💸 DÉPENSES")

# ==================================================
# Optional / Extensions
# ==================================================
LIST_TO_CONFIRM = _env("LIST_TO_CONFIRM", "À confirmer")
LIST_RENTED     = _env("LIST_RENTED", "🚗 En location")
LIST_TO_COLLECT = _env("LIST_TO_COLLECT", "💰 À encaisser")

