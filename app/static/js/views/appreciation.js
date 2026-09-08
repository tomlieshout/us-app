import { api } from '../api.js';
import { escapeHtml, openModal, showToast, confirmDialog, formatRelativeDate } from '../utils.js';
import { partnerMember } from '../state.js';

const REACTION_EMOJI = { love: '❤️', funny: '😂', cute: '🥹', surprised: '😮' };

export function openAppreciationMenu(initialTab = 'received') {
  const { body } = openModal('round-modal', { title: 'Appreciation', render: () => '<div class="skeleton" style="height:280px;"></div>' });
  renderTabs(body, initialTab);
}

function renderTabs(body, activeTab) {
  body.innerHTML = '';

  const writeBtn = document.createElement('button');
  writeBtn.className = 'btn btn-primary btn-block';
  writeBtn.textContent = '💌 Write an Appreciation';
  writeBtn.addEventListener('click', () => renderWriteForm(body));
  body.appendChild(writeBtn);

  const tabRow = document.createElement('div');
  tabRow.style.cssText = 'display:flex;gap:8px;margin:16px 0 14px;';
  [['received', 'Received'], ['sent', 'Sent']].forEach(([key, label]) => {
    const chip = document.createElement('button');
    chip.className = `chip ${key === activeTab ? '' : 'chip-muted'}`;
    chip.style.border = 'none';
    chip.textContent = label;
    chip.addEventListener('click', () => renderTabs(body, key));
    tabRow.appendChild(chip);
  });
  body.appendChild(tabRow);

  const listHolder = document.createElement('div');
  listHolder.innerHTML = '<div class="skeleton" style="height:180px;"></div>';
  body.appendChild(listHolder);

  if (activeTab === 'received') loadReceived(listHolder, body);
  else loadSent(listHolder);
}

function renderWriteForm(body) {
  const partner = partnerMember();
  body.innerHTML = '';
  const back = document.createElement('button');
  back.className = 'btn btn-text';
  back.style.cssText = 'padding:0;margin-bottom:10px;';
  back.textContent = '‹ Back';
  back.addEventListener('click', () => renderTabs(body, 'sent'));
  body.appendChild(back);

  const wrap = document.createElement('div');
  wrap.innerHTML = `
    <p class="page-subtitle" style="margin-top:0;">Something you appreciate about ${partner ? escapeHtml(partner.name) : 'your partner'} - big or small.</p>
    <div class="field"><textarea id="ap-message" rows="4" maxlength="500" placeholder="I love how..."></textarea></div>
    <button class="btn btn-primary btn-block" id="ap-send" disabled>Send</button>
  `;
  body.appendChild(wrap);

  const textarea = wrap.querySelector('#ap-message');
  const sendBtn = wrap.querySelector('#ap-send');
  textarea.addEventListener('input', () => { sendBtn.disabled = !textarea.value.trim(); });

  sendBtn.addEventListener('click', async () => {
    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending…';
    try {
      await api.appreciation.send(textarea.value.trim());
      showToast('Sent ✓');
      renderTabs(body, 'sent');
    } catch (err) {
      showToast(err.message);
      sendBtn.disabled = false;
      sendBtn.textContent = 'Send';
    }
  });
}

async function loadReceived(listHolder, body) {
  let data;
  try {
    data = await api.appreciation.received();
  } catch (err) {
    listHolder.innerHTML = `<p class="text-muted" style="padding:20px 0;">${escapeHtml(err.message)}</p>`;
    return;
  }
  renderList(listHolder, data.appreciations, { mine: false, onChange: () => loadReceived(listHolder, body) });
}

async function loadSent(listHolder) {
  let data;
  try {
    data = await api.appreciation.sent();
  } catch (err) {
    listHolder.innerHTML = `<p class="text-muted" style="padding:20px 0;">${escapeHtml(err.message)}</p>`;
    return;
  }
  renderList(listHolder, data.appreciations, { mine: true, onChange: () => loadSent(listHolder) });
}

