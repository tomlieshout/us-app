import { api } from '../api.js';
import { escapeHtml } from '../utils.js';
import { partnerMember } from '../state.js';
import { openRoundModal } from './round.js';

export async function renderHome(container) {
  container.innerHTML = `
    <h1 class="page-title">Home</h1>
    <div class="card hero-card skeleton" style="height:180px;border:none;"></div>
  `;

  let round, stats;
  try {
    [round, stats] = await Promise.all([api.currentRound(), api.stats()]);
  } catch (err) {
    container.innerHTML = `<h1 class="page-title">Home</h1><p class="text-muted mt-16">${escapeHtml(err.message)}</p>`;
    return;
  }

  container.innerHTML = '';
  container.appendChild(heroCard(round));
  container.appendChild(streakRow(stats));
  container.appendChild(quickActions());
}

function heroCard(round) {
  const partner = partnerMember();
  const wrap = document.createElement('div');
  wrap.className = 'card hero-card';

  let eyebrow = "Today's Question";
  let cta = 'Answer Question';
  let sub = '';

  if (round.revealed) {
    eyebrow = "Today's Question · Revealed";
    cta = 'View Answers';
  } else if (round.my_answered) {
    eyebrow = "Today's Question";
    cta = 'View Status';
    sub = `<p style="color:rgba(255,255,255,0.85);font-size:13px;margin-top:-8px;margin-bottom:14px;">✓ You've answered. Waiting for ${partner ? escapeHtml(partner.name) : 'your partner'}…</p>`;
  } else if (round.partner_answered) {
    sub = `<p style="color:rgba(255,255,255,0.85);font-size:13px;margin-top:-8px;margin-bottom:14px;">❤️ ${partner ? escapeHtml(partner.name) : 'Your partner'} already answered — yours is still hidden.</p>`;
  }

  wrap.innerHTML = `
    <div class="hero-eyebrow">${eyebrow}</div>
    <div class="hero-question">${escapeHtml(round.question.text)}</div>
    ${sub}
    <button class="btn btn-primary btn-block" id="hero-cta">${cta}</button>
  `;

  wrap.querySelector('#hero-cta').addEventListener('click', () => {
    openRoundModal(round.round_id, { onChange: () => renderHome(document.getElementById('view-home')) });
  });

  return wrap;
}

function streakRow(stats) {
  const wrap = document.createElement('div');
  wrap.className = 'streak-row';
  wrap.innerHTML = `
    <div class="streak-pill"><div class="num">${stats.current_streak}🔥</div><div class="lbl">Current Streak</div></div>
    <div class="streak-pill"><div class="num">${stats.longest_streak}</div><div class="lbl">Longest Streak</div></div>
    <div class="streak-pill"><div class="num">${stats.questions_answered}</div><div class="lbl">Answered</div></div>
  `;
  return wrap;
}

function quickActions() {
  const wrap = document.createElement('div');
  wrap.className = 'quick-actions';
  wrap.innerHTML = `
    <button class="quick-action" id="qa-random"><span class="emoji">🎲</span>Random Question</button>
    <button class="quick-action" id="qa-browse"><span class="emoji">📚</span>Browse Categories</button>
  `;
  wrap.querySelector('#qa-random').addEventListener('click', async () => {
    try {
      const round = await api.randomRound();
      openRoundModal(round.round_id, { onChange: () => renderHome(document.getElementById('view-home')) });
    } catch (err) {
      const { showToast } = await import('../utils.js');
      showToast(err.message);
    }
  });
  wrap.querySelector('#qa-browse').addEventListener('click', () => {
    document.querySelector('.nav-btn[data-view="questions"]').click();
  });
  return wrap;
}
