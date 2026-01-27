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
