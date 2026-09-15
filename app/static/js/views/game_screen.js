import { api } from '../api.js';
import { escapeHtml, showToast } from '../utils.js';
import { partnerMember } from '../state.js';
import { renderPastAnswers } from './past_answers.js';

/**
 * The shared shell for Would You Rather, Know Each Other and Who Would.
 *
 * Everything these three games do identically lives here once: the
 * Answer Coordination toggle, fetching the next activity in the selected
 * mode, the bank-exhausted completion state with Play Again, and the
 * link into the three-way Past Answers view. Each game passes in only
 * the parts that are genuinely game-specific (how to render a round, how
 * to render a past mutual round, how to describe its own submission) -
 * the same generic-vs-type-specific split as
 * app/services/activities/base.py.
 *
 * Toggle modes (mirrors /api/activities/random's `mode`):
 *   unanswered       - anything I personally haven't answered this cycle.
 *   partner_pending  - specifically something my partner has already
 *                      answered, so answering completes it and reveals
 *                      right away. Never silently falls back to the other
 *                      mode: if nothing is waiting, it says so.
 */

const MODES = [
  { key: 'unanswered', label: 'Unanswered' },
  { key: 'partner_pending', label: "Partner's answered" },
];

export function createGameScreen(body, {
  activityType,
  pastAnswersTitle = 'Past Answers',
  skeletonHeight = 260,
  renderActivity,
  renderMutual,
  describeMine,
  completion = {},
}) {
  let mode = 'unanswered';

  const chrome = document.createElement('div');
  const slot = document.createElement('div');

  function mountChrome() {
    chrome.innerHTML = '';

    const toggleRow = document.createElement('div');
    toggleRow.style.cssText = 'display:flex;gap:8px;overflow-x:auto;padding-bottom:4px;';
    toggleRow.setAttribute('role', 'tablist');
    MODES.forEach((m) => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = `chip ${m.key === mode ? '' : 'chip-muted'}`;
      chip.style.cssText = 'white-space:nowrap;border:none;';
      chip.dataset.mode = m.key;
      chip.textContent = m.label;
      chip.setAttribute('role', 'tab');
      chip.setAttribute('aria-selected', m.key === mode ? 'true' : 'false');
      chip.addEventListener('click', () => {
        if (mode === m.key) return;
        mode = m.key;
        loadNext();
      });
      toggleRow.appendChild(chip);
    });
    chrome.appendChild(toggleRow);

    const pastLink = document.createElement('button');
    pastLink.type = 'button';
    pastLink.className = 'btn btn-ghost btn-block mt-8';
    pastLink.textContent = '📜 Past Answers';
    pastLink.addEventListener('click', () => openPastAnswers());
    chrome.appendChild(pastLink);
  }

  function shell() {
    body.innerHTML = '';
    mountChrome();
    body.appendChild(chrome);
    body.appendChild(slot);
  }

  function skeleton() {
    slot.innerHTML = `<div class="skeleton mt-16" style="height:${skeletonHeight}px;"></div>`;
  }

  function message(emoji, heading, text, actions = []) {
    slot.innerHTML = '';
    const wrap = document.createElement('div');
    wrap.className = 'empty-state';
    wrap.innerHTML = `
      <div class="empty-emoji">${emoji}</div>
      <h3>${escapeHtml(heading)}</h3>
      <p>${escapeHtml(text)}</p>
    `;
    actions.forEach(({ label, className, onClick }) => {
      const btn = document.createElement('button');
      btn.className = `btn ${className || 'btn-primary'} btn-block mt-16`;
      btn.textContent = label;
      btn.addEventListener('click', onClick);
      wrap.appendChild(btn);
    });
    slot.appendChild(wrap);
  }

  function showBankExhausted() {
    message(
      completion.emoji || '🎉',
      completion.heading || "You've answered every question!",
      completion.body || "That's the whole bank. Start a fresh round of them, or leave it here for now.",
      [
        {
          label: 'Play Again',
          onClick: async () => {
            try {
              await api.activities.playAgain(activityType);
            } catch (err) {
              showToast(err.message || "Couldn't start a new round.");
              return;
            }
            loadNext();
          },
        },
        { label: 'Leave it for now', className: 'btn-ghost', onClick: () => showPastAnswersOrClose() },
      ],
    );
  }

  function showPastAnswersOrClose() {
    // "Leave it" shouldn't dead-end on the same completion screen, and
    // shouldn't close the sheet out from under the person either - the
    // most useful neighbouring thing is their own history.
    openPastAnswers();
  }

  function showNothingPending() {
    const partner = partnerMember();
    message(
      '📭',
      'Nothing to catch up on',
      `Nothing waiting from ${partner ? partner.name : 'your partner'} right now.`,
      [
        {
          label: 'Show unanswered questions instead',
          onClick: () => { mode = 'unanswered'; loadNext(); },
        },
      ],
    );
  }

  function openPastAnswers() {
    renderPastAnswers(body, {
      activityType,
      title: pastAnswersTitle,
      renderMutual,
      describeMine,
      onBack: () => loadNext(),
      onOpenActivity: (activity) => showActivity(activity),
    });
  }

  async function loadNext() {
    shell();
    skeleton();

    let activity;
    try {
      activity = await api.activities.random({ activity_type: activityType, mode });
    } catch (err) {
      if (err.code === 'bank_exhausted') return showBankExhausted();
      if (err.code === 'no_pending') return showNothingPending();
      slot.innerHTML = `<p class="text-muted" style="padding:30px 0;text-align:center;">${escapeHtml(err.message)}</p>`;
      return;
    }
    renderActivity(slot, activity, screenApi);
  }

  function showActivity(activity) {
    shell();
    renderActivity(slot, activity, screenApi);
  }

  const screenApi = { loadNext, showActivity, openPastAnswers };
  return screenApi;
}
