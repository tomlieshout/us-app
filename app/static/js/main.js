import { api } from './api.js';
import { escapeHtml, initials, applyTheme } from './utils.js';
import { state, setAuth } from './state.js';
import { renderOnboarding } from './views/onboarding.js';
import { renderHome } from './views/home.js';
import { renderGames } from './views/games.js';
import { renderQuestions } from './views/questions.js';
import { renderMemories } from './views/memories.js';
import { renderPlans } from './views/plans.js';
import { renderHistory } from './views/history.js';
import { renderStats } from './views/stats.js';
import { renderSettings } from './views/settings.js';

const VIEWS = {
  home: renderHome,
  games: renderGames,
  questions: renderQuestions,
  memories: renderMemories,
  plans: renderPlans,
  history: renderHistory,
  stats: renderStats,
  settings: renderSettings,
};

let currentView = 'home';

async function boot() {
  let me;
  try {
    me = await api.me();
  } catch (err) {
    me = { authenticated: false };
  }

  document.getElementById('view-loading').classList.add('hidden');

  if (!me.authenticated) {
    const onboardingEl = document.getElementById('view-onboarding');
    onboardingEl.classList.remove('hidden');
    renderOnboarding(onboardingEl, async () => {
      onboardingEl.classList.add('hidden');
      onboardingEl.innerHTML = '';
      await boot();
    });
    return;
  }

  setAuth(me.user, me.couple);
  applyTheme(me.user.dark_mode_pref || 'system');
  showAppShell();
}

function showAppShell() {
  document.getElementById('view-onboarding').classList.add('hidden');
  const shell = document.getElementById('app-shell');
  shell.classList.remove('hidden');
  renderTopbar();
  wireNav();
  switchView('home');
}

function renderTopbar() {
  const couple = state.couple;
  document.getElementById('topbar-couple-name').textContent = couple.name;
  const avatarWrap = document.getElementById('topbar-avatars');
  avatarWrap.innerHTML = couple.members
    .map((m) => `<span class="avatar" style="background:${escapeHtml(m.avatar_color)};">${initials(m.name)}</span>`)
    .join('');
}

function wireNav() {
  document.querySelectorAll('.nav-btn').forEach((btn) => {
    btn.addEventListener('click', () => switchView(btn.dataset.view));
  });
  document.getElementById('topbar-settings-btn').addEventListener('click', () => switchView('settings'));
}

function switchView(viewName) {
  currentView = viewName;
  document.querySelectorAll('.nav-btn').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.view === viewName);
  });
  document.querySelectorAll('.view').forEach((section) => {
    section.classList.toggle('hidden', section.id !== `view-${viewName}`);
  });
  document.getElementById('view-container').scrollTop = 0;
  const renderFn = VIEWS[viewName];
  const container = document.getElementById(`view-${viewName}`);
  if (renderFn) renderFn(container);
}

// Re-render the current view when returning to the tab/app, so a daily
// question created on the partner's phone shows up without a manual reload.
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && state.user) {
    const renderFn = VIEWS[currentView];
    const container = document.getElementById(`view-${currentView}`);
    if (renderFn) renderFn(container);
  }
});

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => { /* offline shell just won't be available */ });
  });
}

boot();
