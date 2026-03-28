const API = '/api/goals';

const state = {
  goals: [],
  stats: { pending: 0, done: 0, categories: [] },
  filterStatus: '',
  filterCat: '',
  editingId: null,
};

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  loadGoals();

  document.getElementById('btn-add').addEventListener('click', openAddModal);
  document.getElementById('btn-cancel').addEventListener('click', closeModal);
  document.getElementById('btn-save').addEventListener('click', saveGoal);

  document.getElementById('filter-status').addEventListener('change', e => {
    state.filterStatus = e.target.value;
    loadGoals();
  });
  document.getElementById('filter-cat').addEventListener('change', e => {
    state.filterCat = e.target.value;
    loadGoals();
  });

  document.getElementById('btn-enable-notify').addEventListener('click', enableNotifications);
  document.getElementById('btn-test-notify').addEventListener('click', testNotify);

  document.getElementById('modal').addEventListener('click', e => {
    if (e.target === document.getElementById('modal')) closeModal();
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
    if (e.key === 'Enter' && !document.getElementById('modal').classList.contains('hidden')) {
      saveGoal();
    }
  });

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
      .then(() => _resubscribeIfNeeded())
      .catch(() => {});
  }
});

// ── Push notifications ────────────────────────────────────────────────────────

async function _resubscribeIfNeeded() {
  // Silently re-send an existing subscription to the server (e.g. after redeploy wipes DB)
  if (!('PushManager' in window)) return;
  const reg = await navigator.serviceWorker.ready;
  const existing = await reg.pushManager.getSubscription();
  if (!existing) return;
  await fetch('/api/subscribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(existing.toJSON()),
  });
}

async function enableNotifications() {
  const banner = document.getElementById('notify-banner');
  const msg    = document.getElementById('notify-msg');

  if (!('Notification' in window) || !('PushManager' in window)) {
    banner.classList.remove('hidden');
    banner.classList.add('error');
    msg.textContent = 'Push notifications are not supported on this browser.';
    return;
  }

  if (Notification.permission === 'denied') {
    banner.classList.remove('hidden');
    banner.classList.add('error');
    msg.textContent = 'Notifications are blocked. Enable them in iPhone Settings → Notifications → Goal Tracker.';
    return;
  }

  const permission = await Notification.requestPermission();
  if (permission !== 'granted') {
    banner.classList.remove('hidden');
    banner.classList.add('error');
    msg.textContent = 'Permission not granted.';
    return;
  }

  try {
    const reg = await navigator.serviceWorker.ready;
    const res = await fetch('/api/vapid-public-key');
    const { publicKey } = await res.json();

    const subscription = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: _urlBase64ToUint8Array(publicKey),
    });

    await fetch('/api/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(subscription.toJSON()),
    });

    banner.classList.remove('hidden', 'error');
    msg.textContent = 'Notifications enabled! Tap "Test Notification" to verify.';
    setTimeout(() => banner.classList.add('hidden'), 5000);
  } catch (err) {
    banner.classList.remove('hidden');
    banner.classList.add('error');
    msg.textContent = 'Error: ' + err.message;
  }
}

async function testNotify() {
  const banner = document.getElementById('notify-banner');
  const msg    = document.getElementById('notify-msg');
  const res    = await fetch('/api/test-notify', { method: 'POST' });
  const data   = await res.json();
  banner.classList.remove('hidden', 'error');
  if (res.ok) {
    msg.textContent = `Notification sent to ${data.sent} device(s) — check your iPhone!`;
  } else {
    banner.classList.add('error');
    msg.textContent = data.error;
  }
  setTimeout(() => banner.classList.add('hidden'), 6000);
}

