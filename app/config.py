# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

def env(name: str, default: str = "") -> str:
    v = os.getenv(name)
    return v if (v is not None and v != "") else default

# --- Flask ---
SECRET_KEY = env("SECRET_KEY", "dev-secret-key-123456")

# --- Auth (2 comptes simples) ---
# Tu peux les mettre en variables Render pour éviter de les laisser en dur.
ADMIN_PASSWORD = env("ADMIN_PASSWORD", "admin123")
AGENT_PASSWORD = env("AGENT_PASSWORD", "agent123")

# --- Trello ---
TRELLO_KEY = env("TRELLO_KEY", "")
TRELLO_TOKEN = env("TRELLO_TOKEN", "")
TRELLO_BOARD = env("TRELLO_BOARD", "")  # shortLink ou id

# --- Lists (noms ou IDs) ---
# Garde tes valeurs actuelles si tu utilises des noms avec emoji
LIST_DEMANDES  = env("LIST_DEMANDES", "📥 DEMANDES")
LIST_RESERVED  = env("LIST_RESERVED", "✅ RÉSERVÉES")
LIST_INPROGRESS = env("LIST_INPROGRESS", "🚗 EN COURS")
LIST_CLOSED    = env("LIST_CLOSED", "🏁 TERMINÉES")
LIST_CANCEL    = env("LIST_CANCEL", "❌ ANNULÉES")

