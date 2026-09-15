import { api } from '../api.js';
import { escapeHtml, openModal, showToast } from '../utils.js';
import { meMember, partnerMember } from '../state.js';
import { createGameScreen } from './game_screen.js';

/** Opens the Would You Rather sheet. With no argument, fetches the next
 * WYR activity in whichever toggle mode is selected. Passed a pre-fetched
 * activity (e.g. Home's daily pick), opens that specific one first
 * instead - "Next Question" still moves on from there. Lets Home
 * deep-link into the exact activity it displayed.
 *
 * The toggle, completion/Play Again state and Past Answers link all come
 * from createGameScreen - see game_screen.js. This file only supplies the
 * Would-You-Rather-specific rendering. */
export function openWyrGame(initialActivity = null) {
  const { body } = openModal('round-modal', { title: 'Would You Rather', render: () => '<div class="skeleton" style="height:260px;"></div>' });

  const screen = createGameScreen(body, {
    activityType: 'would_you_rather',
    skeletonHeight: 260,
    renderActivity,
    renderMutual: renderPastMutual,
    describeMine,
    completion: {
      emoji: '🎉',
      heading: "You've answered every Would You Rather question!",
      body: "That's the whole bank. Start a fresh round of them, or leave it here for now.",
    },
  });

  if (initialActivity) {
    screen.showActivity(initialActivity);
  } else {
    screen.loadNext();
  }
}

function renderActivity(slot, activity, screen) {
  slot.innerHTML = '';
  if (!activity.my_submitted) {
    slot.appendChild(renderChooser(activity, screen));
  } else if (!activity.revealed) {
    slot.appendChild(renderWaiting(activity, screen));
  } else {
    slot.appendChild(renderReveal(activity, screen));
  }
}

function renderChooser(activity, screen) {
  const wrap = document.createElement('div');
  const { option_a, option_b, emoji_a, emoji_b } = activity.content.payload;

  wrap.innerHTML = `
    <p class="wyr-prompt mt-16">${escapeHtml(activity.content.prompt)}</p>
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
        const updated = await api.activities.submit(activity.activity_id, { choice: btn.dataset.choice });
        showToast('Choice locked in ✓');
        // If this submission completed a round the partner had already
        // answered, the response is already revealed - show that reveal
        // rather than skipping straight past it to the next question.
        if (updated && updated.revealed) {
          screen.showActivity(updated);
        } else {
          screen.loadNext();
        }
      } catch (err) {
        showToast(err.message || 'Could not submit your choice.');
        wrap.querySelectorAll('.wyr-option-card').forEach((b) => (b.disabled = false));
      }
    });
  });

  return wrap;
}

function renderWaiting(activity, screen) {
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
  const nextBtn = document.createElement('button');
  nextBtn.className = 'btn btn-primary btn-block mt-16';
  nextBtn.textContent = 'Next Question';
  nextBtn.addEventListener('click', () => screen.loadNext());
  wrap.appendChild(nextBtn);
  return wrap;
}

function renderReveal(activity, screen) {
  const wrap = document.createElement('div');
  wrap.appendChild(revealBody(activity));

  const nextBtn = document.createElement('button');
  nextBtn.className = 'btn btn-primary btn-block mt-16';
  nextBtn.textContent = 'Next Question';
  nextBtn.addEventListener('click', () => screen.loadNext());
  wrap.appendChild(nextBtn);

  return wrap;
}

/** The reveal itself, with no navigation attached - shared by the live
 * reveal screen and the Past Answers "Mutual" list, so a past round looks
 * exactly like it did when it revealed. */
function revealBody(activity) {
  const wrap = document.createElement('div');
  const me = meMember();
  const partner = partnerMember();
  const { option_a, option_b, emoji_a, emoji_b } = activity.content.payload;
  const myChoice = activity.my_submission.payload.choice;
  const partnerChoice = activity.partner_submission.payload.choice;
  const matched = activity.result && activity.result.outcome === 'match';

  wrap.innerHTML = `
    <p class="wyr-prompt mt-16">${escapeHtml(activity.content.prompt)}</p>
    <div class="wyr-options">
      ${optionCard('a', option_a, emoji_a, myChoice, partnerChoice, me, partner)}
      <div class="wyr-divider">OR</div>
      ${optionCard('b', option_b, emoji_b, myChoice, partnerChoice, me, partner)}
    </div>
    <div class="wyr-result-banner ${matched ? 'match' : 'no-match'}">
      ${matched ? '🎉 You matched! +1 point each.' : '🤷 Different picks this time — no points, but hey, now you know.'}
    </div>
  `;
  return wrap;
}

function renderPastMutual(activity) {
  const card = document.createElement('div');
  card.className = 'card mt-8';
  card.style.padding = '14px';
  card.appendChild(revealBody(activity));
  return card;
}

/** One-line summary of my own choice, for the Past Answers "Mine" tab
 * (which can include rounds the partner hasn't answered yet, so it must
 * never read anything but my own submission). */
function describeMine(activity) {
  const sub = activity.my_submission;
  if (!sub || !sub.payload) return '';
  const { option_a, option_b } = activity.content.payload;
  const chosen = sub.payload.choice === 'a' ? option_a : option_b;
  return chosen ? `You chose: ${chosen}` : '';
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