function _urlBase64ToUint8Array(base64) {
  const padding = '='.repeat((4 - base64.length % 4) % 4);
  const b64 = (base64 + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(b64);
  return Uint8Array.from([...raw].map(c => c.charCodeAt(0)));
}

// ── Data ──────────────────────────────────────────────────────────────────────

async function loadGoals() {
  const params = new URLSearchParams();
  if (state.filterStatus) params.set('status', state.filterStatus);
  if (state.filterCat)    params.set('category', state.filterCat);

  const res  = await fetch(`${API}?${params}`);
  const data = await res.json();

  state.goals = data.goals;
  state.stats = data.stats;

  renderGoals();
  renderStats();
  updateCategoryFilter();
}

// ── Render ─────────────────────────────────────────────────────────────────────

function renderGoals() {
  const list  = document.getElementById('goals-list');
  const today = new Date().toISOString().split('T')[0];

  if (state.goals.length === 0) {
    list.innerHTML = '<p class="empty">No goals yet — tap + Add to get started.</p>';
    return;
  }

  list.innerHTML = state.goals.map((g, i) => {
    let dueLabel  = '';
    let cardClass = 'goal-card';

    if (g.status === 'done') {
      cardClass += ' done';
      dueLabel   = g.due_date ? formatDate(g.due_date) : '';
    } else if (g.due_date) {
      if (g.due_date < today) {
        cardClass += ' overdue';
        dueLabel   = formatDate(g.due_date) + ' · overdue';
      } else if (g.due_date === today) {
        cardClass += ' today';
        dueLabel   = 'Due today';
      } else {
        dueLabel = formatDate(g.due_date);
      }
    }

    const statusBtn = g.status === 'pending'
      ? `<button class="btn-done"    onclick="markDone(${g.id})">Done</button>`
      : `<button class="btn-pending" onclick="markPending(${g.id})">Pending</button>`;

    return `
      <div class="${cardClass}">
        <div class="goal-header">
          <span class="goal-num">${i + 1}</span>
          <div class="goal-body">
            <span class="goal-title">${esc(g.title)}</span>
            ${g.description ? `<span class="goal-desc">${esc(g.description)}</span>` : ''}
          </div>
          <span class="cat-badge">${esc(g.category)}</span>
        </div>
        <div class="goal-footer">
          ${dueLabel ? `<span class="due-label">${dueLabel}</span>` : ''}
          <div class="goal-actions">
            ${statusBtn}
            <button class="btn-edit"   onclick="openEditModal(${g.id})">Edit</button>
            <button class="btn-delete" onclick="deleteGoal(${g.id})">Remove</button>
          </div>
        </div>
      </div>`;
  }).join('');
}

function renderStats() {
  const { pending, done } = state.stats;
  document.getElementById('stats').textContent = `${pending} pending  ·  ${done} done`;
}

function updateCategoryFilter() {
  const sel     = document.getElementById('filter-cat');
  const current = state.filterCat;
  sel.innerHTML =
    '<option value="">All Categories</option>' +
    state.stats.categories
      .map(c => `<option value="${esc(c)}"${c === current ? ' selected' : ''}>${esc(c)}</option>`)
      .join('');
}

// ── Modal ─────────────────────────────────────────────────────────────────────

function openAddModal() {
  state.editingId = null;
  document.getElementById('modal-title').textContent  = 'New Goal';
  document.getElementById('btn-save').textContent     = 'Add Goal';
  document.getElementById('input-title').value = '';
  document.getElementById('input-desc').value  = '';
  document.getElementById('input-cat').value   = 'general';
  document.getElementById('input-due').value   = '';
  document.getElementById('modal').classList.remove('hidden');
  document.getElementById('input-title').focus();
}

function openEditModal(id) {
  const goal = state.goals.find(g => g.id === id);
  if (!goal) return;
  state.editingId = id;
  document.getElementById('modal-title').textContent  = 'Edit Goal';
  document.getElementById('btn-save').textContent     = 'Save Changes';
  document.getElementById('input-title').value = goal.title;
  document.getElementById('input-desc').value  = goal.description;
  document.getElementById('input-cat').value   = goal.category;
  document.getElementById('input-due').value   = goal.due_date || '';
  document.getElementById('modal').classList.remove('hidden');
  document.getElementById('input-title').focus();
}

function closeModal() {
  document.getElementById('modal').classList.add('hidden');
}

// ── Actions ───────────────────────────────────────────────────────────────────

async function saveGoal() {
  const title = document.getElementById('input-title').value.trim();
  if (!title) {
    alert('Please enter a goal title.');
    return;
  }

  const payload = {
    title,
    description: document.getElementById('input-desc').value.trim(),
    category:    document.getElementById('input-cat').value.trim() || 'general',
    due_date:    document.getElementById('input-due').value || null,
  };

  if (state.editingId) {
    await fetch(`${API}/${state.editingId}`, {
      method:  'PUT',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });
  } else {
    await fetch(API, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });
  }

  closeModal();
  loadGoals();
}

async function markDone(id) {
  await fetch(`${API}/${id}/done`, { method: 'PATCH' });
  loadGoals();
}

async function markPending(id) {
  await fetch(`${API}/${id}/pending`, { method: 'PATCH' });
  loadGoals();
}

async function deleteGoal(id) {
  const goal = state.goals.find(g => g.id === id);
  if (!goal || !confirm(`Remove "${goal.title}"?`)) return;
  await fetch(`${API}/${id}`, { method: 'DELETE' });
  loadGoals();
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function formatDate(iso) {
  const [y, m, d] = iso.split('-');
  return `${m}-${d}-${y}`;
}

function esc(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
