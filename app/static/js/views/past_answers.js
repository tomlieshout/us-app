import { api } from '../api.js';
import { escapeHtml, showToast } from '../utils.js';
import { partnerMember } from '../state.js';

/**
 * "Past Answers" - the three-way history view, shared by Would You
 * Rather, Know Each Other, Who Would, and the general History page.
 * Replaces the earlier single-view "Past Rounds" list (game_history.js).
 *
 * Three switchable views, all served by the same GET
 * /api/activities/history endpoint (see app/routes/activities.py) rather
 * than four separate implementations:
 *   Mine     - questions I've personally answered, whether or not my
 *              partner has yet.
 *   Mutual   - questions we've both answered, shown like the reveal screen.
 *   Partner's- questions my partner has answered that I haven't. The
 *              question is shown so I can go answer it; their answer is
 *              never here, because the server never sends it pre-reveal
 *              (serialize_activity simply omits partner_submission). This
 *              view renders only fields that are always present, so there
 *              is no client-side path that could display it either.
 *
 * The generic/type-specific split mirrors services/activities/base.py:
 * fetch, tabs, pagination and the Partner's view live here once; each
 * caller supplies renderMutual()/describeMine() for its own game's detail.
 */

const VIEWS = [
  { key: 'mine', label: 'Mine' },
  { key: 'mutual', label: 'Mutual' },
  { key: 'partner', label: "Partner's" },
];

export function renderPastAnswers(body, {
  activityType,
  title = 'Past Answers',
  renderMutual,
  describeMine,
  onBack,
  onOpenActivity,
  initialView = 'mine',
}) {
  body.innerHTML = '';

  const header = document.createElement('div');
  header.className = 'back-row';
  header.innerHTML = `<button class="icon-btn" id="pa-back" aria-label="Back"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg></button>`;
  body.appendChild(header);
  header.querySelector('#pa-back').addEventListener('click', onBack);

  const heading = document.createElement('h2');
  heading.style.cssText = 'font-size:19px;margin:4px 0 14px;';
  heading.textContent = title;
  body.appendChild(heading);

  const tabs = document.createElement('div');
  tabs.style.cssText = 'display:flex;gap:8px;overflow-x:auto;padding-bottom:4px;';
  tabs.setAttribute('role', 'tablist');
  body.appendChild(tabs);

  const list = document.createElement('div');
  list.className = 'mt-16';
  body.appendChild(list);

  const moreBtn = document.createElement('button');
  moreBtn.className = 'btn btn-ghost btn-block mt-16 hidden';
  moreBtn.textContent = 'Load more';
  body.appendChild(moreBtn);

  let view = initialView;
  let page = 1;

  VIEWS.forEach((v) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'chip';
    btn.style.cssText = 'white-space:nowrap;border:none;';
    btn.dataset.view = v.key;
    btn.textContent = v.label;
    btn.setAttribute('role', 'tab');
    btn.addEventListener('click', () => {
      if (view === v.key) return;
      view = v.key;
      page = 1;
      syncTabs();
      load(true);
    });
    tabs.appendChild(btn);
  });

  function syncTabs() {
    tabs.querySelectorAll('.chip').forEach((b) => {
      const active = b.dataset.view === view;
      b.classList.toggle('chip-muted', !active);
      b.setAttribute('aria-selected', active ? 'true' : 'false');
    });
  }

  function emptyState() {
    const partner = partnerMember();
    const partnerName = partner ? escapeHtml(partner.name) : 'Your partner';
    const copy = {
      mine: { emoji: '✍️', heading: 'Nothing answered yet', body: 'Answer a question and it\'ll show up here straight away.' },
      mutual: { emoji: '💞', heading: 'Nothing revealed yet', body: 'Once you\'ve both answered the same question, it\'ll appear here.' },
      // Deliberately framed as "nothing to catch up on", never as a
      // comment on how much either partner has or hasn't played.
      partner: { emoji: '📭', heading: 'Nothing to catch up on', body: `Nothing waiting from ${partnerName} right now.` },
    }[view];
    return `<div class="empty-state"><div class="empty-emoji">${copy.emoji}</div><h3>${copy.heading}</h3><p>${copy.body}</p></div>`;
  }

  function renderMineItem(activity) {
    const card = document.createElement('div');
    card.className = 'card mt-8';
    card.style.padding = '14px';
    const summary = describeMine ? describeMine(activity) : '';
    card.innerHTML = `
      <p class="qtext">${escapeHtml(activity.content.prompt)}</p>
      ${summary ? `<p class="text-muted small mt-8">${escapeHtml(summary)}</p>` : ''}
      ${activity.revealed ? '' : '<p class="text-muted small mt-8">Waiting on your partner to answer.</p>'}
    `;
    return card;
  }

  function renderPartnerItem(activity) {
    // Renders the question only. There is no partner answer in this
    // payload to render even if we wanted to - the server omits it until
    // the current user has submitted their own (activity_privacy.py).
    const card = document.createElement('div');
    card.className = 'card mt-8';
    card.style.padding = '14px';
    card.innerHTML = `
      <p class="qtext">${escapeHtml(activity.content.prompt)}</p>
      <p class="text-muted small mt-8">Answer this to see what they said.</p>
    `;
    if (onOpenActivity) {
      const btn = document.createElement('button');
      btn.className = 'btn btn-secondary btn-block mt-8';
      btn.textContent = 'Answer it';
      btn.addEventListener('click', () => onOpenActivity(activity));
      card.appendChild(btn);
    }
    return card;
  }

  function itemFor(activity) {
    if (view === 'mutual') {
      return renderMutual ? renderMutual(activity) : renderMineItem(activity);
    }
    if (view === 'partner') return renderPartnerItem(activity);
    return renderMineItem(activity);
  }

  async function load(reset) {
    if (reset) {
      list.innerHTML = '<div class="skeleton" style="height:90px;margin-bottom:10px;"></div>'.repeat(3);
      moreBtn.classList.add('hidden');
    }
    let data;
    try {
      data = await api.activities.history({ page, activityType, view });
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

    data.activities.forEach((a) => list.appendChild(itemFor(a)));
    moreBtn.classList.toggle('hidden', !data.has_more);
  }

  moreBtn.addEventListener('click', () => { page += 1; load(false); });

  syncTabs();
  load(true);
}
