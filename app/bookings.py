{% extends "layout.html" %}
{% block content %}

<div class="page-head">
  <div>
    <h1>Réservations</h1>
    <div class="muted">Planning semaine • filtres • contrat FR/AR • workflow Trello</div>
  </div>

  <div class="stats">
    <div class="stat neon-cyan"><div class="n">{{stats.demandes}}</div><div class="l">Demandes</div></div>
    <div class="stat neon-purple"><div class="n">{{stats.reserved}}</div><div class="l">Réservées</div></div>
    <div class="stat neon-green"><div class="n">{{stats.ongoing}}</div><div class="l">En cours</div></div>
    <div class="stat neon-orange"><div class="n">{{stats.done}}</div><div class="l">Terminées</div></div>
  </div>
</div>

<div class="grid-2 mt">

  <!-- FORM -->
  <div class="card neon form-card">
    <div class="card-head">
      <div>
        <div class="card-title">➕ Nouvelle demande</div>
        <div class="muted">Le site = opérationnel pour ton ami (pas besoin Trello)</div>
      </div>
      <span class="pill">Create</span>
    </div>

    <form method="post" action="/bookings/create" class="grid">
      <div class="field full">
        <label>Titre</label>
        <input name="title" placeholder="Ex: Location Clio 10-12" />
      </div>

      <div class="field">
        <label>Client</label>
        <select name="client_id">
          <option value="">-- choisir --</option>
          {% for c in clients %}
            <option value="{{c.id}}">{{c.name}}</option>
          {% endfor %}
        </select>
        <div class="hint">Si vide: créer une carte dans “Clients” sur Trello.</div>
      </div>

      <div class="field">
        <label>Véhicule</label>
        <select name="vehicle_id">
          <option value="">-- choisir --</option>
          {% for v in vehicles %}
            <option value="{{v.id}}">{{v.name}}</option>
          {% endfor %}
        </select>
        <div class="hint">Si vide: créer une carte dans “Véhicules”.</div>
      </div>

      <div class="field">
        <label>Début</label>
        <input name="start" placeholder="YYYY-MM-DD" />
      </div>

      <div class="field">
        <label>Fin</label>
        <input name="end" placeholder="YYYY-MM-DD" />
      </div>

      <div class="field">
        <label>Prix / jour (DZD)</label>
        <input name="ppd" placeholder="Ex: 8500" />
      </div>

      <div class="field">
        <label>Dépôt (DZD)</label>
        <input name="deposit" placeholder="Ex: 20000" />
      </div>

      <div class="field">
        <label>Déjà payé (DZD)</label>
        <input name="paid" placeholder="Ex: 17000" />
      </div>

      <div class="field">
        <label>Méthode</label>
        <select name="method">
          <option value="Cash">Cash</option>
          <option value="Virement">Virement</option>
          <option value="Carte">Carte</option>
        </select>
      </div>

      <div class="field">
        <label>Document</label>
        <select name="doc">
          <option value="">--</option>
          <option value="CNI">Carte Nationale</option>
          <option value="PASSPORT">Passeport</option>
        </select>
      </div>

      <div class="field">
        <label>Lieu remise</label>
        <input name="pickup" placeholder="Ex: Aéroport" />
      </div>

      <div class="field">
        <label>Lieu retour</label>
        <input name="return_place" placeholder="Ex: Centre ville" />
      </div>

      <div class="field full">
        <label>Options</label>
        <div class="checks">
          <label><input type="checkbox" name="extra_driver"> Chauffeur</label>
          <label><input type="checkbox" name="extra_gps"> GPS</label>
          <label><input type="checkbox" name="extra_baby"> Siège bébé</label>
        </div>
      </div>

      <div class="field full">
        <label>Notes</label>
        <textarea name="notes" placeholder="Remarques..."></textarea>
      </div>

      <div class="actions full">
        <button class="btn primary">Créer demande</button>
      </div>
    </form>
  </div>

  <!-- CALENDAR -->
  <div class="card neon">
    <div class="card-head">
      <div>
        <div class="card-title">🗓️ Planning</div>
        <div class="muted">Semaine par défaut • click event = PDF contrat</div>
      </div>
      <div class="row gap">
        <button id="calendarRefresh" class="btn" type="button">↻ Refresh</button>
        <button id="filterReset" class="btn" type="button">🧹 Reset</button>
      </div>
    </div>

    <div class="filters">
      <div class="filter">
        <label>Statut</label>
        <select id="filterStatus">
          <option value="all">Tous</option>
          <option value="reserved">Réservées</option>
          <option value="ongoing">En cours</option>
          <option value="done">Terminées</option>
          <option value="cancel">Annulées</option>
        </select>
      </div>

      <div class="filter">
        <label>Véhicule</label>
        <select id="filterVehicle">
          <option value="all">Tous</option>
        </select>
      </div>

      <div class="filter">
        <label>Recherche</label>
        <input id="filterSearch" placeholder="Client / véhicule..." />
      </div>

      <div class="legend">
        <div class="lg">
          <span class="dot dot-purple"></span> Réservée (<b id="countReserved">0</b>)
        </div>
        <div class="lg">
          <span class="dot dot-green"></span> En cours (<b id="countOngoing">0</b>)
        </div>
        <div class="lg">
          <span class="dot dot-orange"></span> Terminée (<b id="countDone">0</b>)
        </div>
        <div class="lg">
          <span class="dot dot-red"></span> Annulée (<b id="countCancel">0</b>)
        </div>
      </div>
    </div>

    <!-- Embed events -->
    <div id="calendar" class="calendar"
      data-events='[
        {% set all = reserved + ongoing %}
        {% for c in all %}
          {
            "title": "{{ (c.vehicle ~ " • " ~ c.client)|e }}",
            "start": "{{ c.start|e }}",
            "end": "{{ c.end|e }}",
            "url": "/bookings/contract.pdf/{{ c.id }}",
            "extendedProps": {
              "id": "{{ c.id|e }}",
              "status": "{{ "reserved" if c in reserved else "ongoing" }}",
              "vehicle": "{{ c.vehicle|e }}",
              "client": "{{ c.client|e }}"
            }
          }{{ "," if not loop.last else "" }}
        {% endfor %}
      ]'>
    </div>

    <div class="muted small mt">
      Astuce: passe en “Mois” si tu veux une vue globale (boutons en haut du calendrier).
    </div>
  </div>

