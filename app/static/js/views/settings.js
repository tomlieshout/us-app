import { api } from '../api.js';
import { escapeHtml, showToast, openModal, closeModal, confirmDialog, applyTheme } from '../utils.js';
import { state, setAuth, partnerMember, meMember } from '../state.js';

const COMMON_TIMEZONES = [
  'UTC', 'Pacific/Auckland', 'Australia/Sydney', 'Australia/Perth', 'Asia/Tokyo', 'Asia/Singapore',
  'Asia/Kolkata', 'Asia/Dubai', 'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Moscow',
  'Africa/Johannesburg', 'America/Sao_Paulo', 'America/New_York', 'America/Chicago', 'America/Denver',
  'America/Los_Angeles', 'Pacific/Honolulu',
];

export async function renderSettings(container) {
  const partner = partnerMember();
  const me = meMember();
  const couple = state.couple;
  const user = state.user;

  container.innerHTML = `
    <h1 class="page-title">Settings</h1>

    <p class="section-title">Profile</p>
    <div class="settings-list">
      <button class="settings-row link" id="row-name">
        <div><div class="row-label">Your name</div><div class="row-sub">${escapeHtml(user.name)}</div></div>
        <span>›</span>
      </button>
      <div class="settings-row">
        <div class="row-label">Theme</div>
      </div>
      <div style="padding:0 18px 16px;">
        <div class="theme-picker" id="theme-picker">
          <button class="theme-option" data-theme="system">Auto</button>
          <button class="theme-option" data-theme="light">Light</button>
          <button class="theme-option" data-theme="dark">Dark</button>
        </div>
      </div>
    </div>

    <p class="section-title">Your Couple</p>
    <div class="settings-list">
      <button class="settings-row link" id="row-couple-name">
        <div><div class="row-label">Couple name</div><div class="row-sub">${escapeHtml(couple.name)}</div></div>
        <span>›</span>
      </button>
      <button class="settings-row link" id="row-timezone">
        <div><div class="row-label">Timezone</div><div class="row-sub">${escapeHtml(couple.timezone)} — used for the daily question</div></div>
        <span>›</span>
      </button>
      ${!couple.is_complete ? `
      <button class="settings-row link" id="row-invite">
        <div><div class="row-label">Invite code</div><div class="row-sub">Share this with your partner: ${escapeHtml(couple.invite_code)}</div></div>
        <span>›</span>
      </button>` : ''}
    </div>

    <p class="section-title">Spicy Questions</p>
    <div class="card">
      <p style="font-size:14px;line-height:1.5;color:var(--text-muted);">🔥 Explore more intimate questions together. Both of you need to opt in independently, and either of you can turn it off anytime.</p>
      <div class="settings-row" style="padding:14px 0 0;border:none;">
        <div class="row-label">Enabled for you</div>
        <button class="toggle ${me && me_spicy_on(user) ? 'on' : ''}" id="spicy-toggle"></button>
      </div>
      <p class="text-muted small mt-8">
        ${partner ? escapeHtml(partner.name) : 'Your partner'}: ${couple.spicy_unlocked ? 'enabled ✓' : 'not enabled yet'}
      </p>
    </div>

    <p class="section-title">Account</p>
    <div class="settings-list">
      <button class="settings-row link" id="row-password">
        <div class="row-label">Change password</div><span>›</span>
      </button>
      <button class="settings-row link" id="row-logout">
        <div class="row-label">Log out</div><span>›</span>
      </button>
    </div>

    <p class="section-title">Danger Zone</p>
    <div class="settings-list">
      <button class="settings-row danger" id="row-delete-answers">
        <div><div class="row-label">Delete my answers</div><div class="row-sub" style="color:var(--text-muted);">Erases the content of everything you've answered</div></div>
      </button>
      <button class="settings-row danger" id="row-delete-account">
        <div><div class="row-label">Delete my account</div><div class="row-sub" style="color:var(--text-muted);">Removes your login and personal content</div></div>
      </button>
      <button class="settings-row danger" id="row-delete-couple">
        <div><div class="row-label">Delete our couple</div><div class="row-sub" style="color:var(--text-muted);">Permanently deletes everything for both of you</div></div>
      </button>
    </div>
    <div style="height:20px;"></div>
  `;

  // Theme picker
  const pref = user.dark_mode_pref || 'system';
  container.querySelectorAll('#theme-picker .theme-option').forEach((btn) => {
    if (btn.dataset.theme === pref) btn.classList.add('selected');
    btn.addEventListener('click', async () => {
      container.querySelectorAll('#theme-picker .theme-option').forEach((b) => b.classList.remove('selected'));
      btn.classList.add('selected');
      applyTheme(btn.dataset.theme);
      try {
        const updated = await api.updateProfile({ dark_mode_pref: btn.dataset.theme });
        setAuth(updated, state.couple);
      } catch (err) { /* theme still applied locally even if the save fails */ }
    });
  });

  container.querySelector('#row-name').addEventListener('click', () => {
    openTextEditModal('Your name', user.name, async (value) => {
      const updated = await api.updateProfile({ name: value });
      setAuth(updated, state.couple);
      renderSettings(container);
    });
  });

  container.querySelector('#row-couple-name').addEventListener('click', () => {
    openTextEditModal('Couple name', couple.name, async (value) => {
      const updatedCouple = await api.updateCouple({ name: value });
      setAuth(state.user, updatedCouple);
      renderSettings(container);
    });
  });

  container.querySelector('#row-timezone').addEventListener('click', () => {
    openTimezoneModal(couple.timezone, async (value) => {
      const updatedCouple = await api.updateCouple({ timezone: value });
      setAuth(state.user, updatedCouple);
      showToast('Timezone updated');
      renderSettings(container);
    });
  });

  const inviteRow = container.querySelector('#row-invite');
  if (inviteRow) {
    inviteRow.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(couple.invite_code);
        showToast('Invite code copied');
      } catch (e) {
        showToast(couple.invite_code);
      }
    });
  }

  container.querySelector('#spicy-toggle').addEventListener('click', async () => {
    const currentlyOn = me_spicy_on(user);
    if (currentlyOn) {
      await api.setSpicy(false);
      const me2 = await api.me();
      setAuth(me2.user, me2.couple);
      renderSettings(container);
      return;
    }
    const ok = await confirmDialog({
      title: 'Enable Spicy questions?',
      message: "This category contains mature relationship and intimacy topics. Only enable it if you're both comfortable exploring them together, and if you're an adult.",
      confirmLabel: 'Enable for me',
    });
    if (!ok) return;
    try {
      const result = await api.setSpicy(true, true);
      setAuth(result.user, result.couple);
      showToast(result.couple.spicy_unlocked ? 'Spicy unlocked for both of you 🔥' : "Enabled — waiting on your partner too");
      renderSettings(container);
    } catch (err) {
      showToast(err.message);
    }
  });

  container.querySelector('#row-password').addEventListener('click', openPasswordModal);

  container.querySelector('#row-logout').addEventListener('click', async () => {
    await api.logout();
    window.location.reload();
  });

  container.querySelector('#row-delete-answers').addEventListener('click', async () => {
    const ok = await confirmDialog({
      title: 'Delete all your answers?',
      message: "This erases the content of every answer you've ever submitted. Rounds your partner already saw stay revealed to them, but the content will be gone.",
      confirmLabel: 'Delete answers',
      danger: true,
    });
    if (!ok) return;
    await api.deleteMyAnswers();
    showToast('Your answers have been deleted.');
  });

  container.querySelector('#row-delete-account').addEventListener('click', async () => {
    const ok = await confirmDialog({
      title: 'Delete your account?',
      message: 'This removes your login and personal content. This cannot be undone.',
      confirmLabel: 'Delete account',
      danger: true,
      requireText: 'DELETE',
    });
    if (!ok) return;
    await api.deleteAccount();
    window.location.reload();
  });

  container.querySelector('#row-delete-couple').addEventListener('click', async () => {
    const ok = await confirmDialog({
      title: 'Delete your couple?',
      message: 'This permanently deletes everything — every question, answer, memory and account — for both of you. This cannot be undone.',
      confirmLabel: 'Delete everything',
      danger: true,
      requireText: 'DELETE',
    });
    if (!ok) return;
    try {
      await api.deleteCouple('DELETE');
      window.location.reload();
    } catch (err) {
      showToast(err.message);
    }
  });
}

