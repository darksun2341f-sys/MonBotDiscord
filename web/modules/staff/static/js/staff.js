const guildId = document.querySelector('[data-guild-id]')?.dataset.guildId || window.location.pathname.split('/').pop();
const wsUrl = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/modules/staff/${guildId}`;
const searchInput = document.getElementById('staff-search');
const sortSelect = document.getElementById('staff-sort');
const table = document.getElementById('staff-table');
const overview = {
  total: document.getElementById('overview-total'),
  rating: document.getElementById('overview-rating'),
  tickets: document.getElementById('overview-tickets'),
  messages: document.getElementById('overview-messages'),
};

let members = [];
let filter = 'all';
let sortKey = 'status';

const state = {
  search: '',
  category: 'all',
  settings: null,
};

function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  return date.toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' });
}

function getStatusColor(status) {
  switch ((status || '').toLowerCase()) {
    case 'online': return 'var(--success)';
    case 'idle': return 'var(--warning)';
    case 'dnd': return 'var(--danger)';
    default: return 'rgba(255,255,255,.16)';
  }
}

function renderBadges(badges) {
  if (!badges || !badges.length) return '';
  return badges.map(b => `<span class="badge">${b}</span>`).join('');
}

function renderStats(member) {
  return `
    <div class="stat"><strong>${member.stats.tickets_handled}</strong>Tickets</div>
    <div class="stat"><strong>${member.stats.moderation_actions}</strong>Modérations</div>
    <div class="stat"><strong>${member.stats.messages_sent}</strong>Messages</div>
    <div class="stat"><strong>${member.stats.voice_minutes}</strong>Min. vocal</div>
  `;
}

function renderMember(member) {
  return `
  <article class="member-card" data-category="${member.category || ''}">
    <div class="profile">
      <img src="${member.avatar_url || '/static/modules/staff/img/default-avatar.svg'}" alt="${member.username}" class="avatar" />
      <div class="member-info">
        <strong>${member.username}${member.discriminator ? '#' + member.discriminator : ''}</strong>
        <span>${member.category || 'Staff'}</span>
        <span>${member.role_names?.join(' • ') || 'Aucun rôle'}</span>
        <div class="badges">${renderBadges(member.badges)}</div>
        <span style="color:${getStatusColor(member.status)}">Statut : ${member.status || 'offline'}</span>
      </div>
    </div>
    <div class="stats">
      <div class="stat"><strong>${member.stats.xp}</strong>XP</div>
      <div class="stat"><strong>${member.stats.level}</strong>Niveau</div>
      <div class="stat"><strong>${member.stats.warns}</strong>Warns</div>
      <div class="stat"><strong>${member.stats.average_rating}</strong>Note</div>
      <div class="stat"><strong>${formatDate(member.last_activity)}</strong>Dernière activité</div>
      <div class="stat"><strong>${formatDate(member.joined_at)}</strong>Entré(e) le</div>
    </div>
  </article>
  `;
}

function sortMembers(items) {
  return [...items].sort((a, b) => {
    let left = a[sortKey];
    let right = b[sortKey];
    if (sortKey === 'name') {
      left = a.username;
      right = b.username;
    }
    if (sortKey === 'level') {
      left = a.stats?.level ?? 0;
      right = b.stats?.level ?? 0;
    }
    if (sortKey === 'tickets_handled') {
      left = a.stats?.tickets_handled ?? 0;
      right = b.stats?.tickets_handled ?? 0;
    }
    if (sortKey === 'last_activity') {
      left = a.last_activity || '';
      right = b.last_activity || '';
    }
    if (typeof left === 'number' || typeof right === 'number') {
      return Number(right) - Number(left);
    }
    return String(left).localeCompare(String(right), 'fr', { numeric: true });
  });
}

function filterMembers(items) {
  return items.filter(member => {
    const query = state.search.toLowerCase();
    const categoryMatch = state.category === 'all' || (member.category || '').toLowerCase().includes(state.category);
    const searchMatch = !query || [member.username, member.discriminator, member.category, ...(member.role_names || [])].some(value => String(value || '').toLowerCase().includes(query));
    return categoryMatch && searchMatch;
  });
}

function renderTable() {
  const filtered = filterMembers(sortMembers(members));
  table.innerHTML = filtered.map(renderMember).join('') || '<p style="color:var(--muted)">Aucun membre trouvé.</p>';
}

function renderOverview(data) {
  overview.total.textContent = data.total_members;
  overview.rating.textContent = data.average_rating.toFixed(2);
  overview.tickets.textContent = data.total_tickets;
  overview.messages.textContent = data.total_messages;
}

function renderSettings(settings) {
  if (!settings) return;
  document.getElementById('settings-channel').value = settings.channel_id || '';
  document.getElementById('settings-roles').value = (settings.staff_role_ids || []).join(', ');
  document.getElementById('toggle-entry').checked = settings.announce_entry;
  document.getElementById('toggle-exit').checked = settings.announce_exit;
  document.getElementById('toggle-promotion').checked = settings.announce_promotion;
  document.getElementById('toggle-demotion').checked = settings.announce_demotion;
  document.getElementById('toggle-role-add').checked = settings.announce_role_add;
  document.getElementById('toggle-role-remove').checked = settings.announce_role_remove;
  state.settings = settings;
}

function renderEvents(events) {
  const list = document.getElementById('events-list');
  if (!events || events.length === 0) {
    list.innerHTML = '<p class="empty">Aucun événement enregistré.</p>';
    return;
  }

  list.innerHTML = events
    .map(event => {
      return `
      <article class="event-card">
        <div class="event-badge ${event.event_type}">${event.event_type.replace(/_/g, ' ').toUpperCase()}</div>
        <div class="event-meta">
          <strong>${event.username || event.user_id}</strong>
          <span>${formatDate(event.created_at)}</span>
        </div>
        <div class="event-details">
          <p>${event.old_role_names?.join(', ') || 'Aucun rôle staff'}</p>
          <p>→ ${event.new_role_names?.join(', ') || 'Aucun rôle staff'}</p>
        </div>
      </article>
      `;
    })
    .join('');
}

function parseRoleIds(raw) {
  return raw
    .split(/[,\s]+/)
    .map(value => value.trim())
    .filter(Boolean)
    .map(Number)
    .filter(Number.isFinite);
}

function getSettingsPayload() {
  return {
    channel_id: document.getElementById('settings-channel').value || null,
    staff_role_ids: parseRoleIds(document.getElementById('settings-roles').value),
    announce_entry: document.getElementById('toggle-entry').checked,
    announce_exit: document.getElementById('toggle-exit').checked,
    announce_promotion: document.getElementById('toggle-promotion').checked,
    announce_demotion: document.getElementById('toggle-demotion').checked,
    announce_role_add: document.getElementById('toggle-role-add').checked,
    announce_role_remove: document.getElementById('toggle-role-remove').checked,
  };
}

async function loadSettings() {
  try {
    const response = await fetch(`/api/modules/staff/guilds/${guildId}/settings`, { headers: { 'Accept': 'application/json' } });
    if (!response.ok) {
      return;
    }
    const settings = await response.json();
    renderSettings(settings);
  } catch (error) {
    console.warn('Erreur lors du chargement des paramètres staff', error);
  }
}

async function saveSettings() {
  const payload = getSettingsPayload();
  const method = state.settings?.id ? 'PUT' : 'POST';
  const path = state.settings?.id
    ? `/api/modules/staff/guilds/${guildId}/settings/${state.settings.id}`
    : `/api/modules/staff/guilds/${guildId}/settings`;

  try {
    const response = await fetch(path, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error('Impossible d’enregistrer les paramètres.');
    }
    const saved = await response.json();
    renderSettings(saved);
    alert('Paramètres enregistrés.');
  } catch (error) {
    console.error(error);
    alert('Erreur lors de l’enregistrement des paramètres.');
  }
}

async function loadEvents() {
  try {
    const response = await fetch(`/api/modules/staff/guilds/${guildId}/events`, { headers: { 'Accept': 'application/json' } });
    if (!response.ok) {
      document.getElementById('events-list').innerHTML = '<p class="empty">Impossible de charger l’historique.</p>';
      return;
    }
    const events = await response.json();
    renderEvents(events);
  } catch (error) {
    console.warn('Erreur lors du chargement des événements', error);
    document.getElementById('events-list').innerHTML = '<p class="empty">Impossible de charger l’historique.</p>';
  }
}

function applySettingsListeners() {
  document.getElementById('save-settings').addEventListener('click', saveSettings);
  document.getElementById('refresh-events').addEventListener('click', loadEvents);
}

function applyTheme() {
  document.body.classList.toggle('dark');
}

function initFilters() {
  document.querySelectorAll('.filters button').forEach(button => {
    button.addEventListener('click', () => {
      state.category = button.dataset.filter;
      document.querySelectorAll('.filters button').forEach(btn => btn.classList.remove('active'));
      button.classList.add('active');
      renderTable();
    });
  });

  sortSelect.addEventListener('change', () => {
    sortKey = sortSelect.value;
    renderTable();
  });

  searchInput.addEventListener('input', event => {
    state.search = event.target.value;
    renderTable();
  });
}

function hydrate(data) {
  members = data.members;
  renderOverview(data.overview);
  renderTable();
}

const ws = new WebSocket(wsUrl);
ws.addEventListener('message', event => {
  const payload = JSON.parse(event.data);
  if (payload.type === 'staff.update') {
    hydrate({ members: payload.members, overview: payload.overview });
  }
});

ws.addEventListener('open', () => console.log('Staff socket connected'));
ws.addEventListener('close', () => console.log('Staff socket disconnected'));

initFilters();
applySettingsListeners();

fetch(`/api/modules/staff/guilds/${guildId}/overview`, { headers: { 'Accept': 'application/json' } })
  .then(res => res.json())
  .then(overviewData => renderOverview(overviewData))
  .catch(() => null);

fetch(`/api/modules/staff/guilds/${guildId}`, { headers: { 'Accept': 'application/json' } })
  .then(res => res.json())
  .then(membersData => {
    members = membersData;
    renderTable();
  })
  .catch(() => table.innerHTML = '<p style="color:var(--muted)">Impossible de charger les membres.</p>');

loadSettings();
loadEvents();

document.getElementById('toggle-theme').addEventListener('click', applyTheme);
