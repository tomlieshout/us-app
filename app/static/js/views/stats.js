import { api } from '../api.js';
import { escapeHtml } from '../utils.js';
import { partnerMember } from '../state.js';

export async function renderStats(container) {
  container.innerHTML = `
    <h1 class="page-title">Stats</h1>
    <p class="page-subtitle">Playful, not competitive — just a little record of you two.</p>
    <div class="skeleton" style="height:260px;"></div>
  `;

  let stats;
  try {
    stats = await api.stats();
  } catch (err) {
    container.innerHTML = `<h1 class="page-title">Stats</h1><p class="text-muted mt-16">${escapeHtml(err.message)}</p>`;
    return;
  }

  const partner = partnerMember();

  container.innerHTML = `
    <h1 class="page-title">Stats</h1>
    <p class="page-subtitle">Playful, not competitive — just a little record of you two.</p>

    <div class="stat-grid">
      <div class="stat-card"><div class="num">${stats.questions_answered}</div><div class="lbl">Questions Answered</div></div>
      <div class="stat-card"><div class="num">${stats.questions_this_week}</div><div class="lbl">This Week</div></div>
      <div class="stat-card"><div class="num">${stats.current_streak}🔥</div><div class="lbl">Current Streak</div></div>
      <div class="stat-card"><div class="num">${stats.longest_streak}</div><div class="lbl">Longest Streak</div></div>
      <div class="stat-card"><div class="num">${stats.favourites_count}</div><div class="lbl">Favourites</div></div>
      <div class="stat-card"><div class="num">${stats.reactions_exchanged}</div><div class="lbl">Reactions Exchanged</div></div>
    </div>

    <p class="section-title">How well do you know ${partner ? escapeHtml(partner.name) : 'your partner'}?</p>
    <div class="card">
      ${stats.prediction.enough_data ? `
        <div style="text-align:center;">
          <div class="num" style="font-family:'Lora',serif;font-size:38px;font-weight:700;color:var(--accent-strong);">${stats.prediction.percent}%</div>
          <p class="text-muted small mt-8">${stats.prediction.correct} correct out of ${stats.prediction.rounds} predictions</p>
        </div>
      ` : `
        <p class="text-muted" style="font-size:14px;line-height:1.5;">
          Play a few more "How Well Do You Know Me?" questions and your prediction score will show up here
          (${stats.prediction.rounds}/5 so far).
        </p>
        <div class="progress-bar mt-16"><div class="progress-bar-fill" style="width:${Math.min(100, (stats.prediction.rounds / 5) * 100)}%;"></div></div>
      `}
    </div>
  `;
}
