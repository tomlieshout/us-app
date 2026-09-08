import { api } from '../api.js';
import { escapeHtml, openModal, showToast } from '../utils.js';
import { partnerMember } from '../state.js';

const CATEGORIES = [
  { key: null, label: 'All', emoji: '🎲' },
  { key: 'cute', label: 'Cute', emoji: '🥰' },
  { key: 'funny', label: 'Funny', emoji: '😂' },
  { key: 'deep', label: 'Deep', emoji: '💭' },
  { key: 'romantic', label: 'Romantic', emoji: '❤️' },
];

export function openChallengesMenu() {
  const { body } = openModal('round-modal', { title: 'Challenges', render: () => '<div class="skeleton" style="height:280px;"></div>' });
  renderBrowse(body, null);
}

function categoryChips(body, activeCategory) {
  const row = document.createElement('div');
  row.style.cssText = 'display:flex;gap:8px;overflow-x:auto;padding-bottom:6px;margin-bottom:14px;';
  CATEGORIES.forEach((c) => {
    const chip = document.createElement('button');
    chip.className = `chip ${c.key === activeCategory ? '' : 'chip-muted'}`;
    chip.style.cssText = 'white-space:nowrap;border:none;flex-shrink:0;';
    chip.textContent = `${c.emoji} ${c.label}`;
    chip.addEventListener('click', () => renderBrowse(body, c.key));
    row.appendChild(chip);
  });
  return row;
}

async function renderBrowse(body, category) {
  body.innerHTML = '';
  body.appendChild(categoryChips(body, category));

  const mineBtn = document.createElement('button');
  mineBtn.className = 'btn btn-ghost btn-block mt-8';
  mineBtn.textContent = '📋 My Challenges';
  mineBtn.addEventListener('click', () => renderMine(body));
  body.appendChild(mineBtn);

  const cardHolder = document.createElement('div');
  cardHolder.className = 'mt-16';
  cardHolder.innerHTML = '<div class="skeleton" style="height:160px;"></div>';
  body.appendChild(cardHolder);

  await loadCandidate(cardHolder, category, body);
}

async function loadCandidate(cardHolder, category, body) {
  cardHolder.innerHTML = '<div class="skeleton" style="height:160px;"></div>';
  let content;
  try {
    content = await api.challenges.random(category);
  } catch (err) {
    cardHolder.innerHTML = `<p class="text-muted" style="padding:20px 0;text-align:center;">${escapeHtml(err.message)}</p>`;
    return;
  }

  cardHolder.innerHTML = '';
  const card = document.createElement('div');
  card.className = 'card hero-card';
  card.innerHTML = `
    <div class="hero-eyebrow">${content.category.charAt(0).toUpperCase() + content.category.slice(1)}${content.payload.requires_both ? ' · Both of you' : ''}</div>
    <div class="hero-question">${escapeHtml(content.prompt)}</div>
    <div style="display:flex;gap:10px;">
      <button class="btn btn-ghost btn-block" id="ch-skip" style="background:rgba(255,255,255,0.15);color:#fff;border-color:rgba(255,255,255,0.4);">Skip</button>
      <button class="btn btn-block" id="ch-accept" style="background:#fff;color:var(--accent-strong);">Accept</button>
    </div>
  `;
  cardHolder.appendChild(card);

  card.querySelector('#ch-skip').addEventListener('click', () => loadCandidate(cardHolder, category, body));
  card.querySelector('#ch-accept').addEventListener('click', async () => {
    try {
      await api.challenges.accept(content.id);
      showToast('Challenge accepted ✓');
      renderMine(body);
    } catch (err) {
      showToast(err.message);
    }
  });
}

async function renderMine(body) {
  body.innerHTML = '<div class="skeleton" style="height:220px;"></div>';
  let data;
  try {
    data = await api.challenges.mine();
  } catch (err) {
    showToast(err.message);
    return;
  }

  body.innerHTML = '';
  const backBtn = document.createElement('button');
  backBtn.className = 'btn btn-text';
  backBtn.style.cssText = 'padding:0;margin-bottom:10px;';
  backBtn.textContent = '‹ Back to Challenges';
  backBtn.addEventListener('click', () => renderBrowse(body, null));
  body.appendChild(backBtn);

  if (data.challenges.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.style.padding = '30px 10px';
    empty.innerHTML = `<div class="empty-emoji">🎲</div><h3>No challenges yet</h3><p>Accept one to get started - no pressure, skip anything that's not for you.</p>`;
    body.appendChild(empty);
    return;
  }

  const partner = partnerMember();
  data.challenges.forEach((c) => {
    const card = document.createElement('div');
    card.className = 'card';
    card.style.marginBottom = '10px';

    let statusLine;
    if (c.status === 'completed') {
      statusLine = `<span class="chip chip-success">✅ Completed</span>`;
    } else if (c.requires_both && c.completed_by.length > 0) {
      statusLine = c.i_have_completed
        ? `<span class="chip chip-warn">Waiting on ${partner ? escapeHtml(partner.name) : 'your partner'}</span>`
        : `<span class="chip chip-warn">${partner ? escapeHtml(partner.name) : 'Your partner'} confirmed - your turn</span>`;
    } else {
      statusLine = `<span class="chip chip-muted">${c.requires_both ? 'Needs both of you' : 'Accepted'}</span>`;
    }

    card.innerHTML = `
      <div class="status-row">${statusLine}</div>
      <p style="font-weight:600;font-size:15px;line-height:1.4;">${escapeHtml(c.prompt)}</p>
    `;

    if (c.status !== 'completed' && !c.i_have_completed) {
      const completeBtn = document.createElement('button');
      completeBtn.className = 'btn btn-primary btn-sm mt-8';
      completeBtn.textContent = 'Mark Complete';
      completeBtn.addEventListener('click', async () => {
        completeBtn.disabled = true;
        try {
          await api.challenges.complete(c.id);
          renderMine(body);
        } catch (err) {
          showToast(err.message);
          completeBtn.disabled = false;
        }
      });
      card.appendChild(completeBtn);
    }

    body.appendChild(card);
  });
}
