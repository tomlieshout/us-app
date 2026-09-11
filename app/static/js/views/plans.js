import { api } from '../api.js';
import { escapeHtml, openModal, closeModal, showToast, confirmDialog } from '../utils.js';
import { meMember } from '../state.js';

const BACK_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>';

export async function renderPlans(container) {
  await renderCategoryGrid(container);
}

async function renderCategoryGrid(container) {
  container.innerHTML = `
    <h1 class="page-title">Plans</h1>
    <p class="page-subtitle">Movies, dates, trips, wishlist ideas - everything you want to do together, sorted.</p>
    <div class="category-grid">${Array(6).fill('<div class="skeleton" style="height:110px;border-radius:18px;"></div>').join('')}</div>
  `;

  let categories;
  try {
    categories = (await api.plans.categories()).categories;
  } catch (err) {
    container.innerHTML = `<h1 class="page-title">Plans</h1><p class="text-muted mt-16">${escapeHtml(err.message)}</p>`;
    return;
  }

  const grid = document.createElement('div');
  grid.className = 'category-grid';
  categories.forEach((cat) => {
    const card = document.createElement('button');
    card.className = 'category-card card-tap';
    card.innerHTML = `
      <span class="emoji">${cat.emoji}</span>
      <span class="label">${escapeHtml(cat.label)}</span>
      <span class="desc">${cat.count} item${cat.count === 1 ? '' : 's'}</span>
    `;
    card.addEventListener('click', () => renderPlanList(container, cat));
    grid.appendChild(card);
  });

  container.innerHTML = '<h1 class="page-title">Plans</h1><p class="page-subtitle">Movies, dates, trips, wishlist ideas - everything you want to do together, sorted.</p>';
  container.appendChild(grid);

  const addBtn = document.createElement('button');
  addBtn.className = 'btn btn-primary btn-block mt-16';
  addBtn.textContent = '+ Add a Plan';
  addBtn.addEventListener('click', () => openPlanForm({ onSaved: () => renderCategoryGrid(container) }));
  container.appendChild(addBtn);
}

async function renderPlanList(container, cat) {
  container.innerHTML = `
    <div class="back-row"><button class="icon-btn" id="p-back">${BACK_ICON}</button></div>
    <h1 class="page-title">${cat.emoji} ${escapeHtml(cat.label)}</h1>
    <div class="skeleton" style="height:260px;"></div>
  `;
  container.querySelector('#p-back').addEventListener('click', () => renderCategoryGrid(container));

  await loadAndRenderList(container, cat);
}

async function loadAndRenderList(container, cat) {
  let plans;
  try {
    plans = (await api.plans.list({ category: cat.key })).plans;
  } catch (err) {
    showToast(err.message);
    return;
  }

  const header = document.createElement('div');
  header.innerHTML = `
    <div class="back-row"><button class="icon-btn" id="p-back">${BACK_ICON}</button></div>
    <h1 class="page-title">${cat.emoji} ${escapeHtml(cat.label)}</h1>
  `;

  container.innerHTML = '';
  container.appendChild(header);
  container.querySelector('#p-back').addEventListener('click', () => renderCategoryGrid(container));

  const addBtn = document.createElement('button');
  addBtn.className = 'btn btn-primary btn-block mt-8';
  addBtn.textContent = `+ Add to ${cat.label}`;
  addBtn.addEventListener('click', () => openPlanForm({ category: cat, onSaved: () => loadAndRenderList(container, cat) }));
  container.appendChild(addBtn);

  const listCard = document.createElement('div');
  listCard.className = 'card mt-16';

  if (plans.length === 0) {
    listCard.innerHTML = `<div class="empty-state" style="padding:30px 10px;"><div class="empty-emoji">${cat.emoji}</div><p>Nothing here yet.</p></div>`;
  } else {
    // Not-done items first, most recently updated first within each group.
    const sorted = [...plans].sort((a, b) => {
      if ((a.status === 'done') !== (b.status === 'done')) return a.status === 'done' ? 1 : -1;
      return new Date(b.updated_at) - new Date(a.updated_at);
    });
    sorted.forEach((plan) => listCard.appendChild(renderPlanItem(plan, cat, () => loadAndRenderList(container, cat))));
  }
  container.appendChild(listCard);
}

function statusLabel(status) {
  return { someday: 'Someday', want_to_do: 'Want to do', planned: 'Planned', done: 'Done' }[status] || status;
}

