import os

# ==========================
# Flask
# ==========================

# Utilisé par Flask pour les sessions / login
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

# ==========================
# Trello Lists (NOMS EXACTS)
# ==========================
# ⚠️ Ces noms doivent correspondre EXACTEMENT
#     aux listes sur ton board Trello

LIST_DEMANDES = "📥 DEMANDES"
LIST_RESERVED = "📅 RESERVEES"
LIST_ONGOING = "🔑 EN COURS"
LIST_DONE = "✅ TERMINEES"
LIST_CANCEL = "⛔ ANNULEES"

# Compatibilité avec ancien code
LIST_CANCELLED = LIST_CANCEL

# ==========================
# Master data
# ==========================

LIST_CLIENTS = "👤 CLIENTS"
LIST_VEHICLES = "🚗 VEHICULES"

# ==========================
# Finance (optionnel)
# ==========================

LIST_INVOICES_OPEN = "💳 FACTURES OUVERTES"
LIST_INVOICES_PAID = "✅ FACTURES PAYEES"

