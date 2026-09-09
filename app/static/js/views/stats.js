import { api } from '../api.js';
import { escapeHtml } from '../utils.js';
import { partnerMember, meMember } from '../state.js';

export async function renderStats(container) {
  container.innerHTML = `
    <h1 class="page-title">Stats</h1>
    <p class="page-subtitle">Play together, see how you match up — and everything you're building beyond the games.</p>
    <div class="skeleton" style="height:320px;"></div>
  `;

  let stats;
  try {
    stats = await api.stats();
  } catch (err) {
    container.innerHTML = `<h1 class="page-title">Stats</h1><p class="text-muted mt-16">${escapeHtml(err.message)}</p>`;
    return;
  }

  const me = meMember();
  const partner = partnerMember();
  const partnerName = partner ? escapeHtml(partner.name) : 'your partner';

  container.innerHTML = `
    <h1 class="page-title">Stats</h1>
    <p class="page-subtitle">Play together, see how you match up — and everything you're building beyond the games.</p>

    <p class="section-title">Competitive</p>
    <div class="card">${renderChampionBanner(stats.competitive)}</div>

    <div class="stat-grid mt-16">
      ${renderStatCard(stats.competitive.games_played, 'Games Played')}
      ${renderStatCard(renderRecord(stats.competitive.record, me), 'Your Record (W-L-D)')}
    </div>

    <p class="section-title">How well do you know ${partnerName}?</p>
    <div class="card">${renderPercentBlock(
      me ? stats.competitive.prediction_accuracy[String(me.id)] : null,
      'predictions',
      `Play a few more prediction-style questions and your accuracy will show up here.`
    )}</div>

    <p class="section-title">Would You Rather Agreement</p>
    <div class="card">${renderPercentBlock(
      stats.competitive.would_you_rather_agreement,
      'matches',
      `Play a few more Would You Rather rounds and your agreement rate will show up here.`
    )}</div>

    <p class="section-title">Together</p>
    <div class="stat-grid mt-16">
      ${renderStatCard(stats.together.questions_answered, 'Questions Answered')}
      ${renderStatCard(stats.together.games_played, 'Games Played')}
      ${renderStatCard(`${stats.together.appreciations.sent}/${stats.together.appreciations.received}`, 'Appreciations Sent/Received')}
      ${renderStatCard(stats.together.memories, 'Memories')}
    </div>
  `;
}

function renderStatCard(value, label) {
  return `<div class="stat-card"><div class="num">${value}</div><div class="lbl">${escapeHtml(label)}</div></div>`;
}

function renderRecord(record, me) {
  if (!me || !record[String(me.id)]) return '0-0-0';
  const r = record[String(me.id)];
  return `${r.wins}-${r.losses}-${r.draws}`;
}

function renderChampionBanner(competitive) {
  if (!competitive.games_played) {
    return `
      <div class="champion-banner">
        <div class="crown">🎮</div>
        <p class="text-muted small mt-8">No games played yet — a prediction, a Would You Rather, or Know Each Other will get things started.</p>
      </div>
    `;
  }

  if (competitive.is_draw) {
    const [a, b] = Object.values(competitive.points);
    return `
      <div class="champion-banner">
        <div class="crown">🤝</div>
        <div class="lead-label">It's a draw</div>
        <div class="score-line">${a} — ${b}</div>
      </div>
    `;
  }

  const leader = competitive.leader;
  const leaderPts = competitive.points[String(leader.user_id)];
  const otherId = Object.keys(competitive.points).find((id) => id !== String(leader.user_id));
  const otherPts = competitive.points[otherId];
  const diff = leaderPts - otherPts;

  return `
    <div class="champion-banner">
      <div class="crown">👑</div>
      <div class="lead-label">Current Champion</div>
      <div class="lead-name">${escapeHtml(leader.name)}</div>
      <div class="score-line">${leaderPts} — ${otherPts}</div>
      <div class="diff-line">${escapeHtml(leader.name)} is winning by ${diff} point${diff === 1 ? '' : 's'}.</div>
    </div>
  `;
}

function renderPercentBlock(data, correctLabel, emptyCopy) {
  if (!data) {
    return `<p class="text-muted" style="font-size:14px;line-height:1.5;">${escapeHtml(emptyCopy)}</p>`;
  }

  const total = data.total;
  const correctCount = 'matches' in data ? data.matches : data.correct;

  if (data.enough_data) {
    return `
      <div style="text-align:center;">
        <div class="num" style="font-family:'Lora',serif;font-size:38px;font-weight:700;color:var(--accent-strong);">${data.percent}%</div>
        <p class="text-muted small mt-8">${correctCount} ${correctLabel} out of ${total}</p>
      </div>
    `;
  }

  return `
    <p class="text-muted" style="font-size:14px;line-height:1.5;">
      ${escapeHtml(emptyCopy)} (${total}/5 so far).
    </p>
    <div class="progress-bar mt-16"><div class="progress-bar-fill" style="width:${Math.min(100, (total / 5) * 100)}%;"></div></div>
  `;
}