function renderList(listHolder, items, { mine, onChange }) {
  listHolder.innerHTML = '';

  if (items.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.style.padding = '30px 10px';
    empty.innerHTML = mine
      ? `<div class="empty-emoji">💌</div><h3>Nothing sent yet</h3><p>Write one - it doesn't have to be big.</p>`
      : `<div class="empty-emoji">💌</div><h3>Nothing here yet</h3><p>Appreciations from your partner will show up here.</p>`;
    listHolder.appendChild(empty);
    return;
  }

  items.forEach((a) => {
    // Mark unseen received messages as seen as soon as they're rendered/viewed.
    if (!mine && !a.is_seen) {
      api.appreciation.markSeen(a.id).catch(() => {});
    }

    const card = document.createElement('div');
    card.className = 'card';
    card.style.marginBottom = '10px';
    if (!mine && !a.is_seen) card.style.borderColor = 'var(--accent)';

    card.innerHTML = `
      <div class="status-row" style="margin-bottom:8px;">
        <span class="chip chip-muted">${mine ? `To ${escapeHtml(a.recipient_name)}` : `From ${escapeHtml(a.sender_name)}`}</span>
        <span class="text-muted small">${formatRelativeDate(a.created_at)}</span>
      </div>
      <p class="answer-text">${escapeHtml(a.message_text)}</p>
    `;

    const actionRow = document.createElement('div');
    actionRow.className = 'flex-row mt-16';
    actionRow.style.gap = '8px';

    if (!mine) {
      Object.entries(REACTION_EMOJI).forEach(([type, emoji]) => {
        const btn = document.createElement('button');
        btn.className = `reaction-btn ${a.reaction_type === type ? 'active' : ''}`;
        btn.innerHTML = emoji;
        btn.addEventListener('click', async () => {
          try {
            if (a.reaction_type === type) await api.appreciation.removeReaction(a.id);
            else await api.appreciation.react(a.id, type);
            onChange();
          } catch (err) {
            showToast(err.message);
          }
        });
        actionRow.appendChild(btn);
      });

      const keepBtn = document.createElement('button');
      keepBtn.className = 'btn btn-text';
      keepBtn.style.marginLeft = 'auto';
      keepBtn.textContent = a.is_kept ? '★ Kept' : '☆ Keep';
      keepBtn.addEventListener('click', async () => {
        try {
          await api.appreciation.keep(a.id);
          onChange();
        } catch (err) {
          showToast(err.message);
        }
      });
      actionRow.appendChild(keepBtn);
    } else {
      if (a.reaction_type) {
        const reactedLabel = document.createElement('span');
        reactedLabel.className = 'chip chip-success';
        reactedLabel.textContent = `${REACTION_EMOJI[a.reaction_type]} ${a.is_seen ? 'Seen & reacted' : ''}`;
        actionRow.appendChild(reactedLabel);
      } else {
        const seenLabel = document.createElement('span');
        seenLabel.className = `chip ${a.is_seen ? 'chip-success' : 'chip-muted'}`;
        seenLabel.textContent = a.is_seen ? '✓ Seen' : 'Not seen yet';
        actionRow.appendChild(seenLabel);
      }
    }

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn btn-text';
    deleteBtn.style.color = 'var(--danger)';
    if (mine) deleteBtn.style.marginLeft = 'auto';
    deleteBtn.textContent = 'Delete';
    deleteBtn.addEventListener('click', async () => {
      const ok = await confirmDialog({
        title: 'Delete this appreciation?',
        message: 'This removes it for both of you. This can\'t be undone.',
        confirmLabel: 'Delete',
        danger: true,
      });
      if (!ok) return;
      try {
        await api.appreciation.remove(a.id);
        onChange();
      } catch (err) {
        showToast(err.message);
      }
    });
    actionRow.appendChild(deleteBtn);

    card.appendChild(actionRow);
    listHolder.appendChild(card);
  });
}