function renderPlanItem(plan, cat, onChange) {
  const me = meMember();
  const isOwner = me && plan.added_by_id === me.id;
  const isMutable = !plan.is_private || isOwner;
  const isDone = plan.status === 'done';

  const item = document.createElement('div');
  item.className = `plan-item ${isDone ? 'is-done' : ''}`;

  if (plan.hidden) {
    item.innerHTML = `
      <span class="plan-check"></span>
      <div class="plan-body">
        <div class="plan-title">🔒 Private</div>
        <div class="plan-meta">Added by ${escapeHtml(plan.added_by_name || 'your partner')} · <span class="chip chip-muted" style="padding:2px 8px;">${statusLabel(plan.status)}</span></div>
      </div>
    `;
    return item;
  }

  const check = document.createElement('button');
  check.className = `plan-check ${isDone ? 'checked' : ''}`;
  check.innerHTML = isDone ? '✓' : '';
  check.setAttribute('aria-label', isDone ? 'Mark not done' : 'Mark done');
  if (isMutable) {
    check.addEventListener('click', async () => {
      try {
        await api.plans.update(plan.id, { status: isDone ? 'planned' : 'done' });
        onChange();
      } catch (err) {
        showToast(err.message);
      }
    });
  } else {
    check.disabled = true;
    check.style.opacity = '0.4';
  }
  item.appendChild(check);

  const body = document.createElement('div');
  body.className = 'plan-body';
  body.innerHTML = `
    <div class="plan-title">${escapeHtml(plan.title)}</div>
    ${plan.matched ? '<div class="plan-match-badge">❤️ YOU BOTH WANT THIS!</div>' : ''}
    ${plan.notes ? `<div class="plan-notes">${escapeHtml(plan.notes)}</div>` : ''}
    <div class="plan-meta">
      ${escapeHtml(plan.added_by_name || '')}${plan.is_private ? ' · 🔒 private' : ''} ·
      <span class="chip chip-muted" style="padding:2px 8px;">${statusLabel(plan.status)}</span>
    </div>
  `;
  if (isMutable) {
    body.style.cursor = 'pointer';
    body.addEventListener('click', () => openPlanForm({ plan, category: cat, onSaved: onChange, onDeleted: onChange }));
  }
  item.appendChild(body);

  return item;
}

function openPlanForm({ plan, category, onSaved, onDeleted }) {
  const isEdit = !!plan;
  const { body } = openModal('round-modal', {
    title: isEdit ? 'Edit Plan' : 'Add a Plan',
    render: () => '<div class="skeleton" style="height:320px;"></div>',
  });

  Promise.all([api.plans.categories(), api.plans.statuses()])
    .then(([catData, statusData]) => renderForm(body, catData.categories, statusData.statuses))
    .catch((err) => { body.innerHTML = `<p class="text-muted" style="padding:20px 0;">${escapeHtml(err.message)}</p>`; });

  function renderForm(body, categories, statuses) {
    const selectedCategory = plan ? plan.category : (category ? category.key : categories[0].key);
    body.innerHTML = `
      <div class="field">
        <label>Title</label>
        <input type="text" id="pl-title" maxlength="200" value="${escapeHtml(plan ? plan.title : '')}" placeholder="What's the plan?">
      </div>
      <div class="field">
        <label>Category</label>
        <select id="pl-category">
          ${categories.map((c) => `<option value="${c.key}" ${c.key === selectedCategory ? 'selected' : ''}>${escapeHtml(c.label)}</option>`).join('')}
        </select>
      </div>
      <div class="field">
        <label>Status</label>
        <select id="pl-status">
          ${statuses.map((s) => `<option value="${s.key}" ${plan && plan.status === s.key ? 'selected' : (!plan && s.key === 'someday' ? 'selected' : '')}>${escapeHtml(s.label)}</option>`).join('')}
        </select>
      </div>
      <div class="field">
        <label>Notes (optional)</label>
        <textarea id="pl-notes" rows="3" maxlength="1000" placeholder="Any details...">${escapeHtml(plan && plan.notes ? plan.notes : '')}</textarea>
      </div>
      <div class="settings-row" style="padding:0 0 14px;border:none;">
        <div class="row-label">🔒 Keep this private</div>
        <button class="toggle ${plan && plan.is_private ? 'on' : ''}" id="pl-private" ${plan && plan.added_by_id !== (meMember() || {}).id ? 'disabled' : ''}></button>
      </div>
      <button class="btn btn-primary btn-block" id="pl-save">${isEdit ? 'Save Changes' : 'Add Plan'}</button>
      ${isEdit ? '<button class="btn btn-text btn-block mt-8" id="pl-delete" style="color:var(--danger);">Delete</button>' : ''}
    `;

    const titleInput = body.querySelector('#pl-title');
    const categorySelect = body.querySelector('#pl-category');
    const statusSelect = body.querySelector('#pl-status');
    const notesInput = body.querySelector('#pl-notes');
    const privateToggle = body.querySelector('#pl-private');
    const saveBtn = body.querySelector('#pl-save');

    if (!privateToggle.disabled) {
      privateToggle.addEventListener('click', () => privateToggle.classList.toggle('on'));
    }

    saveBtn.addEventListener('click', async () => {
      const title = titleInput.value.trim();
      if (!title) { showToast('Give it a title.'); return; }

      const payload = {
        title,
        category: categorySelect.value,
        status: statusSelect.value,
        notes: notesInput.value.trim(),
      };
      if (!privateToggle.disabled) payload.is_private = privateToggle.classList.contains('on');

      saveBtn.disabled = true;
      try {
        if (isEdit) await api.plans.update(plan.id, payload);
        else await api.plans.create(payload);
        showToast(isEdit ? 'Saved ✓' : 'Added ✓');
        closeModal('round-modal');
        if (onSaved) onSaved();
      } catch (err) {
        showToast(err.message);
        saveBtn.disabled = false;
      }
    });

    const deleteBtn = body.querySelector('#pl-delete');
    if (deleteBtn) {
      deleteBtn.addEventListener('click', async () => {
        const ok = await confirmDialog({
          title: 'Delete this plan?',
          message: 'This can\'t be undone.',
          confirmLabel: 'Delete',
          danger: true,
        });
        if (!ok) return;
        try {
          await api.plans.remove(plan.id);
          showToast('Deleted');
          closeModal('round-modal');
          if (onDeleted) onDeleted();
        } catch (err) {
          showToast(err.message);
        }
      });
    }
  }
}
