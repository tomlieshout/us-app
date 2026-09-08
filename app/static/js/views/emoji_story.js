import { api } from '../api.js';
import { escapeHtml, openModal, showToast } from '../utils.js';
import { partnerMember } from '../state.js';

/** Emoji Story: a menu leading to four simple screens. No scoring
 * anywhere in this game, by design - it's a conversation starter, not a
 * quiz (see EmojiStoryActivity.compute_result). */
export function openEmojiStoryMenu() {
  const { body } = openModal('round-modal', { title: 'Emoji Story', render: () => '<div class="skeleton" style="height:220px;"></div>' });
  renderMenu(body);
}

function renderMenu(body) {
  const partner = partnerMember();
  body.innerHTML = '';
  const wrap = document.createElement('div');
  wrap.style.display = 'flex';
  wrap.style.flexDirection = 'column';
  wrap.style.gap = '10px';
  wrap.innerHTML = `
    <button class="btn btn-ghost btn-block" id="es-guess-app" style="justify-content:flex-start;">🎲 Guess an App Story</button>
    <button class="btn btn-ghost btn-block" id="es-guess-partner" style="justify-content:flex-start;">💌 Guess ${partner ? escapeHtml(partner.name) : 'Your Partner'}'s Story</button>
    <button class="btn btn-ghost btn-block" id="es-create" style="justify-content:flex-start;">✏️ Create a Story</button>
    <button class="btn btn-ghost btn-block" id="es-mine" style="justify-content:flex-start;">📋 My Stories</button>
  `;
  body.appendChild(wrap);

  wrap.querySelector('#es-guess-app').addEventListener('click', () => loadGuess(body, 'app'));
  wrap.querySelector('#es-guess-partner').addEventListener('click', () => loadGuess(body, 'partner'));
  wrap.querySelector('#es-create').addEventListener('click', () => renderCreate(body));
  wrap.querySelector('#es-mine').addEventListener('click', () => renderMine(body));
}

function backButton(body) {
  const btn = document.createElement('button');
  btn.className = 'btn btn-text';
  btn.style.padding = '0';
  btn.style.marginBottom = '10px';
  btn.textContent = '‹ Back';
  btn.addEventListener('click', () => renderMenu(body));
  return btn;
}

// ------------------------------------------------------------- Guess flows

async function loadGuess(body, source) {
  body.innerHTML = '<div class="skeleton" style="height:260px;"></div>';
  let activity;
  try {
    activity = source === 'app'
      ? await api.activities.random({ activity_type: 'emoji_story', category: 'guess' })
      : await api.emojiStory.guess();
  } catch (err) {
    body.innerHTML = '';
    body.appendChild(backButton(body));
    const p = document.createElement('p');
    p.className = 'text-muted';
    p.style.padding = '20px 0';
    p.textContent = err.message;
    body.appendChild(p);
    return;
  }
  renderGuessScreen(body, activity, source);
}

function renderGuessScreen(body, activity, source) {
  body.innerHTML = '';
  body.appendChild(backButton(body));

  if (!activity.my_submitted) {
    body.appendChild(renderGuessForm(activity, body, source));
  } else {
    body.appendChild(renderGuessReveal(activity, body, source));
  }
}

function renderGuessForm(activity, body, source) {
  const wrap = document.createElement('div');
  wrap.innerHTML = `
    <div style="text-align:center;font-size:52px;margin:20px 0;">${escapeHtml(activity.content.payload.emoji_sequence)}</div>
    <p class="text-muted small text-center" style="margin-bottom:14px;">What's the story?</p>
    <div class="field"><textarea id="es-guess-input" rows="3" placeholder="Type your guess..." maxlength="500"></textarea></div>
    <button class="btn btn-primary btn-block" id="es-guess-submit" disabled>Submit Guess</button>
  `;
  const textarea = wrap.querySelector('#es-guess-input');
  const submitBtn = wrap.querySelector('#es-guess-submit');
  textarea.addEventListener('input', () => { submitBtn.disabled = !textarea.value.trim(); });
  submitBtn.addEventListener('click', async () => {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting…';
    try {
      const updated = await api.activities.submit(activity.activity_id, { guess: textarea.value.trim() });
      renderGuessScreen(body, updated, source);
    } catch (err) {
      showToast(err.message);
      submitBtn.disabled = false;
      submitBtn.textContent = 'Submit Guess';
    }
  });
  return wrap;
}

