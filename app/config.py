# app/config.py
import os
import secrets


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# ==================================================
# Flask
# ==================================================
# Recommandé: définir SECRET_KEY dans Render (env var)
SECRET_KEY = _env("SECRET_KEY") or secrets.token_urlsafe(32)

# ==================================================
# Auth
# ==================================================
ADMIN_PASSWORD = _env("ADMIN_PASSWORD", "")
AGENT_PASSWORD = _env("AGENT_PASSWORD", "")

# ==================================================
# Trello (Render Environment)
# ==================================================
# TRELLO_BOARD = shortLink ou ID du board
TRELLO_BOARD = _env("TRELLO_BOARD", "E7RiQWGZ")
TRELLO_KEY = _env("TRELLO_KEY", "")
TRELLO_TOKEN = _env("TRELLO_TOKEN", "")

# ==================================================
# Trello Lists (IDs recommandés)  ✅ TES LISTES
# ==================================================

# --- Bookings workflow ---
LIST_DEMANDES = _env("LIST_DEMANDES", "69788180292ff516e85394d5")   # 📥 DEMANDES
LIST_RESERVED = _env("LIST_RESERVED", "69788181c616d5ecc7543792")   # 📅 RÉSERVÉES
LIST_ONGOING = _env("LIST_ONGOING", "69788182bb5b1d6bbadee0af")     # 🔑 EN COURS
LIST_DONE = _env("LIST_DONE", "6978818301473d66a8606ee0")           # ✅ TERMINÉES
LIST_CANCELED = _env("LIST_CANCELED", "69788184a8afebcbb86346e7")   # ❌ ANNULÉES

# ==================================================
# Alias compat (anti-bugs / legacy)
# ==================================================
LIST_CLOSED = _env("LIST_CLOSED", LIST_DONE)
LIST_CANCEL = _env("LIST_CANCEL", LIST_CANCELED)

# ==================================================
# Entities
# ==================================================
LIST_VEHICLES = _env("LIST_VEHICLES", "69788185284419004591cb7e")   # 🚗 VÉHICULES
LIST_CLIENTS = _env("LIST_CLIENTS", "69788186bf3992a72582005a")     # 👤 CLIENTS

# ==================================================
# Finance
# ==================================================
LIST_INVOICES_OPEN = _env("LIST_INVOICES_OPEN", "697881872f2e745fa421eee7")  # 🧾 FACTURES - OUVERTES
LIST_INVOICES_PAID = _env("LIST_INVOICES_PAID", "6978818871e1e91417a93ca1")  # 💰 FACTURES - PAYÉES
LIST_EXPENSES = _env("LIST_EXPENSES", "69788189acf32365ffdb72ae")            # 💸 DÉPENSES

# ==================================================
# Optional (si tu veux les utiliser plus tard)
# ==================================================
LIST_TO_CONFIRM = _env("LIST_TO_CONFIRM", "69665299989124da04c56e5c")  # À confirmer
LIST_RENTED = _env("LIST_RENTED", "6966529b80ca81f5d12f9371")          # 🚗 En location (autre liste)
LIST_TO_COLLECT = _env("LIST_TO_COLLECT", "6966529d03f1421a62c8c0cd")  # 💰 À encaisser

