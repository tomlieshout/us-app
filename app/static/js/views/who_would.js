import { api } from '../api.js';
import { escapeHtml, openModal, showToast } from '../utils.js';
import { meMember, partnerMember } from '../state.js';
import { createGameScreen } from './game_screen.js';

/** Opens the Who Would sheet. With no argument, fetches the next activity
 * in whichever toggle mode is selected. Passed a pre-fetched activity
 * (e.g. Home's daily pick), opens that specific one first instead - same
 * pattern as wyr.js's openWyrGame.
 *
 * Toggle, completion/Play Again and Past Answers all come from
 * createGameScreen (game_screen.js); this file supplies only the
 * Who-Would-specific rendering. */
export function openWhoWouldGame(initialActivity = null) {
  const { body } = openModal('round-modal', { title: 'Who Would...?', render: () => '<div class="skeleton" style="height:260px;"></div>' });

  const screen = createGameScreen(body, {
    activityType: 'who_would',
    skeletonHeight: 260,
    renderActivity,
    renderMutual: renderPastMutual,
    describeMine,
    completion: {
      emoji: '🤭',
      heading: "You've answered every Who Would question!",
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
    slot.appendChild(renderWaiting(screen));
  } else {
    slot.appendChild(renderReveal(activity, screen));
  }
}

function renderChooser(activity, screen) {
  const wrap = document.createElement('div');
  const partner = partnerMember();
  const selection = { choice: null, explanation: '' };

  wrap.innerHTML = `
    <p class="wyr-prompt mt-16">${escapeHtml(activity.content.prompt)}</p>
    <div class="answer-option-list mt-16">
      <button type="button" class="answer-option" data-choice="me">🙋 Me</button>
      <button type="button" class="answer-option" data-choice="partner">${partner ? escapeHtml(partner.name) : 'My partner'}</button>
    </div>
    <div class="field mt-16"><label>Why? (optional)</label><textarea id="ww-reason" rows="2" maxlength="300" placeholder="Say more if you want..."></textarea></div>
    <button class="btn btn-primary btn-block" id="ww-submit" disabled>Lock In Answer</button>
  `;

  const optionButtons = wrap.querySelectorAll('.answer-option');
  const submitBtn = wrap.querySelector('#ww-submit');
  const reasonInput = wrap.querySelector('#ww-reason');

  optionButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      optionButtons.forEach((b) => b.classList.remove('selected'));
      btn.classList.add('selected');
      selection.choice = btn.dataset.choice;
      submitBtn.disabled = false;
    });
  });
  reasonInput.addEventListener('input', () => { selection.explanation = reasonInput.value; });

  submitBtn.addEventListener('click', async () => {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting…';
    try {
      const updated = await api.activities.submit(activity.activity_id, { choice: selection.choice, explanation: selection.explanation.trim() });
      showToast('Locked in ✓');
      // Completing a round the partner had already answered reveals
      // immediately - show it rather than skipping past the reveal.
      if (updated && updated.revealed) {
        screen.showActivity(updated);
      } else {
        screen.loadNext();
      }
    } catch (err) {
      showToast(err.message || 'Could not submit.');
      submitBtn.disabled = false;
      submitBtn.textContent = 'Lock In Answer';
    }
  });

  return wrap;
}

function renderWaiting(screen) {
  const wrap = document.createElement('div');
  const partner = partnerMember();
  wrap.innerHTML = `
    <div class="waiting-illustration">
      <div class="emoji">🤭</div>
      <h3 style="margin:14px 0 6px;font-size:18px;">Your answer is locked in.</h3>
      <p class="text-muted" style="font-size:14px;line-height:1.5;">
        ${partner ? escapeHtml(partner.name) : 'Your partner'} hasn't answered yet.
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

/** The reveal itself with no navigation attached - shared by the live
 * reveal screen and Past Answers' "Mutual" tab. */
function revealBody(activity) {
  const wrap = document.createElement('div');
  const me = meMember();
  const partner = partnerMember();
  const picks = (activity.result && activity.result.payload && activity.result.payload.picks) || {};
  const unanimous = activity.result && activity.result.outcome === 'unanimous';

  const nameFor = (userId) => {
    if (me && userId === me.id) return me.name;
    if (partner && userId === partner.id) return partner.name;
    return 'Someone';
  };

  wrap.innerHTML = `<p class="wyr-prompt mt-16">${escapeHtml(activity.content.prompt)}</p>`;

  [
    { member: me, submission: activity.my_submission },
    { member: partner, submission: activity.partner_submission },
  ].forEach(({ member, submission }) => {
    if (!member || !submission) return;
    const pick = picks[String(member.id)];
    const pickedName = pick ? nameFor(pick.chose_user_id) : '?';
    const card = document.createElement('div');
    card.className = 'reveal-answer-card mt-8';
    card.innerHTML = `
      <div class="who"><span class="avatar" style="width:22px;height:22px;font-size:10px;background:${member.avatar_color};">${member.name.charAt(0).toUpperCase()}</span> ${escapeHtml(member.name)}</div>
      <p class="answer-text">${escapeHtml(pickedName)}</p>
      ${submission.payload.explanation ? `<p class="text-muted small mt-8">"${escapeHtml(submission.payload.explanation)}"</p>` : ''}
    `;
    wrap.appendChild(card);
  });

  const banner = document.createElement('div');
  banner.className = `wyr-result-banner ${unanimous ? 'match' : 'no-match'}`;
  banner.textContent = unanimous ? '😂 UNANIMOUS' : '🤷 Split decision!';
  wrap.appendChild(banner);

  return wrap;
}

function renderPastMutual(activity) {
  const card = document.createElement('div');
  card.className = 'card mt-8';
  card.style.padding = '14px';
  card.appendChild(revealBody(activity));
  return card;
}

/** One-line summary of my own pick, for the "Mine" tab - which includes
 * rounds the partner hasn't answered yet, so it must read only my own
 * submission. "me"/"partner" is relative to the submitter (see
 * services/activities/who_would.py), and this is always my submission,
 * so resolving it against my own identity is correct here. */
function describeMine(activity) {
  const sub = activity.my_submission;
  if (!sub || !sub.payload || !sub.payload.choice) return '';
  const me = meMember();
  const partner = partnerMember();
  const picked = sub.payload.choice === 'me'
    ? (me ? me.name : 'you')
    : (partner ? partner.name : 'your partner');
  return `You said: ${picked}`;
}