function me_spicy_on(user) {
  return !!user.spicy_opt_in;
}

function openTextEditModal(title, initialValue, onSave) {
  const { close, body } = openModal('round-modal', {
    center: true,
    render: () => {
      const wrap = document.createElement('div');
      wrap.innerHTML = `
        <h3 style="margin-bottom:14px;">${escapeHtml(title)}</h3>
        <div class="field"><input type="text" id="edit-input" value="${escapeHtml(initialValue || '')}"></div>
        <div style="display:flex;gap:10px;">
          <button class="btn btn-ghost btn-block" id="edit-cancel">Cancel</button>
          <button class="btn btn-primary btn-block" id="edit-save">Save</button>
        </div>
      `;
      return wrap;
    },
  });
  body.querySelector('#edit-cancel').addEventListener('click', close);
  body.querySelector('#edit-save').addEventListener('click', async () => {
    const value = body.querySelector('#edit-input').value.trim();
    if (!value) return;
    try {
      await onSave(value);
      close();
    } catch (err) {
      showToast(err.message);
    }
  });
}

function openTimezoneModal(current, onSave) {
  const { close, body } = openModal('round-modal', {
    center: true,
    render: () => {
      const wrap = document.createElement('div');
      wrap.innerHTML = `
        <h3 style="margin-bottom:14px;">Timezone</h3>
        <p class="text-muted small mt-8" style="margin-bottom:14px;">Used to decide when a new day's question appears.</p>
        <div class="field">
          <select id="tz-select" style="width:100%;padding:13px 14px;border-radius:12px;border:1.5px solid var(--border-strong);background:var(--surface);color:var(--text);">
            ${COMMON_TIMEZONES.map((tz) => `<option value="${tz}" ${tz === current ? 'selected' : ''}>${tz}</option>`).join('')}
          </select>
        </div>
        <div style="display:flex;gap:10px;">
          <button class="btn btn-ghost btn-block" id="tz-cancel">Cancel</button>
          <button class="btn btn-primary btn-block" id="tz-save">Save</button>
        </div>
      `;
      return wrap;
    },
  });
  body.querySelector('#tz-cancel').addEventListener('click', close);
  body.querySelector('#tz-save').addEventListener('click', async () => {
    try {
      await onSave(body.querySelector('#tz-select').value);
      close();
    } catch (err) {
      showToast(err.message);
    }
  });
}

