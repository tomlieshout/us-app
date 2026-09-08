import { api } from '../api.js';
import { escapeHtml, openModal, showToast } from '../utils.js';
import { partnerMember, meMember } from '../state.js';

/** Opens the activity sheet and keeps it in sync as the user submits.
 * `onChange` is called after anything that might affect other screens
 * (e.g. the Home streak/status), so callers can refresh themselves.
 *
 * NOTE (architectural-integration phase): reactions and comments are not
 * shown here yet - ActivityReaction/ActivityComment don't exist as
 * tables yet, only the legacy Reaction/Comment do, and those are keyed to
 * legacy Round/Answer ids, not Activity ids, so wiring them here would
 * either silently do nothing or hit the wrong row. Deferred and flagged,
 * not silently dropped - see the summary given alongside this change. */
export async function openActivityModal(activityId, { onChange } = {}) {
  const { body } = openModal('round-modal', { render: () => '<div class="skeleton" style="height:220px;"></div>' });

  async function refresh() {
    let data;
    try {
      data = await api.activities.get(activityId);
    } catch (err) {
      body.innerHTML = `<p class="text-muted" style="padding:30px 0;text-align:center;">${escapeHtml(err.message)}</p>`;
      return;
    }
    render(data);
    if (onChange) onChange(data);
  }

  function render(data) {
    body.innerHTML = '';
    const content = data.content;

    const header = document.createElement('div');
    header.innerHTML = `
      <div class="chip ${content.category === 'spicy' ? 'chip-warn' : ''}">${categoryEmoji(content.category)} ${categoryLabel(content.category)}${content.spicy_level ? ' · ' + '🌶️'.repeat(content.spicy_level) : ''}</div>
      <h2 style="font-size:21px;line-height:1.35;margin:14px 0 18px;">${escapeHtml(content.prompt)}</h2>
    `;
    body.appendChild(header);

    if (!data.my_submitted) {
      body.appendChild(renderSubmitForm(data, refresh));
    } else if (!data.revealed) {
      body.appendChild(renderWaiting(data));
    } else {
      body.appendChild(renderReveal(data));
    }
  }

  refresh();
}

function categoryEmoji(cat) {
  const map = { relationship: '❤️', know_me: '🧠', future: '🔮', random: '😂', deep: '💭', memories: '📸', longdistance: '🌍', spicy: '🔥' };
  return map[cat] || '💬';
}

function categoryLabel(cat) {
  const labels = {
    relationship: 'Relationship', know_me: 'How Well Do You Know Me?', future: 'Future',
    random: 'Random', deep: 'Deep', memories: 'Memories', longdistance: 'Long Distance', spicy: 'Spicy',
  };
  return labels[cat] || cat;
}

// ------------------------------------------------------------- Submit form