function renderGuessReveal(activity, body, source) {
  const wrap = document.createElement('div');
  const explanation = activity.content.payload.explanation;
  wrap.innerHTML = `
    <div style="text-align:center;font-size:52px;margin:10px 0 20px;">${escapeHtml(activity.content.payload.emoji_sequence)}</div>
    <div class="reveal-answer-card mine">
      <div class="who">Your guess</div>
      <p class="answer-text">${escapeHtml(activity.my_submission.payload.guess)}</p>
    </div>
    <div class="reveal-answer-card">
      <div class="who">${source === 'app' ? 'What it actually meant' : 'What they actually meant'}</div>
      <p class="answer-text">${explanation ? escapeHtml(explanation) : '…waiting to be revealed'}</p>
    </div>
    <button class="btn btn-primary btn-block mt-16" id="es-next">Try Another</button>
  `;
  wrap.querySelector('#es-next').addEventListener('click', () => loadGuess(body, source));
  return wrap;
}

// ---------------------------------------------------------------- Create

function renderCreate(body) {
  body.innerHTML = '';
  body.appendChild(backButton(body));

  const wrap = document.createElement('div');
  wrap.innerHTML = `
    <p class="page-subtitle" style="margin-top:0;">Write a little emoji story for your partner to guess. They won't see what it means until they've guessed.</p>
    <div class="field"><label>Emoji sequence</label><input type="text" id="es-create-emoji" placeholder="🎬🍿😱" maxlength="40"></div>
    <div class="field"><label>What does it mean?</label><textarea id="es-create-explanation" rows="3" placeholder="e.g. Watching a scary movie together" maxlength="500"></textarea></div>
    <button class="btn btn-primary btn-block" id="es-create-submit">Create Story</button>
  `;
  body.appendChild(wrap);

  const emojiInput = wrap.querySelector('#es-create-emoji');
  const explanationInput = wrap.querySelector('#es-create-explanation');
  const submitBtn = wrap.querySelector('#es-create-submit');

  submitBtn.addEventListener('click', async () => {
    const emoji_sequence = emojiInput.value.trim();
    const explanation = explanationInput.value.trim();
    if (!emoji_sequence || !explanation) {
      showToast('Add both an emoji sequence and what it means.');
      return;
    }
    submitBtn.disabled = true;
    try {
      await api.emojiStory.create(emoji_sequence, explanation);
      showToast('Story created ✓ Your partner will find it under "Guess" whenever they\'re ready.');
      renderMenu(body);
    } catch (err) {
      showToast(err.message);
      submitBtn.disabled = false;
    }
  });
}

// -------------------------------------------------------------- My stories

async function renderMine(body) {
  body.innerHTML = '<div class="skeleton" style="height:220px;"></div>';
  let data;
  try {
    data = await api.emojiStory.mine();
  } catch (err) {
    body.innerHTML = '';
    body.appendChild(backButton(body));
    showToast(err.message);
    return;
  }

  body.innerHTML = '';
  body.appendChild(backButton(body));

  if (data.stories.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.style.padding = '30px 10px';
    empty.innerHTML = `<div class="empty-emoji">😂</div><h3>No stories yet</h3><p>Create one and see if they can guess it.</p>`;
    body.appendChild(empty);
    return;
  }

  data.stories.forEach((story) => {
    const card = document.createElement('div');
    card.className = 'card';
    card.style.marginBottom = '10px';
    const status = story.guessed
      ? `<p class="text-muted small mt-8">They guessed: "${escapeHtml(story.guess)}"</p>`
      : `<p class="text-muted small mt-8">Waiting for them to guess…</p>`;
    card.innerHTML = `
      <div style="font-size:32px;">${escapeHtml(story.emoji_sequence)}</div>
      <p class="small text-muted mt-8">You meant: "${escapeHtml(story.explanation)}"</p>
      ${status}
    `;
    body.appendChild(card);
  });
}
