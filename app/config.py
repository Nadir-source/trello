# app/config.py
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
TRELLO_KEY = _env("TRELLO_KEY", "")
TRELLO_TOKEN = _env("TRELLO_TOKEN", "")

# ==================================================
# Trello Lists (IDs RECOMMANDÉS)
# ==================================================
# Board E7RiQWGZ (d'après ton curl)
# 📥 DEMANDES     69788180292ff516e85394d5
# 📅 RÉSERVÉES    69788181c616d5ecc7543792
# 🔑 EN COURS     69788182bb5b1d6bbadee0af
# ✅ TERMINÉES    6978818301473d66a8606ee0
# ❌ ANNULÉES     69788184a8afebcbb86346e7
# 🚗 VÉHICULES    69788185284419004591cb7e
# 👤 CLIENTS      69788186bf3992a72582005a
# 🧾 FACTURES - OUVERTES  697881872f2e745fa421eee7
# 💰 FACTURES - PAYÉES    6978818871e1e91417a93ca1
# 💸 DÉPENSES     69788189acf32365ffdb72ae

# --- Bookings workflow ---
LIST_DEMANDES = _env("LIST_DEMANDES", "69788180292ff516e85394d5")
LIST_RESERVED = _env("LIST_RESERVED", "69788181c616d5ecc7543792")
LIST_ONGOING = _env("LIST_ONGOING", "69788182bb5b1d6bbadee0af")
LIST_DONE = _env("LIST_DONE", "6978818301473d66a8606ee0")
LIST_CANCELED = _env("LIST_CANCELED", "69788184a8afebcbb86346e7")

# ==================================================
# ALIAS COMPATIBILITÉ (ANTI-BUGS)
# ==================================================
LIST_CLOSED = _env("LIST_CLOSED", LIST_DONE)
LIST_CANCEL = _env("LIST_CANCEL", LIST_CANCELED)

# ==================================================
# Entities
# ==================================================
LIST_VEHICLES = _env("LIST_VEHICLES", "69788185284419004591cb7e")
LIST_CLIENTS = _env("LIST_CLIENTS", "69788186bf3992a72582005a")

# ==================================================
# Finance / Facturation
# ==================================================
LIST_INVOICES_OPEN = _env("LIST_INVOICES_OPEN", "697881872f2e745fa421eee7")
LIST_INVOICES_PAID = _env("LIST_INVOICES_PAID", "6978818871e1e91417a93ca1")
LIST_EXPENSES = _env("LIST_EXPENSES", "69788189acf32365ffdb72ae")

# ==================================================
# Optional / Extensions (si tu veux les utiliser plus tard)
# ==================================================
LIST_TO_CONFIRM = _env("LIST_TO_CONFIRM", "")
LIST_RENTED = _env("LIST_RENTED", "")
LIST_TO_COLLECT = _env("LIST_TO_COLLECT", "")


LIST_CONFIG = "69887e5ce183bf02e4160177"
