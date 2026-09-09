import { api } from '../api.js';
import { escapeHtml, showToast, categoryEmoji, formatRelativeDate } from '../utils.js';
import { isSpicyUnlocked } from '../state.js';
import { openActivityModal } from './round.js';

const FILTERS = [
  { key: '', label: 'All' },
  { key: 'relationship', label: '❤️ Relationship' },
  { key: 'know_me', label: '🧠 Know Me' },
  { key: 'future', label: '🔮 Future' },
  { key: 'random', label: '😂 Random' },
  { key: 'deep', label: '💭 Deep' },
  { key: 'memories', label: '📸 Memories' },
  { key: 'longdistance', label: '🌍 Distance' },
];

export async function renderHistory(container) {
  const filters = isSpicyUnlocked() ? [...FILTERS, { key: 'spicy', label: '🔥 Spicy' }] : FILTERS;
  let activeFilter = '';
  let page = 1;

  container.innerHTML = `
    <h1 class="page-title">History</h1>
    <p class="page-subtitle">Your private collection of revealed questions.</p>
    <div id="mem-filters" style="display:flex;gap:8px;overflow-x:auto;padding-bottom:4px;margin-bottom:14px;"></div>
    <div id="mem-list"></div>
    <button class="btn btn-ghost btn-block mt-16 hidden" id="mem-more">Load more</button>
  `;

  const filterRow = container.querySelector('#mem-filters');
  filters.forEach((f) => {
    const chip = document.createElement('button');
    chip.className = `chip ${f.key === activeFilter ? '' : 'chip-muted'}`;
    chip.style.whiteSpace = 'nowrap';
    chip.style.border = 'none';
    chip.textContent = f.label;
    chip.addEventListener('click', () => {
      activeFilter = f.key;
      page = 1;
      Array.from(filterRow.children).forEach((c) => c.classList.add('chip-muted'));
      chip.classList.remove('chip-muted');
      load(true);
    });
    if (f.key === '') chip.classList.remove('chip-muted');
    filterRow.appendChild(chip);
  });

  const list = container.querySelector('#mem-list');
  const moreBtn = container.querySelector('#mem-more');

  async function load(reset) {
    if (reset) {
      list.innerHTML = '<div class="skeleton" style="height:100px;margin-bottom:10px;"></div>'.repeat(3);
    }
    let data;
    try {
      data = await api.activities.history(page, activeFilter || undefined);
    } catch (err) {
      showToast(err.message);
      return;
    }
    if (reset) list.innerHTML = '';

    if (data.activities.length === 0 && page === 1) {
      list.innerHTML = `
        <div class="empty-state">
          <div class="empty-emoji">💭</div>
          <h3>Your history will appear here</h3>
          <p>Answer your first question together to start building it.</p>
        </div>
      `;
      moreBtn.classList.add('hidden');
      return;
    }

    data.activities.forEach((a) => list.appendChild(historyCard(a)));
    moreBtn.classList.toggle('hidden', !data.has_more);
  }

  moreBtn.addEventListener('click', () => { page += 1; load(false); });

  load(true);
}

function historyCard(activity) {
  const card = document.createElement('button');
  card.className = 'card card-tap';
  card.style.display = 'block';
  card.style.width = '100%';
  card.style.textAlign = 'left';
  const submission = activity.my_submission;
  const preview = submission && !submission.is_private
    ? truncate(submission.payload.answer_text ?? submission.payload.answer_option, 60)
    : null;
  card.innerHTML = `
    <div class="status-row" style="margin-bottom:6px;">
      <span class="chip chip-muted">${categoryEmoji(activity.content.category)} ${formatRelativeDate(activity.created_at)}</span>
    </div>
    <p style="font-weight:600;font-size:15px;line-height:1.4;">${escapeHtml(activity.content.prompt)}</p>
    ${preview ? `<p class="text-muted small mt-8">"${escapeHtml(preview)}"</p>` : ''}
  `;
  card.addEventListener('click', () => openActivityModal(activity.activity_id));
  return card;
}

function truncate(str, n) {
  if (!str) return '';
  return str.length > n ? str.slice(0, n).trim() + '…' : str;
}
