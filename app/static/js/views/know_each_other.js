import { api } from '../api.js';
import { escapeHtml, openModal, showToast } from '../utils.js';
import { meMember, partnerMember } from '../state.js';
import { createGameScreen } from './game_screen.js';

/** Opens the Know Each Other sheet. With no argument, fetches the next
 * activity in whichever toggle mode is selected. Passed a pre-fetched
 * activity (e.g. Home's daily pick), opens that specific one first
 * instead - same pattern as wyr.js's openWyrGame.
 *
 * Toggle, completion/Play Again and Past Answers all come from
 * createGameScreen (game_screen.js); this file supplies only the
 * Know-Each-Other-specific rendering. */
export function openKnowEachOtherGame(initialActivity = null) {
  const { body } = openModal('round-modal', { title: 'Know Each Other', render: () => '<div class="skeleton" style="height:300px;"></div>' });

  const screen = createGameScreen(body, {
    activityType: 'know_each_other',
    skeletonHeight: 300,
    renderActivity,
    renderMutual: renderPastMutual,
    describeMine,
    completion: {
      emoji: '🧠',
      heading: "You've answered every Know Each Other question!",
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
    slot.appendChild(renderForm(activity, screen));
  } else if (!activity.revealed) {
    slot.appendChild(renderWaiting(screen));
  } else {
    slot.appendChild(renderReveal(activity, screen));
  }
}

function renderForm(activity, screen) {
  const wrap = document.createElement('div');
  const { question_type, options, predict_text } = activity.content.payload;
  const selection = { answer_option: null, predicted_option: null };

  const header = document.createElement('h2');
  header.style.cssText = 'font-size:19px;line-height:1.35;margin:16px 0;';
  header.textContent = activity.content.prompt;
  wrap.appendChild(header);

  wrap.appendChild(sectionLabel('Your real answer'));
  wrap.appendChild(optionPicker(question_type, options, (val) => { selection.answer_option = val; updateSubmitState(); }));

  wrap.appendChild(sectionLabel(predict_text || 'What do you think your partner will say?'));
  wrap.appendChild(optionPicker(question_type, options, (val) => { selection.predicted_option = val; updateSubmitState(); }));

  const submitBtn = document.createElement('button');
  submitBtn.className = 'btn btn-primary btn-block mt-24';
  submitBtn.textContent = 'Lock In Both Answers';
  submitBtn.disabled = true;
  wrap.appendChild(submitBtn);

  function updateSubmitState() {
    submitBtn.disabled = !selection.answer_option || !selection.predicted_option;
  }

  submitBtn.addEventListener('click', async () => {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting…';
    try {
      const updated = await api.activities.submit(activity.activity_id, selection);
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
      submitBtn.textContent = 'Lock In Both Answers';
    }
  });

  return wrap;
}

function sectionLabel(text) {
  const p = document.createElement('p');
  p.className = 'section-title';
  p.style.marginTop = '18px';
  p.textContent = text;
  return p;
}

function optionPicker(questionType, options, onSelect) {
  if (questionType === 'rating') {
    const row = document.createElement('div');
    row.className = 'rating-scale';
    options.forEach((opt) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'rating-btn';
      btn.textContent = opt;
      btn.addEventListener('click', () => {
        row.querySelectorAll('.rating-btn').forEach((b) => b.classList.remove('selected'));
        btn.classList.add('selected');
        onSelect(opt);
      });
      row.appendChild(btn);
    });
    return row;
  }

  const list = document.createElement('div');
  list.className = 'answer-option-list';
  options.forEach((opt) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'answer-option';
    btn.textContent = opt;
    btn.addEventListener('click', () => {
      list.querySelectorAll('.answer-option').forEach((b) => b.classList.remove('selected'));
      btn.classList.add('selected');
      onSelect(opt);
    });
    list.appendChild(btn);
  });
  return list;
}

function renderWaiting(screen) {
  const wrap = document.createElement('div');
  const partner = partnerMember();
  wrap.innerHTML = `
    <div class="waiting-illustration">
      <div class="emoji">🧠</div>
      <h3 style="margin:14px 0 6px;font-size:18px;">Both answers locked in.</h3>
      <p class="text-muted" style="font-size:14px;line-height:1.5;">
        ${partner ? escapeHtml(partner.name) : 'Your partner'} hasn't answered yet.
        We'll reveal how well you both guessed once they have.
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
  const predictions = (activity.result && activity.result.payload && activity.result.payload.predictions) || {};
  const mine = me && predictions[String(me.id)];
  const theirs = partner && predictions[String(partner.id)];

  const header = document.createElement('h2');
  header.style.cssText = 'font-size:19px;line-height:1.35;margin:16px 0;';
  header.textContent = activity.content.prompt;
  wrap.appendChild(header);

  wrap.appendChild(revealRow(me ? me.name : 'You', activity.my_submission.payload.answer_option, me ? me.avatar_color : '#B7A8B4'));
  wrap.appendChild(revealRow(partner ? partner.name : 'Partner', activity.partner_submission.payload.answer_option, partner ? partner.avatar_color : '#B7A8B4'));

  if (mine) {
    wrap.appendChild(predictionResult(me ? me.name : 'You', mine, true));
  }
  if (theirs) {
    wrap.appendChild(predictionResult(partner ? partner.name : 'Partner', theirs, false));
  }

  return wrap;
}

function renderPastMutual(activity) {
  const card = document.createElement('div');
  card.className = 'card mt-8';
  card.style.padding = '14px';
  card.appendChild(revealBody(activity));
  return card;
}

/** One-line summary of my own answer, for the "Mine" tab - which
 * includes rounds the partner hasn't answered yet, so this must never
 * read anything but my own submission. My prediction is intentionally
 * not shown: it's about them, and showing it before the reveal would
 * spoil my own result. */
function describeMine(activity) {
  const sub = activity.my_submission;
  if (!sub || !sub.payload || !sub.payload.answer_option) return '';
  return `Your answer: ${sub.payload.answer_option}`;
}

function revealRow(name, value, color) {
  const card = document.createElement('div');
  card.className = 'reveal-answer-card';
  card.innerHTML = `
    <div class="who"><span class="avatar" style="width:22px;height:22px;font-size:10px;background:${color};">${name.charAt(0).toUpperCase()}</span> ${escapeHtml(name)}'s real answer</div>
    <p class="answer-text">${escapeHtml(value)}</p>
  `;
  return card;
}

function predictionResult(name, prediction, mine) {
  const good = prediction.points > 0;
  const el = document.createElement('div');
  el.className = `prediction-result ${good ? 'correct' : 'incorrect'}`;
  const verb = mine ? 'You' : name;
  el.textContent = `${good ? '🎯' : '🤔'} ${verb} guessed "${prediction.predicted}" — +${prediction.points} point${prediction.points === 1 ? '' : 's'}.`;
  return el;
}
