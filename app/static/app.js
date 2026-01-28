// app/static/app.js
(function () {
  let calendarInstance = null;

  function $(sel) { return document.querySelector(sel); }
  function $all(sel) { return Array.from(document.querySelectorAll(sel)); }

  function safeJsonParse(s, fallback) {
    try { return JSON.parse(s); } catch { return fallback; }
  }

  function normalizeDateEnd(endStr) {
    // FullCalendar dayGrid end is exclusive; on accepte "YYYY-MM-DD"
    // Si pas d'end => on met start+1j
    if (!endStr) return null;
    return endStr;
  }

  function eventColorByStatus(status) {
    // Neon colors (CSS friendly)
    switch ((status || "").toLowerCase()) {
      case "reserved": return { bg: "rgba(180,92,255,.22)", border: "rgba(180,92,255,.55)" };
      case "ongoing":  return { bg: "rgba(57,255,136,.18)", border: "rgba(57,255,136,.55)" };
      case "done":     return { bg: "rgba(255,176,32,.16)", border: "rgba(255,176,32,.55)" };
      case "cancel":   return { bg: "rgba(255,77,109,.16)", border: "rgba(255,77,109,.55)" };
      default:         return { bg: "rgba(0,229,255,.14)", border: "rgba(0,229,255,.50)" };
    }
  }

  function applyEventTheme(eventObj) {
    const s = eventObj.extendedProps?.status || eventObj.status || "";
    const c = eventColorByStatus(s);
    eventObj.backgroundColor = c.bg;
    eventObj.borderColor = c.border;
    eventObj.textColor = "rgba(234,240,255,.95)";
    return eventObj;
  }

  function buildVehicleOptions(events) {
    const vehicles = new Set();
    events.forEach(ev => {
      const v = ev.extendedProps?.vehicle || ev.vehicle || "";
      if (v) vehicles.add(v);
    });
    return Array.from(vehicles).sort((a,b) => a.localeCompare(b));
  }

  function readCalendarEvents() {
    const el = $("#calendar");
    if (!el) return [];
    const raw = el.getAttribute("data-events") || "[]";
    const parsed = safeJsonParse(raw, []);
    // theme + normalize
    return parsed.map(ev => {
      const e = { ...ev };
      e.end = normalizeDateEnd(e.end);
      return applyEventTheme(e);
    });
  }

  function filterEvents(allEvents) {
    const statusSel = $("#filterStatus");
    const vehicleSel = $("#filterVehicle");
    const qInput = $("#filterSearch");

    const status = statusSel ? statusSel.value : "all";
    const vehicle = vehicleSel ? vehicleSel.value : "all";
    const q = (qInput ? qInput.value : "").trim().toLowerCase();

    return allEvents.filter(ev => {
      const s = (ev.extendedProps?.status || "").toLowerCase();
      const v = (ev.extendedProps?.vehicle || "").toLowerCase();
      const title = (ev.title || "").toLowerCase();
      const client = (ev.extendedProps?.client || "").toLowerCase();

      if (status !== "all" && s !== status) return false;
      if (vehicle !== "all" && v !== vehicle.toLowerCase()) return false;
      if (q) {
        const hay = `${title} ${client} ${v}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }

  function setStatsCounts(allEvents) {
    const counters = {
      reserved: 0, ongoing: 0, done: 0, cancel: 0
    };
    allEvents.forEach(ev => {
      const s = (ev.extendedProps?.status || "").toLowerCase();
      if (counters[s] !== undefined) counters[s] += 1;
    });

    const map = [
      ["#countReserved", counters.reserved],
      ["#countOngoing", counters.ongoing],
      ["#countDone", counters.done],
      ["#countCancel", counters.cancel],
    ];
    map.forEach(([id, val]) => {
      const el = $(id);
      if (el) el.textContent = String(val);
    });
  }

  function renderOrUpdateCalendar() {
    const el = $("#calendar");
    if (!el || !window.FullCalendar) return;

    const allEvents = readCalendarEvents();
    setStatsCounts(allEvents);

    // init filters (vehicle options)
    const vehicleSel = $("#filterVehicle");
    if (vehicleSel && vehicleSel.options.length <= 1) {
      const opts = buildVehicleOptions(allEvents);
      opts.forEach(v => {
        const o = document.createElement("option");
        o.value = v;
        o.textContent = v;
        vehicleSel.appendChild(o);
      });
    }

    const filtered = filterEvents(allEvents);

    if (!calendarInstance) {
      calendarInstance = new FullCalendar.Calendar(el, {
        initialView: "timeGridWeek",
        firstDay: 1, // Monday
        nowIndicator: true,
        height: "auto",
        expandRows: true,
        slotMinTime: "07:00:00",
        slotMaxTime: "22:00:00",
        headerToolbar: {
          left: "prev,next today",
          center: "title",
          right: "timeGridWeek,dayGridMonth,timeGridDay"
        },
        events: filtered,
        eventClick: function(info) {
          if (info.event.url) {
            info.jsEvent.preventDefault();
            window.open(info.event.url, "_blank");
          }
        },
        eventDidMount: function(info) {
          const status = info.event.extendedProps?.status || "";
          const vehicle = info.event.extendedProps?.vehicle || "";
          const client = info.event.extendedProps?.client || "";
          info.el.title = `${client} • ${vehicle} • ${status}`.trim();
        }
      });
      calendarInstance.render();
    } else {
      calendarInstance.removeAllEvents();
      filtered.forEach(ev => calendarInstance.addEvent(ev));
      calendarInstance.render();
    }
  }

  function bindFilters() {
    ["#filterStatus", "#filterVehicle", "#filterSearch"].forEach(id => {
      const el = $(id);
      if (!el) return;
      el.addEventListener("input", () => renderOrUpdateCalendar());
      el.addEventListener("change", () => renderOrUpdateCalendar());
    });

    const resetBtn = $("#filterReset");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        const s = $("#filterStatus"); if (s) s.value = "all";
        const v = $("#filterVehicle"); if (v) v.value = "all";
        const q = $("#filterSearch"); if (q) q.value = "";
        renderOrUpdateCalendar();
      });
    }

    const refreshBtn = $("#calendarRefresh");
    if (refreshBtn) refreshBtn.addEventListener("click", () => renderOrUpdateCalendar());
  }

  // Public function
  window.renderCalendar = function () {
    renderOrUpdateCalendar();
  };

  document.addEventListener("DOMContentLoaded", () => {
    bindFilters();
    renderOrUpdateCalendar();
  });
})();