function renderSubmitForm(data, onSubmitted) {
  const wrap = document.createElement('div');
  const content = data.content;
  const qtype = content.payload.question_type;
  const options = content.payload.options || [];

  if (data.partner_submitted) {
    const notice = document.createElement('div');
    notice.className = 'card';
    notice.style.background = 'var(--accent-soft)';
    notice.style.border = 'none';
    notice.style.marginBottom = '16px';
    notice.innerHTML = `<p style="color:var(--accent-strong);font-weight:600;font-size:14px;">❤️ Your partner has already answered. Your answer is hidden until you submit yours.</p>`;
    wrap.appendChild(notice);
  }

  const selection = { answer_text: null, answer_option: null, predicted_option: null, is_private: false };

  if (qtype === 'free_text') {
    const field = document.createElement('div');
    field.className = 'field';
    field.innerHTML = `<textarea placeholder="Type your answer..." maxlength="2000" rows="4"></textarea>`;
    const textarea = field.querySelector('textarea');
    textarea.addEventListener('input', () => { selection.answer_text = textarea.value; updateSubmitState(); });
    wrap.appendChild(field);
  } else if (qtype === 'prediction') {
    wrap.appendChild(sectionLabel('Your real answer'));
    wrap.appendChild(optionList(options, (val) => { selection.answer_option = val; updateSubmitState(); }));
    wrap.appendChild(sectionLabel(content.payload.predict_text || 'What do you think your partner will say?'));
    wrap.appendChild(optionList(options, (val) => { selection.predicted_option = val; updateSubmitState(); }));
  } else if (qtype === 'rating' && options.every((o) => /^\d+$/.test(o))) {
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
        selection.answer_option = opt;
        updateSubmitState();
      });
      row.appendChild(btn);
    });
    wrap.appendChild(row);
  } else {
    wrap.appendChild(optionList(options, (val) => { selection.answer_option = val; updateSubmitState(); }));
  }

  if (content.category === 'spicy') {
    const privacyRow = document.createElement('label');
    privacyRow.className = 'flex-row mt-16';
    privacyRow.style.gap = '10px';
    privacyRow.style.fontSize = '13.5px';
    privacyRow.style.color = 'var(--text-muted)';
    privacyRow.innerHTML = `<input type="checkbox" style="width:18px;height:18px;"> 🔒 Keep this answer private (your partner won't see the content, just that you answered)`;
    privacyRow.querySelector('input').addEventListener('change', (e) => { selection.is_private = e.target.checked; });
    wrap.appendChild(privacyRow);
  }

  const submitBtn = document.createElement('button');
  submitBtn.className = 'btn btn-primary btn-block mt-24';
  submitBtn.textContent = 'Lock In Answer';
  submitBtn.disabled = true;
  wrap.appendChild(submitBtn);

  function updateSubmitState() {
    if (qtype === 'free_text') {
      submitBtn.disabled = !selection.answer_text || !selection.answer_text.trim();
    } else if (qtype === 'prediction') {
      submitBtn.disabled = !selection.answer_option || !selection.predicted_option;
    } else {
      submitBtn.disabled = !selection.answer_option;
    }
  }

  submitBtn.addEventListener('click', async () => {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting…';
    try {
      await api.activities.submit(data.activity_id, {
        answer_text: selection.answer_text || undefined,
        answer_option: selection.answer_option || undefined,
        predicted_option: selection.predicted_option || undefined,
        is_private: selection.is_private,
      });
      showToast('Answer locked in ✓');
      onSubmitted();
    } catch (err) {
      showToast(err.message || 'Could not submit your answer.');
      submitBtn.disabled = false;
      submitBtn.textContent = 'Lock In Answer';
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

function optionList(options, onSelect) {
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

// ------------------------------------------------------------------ Waiting

function renderWaiting() {
  const wrap = document.createElement('div');
  const partner = partnerMember();
  wrap.innerHTML = `
    <div class="waiting-illustration">
      <div class="emoji">💌</div>
      <h3 style="margin:14px 0 6px;font-size:18px;">Your answer is locked in.</h3>
      <p class="text-muted" style="font-size:14px;line-height:1.5;">
        ${partner ? escapeHtml(partner.name) : 'Your partner'} hasn't answered yet.
        We'll reveal both answers the moment you're both finished — no rush.
      </p>
    </div>
  `;
  return wrap;
}

// ------------------------------------------------------------------- Reveal

function renderReveal(data) {
  const wrap = document.createElement('div');
  const me = meMember();
  const partner = partnerMember();

  wrap.appendChild(submissionCard(me, data.my_submission, true));
  wrap.appendChild(submissionCard(partner, data.partner_submission, false));

  if (data.result && data.content.payload.question_type === 'prediction' && data.result.payload && data.result.payload.predictions) {
    const meCorrect = me && data.result.payload.predictions[String(me.id)];
    if (meCorrect) {
      const el = document.createElement('div');
      el.className = `prediction-result ${meCorrect.correct ? 'correct' : 'incorrect'}`;
      el.textContent = meCorrect.correct
        ? `🎯 You guessed right! You predicted "${data.my_submission.payload.predicted_option}".`
        : `😂 Not quite — you guessed "${data.my_submission.payload.predicted_option}".`;
      wrap.appendChild(el);
    }
  } else if (data.result && data.result.is_competitive) {
    const el = document.createElement('div');
    el.className = `prediction-result ${data.result.outcome === 'match' || data.result.outcome === 'exact' ? 'correct' : 'incorrect'}`;
    const label = { match: '🎉 You matched!', no_match: '🤔 Different picks this time.', exact: '🎯 Exact match!', close: '👍 Close!', different: '🤷 Pretty different answers.' }[data.result.outcome] || data.result.outcome;
    el.textContent = label;
    wrap.appendChild(el);
  }

  const note = document.createElement('p');
  note.className = 'text-muted small mt-16';
  note.textContent = 'Reactions and comments are coming soon for questions played this way.';
  wrap.appendChild(note);

  return wrap;
}

function submissionCard(member, submission, mine) {
  const card = document.createElement('div');
  card.className = `reveal-answer-card ${mine ? 'mine' : ''}`;
  const name = member ? escapeHtml(member.name) : (mine ? 'You' : 'Your partner');
  const color = member ? member.avatar_color : '#B7A8B4';

  let content;
  if (!submission) {
    content = `<p class="private-note">No answer yet.</p>`;
  } else if (submission.hidden) {
    content = `<p class="private-note">🔒 Kept private by ${name}.</p>`;
  } else {
    const value = submission.payload.answer_text !== null && submission.payload.answer_text !== undefined
      ? submission.payload.answer_text
      : submission.payload.answer_option;
    content = `<p class="answer-text">${escapeHtml(value)}</p>`;
  }

  card.innerHTML = `
    <div class="who"><span class="avatar" style="width:22px;height:22px;font-size:10px;background:${color};">${name.charAt(0).toUpperCase()}</span> ${name}${mine ? ' (you)' : ''}</div>
    ${content}
  `;
  return card;
}
