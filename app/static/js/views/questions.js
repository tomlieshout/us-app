import { api } from '../api.js';
import { escapeHtml, showToast, openModal } from '../utils.js';
import { partnerMember } from '../state.js';
import { openActivityModal } from './round.js';

/**
 * The Questions/Browse tab. Category browsing is unchanged - you can
 * still open any category and pick any specific question by hand.
 *
 * Two additions:
 *  - An "Unanswered only" toggle inside each category list, since with a
 *    bank this size it gets hard to spot what you haven't done yet.
 *    "Answered" is per-user (see routes/questions.py) - a question your
 *    partner has answered is still unanswered for YOU until you answer it.
 *  - A "Waiting On You" card in the category grid: classic questions your
 *    partner has already answered and you haven't. Tapping one goes
 *    through the same play flow as any other question, so answering it
 *    completes that pending round and reveals immediately. Their answer
 *    is never sent until you've submitted your own.
 */

// Rendered alongside the real categories, but it's a discovery entry
// point rather than a category - it has no category key and its list
// comes from a different endpoint.
const PARTNER_CARD = {
  key: '__partner_answered__',
  emoji: '💌',
  label: 'Waiting On You',
  description: 'Questions they\'ve answered, ready for yours.',
};

export async function renderQuestions(container) {
  await renderCategoryGrid(container);
}

async function renderCategoryGrid(container) {
  container.innerHTML = `
    <h1 class="page-title">Questions</h1>
    <p class="page-subtitle">Browse by category and pick what to answer next.</p>
    <div class="category-grid">${Array(9).fill('<div class="skeleton" style="height:110px;border-radius:18px;"></div>').join('')}</div>
  `;

  let categories;
  try {
    categories = (await api.categories()).categories;
  } catch (err) {
    container.innerHTML = `<h1 class="page-title">Questions</h1><p class="text-muted mt-16">${escapeHtml(err.message)}</p>`;
    return;
  }

  const grid = document.createElement('div');
  grid.className = 'category-grid';

  [...categories, PARTNER_CARD].forEach((cat) => {
    const card = document.createElement('button');
    card.className = `category-card card-tap ${cat.locked ? 'locked' : ''}`;
    card.innerHTML = `
      <span class="emoji">${cat.emoji}</span>
      <span class="label">${escapeHtml(cat.label)}</span>
      <span class="desc">${escapeHtml(cat.description)}</span>
      ${cat.locked ? '<span class="lock-badge">🔒</span>' : ''}
    `;
    card.addEventListener('click', () => {
      if (cat.locked) {
        renderSpicyLocked(container);
      } else if (cat.key === PARTNER_CARD.key) {
        renderPartnerAnsweredList(container);
      } else {
        renderQuestionList(container, cat);
      }
    });
    grid.appendChild(card);
  });

  container.innerHTML = '<h1 class="page-title">Questions</h1><p class="page-subtitle">Browse by category and pick what to answer next.</p>';
  container.appendChild(grid);
}

function renderSpicyLocked(container) {
  container.innerHTML = `
    <div class="back-row"><button class="icon-btn" id="q-back"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg></button></div>
    <div class="empty-state">
      <div class="empty-emoji">🔒</div>
      <h3>Spicy is locked</h3>
      <p>Both of you need to opt in independently before this category unlocks. Head to Settings to turn it on for your side.</p>
      <button class="btn btn-primary mt-16" id="go-settings">Go to Settings</button>
    </div>
  `;
  container.querySelector('#q-back').addEventListener('click', () => renderCategoryGrid(container));
  container.querySelector('#go-settings').addEventListener('click', () => document.querySelector('.nav-btn[data-view="settings"]').click());
}

function listHeader(container, { emoji, label, description }) {
  const header = document.createElement('div');
  header.innerHTML = `
    <div class="back-row"><button class="icon-btn" id="q-back"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg></button></div>
    <h1 class="page-title">${emoji} ${escapeHtml(label)}</h1>
    <p class="page-subtitle">${escapeHtml(description)}</p>
  `;
  return header;
}

async function renderQuestionList(container, cat, unansweredOnly = false) {
  container.innerHTML = `
    <div class="back-row"><button class="icon-btn" id="q-back"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg></button></div>
    <h1 class="page-title">${cat.emoji} ${escapeHtml(cat.label)}</h1>
    <p class="page-subtitle">${escapeHtml(cat.description)}</p>
    <div class="skeleton" style="height:300px;"></div>
  `;
  container.querySelector('#q-back').addEventListener('click', () => renderCategoryGrid(container));

  let questions;
  try {
    questions = (await api.questions(cat.key, { unansweredOnly })).questions;
  } catch (err) {
    showToast(err.message);
    return;
  }

  container.innerHTML = '';
  container.appendChild(listHeader(container, cat));
  container.querySelector('#q-back').addEventListener('click', () => renderCategoryGrid(container));

  // Filter toggle. Re-fetches rather than hiding client-side, so the
  // server stays the single source of truth for what counts as answered.
  const filterRow = document.createElement('div');
  filterRow.style.cssText = 'display:flex;gap:8px;padding-bottom:4px;';
  [
    { key: false, label: 'All questions' },
    { key: true, label: 'Unanswered only' },
  ].forEach(({ key, label }) => {
    const chip = document.createElement('button');
    chip.className = `chip ${key === unansweredOnly ? '' : 'chip-muted'}`;
    chip.style.cssText = 'white-space:nowrap;border:none;';
    chip.textContent = label;
    chip.addEventListener('click', () => {
      if (key === unansweredOnly) return;
      renderQuestionList(container, cat, key);
    });
    filterRow.appendChild(chip);
  });
  container.appendChild(filterRow);

  if (cat.key === 'spicy') {
    const matchesBtn = document.createElement('button');
    matchesBtn.className = 'btn btn-secondary btn-block mt-8';
    matchesBtn.textContent = '🔥 Find Your Matches';
    matchesBtn.addEventListener('click', showSpicyMatches);
    container.appendChild(matchesBtn);
    const caption = document.createElement('p');
    caption.className = 'text-muted small mt-8';
    caption.style.textAlign = 'center';
    caption.textContent = "Reflects Spicy questions answered so far - matching for questions played just now is being connected up next.";
    container.appendChild(caption);
  }

  const listCard = document.createElement('div');
  listCard.className = 'card mt-16';

  if (questions.length === 0) {
    listCard.innerHTML = unansweredOnly
      ? `<div class="empty-state" style="padding:30px 10px;"><div class="empty-emoji">✅</div><p>You've answered everything in here.</p></div>`
      : `<div class="empty-state" style="padding:30px 10px;"><div class="empty-emoji">💭</div><p>No questions here yet.</p></div>`;
  } else {
    questions.forEach((q) => listCard.appendChild(questionRow(q, { showPlayedState: true })));
  }
  container.appendChild(listCard);
}

