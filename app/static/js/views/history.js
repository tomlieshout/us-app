import { api } from '../api.js';
import { escapeHtml, showToast, categoryEmoji, formatRelativeDate } from '../utils.js';
import { isSpicyUnlocked, partnerMember } from '../state.js';
import { openActivityModal } from './round.js';

/**
 * The general History page - now the same three-way "Past Answers"
 * structure the three games use (see views/past_answers.js), on top of
 * the category filters this page already had:
 *   Mine      - questions I've personally answered, mine shown.
 *   Mutual    - questions we've both answered (this page's original,
 *               only-ever view).
 *   Partner's - questions my partner has answered that I haven't. The
 *               question is shown so I can go answer it; their answer is
 *               never included in the response until I've submitted my
 *               own (app/services/activity_privacy.py), and this view
 *               renders nothing but the prompt regardless.
 *
 * It doesn't reuse renderPastAnswers() itself because this page is a
 * full view with category filters rather than a sheet, but both go
 * through the same GET /api/activities/history?view= endpoint - the
 * shared mechanism is the endpoint, not the widget.
 */

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

const VIEWS = [
  { key: 'mine', label: 'Mine' },
  { key: 'mutual', label: 'Mutual' },
  { key: 'partner', label: "Partner's" },
];

export async function renderHistory(container) {
  const filters = isSpicyUnlocked() ? [...FILTERS, { key: 'spicy', label: '🔥 Spicy' }] : FILTERS;
  let activeFilter = '';
  let view = 'mutual';
  let page = 1;

  container.innerHTML = `
    <h1 class="page-title">Past Answers</h1>
    <p class="page-subtitle" id="mem-subtitle"></p>
    <div id="mem-views" style="display:flex;gap:8px;overflow-x:auto;padding-bottom:4px;margin-bottom:10px;" role="tablist"></div>
    <div id="mem-filters" style="display:flex;gap:8px;overflow-x:auto;padding-bottom:4px;margin-bottom:14px;"></div>
    <div id="mem-list"></div>
    <button class="btn btn-ghost btn-block mt-16 hidden" id="mem-more">Load more</button>
  `;

  const subtitle = container.querySelector('#mem-subtitle');
  const viewRow = container.querySelector('#mem-views');
  const filterRow = container.querySelector('#mem-filters');
  const list = container.querySelector('#mem-list');
  const moreBtn = container.querySelector('#mem-more');

  const SUBTITLES = {
    mine: 'Everything you\'ve answered, whether or not they have yet.',
    mutual: 'Your private collection of revealed questions.',
    partner: 'Questions waiting on you — answer one to see what they said.',
  };

  VIEWS.forEach((v) => {
    const chip = document.createElement('button');
    chip.className = `chip ${v.key === view ? '' : 'chip-muted'}`;
    chip.style.cssText = 'white-space:nowrap;border:none;';
    chip.dataset.view = v.key;
    chip.textContent = v.label;
    chip.setAttribute('role', 'tab');
    chip.addEventListener('click', () => {
      if (view === v.key) return;
      view = v.key;
      page = 1;
      Array.from(viewRow.children).forEach((c) => {
        c.classList.toggle('chip-muted', c.dataset.view !== view);
        c.setAttribute('aria-selected', c.dataset.view === view ? 'true' : 'false');
      });
      subtitle.textContent = SUBTITLES[view];
      load(true);
    });
    viewRow.appendChild(chip);
  });
  subtitle.textContent = SUBTITLES[view];

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

  function emptyState() {
    const partner = partnerMember();
    const partnerName = partner ? escapeHtml(partner.name) : 'your partner';
    const copy = {
      mine: { emoji: '✍️', heading: 'Nothing answered yet', body: 'Answer your first question and it\'ll show up here straight away.' },
      mutual: { emoji: '💭', heading: 'Your history will appear here', body: 'Answer your first question together to start building it.' },
      // Framed as "nothing to catch up on" - never as a comment on how
      // much either of them has played.
      partner: { emoji: '📭', heading: 'Nothing to catch up on', body: `Nothing waiting from ${partnerName} right now.` },
    }[view];
    return `<div class="empty-state"><div class="empty-emoji">${copy.emoji}</div><h3>${copy.heading}</h3><p>${copy.body}</p></div>`;
  }

  async function load(reset) {
    if (reset) {
      list.innerHTML = '<div class="skeleton" style="height:100px;margin-bottom:10px;"></div>'.repeat(3);
      moreBtn.classList.add('hidden');
    }
    let data;
    try {
      data = await api.activities.history({ page, category: activeFilter || undefined, view });
    } catch (err) {
      showToast(err.message);
      if (reset) list.innerHTML = '';
      return;
    }
    if (reset) list.innerHTML = '';

    if (data.activities.length === 0 && page === 1) {
      list.innerHTML = emptyState();
      moreBtn.classList.add('hidden');
      return;
    }

    data.activities.forEach((a) => list.appendChild(historyCard(a, view)));
    moreBtn.classList.toggle('hidden', !data.has_more);
  }

  moreBtn.addEventListener('click', () => { page += 1; load(false); });

  load(true);
}

function historyCard(activity, view) {
  const card = document.createElement('button');
  card.className = 'card card-tap';
  card.style.display = 'block';
  card.style.width = '100%';
  card.style.textAlign = 'left';

  // Only ever my own submission is previewed. In the "Partner's" view
  // there is no partner submission in the payload at all - the server
  // omits it pre-reveal - and nothing here goes looking for one.
  const submission = activity.my_submission;
  const preview = submission && !submission.is_private
    ? truncate(submission.payload.answer_text ?? submission.payload.answer_option, 60)
    : null;

  const note = {
    mine: activity.revealed ? null : 'Waiting on your partner to answer.',
    mutual: null,
    partner: 'Answer this to see what they said.',
  }[view];

  card.innerHTML = `
    <div class="status-row" style="margin-bottom:6px;">
      <span class="chip chip-muted">${categoryEmoji(activity.content.category)} ${formatRelativeDate(activity.created_at)}</span>
    </div>
    <p style="font-weight:600;font-size:15px;line-height:1.4;">${escapeHtml(activity.content.prompt)}</p>
    ${preview ? `<p class="text-muted small mt-8">"${escapeHtml(preview)}"</p>` : ''}
    ${note ? `<p class="text-muted small mt-8">${escapeHtml(note)}</p>` : ''}
  `;
  card.addEventListener('click', () => openActivityModal(activity.activity_id));
  return card;
}

function truncate(str, n) {
  if (!str) return '';
  return str.length > n ? str.slice(0, n).trim() + '…' : str;
}
