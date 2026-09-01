import { api, ApiError } from '../api.js';
import { escapeHtml, showToast } from '../utils.js';

export function renderOnboarding(container, onAuthed) {
  showWelcome();

  function showWelcome() {
    container.innerHTML = `
      <div class="screen screen-center">
        <div class="onboard-logo">❤</div>
        <h1 class="onboard-title">Us</h1>
        <p class="onboard-sub">A private question game for two. Answer independently, reveal your answers together.</p>
        <div class="onboard-actions">
          <button class="btn btn-primary btn-block" id="btn-create">Create a Couple</button>
          <button class="btn btn-ghost btn-block" id="btn-join">Join a Couple</button>
          <button class="btn btn-text" id="btn-login">Already have an account? Log in</button>
        </div>
      </div>
    `;
    container.querySelector('#btn-create').addEventListener('click', showCreate);
    container.querySelector('#btn-join').addEventListener('click', showJoin);
    container.querySelector('#btn-login').addEventListener('click', showLogin);
  }

  function backButton(onClick) {
    return `<button class="icon-btn" id="btn-back" style="margin-left:-8px;"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg></button>`;
  }

  function showCreate() {
    container.innerHTML = `
      <div class="screen">
        <div class="back-row">${backButton()}</div>
        <h2 class="page-title">Create your couple</h2>
        <p class="page-subtitle">You'll get an invite code to share with your partner next.</p>
        <form id="create-form">
          <div class="field"><label>Your name</label><input type="text" name="name" required autocomplete="name"></div>
          <div class="field"><label>Username</label><input type="text" name="username" required autocomplete="username" pattern="[a-zA-Z0-9_.\\-]{3,30}"></div>
          <div class="field"><label>Email (optional)</label><input type="email" name="email" autocomplete="email"></div>
          <div class="field"><label>Password</label><input type="password" name="password" required minlength="8" autocomplete="new-password"></div>
          <div id="create-error" class="field-error hidden"></div>
          <button type="submit" class="btn btn-primary btn-block mt-16">Continue</button>
        </form>
      </div>
    `;
    container.querySelector('#btn-back').addEventListener('click', showWelcome);
    container.querySelector('#create-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const form = e.target;
      const errorBox = container.querySelector('#create-error');
      errorBox.classList.add('hidden');
      const submitBtn = form.querySelector('button[type=submit]');
      submitBtn.disabled = true;
      try {
        const data = await api.registerCouple({
          name: form.name.value.trim(),
          username: form.username.value.trim(),
          email: form.email.value.trim() || null,
          password: form.password.value,
        });
        showInviteCode(data.couple.invite_code);
      } catch (err) {
        errorBox.textContent = err.message;
        errorBox.classList.remove('hidden');
        submitBtn.disabled = false;
      }
    });
  }

  function showInviteCode(code) {
    container.innerHTML = `
      <div class="screen screen-center">
        <div class="onboard-logo">💌</div>
        <h2 class="onboard-title" style="font-size:24px;">You're in!</h2>
        <p class="onboard-sub">Share this invite code with your partner so they can join your couple.</p>
        <div class="invite-code-display">${escapeHtml(code)}</div>
        <div class="onboard-actions">
          <button class="btn btn-primary btn-block" id="btn-copy">Copy Code</button>
          <button class="btn btn-ghost btn-block" id="btn-continue">Continue to Us</button>
        </div>
      </div>
    `;
    container.querySelector('#btn-copy').addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(code);
        showToast('Copied!');
      } catch (e) {
        showToast('Copy this code: ' + code);
      }
    });
    container.querySelector('#btn-continue').addEventListener('click', () => onAuthed());
  }

  function showJoin() {
    container.innerHTML = `
      <div class="screen">
        <div class="back-row">${backButton()}</div>
        <h2 class="page-title">Join your partner</h2>
        <p class="page-subtitle">Enter the invite code they shared with you.</p>
        <form id="join-form">
          <div class="field"><label>Invite code</label><input type="text" name="invite_code" required autocomplete="off" style="text-transform:uppercase;letter-spacing:0.1em;" maxlength="6"></div>
          <div class="field"><label>Your name</label><input type="text" name="name" required autocomplete="name"></div>
          <div class="field"><label>Username</label><input type="text" name="username" required autocomplete="username" pattern="[a-zA-Z0-9_.\\-]{3,30}"></div>
          <div class="field"><label>Email (optional)</label><input type="email" name="email" autocomplete="email"></div>
          <div class="field"><label>Password</label><input type="password" name="password" required minlength="8" autocomplete="new-password"></div>
          <div id="join-error" class="field-error hidden"></div>
          <button type="submit" class="btn btn-primary btn-block mt-16">Join Couple</button>
        </form>
      </div>
    `;
    container.querySelector('#btn-back').addEventListener('click', showWelcome);
    container.querySelector('#join-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const form = e.target;
      const errorBox = container.querySelector('#join-error');
      errorBox.classList.add('hidden');
      const submitBtn = form.querySelector('button[type=submit]');
      submitBtn.disabled = true;
      try {
        await api.joinCouple({
          invite_code: form.invite_code.value.trim(),
          name: form.name.value.trim(),
          username: form.username.value.trim(),
          email: form.email.value.trim() || null,
          password: form.password.value,
        });
        onAuthed();
      } catch (err) {
        errorBox.textContent = err.message;
        errorBox.classList.remove('hidden');
        submitBtn.disabled = false;
      }
    });
  }

  function showLogin() {
    container.innerHTML = `
      <div class="screen">
        <div class="back-row">${backButton()}</div>
        <h2 class="page-title">Welcome back</h2>
        <p class="page-subtitle">Log in to your account.</p>
        <form id="login-form">
          <div class="field"><label>Username</label><input type="text" name="username" required autocomplete="username"></div>
          <div class="field"><label>Password</label><input type="password" name="password" required autocomplete="current-password"></div>
          <div id="login-error" class="field-error hidden"></div>
          <button type="submit" class="btn btn-primary btn-block mt-16">Log In</button>
        </form>
      </div>
    `;
    container.querySelector('#btn-back').addEventListener('click', showWelcome);
    container.querySelector('#login-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const form = e.target;
      const errorBox = container.querySelector('#login-error');
      errorBox.classList.add('hidden');
      const submitBtn = form.querySelector('button[type=submit]');
      submitBtn.disabled = true;
      try {
        await api.login({ username: form.username.value.trim(), password: form.password.value });
        onAuthed();
      } catch (err) {
        errorBox.textContent = err.message;
        errorBox.classList.remove('hidden');
        submitBtn.disabled = false;
      }
    });
  }
}