async function renderPartnerAnsweredList(container) {
  const partner = partnerMember();
  const meta = {
    emoji: PARTNER_CARD.emoji,
    label: PARTNER_CARD.label,
    description: partner
      ? `${partner.name} has answered these. Answer one and you'll both see the results.`
      : "Your partner has answered these. Answer one and you'll both see the results.",
  };

  container.innerHTML = `
    <div class="back-row"><button class="icon-btn" id="q-back"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg></button></div>
    <h1 class="page-title">${meta.emoji} ${escapeHtml(meta.label)}</h1>
    <p class="page-subtitle">${escapeHtml(meta.description)}</p>
    <div class="skeleton" style="height:300px;"></div>
  `;
  container.querySelector('#q-back').addEventListener('click', () => renderCategoryGrid(container));

  let questions;
  try {
    questions = (await api.partnerAnsweredQuestions()).questions;
  } catch (err) {
    showToast(err.message);
    return;
  }

  container.innerHTML = '';
  container.appendChild(listHeader(container, meta));
  container.querySelector('#q-back').addEventListener('click', () => renderCategoryGrid(container));

  const listCard = document.createElement('div');
  listCard.className = 'card mt-16';

  if (questions.length === 0) {
    // Purely "nothing to catch up on" - never framed as a comparison of
    // who has or hasn't been answering more.
    listCard.innerHTML = `
      <div class="empty-state" style="padding:30px 10px;">
        <div class="empty-emoji">📭</div>
        <p>Nothing waiting right now. Browse a category to start something new.</p>
      </div>
    `;
  } else {
    // Only the question text is rendered - the partner's answer isn't in
    // this payload at all (see routes/questions.py's partner-answered).
    questions.forEach((q) => listCard.appendChild(questionRow(q, { showPlayedState: false })));
  }
  container.appendChild(listCard);
}

function questionRow(q, { showPlayedState }) {
  const item = document.createElement('div');
  item.className = 'question-list-item';
  item.innerHTML = `
    <div style="flex:1;" class="q-tap">
      <div class="qtext">${escapeHtml(q.text)}</div>
      <div class="qmeta">${showPlayedState
        ? (q.already_played ? 'Answered' : 'Not answered yet')
        : 'Answer this to see what they said'}</div>
    </div>
    <button class="fav-btn ${q.is_favourite ? 'active' : ''}">${q.is_favourite ? '❤️' : '🤍'}</button>
  `;
  item.querySelector('.q-tap').addEventListener('click', async () => {
    try {
      const activity = await api.activities.play(q.id);
      openActivityModal(activity.activity_id);
    } catch (err) {
      showToast(err.message);
    }
  });
  const favBtn = item.querySelector('.fav-btn');
  favBtn.addEventListener('click', async () => {
    try {
      if (favBtn.classList.contains('active')) {
        await api.removeFavourite(q.id);
        favBtn.classList.remove('active');
        favBtn.textContent = '🤍';
      } else {
        await api.addFavourite(q.id);
        favBtn.classList.add('active');
        favBtn.textContent = '❤️';
      }
    } catch (err) {
      showToast(err.message);
    }
  });
  return item;
}

async function showSpicyMatches() {
  const { body } = openModal('round-modal', { title: '🔥 Find Your Matches', render: () => '<div class="skeleton" style="height:160px;"></div>' });
  try {
    const data = await api.spicyMatches();
    body.innerHTML = `
      <p class="text-muted small mt-8">Based on ${data.explored_together} question${data.explored_together === 1 ? '' : 's'} you've both answered.</p>
      ${data.mutual_matches.length > 0 ? `
        <p class="section-title">You both said yes to</p>
        ${data.mutual_matches.map((m) => `<div class="card" style="padding:14px;margin-bottom:8px;">❤️ ${escapeHtml(m)}</div>`).join('')}
      ` : `<div class="empty-state" style="padding:24px 10px;"><div class="empty-emoji">🔥</div><p>No mutual matches yet — answer a few more Intimate or Adventurous questions together.</p></div>`}
      ${data.discuss_count > 0 ? `<div class="card mt-16" style="background:var(--warn-soft);border:none;"><p style="color:var(--warn);font-size:13.5px;font-weight:600;">💬 You had different comfort levels on ${data.discuss_count} topic${data.discuss_count === 1 ? '' : 's'} — might be worth a conversation.</p></div>` : ''}
    `;
  } catch (err) {
    body.innerHTML = `<p class="text-muted" style="padding:20px 0;">${escapeHtml(err.message)}</p>`;
  }
}
