import { api } from '../api.js';
import { escapeHtml, openModal, showToast } from '../utils.js';
import { meMember, partnerMember } from '../state.js';

/** Opens the Who Would sheet: fetch a random activity, pick "Me" or
 * "Partner" (+ an optional reason), wait for/reveal both picks, show
 * whether it was unanimous. Deliberately no scoring anywhere - see
 * WhoWouldActivity.compute_result. */
export function openWhoWouldGame() {
  const { body } = openModal('round-modal', { title: 'Who Would...?', render: () => '<div class="skeleton" style="height:260px;"></div>' });
  loadNext(body);
}

async function loadNext(body) {
  body.innerHTML = '<div class="skeleton" style="height:260px;"></div>';
  let activity;
  try {
    activity = await api.activities.random({ activity_type: 'who_would' });
  } catch (err) {
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
    body.appendChild(renderWaiting());
  } else {
    body.appendChild(renderReveal(activity, body));
  }
}

function renderChooser(activity, body) {
  const wrap = document.createElement('div');
  const partner = partnerMember();
  const selection = { choice: null, explanation: '' };

  wrap.innerHTML = `
    <p class="wyr-prompt">${escapeHtml(activity.content.prompt)}</p>
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
      await api.activities.submit(activity.activity_id, { choice: selection.choice, explanation: selection.explanation.trim() });
      showToast('Locked in ✓');
      loadNext(body);
    } catch (err) {
      showToast(err.message || 'Could not submit.');
      submitBtn.disabled = false;
      submitBtn.textContent = 'Lock In Answer';
    }
  });

  return wrap;
}

function renderWaiting() {
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
  return wrap;
}

function renderReveal(activity, body) {
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

  wrap.innerHTML = `<p class="wyr-prompt">${escapeHtml(activity.content.prompt)}</p>`;

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

  const nextBtn = document.createElement('button');
  nextBtn.className = 'btn btn-primary btn-block mt-16';
  nextBtn.textContent = 'Next Question';
  nextBtn.addEventListener('click', () => loadNext(body));
  wrap.appendChild(nextBtn);

  return wrap;
}
