import { api } from '../api.js';
import { escapeHtml, openModal, formatRelativeDate } from '../utils.js';
import { openAppreciationMenu } from './appreciation.js';

/** In-app notifications: a small bell + count badge in the topbar (see
 * app/templates/index.html), backed entirely by app/routes/notifications.py.
 * Deliberately simple: opening the panel marks everything seen (standard
 * "read on view" behaviour, no separate per-item dismiss action), and
 * tapping a notification navigates to the relevant TAB rather than
 * deep-linking to the exact item - see app/services/notifications.py's
 * docstring for why. Appreciation is the one exception, since there's
 * already a one-line reusable opener for it (openAppreciationMenu). */

const TAB_FOR_TYPE = {
  plan_added: 'plans',
  shared_match: 'plans',
  new_champion: 'stats',
};

function goToTab(viewName) {
  const btn = document.querySelector(`.nav-btn[data-view="${viewName}"]`);
  if (btn) btn.click();
}

function handleTap(notification) {
  if (notification.type === 'appreciation_received') {
    openAppreciationMenu('received');
    return;
  }
  if (notification.type === 'game_answered' || notification.type === 'game_ready') {
    goToTab(notification.activity_type === 'classic_question' ? 'questions' : 'games');
    return;
  }
  const tab = TAB_FOR_TYPE[notification.type];
  if (tab) goToTab(tab);
}

export async function refreshNotificationBadge() {
  const badge = document.getElementById('topbar-notif-badge');
  if (!badge) return;
  try {
    const data = await api.notifications.list();
    const count = data.unseen_count;
    badge.textContent = count > 9 ? '9+' : String(count);
    badge.classList.toggle('hidden', count === 0);
  } catch (err) {
    // Badge just stays as it was - not worth surfacing a toast for this.
  }
}

export async function openNotificationsPanel() {
  const { body, close } = openModal('round-modal', {
    title: 'Notifications',
    render: () => '<div class="skeleton" style="height:200px;"></div>',
  });

  let data;
  try {
    data = await api.notifications.list();
  } catch (err) {
    body.innerHTML = `<p class="text-muted">${escapeHtml(err.message)}</p>`;
    return;
  }

  body.innerHTML = '';
  if (data.notifications.length === 0) {
    body.innerHTML = '<p class="text-muted small" style="padding:8px 0;">No notifications yet.</p>';
  } else {
    data.notifications.forEach((n) => {
      const item = document.createElement('button');
      item.className = `notif-item${n.is_seen ? '' : ' unseen'}`;
      item.innerHTML = `
        ${n.is_seen ? '' : '<span class="notif-dot"></span>'}
        <span>
          <span class="notif-text">${escapeHtml(n.text)}</span>
          <span class="notif-time">${formatRelativeDate(n.created_at)}</span>
        </span>
      `;
      item.addEventListener('click', () => {
        close();
        handleTap(n);
      });
      body.appendChild(item);
    });
  }

  // Opening the panel is what marks everything seen - the badge clears
  // once the person has actually had a chance to look, not before.
  if (data.unseen_count > 0) {
    try {
      await api.notifications.markSeen();
      refreshNotificationBadge();
    } catch (err) {
      // Non-fatal - the list was still shown correctly either way.
    }
  }
}
