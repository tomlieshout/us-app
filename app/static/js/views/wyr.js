import { api } from '../api.js';
import { escapeHtml, openModal, showToast } from '../utils.js';
import { meMember, partnerMember } from '../state.js';

/** Opens the Would You Rather sheet: fetches a fresh random WYR activity,
 * lets the user pick privately, waits for/reveals the partner's pick, and
 * offers "Next Question" to keep playing without ever repeating a
 * question the couple has already been shown (the /api/activities/random
 * picker already guarantees that - see services/activity_questions.py). */
export function openWyrGame() {
  const { close, body } = openModal('round-modal', { title: 'Would You Rather', render: () => '<div class="skeleton" style="height:260px;"></div>' });
  loadNext(body);
}

async function loadNext(body) {
  body.innerHTML = '<div class="skeleton" style="height:260px;"></div>';
  let activity;
  try {
    activity = await api.activities.random({ activity_type: 'would_you_rather' });
  } catch (err) {
    // no more content in this activity_type/category combo, or a network issue
    body.innerHTML = `<p class="text-muted" style="padding:30px 0;text-align:center;">${escapeHtml(err.message)}</p>`;
    return;
  }
  render(body, activity);
}

function render(body, activity) {
  body.innerHTML = '';
  if (!activity.my_submitted) {
    body.appendChild(renderChooser(activity, body));
  } else if (!activity.revealed) {
    body.appendChild(renderWaiting(activity));
  } else {
    body.appendChild(renderReveal(activity, body));
  }
}

function renderChooser(activity, body) {
  const wrap = document.createElement('div');
  const { option_a, option_b, emoji_a, emoji_b } = activity.content.payload;

  wrap.innerHTML = `
    <p class="wyr-prompt">${escapeHtml(activity.content.prompt)}</p>
    <div class="wyr-options">
      <button class="wyr-option-card" data-choice="a">
        ${emoji_a ? `<span class="wyr-emoji">${emoji_a}</span>` : ''}
        <span class="wyr-text">${escapeHtml(option_a)}</span>
      </button>
      <div class="wyr-divider">OR</div>
      <button class="wyr-option-card" data-choice="b">
        ${emoji_b ? `<span class="wyr-emoji">${emoji_b}</span>` : ''}
        <span class="wyr-text">${escapeHtml(option_b)}</span>
      </button>
    </div>
  `;

  wrap.querySelectorAll('.wyr-option-card').forEach((btn) => {
    btn.addEventListener('click', async () => {
      wrap.querySelectorAll('.wyr-option-card').forEach((b) => (b.disabled = true));
      btn.classList.add('selected');
      try {
        await api.activities.submit(activity.activity_id, { choice: btn.dataset.choice });
        showToast('Choice locked in ✓');
        loadNext(body);
      } catch (err) {
        showToast(err.message || 'Could not submit your choice.');
        wrap.querySelectorAll('.wyr-option-card').forEach((b) => (b.disabled = false));
      }
    });
  });

  return wrap;
}

function renderWaiting(activity) {
  const wrap = document.createElement('div');
  const partner = partnerMember();
  wrap.innerHTML = `
    <div class="waiting-illustration">
      <div class="emoji">🤔</div>
      <h3 style="margin:14px 0 6px;font-size:18px;">Your pick is locked in.</h3>
      <p class="text-muted" style="font-size:14px;line-height:1.5;">
        ${partner ? escapeHtml(partner.name) : 'Your partner'} hasn't chosen yet.
        Come back and check, or answer a few more in the meantime.
      </p>
    </div>
  `;
  return wrap;
}

function renderReveal(activity, body) {
  const wrap = document.createElement('div');
  const me = meMember();
  const partner = partnerMember();
  const { option_a, option_b, emoji_a, emoji_b } = activity.content.payload;
  const myChoice = activity.my_submission.payload.choice;
  const partnerChoice = activity.partner_submission.payload.choice;
  const matched = activity.result && activity.result.outcome === 'match';

  wrap.innerHTML = `
    <p class="wyr-prompt">${escapeHtml(activity.content.prompt)}</p>
    <div class="wyr-options">
      ${optionCard('a', option_a, emoji_a, myChoice, partnerChoice, me, partner)}
      <div class="wyr-divider">OR</div>
      ${optionCard('b', option_b, emoji_b, myChoice, partnerChoice, me, partner)}
    </div>
    <div class="wyr-result-banner ${matched ? 'match' : 'no-match'}">
      ${matched ? '🎉 You matched! +1 point each.' : '🤷 Different picks this time — no points, but hey, now you know.'}
    </div>
    <button class="btn btn-primary btn-block mt-16" id="wyr-next">Next Question</button>
  `;

  wrap.querySelector('#wyr-next').addEventListener('click', () => loadNext(body));

  return wrap;
}

function optionCard(key, text, emoji, myChoice, partnerChoice, me, partner) {
  const pickers = [];
  if (myChoice === key) pickers.push(me ? me.name : 'You');
  if (partnerChoice === key) pickers.push(partner ? partner.name : 'Partner');
  const chosen = pickers.length > 0;
  return `
    <div class="wyr-option-card ${chosen ? 'selected' : ''}">
      ${emoji ? `<span class="wyr-emoji">${emoji}</span>` : ''}
      <span class="wyr-text">${escapeHtml(text)}</span>
      ${chosen ? `<div class="wyr-pickers"><span class="chip chip-muted">${escapeHtml(pickers.join(' & '))}</span></div>` : ''}
    </div>
  `;
}
