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
