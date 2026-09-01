export function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function el(html) {
  const template = document.createElement('template');
  template.innerHTML = html.trim();
  return template.content.firstElementChild;
}

export function showToast(message) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.transition = 'opacity 0.25s ease';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 260);
  }, 2400);
}

export function initials(name) {
  if (!name) return '?';
  return name.trim().charAt(0).toUpperCase();
}

const CATEGORY_ICON = {
  relationship: '❤️', know_me: '🧠', future: '🔮', random: '😂',
  deep: '💭', memories: '📸', longdistance: '🌍', spicy: '🔥',
};
export function categoryEmoji(category) { return CATEGORY_ICON[category] || '💬'; }

export function formatRelativeDate(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now - date;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays <= 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: diffDays > 300 ? 'numeric' : undefined });
}

export function applyTheme(pref) {
  const resolved = pref === 'system'
    ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
    : pref;
  document.documentElement.setAttribute('data-theme', resolved);
  try { localStorage.setItem('us_theme_pref', pref); } catch (e) { /* ignore */ }
}

/** A simple bottom-sheet / center-card modal helper.
 *  render(closeFn) must return either an HTMLElement or an HTML string. */
export function openModal(targetId, { title, render, center } = {}) {
  const modal = document.getElementById(targetId);
  modal.innerHTML = '';
  modal.classList.remove('hidden');
  modal.style.alignItems = center ? 'center' : 'flex-end';

  const backdrop = document.createElement('div');
  backdrop.className = 'modal-backdrop';
  const close = () => closeModal(targetId);
  backdrop.addEventListener('click', close);

  const sheet = document.createElement('div');
  sheet.className = center ? 'modal-sheet modal-center-card' : 'modal-sheet';

  if (!center) {
    const grabber = document.createElement('div');
    grabber.className = 'modal-grabber';
    sheet.appendChild(grabber);
  }

  if (title !== undefined) {
    const header = document.createElement('div');
    header.className = 'modal-header';
    header.innerHTML = `<h3>${escapeHtml(title)}</h3>`;
    const closeBtn = document.createElement('button');
    closeBtn.className = 'icon-btn';
    closeBtn.setAttribute('aria-label', 'Close');
    closeBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>';
    closeBtn.addEventListener('click', close);
    header.appendChild(closeBtn);
    sheet.appendChild(header);
  }

  const body = document.createElement('div');
  body.className = 'modal-body';
  const content = render(close, body);
  if (typeof content === 'string') body.innerHTML = content;
  else if (content instanceof HTMLElement) body.appendChild(content);
  sheet.appendChild(body);

  modal.appendChild(backdrop);
  modal.appendChild(sheet);

  return { close, body };
}

export function closeModal(targetId) {
  const modal = document.getElementById(targetId);
  modal.classList.add('hidden');
  modal.innerHTML = '';
}

export function confirmDialog({ title, message, confirmLabel = 'Confirm', danger = false, requireText = null }) {
  return new Promise((resolve) => {
    const { close, body } = openModal('confirm-modal', {
      center: true,
      render: () => {
        const wrap = document.createElement('div');
        wrap.innerHTML = `
          <h3 style="margin-bottom:8px;">${escapeHtml(title)}</h3>
          <p class="text-muted" style="font-size:14px;line-height:1.5;margin-bottom:18px;">${escapeHtml(message)}</p>
          ${requireText ? `<div class="field"><input type="text" id="confirm-text-input" placeholder="Type ${escapeHtml(requireText)} to confirm" autocomplete="off"></div>` : ''}
          <div style="display:flex;gap:10px;">
            <button class="btn btn-ghost btn-block" id="confirm-cancel-btn">Cancel</button>
            <button class="btn ${danger ? 'btn-danger' : 'btn-primary'} btn-block" id="confirm-ok-btn">${escapeHtml(confirmLabel)}</button>
          </div>
        `;
        return wrap;
      },
    });

    const okBtn = body.querySelector('#confirm-ok-btn');
    const cancelBtn = body.querySelector('#confirm-cancel-btn');
    const textInput = body.querySelector('#confirm-text-input');
    if (requireText) okBtn.disabled = true;
    if (textInput) {
      textInput.addEventListener('input', () => {
        okBtn.disabled = textInput.value.trim() !== requireText;
      });
    }
    cancelBtn.addEventListener('click', () => { close(); resolve(false); });
    okBtn.addEventListener('click', () => { close(); resolve(true); });
  });
}
