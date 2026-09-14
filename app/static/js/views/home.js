import { api } from '../api.js';
import { escapeHtml, showToast, formatRelativeDate } from '../utils.js';
import { partnerMember } from '../state.js';
import { openActivityModal } from './round.js';
import { openWyrGame } from './wyr.js';
import { openKnowEachOtherGame } from './know_each_other.js';
import { openWhoWouldGame } from './who_would.js';
import { openAppreciationMenu } from './appreciation.js';
import { openChallengesMenu } from './challenges.js';
import { openPlanForm } from './plans.js';
import { renderChampionBanner } from './stats.js';

/** Home: the app's daily starting point, not a nav menu. Everything here
 * is aggregated from systems that already exist (see app/services/home.py) -
 * no new data model, no new scoring, no new privacy rules. This file's
 * only job is to render what GET /api/home already computed and route
 * taps into the SAME modals/forms every other tab already uses, so a
 * "today's activity" tap opens the exact same experience it would from
 * Games/Questions/Challenges/Plans - nothing is reimplemented here. */

// "game" lane sub-rotates across these three - see _GAME_TYPES in
// app/services/home.py. Emoji Story is deliberately not part of the daily
// rotation there, so it never needs an opener here either.
const GAME_OPENERS = {
  would_you_rather: openWyrGame,
  know_each_other: openKnowEachOtherGame,
  who_would: openWhoWouldGame,
};

const FEED_ICON = {
  game_completed: '🎮',
  appreciation_received: '💌',
  plan_added: '📝',
  shared_match: '🔥',
  challenge_completed: '🎲',
  memory_created: '📸',
};

export async function renderHome(container) {
  container.innerHTML = `
    <h1 class="page-title">Home</h1>
    <div class="card hero-card skeleton" style="height:170px;border:none;"></div>
    <div class="card skeleton mt-16" style="height:90px;"></div>
  `;

  let data;
  try {
    data = await api.home();
  } catch (err) {
    container.innerHTML = `<h1 class="page-title">Home</h1><p class="text-muted mt-16">${escapeHtml(err.message)}</p>`;
    return;
  }

  container.innerHTML = '<h1 class="page-title">Home</h1>';
  container.appendChild(todaysActivityCard(data.today));

  const quickTitle = document.createElement('p');
  quickTitle.className = 'section-title';
  quickTitle.textContent = 'Quick Actions';
  container.appendChild(quickTitle);
  container.appendChild(quickActionsGrid());

  const champTitle = document.createElement('p');
  champTitle.className = 'section-title';
  champTitle.textContent = 'Current Champion';
  container.appendChild(champTitle);
  const champWrap = document.createElement('div');
  champWrap.className = 'card';
  champWrap.innerHTML = renderChampionBanner(data.champion);
  container.appendChild(champWrap);

  const feedTitle = document.createElement('p');
  feedTitle.className = 'section-title';
  feedTitle.textContent = 'Recent Activity';
  container.appendChild(feedTitle);
  container.appendChild(recentActivityCard(data.recent_activity));
}

function refresh() {
  const container = document.getElementById('view-home');
  if (container) renderHome(container);
}

// ------------------------------------------------------- Today's Activity

function todaysActivityCard(today) {
  return today.kind === 'reveal' ? revealCard(today) : actionCard(today);
}

