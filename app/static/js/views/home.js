import { api } from '../api.js';
import { escapeHtml, showToast } from '../utils.js';
import { partnerMember } from '../state.js';
import { openActivityModal } from './round.js';
import { openAppreciationMenu } from './appreciation.js';

// NOTE (architectural-integration phase): the streak/questions-answered
// numbers below still come from the legacy /api/stats, which reads
// legacy Round/Answer/DailySelection history. They're accurate up to the
// point of this integration but won't increment from new activity played
// through the new engine until stats gets ported too - flagged, not
// silently wrong-looking. See the summary given alongside this change.

export async function renderHome(container) {
  container.innerHTML = `
    <h1 class="page-title">Home</h1>
    <div class="card hero-card skeleton" style="height:180px;border:none;"></div>
  `;

  let activity, stats, unseenAppreciation;
  try {
    [activity, stats, unseenAppreciation] = await Promise.all([
      api.activities.current(),
      api.stats(),
      api.appreciation.unseenCount(),
    ]);
  } catch (err) {
    container.innerHTML = `<h1 class="page-title">Home</h1><p class="text-muted mt-16">${escapeHtml(err.message)}</p>`;
    return;
  }

  container.innerHTML = '';
  if (unseenAppreciation.unseen_count > 0) {
    container.appendChild(appreciationBanner(unseenAppreciation.unseen_count));
  }
  container.appendChild(heroCard(activity));
  container.appendChild(streakRow(stats));
  container.appendChild(quickActions());
}

function appreciationBanner(count) {
  const partner = partnerMember();
  const wrap = document.createElement('button');
  wrap.className = 'card card-tap mt-16';
  wrap.style.cssText = 'display:flex;align-items:center;gap:12px;text-align:left;width:100%;background:var(--accent-soft);border:none;';
  wrap.innerHTML = `
    <span style="font-size:26px;">💌</span>
    <span>
      <span style="font-weight:700;font-size:14.5px;color:var(--accent-strong);display:block;">
        New appreciation from ${partner ? escapeHtml(partner.name) : 'your partner'}
      </span>
      <span class="text-muted small">Tap to read it</span>
    </span>
  `;
  wrap.addEventListener('click', () => openAppreciationMenu('received'));
  return wrap;
}

function heroCard(activity) {
  const partner = partnerMember();
  const wrap = document.createElement('div');
  wrap.className = 'card hero-card';

  let eyebrow = "Today's Question";
  let cta = 'Answer Question';
  let sub = '';

  if (activity.revealed) {
    eyebrow = "Today's Question · Revealed";
    cta = 'View Answers';
  } else if (activity.my_submitted) {
    eyebrow = "Today's Question";
    cta = 'View Status';
    sub = `<p style="color:rgba(255,255,255,0.85);font-size:13px;margin-top:-8px;margin-bottom:14px;">✓ You've answered. Waiting for ${partner ? escapeHtml(partner.name) : 'your partner'}…</p>`;
  } else if (activity.partner_submitted) {
    sub = `<p style="color:rgba(255,255,255,0.85);font-size:13px;margin-top:-8px;margin-bottom:14px;">❤️ ${partner ? escapeHtml(partner.name) : 'Your partner'} already answered — yours is still hidden.</p>`;
  }

  wrap.innerHTML = `
    <div class="hero-eyebrow">${eyebrow}</div>
    <div class="hero-question">${escapeHtml(activity.content.prompt)}</div>
    ${sub}
    <button class="btn btn-primary btn-block" id="hero-cta">${cta}</button>
  `;

  wrap.querySelector('#hero-cta').addEventListener('click', () => {
    openActivityModal(activity.activity_id, { onChange: () => renderHome(document.getElementById('view-home')) });
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
    <button class="quick-action" id="qa-appreciate"><span class="emoji">💌</span>Appreciate</button>
  `;
  wrap.querySelector('#qa-random').addEventListener('click', async () => {
    try {
      const activity = await api.activities.random();
      openActivityModal(activity.activity_id, { onChange: () => renderHome(document.getElementById('view-home')) });
    } catch (err) {
      showToast(err.message);
    }
  });
  wrap.querySelector('#qa-browse').addEventListener('click', () => {
    document.querySelector('.nav-btn[data-view="questions"]').click();
  });
  wrap.querySelector('#qa-appreciate').addEventListener('click', () => openAppreciationMenu('sent'));
  return wrap;
}
