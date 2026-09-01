import { api, ApiError } from '../api.js';
import { escapeHtml, openModal, closeModal, showToast, confirmDialog, categoryEmoji, initials } from '../utils.js';
import { state, partnerMember, meMember } from '../state.js';

const REACTION_EMOJI = { love: '❤️', funny: '😂', cute: '🥹', surprised: '😮' };

/** Opens the round sheet and keeps it in sync as the user answers/reacts/
 * comments. `onChange` is called after anything that might affect other
 * screens (e.g. the Home streak/status), so callers can refresh themselves. */
export async function openRoundModal(roundId, { onChange } = {}) {
  const { body } = openModal('round-modal', { render: () => '<div class="skeleton" style="height:220px;"></div>' });

  async function refresh() {
    let data;
    try {
      data = await api.round(roundId);
    } catch (err) {
      body.innerHTML = `<p class="text-muted" style="padding:30px 0;text-align:center;">${escapeHtml(err.message)}</p>`;
      return;
    }
    render(data);
    if (onChange) onChange(data);
  }

  function render(data) {
    body.innerHTML = '';
    const q = data.question;

    const header = document.createElement('div');
    header.innerHTML = `
      <div class="chip ${q.category === 'spicy' ? 'chip-warn' : ''}">${categoryEmoji(q.category)} ${categoryLabel(q.category)}${q.spicy_level ? ' · ' + '🌶️'.repeat(q.spicy_level) : ''}</div>
      <h2 style="font-size:21px;line-height:1.35;margin:14px 0 18px;">${escapeHtml(q.text)}</h2>
    `;
    body.appendChild(header);

    if (!data.my_answered) {
      body.appendChild(renderAnswerForm(data, refresh));
    } else if (!data.revealed) {
      body.appendChild(renderWaiting(data));
    } else {
      body.appendChild(renderReveal(data, refresh, roundId));
    }
  }

  refresh();
}

function categoryLabel(cat) {
  const labels = {
    relationship: 'Relationship', know_me: 'How Well Do You Know Me?', future: 'Future',
    random: 'Random', deep: 'Deep', memories: 'Memories', longdistance: 'Long Distance', spicy: 'Spicy',
  };
  return labels[cat] || cat;
}

// ------------------------------------------------------------- Answer form