</div>

<div class="columns mt">

  <section class="col">
    <div class="col-head"><h3>📥 Demandes</h3><span class="pill">{{ demandes|length }}</span></div>
    {% for c in demandes %}
      <div class="card item neon-soft">
        <div class="title">{{c.name}}</div>
        <div class="meta">
          <div><span class="tag">👤</span>{{c.client}}</div>
          <div><span class="tag">🚗</span>{{c.vehicle}}</div>
          <div><span class="tag">📅</span>{{c.start}} → {{c.end}}</div>
        </div>
        <div class="row">
          <form method="post" action="/bookings/move/{{c.id}}/reserved"><button class="btn">➡️ Confirmer</button></form>
          <form method="post" action="/bookings/move/{{c.id}}/cancel"><button class="btn danger">Annuler</button></form>
        </div>
      </div>
    {% endfor %}
    {% if demandes|length == 0 %}<div class="empty">Aucune demande.</div>{% endif %}
  </section>

  <section class="col">
    <div class="col-head"><h3>📅 Réservées</h3><span class="pill">{{ reserved|length }}</span></div>
    {% for c in reserved %}
      <div class="card item neon-soft">
        <div class="title">{{c.name}}</div>
        <div class="meta">
          <div><span class="tag">👤</span>{{c.client}}</div>
          <div><span class="tag">🚗</span>{{c.vehicle}}</div>
          <div><span class="tag">📅</span>{{c.start}} → {{c.end}}</div>
        </div>
        <div class="row">
          <a class="btn" href="/bookings/contract.pdf/{{c.id}}">📄 Contrat FR+AR</a>
          <form method="post" action="/bookings/move/{{c.id}}/ongoing"><button class="btn ok">🔑 En cours</button></form>
        </div>
      </div>
    {% endfor %}
    {% if reserved|length == 0 %}<div class="empty">Aucune réservation.</div>{% endif %}
  </section>

  <section class="col">
    <div class="col-head"><h3>🔑 En cours</h3><span class="pill">{{ ongoing|length }}</span></div>
    {% for c in ongoing %}
      <div class="card item neon-soft">
        <div class="title">{{c.name}}</div>
        <div class="meta">
          <div><span class="tag">👤</span>{{c.client}}</div>
          <div><span class="tag">🚗</span>{{c.vehicle}}</div>
          <div><span class="tag">📅</span>{{c.start}} → {{c.end}}</div>
        </div>
        <div class="row">
          <a class="btn" href="/bookings/contract.pdf/{{c.id}}">📄 Contrat</a>
          <form method="post" action="/bookings/move/{{c.id}}/done"><button class="btn ok">✅ Terminer</button></form>
        </div>
      </div>
    {% endfor %}
    {% if ongoing|length == 0 %}<div class="empty">Aucun en cours.</div>{% endif %}
  </section>

</div>

{% endblock %}