function revealCard(today) {
  const partner = partnerMember();
  const activity = today.activity;

  const wrap = document.createElement('button');
  wrap.className = 'card card-tap hero-card';
  wrap.style.cssText = 'display:block;width:100%;text-align:left;';

  let eyebrow = `Today's ${today.label}`;
  let sub = '';
  let cta = today.lane === 'question' ? 'Answer now' : 'Play now';

  if (activity.my_submitted && !activity.revealed) {
    eyebrow += ' · Waiting';
    sub = `<p class="reveal-sub">❤️ Waiting for ${partner ? escapeHtml(partner.name) : 'your partner'}</p>`;
    cta = 'View status';
  } else if (activity.revealed) {
    eyebrow += ' · Ready';
    sub = `<p class="reveal-sub">💌 Your answers are ready</p>`;
    cta = 'Reveal';
  } else if (activity.partner_submitted) {
    // Never reveals what the partner said - just that they went first.
    sub = `<p class="reveal-sub">❤️ ${partner ? escapeHtml(partner.name) : 'Your partner'} already went - yours is still hidden.</p>`;
  }

  wrap.innerHTML = `
    <div class="hero-eyebrow">${escapeHtml(eyebrow)}</div>
    <div class="hero-question">${escapeHtml(activity.content.prompt)}</div>
    ${sub}
    <span class="btn btn-primary btn-block" style="pointer-events:none;">${escapeHtml(cta)}</span>
  `;

  wrap.addEventListener('click', () => {
    if (today.activity_type === 'classic_question') {
      openActivityModal(activity.activity_id, { onChange: refresh });
    } else {
      const opener = GAME_OPENERS[today.activity_type];
      if (opener) opener(activity);
    }
  });

  return wrap;
}

function actionCard(today) {
  const done = today.state === 'done_today';

  const wrap = document.createElement('button');
  wrap.className = 'card card-tap action-lane-card';
  wrap.innerHTML = `
    <span class="emoji-badge">${today.emoji}</span>
    <span style="flex:1;">
      <span class="title">${escapeHtml(today.title)}</span>
      <span class="text-muted small">${escapeHtml(done ? today.done_subtitle : today.subtitle)}</span>
    </span>
    ${done ? '<span class="done-check">✓</span>' : ''}
  `;

  wrap.addEventListener('click', () => {
    if (today.lane === 'appreciation') openAppreciationMenu('sent');
    else if (today.lane === 'challenge') openChallengesMenu();
    else if (today.lane === 'plan') openPlanForm({ onSaved: refresh });
  });

  return wrap;
}

// ----------------------------------------------------------- Quick Actions

function quickActionsGrid() {
  const wrap = document.createElement('div');
  wrap.className = 'quick-actions-grid';
  wrap.innerHTML = `
    <button class="quick-action" id="qa-game"><span class="emoji">🎮</span>Play a Game</button>
    <button class="quick-action" id="qa-question"><span class="emoji">❓</span>Answer Question</button>
    <button class="quick-action" id="qa-appreciate"><span class="emoji">💌</span>Send Appreciation</button>
    <button class="quick-action" id="qa-plan"><span class="emoji">📝</span>Add Plan</button>
  `;

  wrap.querySelector('#qa-game').addEventListener('click', () => {
    document.querySelector('.nav-btn[data-view="games"]').click();
  });
  wrap.querySelector('#qa-question').addEventListener('click', async () => {
    try {
      const activity = await api.activities.random({ activity_type: 'classic_question' });
      openActivityModal(activity.activity_id, { onChange: refresh });
    } catch (err) {
      showToast(err.message);
    }
  });
  wrap.querySelector('#qa-appreciate').addEventListener('click', () => openAppreciationMenu('sent'));
  wrap.querySelector('#qa-plan').addEventListener('click', () => openPlanForm({ onSaved: refresh }));

  return wrap;
}

// --------------------------------------------------------- Recent Activity

function recentActivityCard(items) {
  const wrap = document.createElement('div');
  wrap.className = 'card';

  if (items.length === 0) {
    wrap.innerHTML = `<p class="text-muted small" style="padding:8px 0;">Nothing yet - play a game, send an appreciation, or add a plan to get started.</p>`;
    return wrap;
  }

  items.forEach((item) => {
    const row = document.createElement('div');
    row.className = 'feed-item';
    row.innerHTML = `
      <span class="feed-icon">${FEED_ICON[item.type] || '✨'}</span>
      <span>
        <span class="feed-text">${escapeHtml(item.text)}</span>
        <span class="feed-time">${formatRelativeDate(item.timestamp)}</span>
      </span>
    `;
    wrap.appendChild(row);
  });

  return wrap;
}