function renderAnswerForm(data, onSubmitted) {
  const wrap = document.createElement('div');
  const q = data.question;

  if (data.partner_answered) {
    const notice = document.createElement('div');
    notice.className = 'card';
    notice.style.background = 'var(--accent-soft)';
    notice.style.border = 'none';
    notice.style.marginBottom = '16px';
    notice.innerHTML = `<p style="color:var(--accent-strong);font-weight:600;font-size:14px;">❤️ Your partner has already answered. Your answer is hidden until you submit yours.</p>`;
    wrap.appendChild(notice);
  }

  const selection = { answer_text: null, answer_option: null, predicted_option: null, is_private: false };

  if (q.question_type === 'free_text') {
    const field = document.createElement('div');
    field.className = 'field';
    field.innerHTML = `<textarea placeholder="Type your answer..." maxlength="2000" rows="4"></textarea>`;
    const textarea = field.querySelector('textarea');
    textarea.addEventListener('input', () => { selection.answer_text = textarea.value; updateSubmitState(); });
    wrap.appendChild(field);
  } else if (q.question_type === 'prediction') {
    wrap.appendChild(sectionLabel('Your real answer'));
    wrap.appendChild(optionList(q.options, (val) => { selection.answer_option = val; updateSubmitState(); }));
    wrap.appendChild(sectionLabel(q.predict_text || 'What do you think your partner will say?'));
    wrap.appendChild(optionList(q.options, (val) => { selection.predicted_option = val; updateSubmitState(); }));
  } else if (q.question_type === 'rating' && q.options.every((o) => /^\d+$/.test(o))) {
    const row = document.createElement('div');
    row.className = 'rating-scale';
    q.options.forEach((opt) => {
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
    wrap.appendChild(optionList(q.options, (val) => { selection.answer_option = val; updateSubmitState(); }));
  }

  if (q.category === 'spicy') {
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
    if (q.question_type === 'free_text') {
      submitBtn.disabled = !selection.answer_text || !selection.answer_text.trim();
    } else if (q.question_type === 'prediction') {
      submitBtn.disabled = !selection.answer_option || !selection.predicted_option;
    } else {
      submitBtn.disabled = !selection.answer_option;
    }
  }

  submitBtn.addEventListener('click', async () => {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting…';
    try {
      await api.submitAnswer({
        round_id: data.round_id,
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

function renderWaiting(data) {
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

function renderReveal(data, refresh, roundId) {
  const wrap = document.createElement('div');
  const me = meMember();
  const partner = partnerMember();
  const q = data.question;

  wrap.appendChild(answerCard(me, data.my_answer, true));
  wrap.appendChild(answerCard(partner, data.partner_answer, false, roundId, refresh));

  if (q.question_type === 'prediction' && data.prediction) {
    const p = data.prediction;
    const mine = document.createElement('div');
    mine.className = `prediction-result ${p.i_guessed_correctly ? 'correct' : 'incorrect'}`;
    mine.textContent = p.i_guessed_correctly
      ? `🎯 You guessed right! You predicted "${p.my_prediction_of_partner}".`
      : `😂 Not quite — you guessed "${p.my_prediction_of_partner}".`;
    wrap.appendChild(mine);
  }

  if (q.category === 'spicy') {
    const delRow = document.createElement('button');
    delRow.className = 'btn btn-text mt-16';
    delRow.textContent = '🗑 Permanently delete this answer';
    delRow.addEventListener('click', async () => {
      const ok = await confirmDialog({
        title: 'Delete this answer?',
        message: 'This permanently removes this question and both answers for both of you. This can\'t be undone.',
        confirmLabel: 'Delete',
        danger: true,
      });
      if (!ok) return;
      try {
        await api.deleteSpicyRound(roundId);
        showToast('Deleted.');
        closeModal('round-modal');
      } catch (err) {
        showToast(err.message);
      }
    });
    wrap.appendChild(delRow);
  }

  wrap.appendChild(commentSection(data, roundId, refresh));

  return wrap;
}

function answerCard(member, answer, mine, roundId, refresh) {
  const card = document.createElement('div');
  card.className = `reveal-answer-card ${mine ? 'mine' : ''}`;
  const name = member ? escapeHtml(member.name) : (mine ? 'You' : 'Your partner');
  const color = member ? member.avatar_color : '#B7A8B4';

  let content;
  if (!answer) {
    content = `<p class="private-note">No answer yet.</p>`;
  } else if (answer.hidden) {
    content = `<p class="private-note">🔒 Kept private by ${name}.</p>`;
  } else {
    content = `<p class="answer-text">${escapeHtml(answer.text !== null && answer.text !== undefined ? answer.text : answer.option)}</p>`;
  }

  card.innerHTML = `
    <div class="who"><span class="avatar" style="width:22px;height:22px;font-size:10px;background:${color};">${initials(name)}</span> ${name}${mine ? ' (you)' : ''}</div>
    ${content}
  `;

  if (!mine && answer && !answer.hidden) {
    const reactionRow = document.createElement('div');
    reactionRow.className = 'reaction-row';
    Object.entries(REACTION_EMOJI).forEach(([type, emoji]) => {
      const btn = document.createElement('button');
      btn.className = 'reaction-btn';
      btn.innerHTML = emoji;
      btn.addEventListener('click', async () => {
        try {
          await api.addReaction(answer.id, type);
          showToast(`${emoji} sent`);
          refresh();
        } catch (err) {
          showToast(err.message);
        }
      });
      reactionRow.appendChild(btn);
    });
    card.appendChild(reactionRow);
  }

  return card;
}

function commentSection(data, roundId, refresh) {
  const wrap = document.createElement('div');
  wrap.className = 'mt-16';
  wrap.appendChild(sectionLabel('Conversation'));

  const list = document.createElement('div');
  list.className = 'comment-list';
  (data.comments || []).forEach((c) => {
    const bubble = document.createElement('div');
    bubble.className = 'comment-bubble';
    bubble.innerHTML = `<div class="comment-author">${escapeHtml(c.user_name)}</div>${escapeHtml(c.comment_text)}`;
    list.appendChild(bubble);
  });
  if (!data.comments || data.comments.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'text-muted small';
    empty.textContent = 'No comments yet — say something about their answer!';
    list.appendChild(empty);
  }
  wrap.appendChild(list);

  const row = document.createElement('div');
  row.className = 'comment-input-row';
  row.innerHTML = `<input type="text" maxlength="500" placeholder="Add a comment…"> <button class="btn btn-primary btn-sm">Send</button>`;
  const input = row.querySelector('input');
  const btn = row.querySelector('button');
  const send = async () => {
    const text = input.value.trim();
    if (!text) return;
    btn.disabled = true;
    try {
      await api.addComment(roundId, text);
      input.value = '';
      refresh();
    } catch (err) {
      showToast(err.message);
    } finally {
      btn.disabled = false;
    }
  };
  btn.addEventListener('click', send);
  input.addEventListener('keydown', (e) => { if (e.key === 'Enter') send(); });
  wrap.appendChild(row);

  return wrap;
}
