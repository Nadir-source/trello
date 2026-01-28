import os

def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()

# ===== Auth =====
ADMIN_PASSWORD = _env("ADMIN_PASSWORD", "")
AGENT_PASSWORD = _env("AGENT_PASSWORD", "")

# ===== Trello board =====
# Peut être un ID (24 hex) OU un shortLink, ton trello_client resolve les deux
TRELLO_BOARD = _env("TRELLO_BOARD", "")

# ===== Trello Lists (NOMS ou IDs) =====
# Astuce: tu peux mettre directement les IDs Trello ici (recommandé),
# sinon mets les noms exacts, et trello_client fera le match (même si emoji change)
LIST_DEMANDES   = _env("LIST_DEMANDES", "📥 DEMANDES")

# "Réservé / Réservées"
# sur ton board on voit "📅 RÉSERVÉES" et aussi "✅ Réservé"
# ici on choisit "📅 RÉSERVÉES" (réservations planifiées)
LIST_RESERVED   = _env("LIST_RESERVED", "📅 RÉSERVÉES")

# "En cours" (à toi de choisir la bonne)
# sur ton board on voit "🔑 EN COURS"
LIST_ONGOING    = _env("LIST_ONGOING", "🔑 EN COURS")

# Terminé / Clôturé
LIST_DONE       = _env("LIST_DONE", "✅ TERMINÉES")

# Annulé (si ton code l’utilise)
LIST_CANCELED   = _env("LIST_CANCELED", "❌ ANNULÉES")

# Vehicules / Clients / Factures (si utilisés ailleurs)
LIST_VEHICLES   = _env("LIST_VEHICLES", "🚗 VÉHICULES")
LIST_CLIENTS    = _env("LIST_CLIENTS", "👤 CLIENTS")
LIST_INVOICES_OPEN = _env("LIST_INVOICES_OPEN", "🧾 FACTURES - OUVERTES")
LIST_INVOICES_PAID = _env("LIST_INVOICES_PAID", "💰 FACTURES - PAYÉES")
LIST_EXPENSES   = _env("LIST_EXPENSES", "💸 DÉPENSES")

