// app/static/app.js

function qs(sel, root = document) { return root.querySelector(sel); }
function qsa(sel, root = document) { return Array.from(root.querySelectorAll(sel)); }

function escapeHtml(str) {
  return (str ?? "").toString()
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function openModal() {
  const b = qs("#modalBackdrop");
  if (!b) return;
  b.classList.add("open");
  b.setAttribute("aria-hidden", "false");
}

function closeModal() {
  const b = qs("#modalBackdrop");
  if (!b) return;
  b.classList.remove("open");
  b.setAttribute("aria-hidden", "true");
}

async function loadCard(cardId) {
  const r = await fetch(`/bookings/api/card/${cardId}`);
  if (!r.ok) throw new Error("Failed to load card");
  return r.json();
}

function renderCardModal(data) {
  const title = qs("#modalTitle");
  const sub = qs("#modalSub");
  const body = qs("#modalBody");
  const footer = qs("#modalFooter");

  const p = data.payload || {};
  title.textContent = data.name || "Carte";
  sub.textContent = `${p.start_date || ""} → ${p.end_date || ""}`;

  body.innerHTML = `
    <div class="modal-grid">
      <div class="modal-box">
        <div class="k">Client</div><div class="v">${escapeHtml(p.client_name || "")}</div>
        <div class="k">Téléphone</div><div class="v">${escapeHtml(p.client_phone || "")}</div>
        <div class="k">Adresse</div><div class="v">${escapeHtml(p.client_address || "")}</div>
        <div class="k">Document</div><div class="v">${escapeHtml(p.doc_id || "")}</div>
        <div class="k">Permis</div><div class="v">${escapeHtml(p.driver_license || "")}</div>
      </div>

      <div class="modal-box">
        <div class="k">Véhicule</div><div class="v">${escapeHtml(p.vehicle_name || p.vehicle_model || "")}</div>
        <div class="k">Modèle</div><div class="v">${escapeHtml(p.vehicle_model || "")}</div>
        <div class="k">Plaque</div><div class="v">${escapeHtml(p.vehicle_plate || "")}</div>
        <div class="k">VIN</div><div class="v">${escapeHtml(p.vehicle_vin || "")}</div>
      </div>

      <div class="modal-box span2">
        <div class="k">Lieux</div>
        <div class="v">
          📍 Livraison: ${escapeHtml(p.pickup_location || "")}<br/>
          📍 Retour: ${escapeHtml(p.return_location || "")}
        </div>

        <div class="k">Options</div>
        <div class="v">
          ${(p.options?.gps ? "✅" : "⬜")} GPS &nbsp;&nbsp;
          ${(p.options?.chauffeur ? "✅" : "⬜")} Chauffeur &nbsp;&nbsp;
          ${(p.options?.baby_seat ? "✅" : "⬜")} Siège bébé
        </div>

        <div class="k">Notes</div>
        <div class="v">${escapeHtml(p.notes || "-")}</div>

        <div class="k">Trello</div>
        <div class="v"><a class="link" target="_blank" href="${escapeHtml(data.url || "#")}">Ouvrir la carte</a></div>
      </div>
    </div>
  `;

  footer.innerHTML = `
    <div class="modal-actions">
      <a class="btn btn-ghost" target="_blank" href="/contracts/${data.id}.pdf?lang=fr">Contrat FR</a>
      <a class="btn btn-ghost" target="_blank" href="/contracts/${data.id}.pdf?lang=en">EN</a>
      <a class="btn btn-ghost" target="_blank" href="/contracts/${data.id}.pdf?lang=ar">AR</a>
    </div>
  `;
}

function bindModal() {
  const closeBtn = qs("#modalClose");
  const backdrop = qs("#modalBackdrop");

  if (closeBtn) closeBtn.addEventListener("click", closeModal);
  if (backdrop) backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) closeModal();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });

  qsa(".js-open-modal").forEach((el) => {
    el.addEventListener("click", async () => {
      const cardId = el.getAttribute("data-card-id");
      if (!cardId) return;

      const modalBody = qs("#modalBody");
      if (modalBody) modalBody.innerHTML = `<div class="skeleton">Chargement…</div>`;
      openModal();

      try {
        const data = await loadCard(cardId);
        renderCardModal(data);
      } catch (err) {
        if (modalBody) modalBody.innerHTML = `<div class="errorbox">Erreur chargement carte.</div>`;
      }
    });
  });
}

function bindConfirmDelete() {
  qsa(".js-confirm-delete").forEach((f) => {
    f.addEventListener("submit", (e) => {
      if (!confirm("Supprimer = archiver la carte Trello. Continuer ?")) {
        e.preventDefault();
      }
    });
  });
}

async function loadCalendar() {
  const list = qs("#calendarList");
  if (!list) return;

  list.innerHTML = `<div class="skeleton">Chargement…</div>`;
  const r = await fetch("/bookings/api/calendar");
  if (!r.ok) {
    list.innerHTML = `<div class="errorbox">Erreur calendrier.</div>`;
    return;
  }

  const events = await r.json();

  const groups = {};
  for (const ev of events) {
    const d = (ev.start || "").substring(0, 10) || "????-??-??";
    groups[d] = groups[d] || [];
    groups[d].push(ev);
  }

  const days = Object.keys(groups).sort();
  if (days.length === 0) {
    list.innerHTML = `<div class="muted">Aucun événement.</div>`;
    return;
  }

  let html = "";
  for (const d of days) {
    html += `<div class="cal-day">
      <div class="cal-day-h">${escapeHtml(d)}</div>
      <div class="cal-items">`;
    for (const ev of groups[d]) {
      html += `
        <div class="cal-item js-open-modal" data-card-id="${escapeHtml(ev.id)}">
          <div class="cal-title">${escapeHtml(ev.title)}</div>
          <div class="cal-meta">${escapeHtml((ev.start || "").replace("T"," "))} → ${escapeHtml((ev.end || "").replace("T"," "))}</div>
          <div class="cal-badge">${escapeHtml(ev.status || "")}</div>
        </div>`;
    }
    html += `</div></div>`;
  }

  list.innerHTML = html;
  bindModal();
}

document.addEventListener("DOMContentLoaded", () => {
  bindModal();
  bindConfirmDelete();

  const refresh = qs("#calRefresh");
  if (refresh) refresh.addEventListener("click", loadCalendar);
  if (qs("#calendarList")) loadCalendar();
});