function openPasswordModal() {
  const { close, body } = openModal('round-modal', {
    center: true,
    render: () => {
      const wrap = document.createElement('div');
      wrap.innerHTML = `
        <h3 style="margin-bottom:14px;">Change password</h3>
        <div class="field"><label>Current password</label><input type="password" id="pw-current" autocomplete="current-password"></div>
        <div class="field"><label>New password</label><input type="password" id="pw-new" autocomplete="new-password" minlength="8"></div>
        <div id="pw-error" class="field-error hidden"></div>
        <div style="display:flex;gap:10px;">
          <button class="btn btn-ghost btn-block" id="pw-cancel">Cancel</button>
          <button class="btn btn-primary btn-block" id="pw-save">Save</button>
        </div>
      `;
      return wrap;
    },
  });
  body.querySelector('#pw-cancel').addEventListener('click', close);
  body.querySelector('#pw-save').addEventListener('click', async () => {
    const errorBox = body.querySelector('#pw-error');
    errorBox.classList.add('hidden');
    try {
      await api.changePassword({
        current_password: body.querySelector('#pw-current').value,
        new_password: body.querySelector('#pw-new').value,
      });
      showToast('Password updated');
      close();
    } catch (err) {
      errorBox.textContent = err.message;
      errorBox.classList.remove('hidden');
    }
  });
}
