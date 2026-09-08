import { api } from '../api.js';
import { escapeHtml, openModal, showToast, confirmDialog } from '../utils.js';
import { meMember, partnerMember } from '../state.js';

const CATEGORY_LABEL = { person: '🧑 Person', place: '🌍 Place', thing: '📦 Thing' };

export function open20QGame() {
  const { body } = openModal('round-modal', { title: '20 Questions', render: () => '<div class="skeleton" style="height:300px;"></div>' });
  load(body);
}

async function load(body) {
  body.innerHTML = '<div class="skeleton" style="height:300px;"></div>';
  let game;
  try {
    game = await api.twentyQuestions.current();
  } catch (err) {
    if (err.status === 404) {
      renderCreateForm(body);
      return;
    }
    body.innerHTML = `<p class="text-muted" style="padding:30px 0;text-align:center;">${escapeHtml(err.message)}</p>`;
    return;
  }
  render(body, game);
}

function render(body, game) {
  body.innerHTML = '';

  if (game.status !== 'in_progress') {
    body.appendChild(renderFinished(game, body));
    return;
  }

  body.appendChild(renderProgressHeader(game));
  body.appendChild(renderHistory(game));

  if (game.is_chooser && game.next_action === 'answer') {
    body.appendChild(renderAnswerForm(game, body));
  } else if (game.is_chooser && game.next_action === 'ask') {
    body.appendChild(waitingMessage(`Waiting for ${guesserName(game)} to ask their next question…`));
  } else if (game.is_guesser && game.next_action === 'ask') {
    body.appendChild(renderAskForm(game, body));
  } else if (game.is_guesser && game.next_action === 'answer') {
    body.appendChild(waitingMessage(`Waiting for ${chooserName(game)} to answer…`));
  }

  body.appendChild(abandonLink(game, body));
}

function chooserName(game) {
  const me = meMember();
  const partner = partnerMember();
  if (me && me.id === game.chooser_user_id) return 'you';
  return partner ? escapeHtml(partner.name) : 'your partner';
}
function guesserName(game) {
  const me = meMember();
  const partner = partnerMember();
  if (me && me.id === game.guesser_user_id) return 'you';
  return partner ? escapeHtml(partner.name) : 'your partner';
}

function renderProgressHeader(game) {
  const wrap = document.createElement('div');
  wrap.innerHTML = `
    <div class="status-row">
      <span class="chip chip-muted">${CATEGORY_LABEL[game.category] || game.category}</span>
      <span class="chip">Question ${Math.min(game.turn_count + (game.next_action === 'ask' && game.is_guesser ? 1 : 0), game.max_turns)} / ${game.max_turns}</span>
    </div>
  `;
  return wrap;
}

function renderHistory(game) {
  const wrap = document.createElement('div');
  wrap.className = 'mt-16';
  if (game.turns.length === 0) {
    const p = document.createElement('p');
    p.className = 'text-muted small';
    p.textContent = 'No questions asked yet.';
    wrap.appendChild(p);
    return wrap;
  }
  game.turns.forEach((t) => {
    const row = document.createElement('div');
    row.className = 'comment-bubble';
    row.style.marginBottom = '8px';
    const label = t.is_guess ? 'Guess' : `Q${t.turn_number}`;
    const answerLabel = t.answer === null
      ? '<span class="text-muted">pending…</span>'
      : t.is_guess
        ? (t.answer === 'correct' ? '✅ Correct!' : '❌ Not quite')
        : (t.answer === 'yes' ? '✅ Yes' : '🚫 No');
    row.innerHTML = `<div class="comment-author">${label}</div>${escapeHtml(t.question_text)} — ${answerLabel}`;
    wrap.appendChild(row);
  });
  return wrap;
}

function waitingMessage(text) {
  const wrap = document.createElement('div');
  wrap.className = 'waiting-illustration';
  wrap.innerHTML = `<div class="emoji">⏳</div><p class="text-muted mt-8" style="font-size:14px;">${text}</p>`;
  return wrap;
}

function renderAskForm(game, body) {
  const wrap = document.createElement('div');
  wrap.className = 'mt-16';
  wrap.innerHTML = `
    <div class="field"><textarea id="q-input" rows="2" placeholder="Ask a yes/no question…" maxlength="300"></textarea></div>
    <label class="flex-row" style="gap:8px;font-size:13.5px;color:var(--text-muted);margin-bottom:12px;">
      <input type="checkbox" id="q-is-guess" style="width:18px;height:18px;"> This is my final guess (name the secret directly)
    </label>
    <button class="btn btn-primary btn-block" id="q-submit" disabled>Ask</button>
  `;
  const textarea = wrap.querySelector('#q-input');
  const isGuessBox = wrap.querySelector('#q-is-guess');
  const submitBtn = wrap.querySelector('#q-submit');
  textarea.addEventListener('input', () => { submitBtn.disabled = !textarea.value.trim(); });
  isGuessBox.addEventListener('change', () => {
    submitBtn.textContent = isGuessBox.checked ? 'Submit Guess' : 'Ask';
    textarea.placeholder = isGuessBox.checked ? 'What do you think the secret is?' : 'Ask a yes/no question…';
  });

  submitBtn.addEventListener('click', async () => {
    submitBtn.disabled = true;
    try {
      const updated = await api.twentyQuestions.ask(game.game_id, textarea.value.trim(), isGuessBox.checked);
      showToast(isGuessBox.checked ? 'Guess sent ✓' : 'Question sent ✓');
      render(body, updated);
    } catch (err) {
      showToast(err.message);
      submitBtn.disabled = false;
    }
  });

  return wrap;
}

