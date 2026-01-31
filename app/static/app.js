// app/static/app.js
// - Modal détails carte
// - Confirm delete (archive Trello)
// - Tabs Kanban / Calendrier
// - Search + filtre status
// - Vue compacte (toggle data-mode)
// - Calendrier "vrai" (grille mensuelle) avec navigation mois

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

/* =========================
   MODAL
========================= */
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
      <button class="btn btn-ghost" type="button" id="modalClose2">Fermer</button>
    </div>
  `;

  qs("#modalClose2")?.addEventListener("click", closeModal);
}

function bindModal() {
  const closeBtn = qs("#modalClose");
  const backdrop = qs("#modalBackdrop");

  if (closeBtn && !closeBtn.__bound) {
    closeBtn.__bound = true;
    closeBtn.addEventListener("click", closeModal);
  }

  if (backdrop && !backdrop.__bound) {
    backdrop.__bound = true;
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) closeModal();
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });

  qsa(".js-open-modal").forEach((el) => {
    if (el.__modalBound) return;
    el.__modalBound = true;

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

/* =========================
   CONFIRM DELETE
========================= */
function bindConfirmDelete() {
  qsa(".js-confirm-delete").forEach((f) => {
    if (f.__delBound) return;
    f.__delBound = true;

    f.addEventListener("submit", (e) => {
      if (!confirm("Supprimer = archiver la carte Trello. Continuer ?")) {
        e.preventDefault();
      }
    });
  });
}

/* =========================
   TABS (KANBAN / CALENDAR)
========================= */
function bindTabs() {
  const tabs = qsa(".tab");
  const panels = qsa(".tab-panel");
  if (!tabs.length || !panels.length) return;

  tabs.forEach((t) => {
    if (t.__tabBound) return;
    t.__tabBound = true;

    t.addEventListener("click", () => {
      const key = t.getAttribute("data-tab");
      tabs.forEach((x) => x.classList.remove("active"));
      t.classList.add("active");

      panels.forEach((p) => {
        p.style.display = (p.getAttribute("data-panel") === key) ? "" : "none";
      });

      if (key === "calendar") {
        loadCalendar();
      }
    });
  });
}

/* =========================
   PANELS (OPEN/CLOSE)
   - boutons data-open="id" / data-close="id"
========================= */
function bindPanels() {
  if (document.__panelsBound) return;
  document.__panelsBound = true;

  document.addEventListener("click", (e) => {
    const tgt = e.target;
    if (!tgt?.getAttribute) return;

    const openId = tgt.getAttribute("data-open");
    const closeId = tgt.getAttribute("data-close");

    if (openId) qs("#" + openId)?.classList.add("open");
    if (closeId) qs("#" + closeId)?.classList.remove("open");
  });
}

/* =========================
   SEARCH + FILTER
   - nécessite .js-card data-search="" data-status=""
========================= */
function bindSearchAndFilter() {
  const q = qs("#q");
  const statusFilter = qs("#statusFilter");

  function apply() {
    const term = (q?.value || "").trim().toLowerCase();
    const st = (statusFilter?.value || "").trim();

    qsa(".js-card").forEach((el) => {
      const s = (el.getAttribute("data-search") || "").toLowerCase();
      const status = el.getAttribute("data-status") || "";
      const okTerm = !term || s.includes(term);
      const okStatus = !st || status === st;
      el.style.display = (okTerm && okStatus) ? "" : "none";
    });
  }

  if (q && !q.__bound) {
    q.__bound = true;
    q.addEventListener("input", apply);
  }

  if (statusFilter && !statusFilter.__bound) {
    statusFilter.__bound = true;
    statusFilter.addEventListener("change", apply);
  }
}

/* =========================
   COMPACT MODE
   - nécessite #board data-mode
========================= */
function bindCompactMode() {
  const board = qs("#board");
  const btn = qs("#btnCompact");
  if (!board || !btn) return;

  if (btn.__bound) return;
  btn.__bound = true;

  btn.addEventListener("click", () => {
    const current = board.getAttribute("data-mode") || "normal";
    const next = (current === "compact") ? "normal" : "compact";
    board.setAttribute("data-mode", next);
    btn.textContent = (next === "compact") ? "Vue normale" : "Vue compacte";
  });
}

/* =========================
   MONTH CALENDAR (GRID)
========================= */
let CAL_MONTH_OFFSET = 0; // 0=mois courant

function pad2(n){ return String(n).padStart(2,"0"); }
function ymd(d){ return `${d.getFullYear()}-${pad2(d.getMonth()+1)}-${pad2(d.getDate())}`; }
function monthLabel(d){ return d.toLocaleDateString("fr-FR", { month:"long", year:"numeric" }); }
function startOfMonth(d){ return new Date(d.getFullYear(), d.getMonth(), 1); }
function endOfMonth(d){ return new Date(d.getFullYear(), d.getMonth()+1, 0); }
function dowMondayIndex(d){ return (d.getDay() + 6) % 7; } // Mon=0..Sun=6

function toDate(s){
  if(!s) return null;

  // Try native first
  const dt = new Date(s);
  if (!isNaN(dt.getTime())) return dt;

  // Fallback manual parse: YYYY-MM-DDTHH:MM
  const m = String(s).match(/^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}))?/);
  if(!m) return null;
  const Y=+m[1], M=+m[2]-1, D=+m[3], h=+(m[4]||0), mi=+(m[5]||0);
  return new Date(Y,M,D,h,mi,0,0);
}

function daysBetweenInclusive(d1, d2){
  const out = [];
  const a = new Date(d1.getFullYear(), d1.getMonth(), d1.getDate());
  const b = new Date(d2.getFullYear(), d2.getMonth(), d2.getDate());
  const max = 370; // sécurité
  for(let i=0; i<max; i++){
    out.push(new Date(a));
    if (a.getTime() === b.getTime()) break;
    a.setDate(a.getDate()+1);
  }
  return out;
}

async function loadCalendar() {
  const root = qs("#calendarList");
  if (!root) return;

  root.innerHTML = `<div class="skeleton">Chargement…</div>`;

  const r = await fetch("/bookings/api/calendar");
  if (!r.ok) {
    root.innerHTML = `<div class="errorbox">Erreur calendrier.</div>`;
    return;
  }

  const events = await r.json();

  const now = new Date();
  const target = new Date(now.getFullYear(), now.getMonth() + CAL_MONTH_OFFSET, 1);
  const mStart = startOfMonth(target);
  const mEnd = endOfMonth(target);

  // Map day -> events
  const map = {};

  for (const ev of events) {
    const s = toDate(ev.start);
    if (!s) continue;
    const e = toDate(ev.end) || s;

    const days = daysBetweenInclusive(s, e);
    for (const d of days) {
      if (d < mStart || d > mEnd) continue;
      const key = ymd(d);
      map[key] = map[key] || [];
      map[key].push(ev);
    }
  }

  // Grid boundaries (Monday week)
  const firstDow = dowMondayIndex(mStart);
  const gridStart = new Date(mStart);
  gridStart.setDate(mStart.getDate() - firstDow);

  const lastDow = dowMondayIndex(mEnd);
  const gridEnd = new Date(mEnd);
  gridEnd.setDate(mEnd.getDate() + (6 - lastDow));

  const dows = ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"];
  const todayKey = ymd(now);

  let html = `
    <div class="cal-wrap">
      <div class="cal-toolbar">
        <div class="cal-title">${escapeHtml(monthLabel(target))}</div>
        <div class="cal-btns">
          <button class="btn btn-ghost" id="calPrev" type="button">←</button>
          <button class="btn btn-ghost" id="calToday" type="button">Aujourd’hui</button>
          <button class="btn btn-ghost" id="calNext" type="button">→</button>
        </div>
      </div>

      <div class="cal-grid">
        ${dows.map(x => `<div class="cal-dow">${x}</div>`).join("")}
      </div>

      <div class="cal-grid" id="calGrid">
  `;

  const cursor = new Date(gridStart);
  while (cursor <= gridEnd) {
    const key = ymd(cursor);
    const inMonth = (cursor.getMonth() === target.getMonth());
    const isToday = (key === todayKey);

    const items = (map[key] || []).slice().sort((a,b)=> (a.start||"").localeCompare(b.start||""));

    const visible = items.slice(0, 3);
    const hiddenCount = items.length - visible.length;

    html += `
      <div class="cal-cell ${inMonth ? "" : "muted"} ${isToday ? "today" : ""}">
        <div class="cal-daynum">
          <div>${escapeHtml(String(cursor.getDate()))}</div>
          <span>${inMonth ? "" : escapeHtml(String(cursor.getMonth()+1))}</span>
        </div>

        <div class="cal-items">
          ${visible.map(ev => {
            const st = (ev.status || "").toLowerCase();
            const title = ev.title || "Réservation";
            return `
              <div class="cal-chip js-open-modal"
                   data-card-id="${escapeHtml(ev.id)}"
                   data-status="${escapeHtml(st)}"
                   title="${escapeHtml(title)}">
                <div style="overflow:hidden;text-overflow:ellipsis">${escapeHtml(title)}</div>
                <div class="tag">${escapeHtml(st || "—")}</div>
              </div>
            `;
          }).join("")}

          ${hiddenCount > 0 ? `<div class="cal-more">+${hiddenCount} autres…</div>` : ``}
        </div>
      </div>
    `;

    cursor.setDate(cursor.getDate() + 1);
  }

  html += `</div></div>`;

  root.innerHTML = html;

  // Chips open modal
  bindModal();

  // Navigation
  qs("#calPrev")?.addEventListener("click", () => { CAL_MONTH_OFFSET -= 1; loadCalendar(); });
  qs("#calNext")?.addEventListener("click", () => { CAL_MONTH_OFFSET += 1; loadCalendar(); });
  qs("#calToday")?.addEventListener("click", () => { CAL_MONTH_OFFSET = 0; loadCalendar(); });
}

/* =========================
   INIT
========================= */
document.addEventListener("DOMContentLoaded", () => {
  bindModal();
  bindConfirmDelete();

  bindTabs();
  bindPanels();
  bindSearchAndFilter();
  bindCompactMode();

  // Bouton refresh (si présent)
  const refresh = qs("#calRefresh");
  if (refresh && !refresh.__bound) {
    refresh.__bound = true;
    refresh.addEventListener("click", loadCalendar);
  }

  // Si l’onglet calendrier est actif au chargement
  if (qs("#calendarList") && qs(".tab.active")?.getAttribute("data-tab") === "calendar") {
    loadCalendar();
  }
});

