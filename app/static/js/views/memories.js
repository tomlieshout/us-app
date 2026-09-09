import { api } from '../api.js';
import { escapeHtml, showToast, openModal, confirmDialog, formatRelativeDate } from '../utils.js';

export async function renderMemories(container) {
  container.innerHTML = `
    <h1 class="page-title">Memories</h1>
    <p class="page-subtitle">Moments you want to hold onto — added by either of you.</p>
    <button class="btn btn-primary btn-block" id="mem-add-btn">+ Add a Memory</button>
    <div id="mem-list" class="mt-16"></div>
  `;

  const list = container.querySelector('#mem-list');

  async function load() {
    list.innerHTML = '<div class="skeleton" style="height:100px;margin-bottom:10px;"></div>'.repeat(3);
    let data;
    try {
      data = await api.memories.list();
    } catch (err) {
      list.innerHTML = `<p class="text-muted" style="padding:20px 0;">${escapeHtml(err.message)}</p>`;
      return;
    }
    list.innerHTML = '';

    if (data.memories.length === 0) {
      list.innerHTML = `
        <div class="empty-state">
          <div class="empty-emoji">📸</div>
          <h3>Nothing here yet</h3>
          <p>Add your first shared memory.</p>
        </div>
      `;
      return;
    }

    data.memories.forEach((m) => list.appendChild(memoryCard(m, load)));
  }

  container.querySelector('#mem-add-btn').addEventListener('click', () => openMemoryForm(null, load));

  load();
}

function memoryCard(memory, onChange) {
  const card = document.createElement('button');
  card.className = 'card card-tap';
  card.style.cssText = 'display:block;width:100%;text-align:left;margin-bottom:10px;';

  const tagChips = (memory.tags || [])
    .map((t) => `<span class="chip chip-muted" style="margin-right:4px;">${escapeHtml(t)}</span>`)
    .join('');

  card.innerHTML = `
    <div class="status-row" style="margin-bottom:6px;">
      <span class="text-muted small">${memory.date ? escapeHtml(memory.date) : formatRelativeDate(memory.created_at)}</span>
    </div>
    <p style="font-weight:600;font-size:15px;">${escapeHtml(memory.title)}</p>
    ${memory.description ? `<p class="text-muted small mt-8">${escapeHtml(truncate(memory.description, 90))}</p>` : ''}
    ${tagChips ? `<div class="mt-8">${tagChips}</div>` : ''}
  `;
  card.addEventListener('click', () => openMemoryDetail(memory, onChange));
  return card;
}

function truncate(str, n) {
  if (!str) return '';
  return str.length > n ? str.slice(0, n).trim() + '…' : str;
}

function openMemoryDetail(memory, onChange) {
  const { body } = openModal('round-modal', { title: memory.title, render: () => '' });

  body.innerHTML = `
    <div class="status-row" style="margin-bottom:10px;">
      <span class="chip chip-muted">${memory.date ? escapeHtml(memory.date) : 'No date'}</span>
    </div>
    <p class="answer-text">${memory.description ? escapeHtml(memory.description) : '<span class="text-muted">No description.</span>'}</p>
    <div class="mt-16">${(memory.tags || []).map((t) => `<span class="chip chip-muted" style="margin-right:4px;">${escapeHtml(t)}</span>`).join('')}</div>
    <div class="flex-row mt-16" style="gap:8px;">
      <button class="btn btn-ghost" id="mem-edit-btn">Edit</button>
      <button class="btn btn-text" id="mem-delete-btn" style="color:var(--danger);margin-left:auto;">Delete</button>
    </div>
  `;

  body.querySelector('#mem-edit-btn').addEventListener('click', () => openMemoryForm(memory, onChange));
  body.querySelector('#mem-delete-btn').addEventListener('click', async () => {
    const ok = await confirmDialog({
      title: 'Delete this memory?',
      message: "This removes it for both of you. This can't be undone.",
      confirmLabel: 'Delete',
      danger: true,
    });
    if (!ok) return;
    try {
      await api.memories.remove(memory.id);
      showToast('Deleted');
      onChange();
    } catch (err) {
      showToast(err.message);
    }
  });
}

function openMemoryForm(memory, onChange) {
  const isEdit = Boolean(memory);
  const { body } = openModal('round-modal', { title: isEdit ? 'Edit Memory' : 'Add a Memory', render: () => '' });

  body.innerHTML = `
    <div class="field"><label>Title</label><input id="mem-title" type="text" maxlength="200" value="${isEdit ? escapeHtml(memory.title) : ''}" placeholder="Our first trip together"></div>
    <div class="field"><label>Date</label><input id="mem-date" type="date" value="${isEdit && memory.date ? memory.date : ''}"></div>
    <div class="field"><label>Description</label><textarea id="mem-description" rows="4" placeholder="That weekend when...">${isEdit && memory.description ? escapeHtml(memory.description) : ''}</textarea></div>
    <div class="field"><label>Tags (comma separated, optional)</label><input id="mem-tags" type="text" value="${isEdit ? escapeHtml((memory.tags || []).join(', ')) : ''}" placeholder="trip, milestone"></div>
    <button class="btn btn-primary btn-block" id="mem-save-btn">${isEdit ? 'Save Changes' : 'Add Memory'}</button>
  `;

  body.querySelector('#mem-save-btn').addEventListener('click', async () => {
    const title = body.querySelector('#mem-title').value.trim();
    if (!title) { showToast('Give it a title.'); return; }

    const payload = {
      title,
      date: body.querySelector('#mem-date').value || null,
      description: body.querySelector('#mem-description').value.trim(),
      tags: body.querySelector('#mem-tags').value.split(',').map((t) => t.trim()).filter(Boolean),
    };

    const btn = body.querySelector('#mem-save-btn');
    btn.disabled = true;
    try {
      if (isEdit) await api.memories.update(memory.id, payload);
      else await api.memories.create(payload);
      showToast(isEdit ? 'Saved ✓' : 'Added ✓');
      onChange();
    } catch (err) {
      showToast(err.message);
      btn.disabled = false;
    }
  });
}