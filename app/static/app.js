// app/static/app.js
(function () {
  let calendarInstance = null;

  window.renderCalendar = function () {
    const el = document.getElementById("calendar");
    if (!el || !window.FullCalendar) return;

    let events = [];
    try {
      const raw = el.getAttribute("data-events");
      events = raw ? JSON.parse(raw) : [];
    } catch (e) {
      console.warn("Invalid calendar events JSON", e);
    }

    if (calendarInstance) {
      calendarInstance.removeAllEvents();
      events.forEach(ev => calendarInstance.addEvent(ev));
      calendarInstance.render();
      return;
    }

    calendarInstance = new FullCalendar.Calendar(el, {
      initialView: "dayGridMonth",
      height: "auto",
      headerToolbar: {
        left: "prev,next today",
        center: "title",
        right: "dayGridMonth,timeGridWeek,timeGridDay"
      },
      nowIndicator: true,
      navLinks: true,
      eventDisplay: "block",
      events: events,
      eventClick: function(info) {
        // open PDF in new tab
        if (info.event.url) {
          info.jsEvent.preventDefault();
          window.open(info.event.url, "_blank");
        }
      }
    });

    calendarInstance.render();
  };
})();