function renderAnswerForm(game, body) {
  const wrap = document.createElement('div');
  wrap.className = 'mt-16';
  const pending = game.turns[game.turns.length - 1];
  const isGuess = pending.is_guess;

  wrap.innerHTML = `
    <div class="card" style="background:var(--accent-soft);border:none;">
      <p style="font-weight:700;font-size:15px;">${isGuess ? '🎯 Their guess:' : '❓ Their question:'}</p>
      <p class="mt-8">${escapeHtml(pending.question_text)}</p>
    </div>
    <div style="display:flex;gap:10px;margin-top:14px;">
      ${isGuess
        ? `<button class="btn btn-danger btn-block" id="q-no">Not Correct</button><button class="btn btn-primary btn-block" id="q-yes">Correct!</button>`
        : `<button class="btn btn-ghost btn-block" id="q-no">No</button><button class="btn btn-primary btn-block" id="q-yes">Yes</button>`}
    </div>
  `;

  const respond = async (value) => {
    wrap.querySelectorAll('button').forEach((b) => (b.disabled = true));
    try {
      const updated = await api.twentyQuestions.answer(game.game_id, value);
      render(body, updated);
    } catch (err) {
      showToast(err.message);
      wrap.querySelectorAll('button').forEach((b) => (b.disabled = false));
    }
  };

  wrap.querySelector('#q-yes').addEventListener('click', () => respond(isGuess ? 'correct' : 'yes'));
  wrap.querySelector('#q-no').addEventListener('click', () => respond(isGuess ? 'incorrect' : 'no'));

  return wrap;
}

function abandonLink(game, body) {
  const btn = document.createElement('button');
  btn.className = 'btn btn-text mt-16';
  btn.style.color = 'var(--danger)';
  btn.textContent = 'Abandon this game';
  btn.addEventListener('click', async () => {
    const ok = await confirmDialog({
      title: 'Abandon this game?',
      message: 'The secret will be revealed and this game will end. This can\'t be undone.',
      confirmLabel: 'Abandon',
      danger: true,
    });
    if (!ok) return;
    try {
      const updated = await api.twentyQuestions.abandon(game.game_id);
      render(body, updated);
    } catch (err) {
      showToast(err.message);
    }
  });
  return btn;
}

function renderFinished(game, body) {
  const wrap = document.createElement('div');
  const banners = {
    won: `🎉 ${guesserName(game) === 'you' ? 'You' : guesserName(game)} guessed it!`,
    lost: `😅 Out of questions! The secret was...`,
    abandoned: `🏳️ Game abandoned. The secret was...`,
  };
  wrap.innerHTML = `
    <div class="card" style="text-align:center;background:var(--accent-soft);border:none;">
      <p style="font-weight:700;font-size:16px;">${banners[game.status] || game.status}</p>
      <p class="mt-8" style="font-family:'Lora',serif;font-size:22px;font-weight:600;color:var(--accent-strong);">${escapeHtml(game.secret_text || '')}</p>
      <p class="text-muted small mt-8">${CATEGORY_LABEL[game.category] || game.category} · guessed in ${game.turn_count} question${game.turn_count === 1 ? '' : 's'}</p>
    </div>
  `;
  wrap.appendChild(renderHistory(game));
  const again = document.createElement('button');
  again.className = 'btn btn-primary btn-block mt-16';
  again.textContent = 'Play Again';
  again.addEventListener('click', () => renderCreateForm(body));
  wrap.appendChild(again);
  return wrap;
}

function renderCreateForm(body) {
  body.innerHTML = '';
  const wrap = document.createElement('div');
  wrap.innerHTML = `
    <p class="page-subtitle" style="margin-top:0;">Pick a secret. Your partner will ask yes/no questions to try to guess it in 20 or fewer.</p>
    <p class="section-title">Category</p>
    <div class="answer-option-list" id="q-category-list">
      <button type="button" class="answer-option" data-category="person">🧑 Person</button>
      <button type="button" class="answer-option" data-category="place">🌍 Place</button>
      <button type="button" class="answer-option" data-category="thing">📦 Thing</button>
    </div>
    <div class="field mt-16"><label>Your secret</label><input type="text" id="q-secret-input" placeholder="e.g. Albert Einstein" maxlength="200"></div>
    <button class="btn btn-primary btn-block" id="q-create-submit" disabled>Start the Game</button>
  `;
  body.appendChild(wrap);

  let category = null;
  const list = wrap.querySelector('#q-category-list');
  const input = wrap.querySelector('#q-secret-input');
  const submitBtn = wrap.querySelector('#q-create-submit');
  const updateState = () => { submitBtn.disabled = !category || !input.value.trim(); };

  list.querySelectorAll('.answer-option').forEach((btn) => {
    btn.addEventListener('click', () => {
      list.querySelectorAll('.answer-option').forEach((b) => b.classList.remove('selected'));
      btn.classList.add('selected');
      category = btn.dataset.category;
      updateState();
    });
  });
  input.addEventListener('input', updateState);

  submitBtn.addEventListener('click', async () => {
    submitBtn.disabled = true;
    try {
      const game = await api.twentyQuestions.create(category, input.value.trim());
      showToast('Game started ✓');
      render(body, game);
    } catch (err) {
      showToast(err.message);
      submitBtn.disabled = false;
    }
  });
}
