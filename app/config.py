import os

def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()

# =========================
# Auth (Render Environment)
# =========================
ADMIN_PASSWORD = _env("ADMIN_PASSWORD", "")
AGENT_PASSWORD = _env("AGENT_PASSWORD", "")

# =========================
# Trello (Render Environment)
# =========================
# TRELLO_BOARD = id (24 hex) OU shortLink
TRELLO_BOARD = _env("TRELLO_BOARD", "")
TRELLO_KEY = _env("TRELLO_KEY", "")
TRELLO_TOKEN = _env("TRELLO_TOKEN", "")

# =========================
# Trello Lists (NOMS ou IDs)
# =========================
# Conseil: mets les IDs Trello en env vars si possible.
# Sinon noms: le client Trello fera le match même si emoji/accents changent.

# Bookings / workflow
LIST_DEMANDES = _env("LIST_DEMANDES", "📥 DEMANDES")

# Sur ton board: on voit "📅 RÉSERVÉES" (et pas forcément "✅ RÉSERVÉES")
LIST_RESERVED = _env("LIST_RESERVED", "📅 RÉSERVÉES")

# Sur ton board: on voit "🔑 EN COURS"
LIST_ONGOING = _env("LIST_ONGOING", "🔑 EN COURS")

# Sur ton board: on voit "✅ TERMINÉES" et aussi "✅ Clôturé"
# Choisis celle que ton dashboard considère comme "closed"
LIST_CLOSED = _env("LIST_CLOSED", "✅ TERMINÉES")

LIST_CANCELED = _env("LIST_CANCELED", "❌ ANNULÉES")

# Entities
LIST_VEHICLES = _env("LIST_VEHICLES", "🚗 VÉHICULES")
LIST_CLIENTS = _env("LIST_CLIENTS", "👤 CLIENTS")

# Finance / invoices
LIST_INVOICES_OPEN = _env("LIST_INVOICES_OPEN", "🧾 FACTURES - OUVERTES")
LIST_INVOICES_PAID = _env("LIST_INVOICES_PAID", "💰 FACTURES - PAYÉES")
LIST_EXPENSES = _env("LIST_EXPENSES", "💸 DÉPENSES")

# Optionnels (si tu les utilises ailleurs)
LIST_TO_CONFIRM = _env("LIST_TO_CONFIRM", "À confirmer")
LIST_RENTED = _env("LIST_RENTED", "🚗 En location")
LIST_TO_COLLECT = _env("LIST_TO_COLLECT", "💰 À encaisser")

