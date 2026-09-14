import { api } from '../api.js';
import { showToast } from '../utils.js';

/**
 * Generic "Past Rounds" list for any activity_type built on the reusable
 * Activity system. Each game file supplies its own renderItem() so the
 * list can show game-specific detail (Would You Rather's match banner,
 * Know Each Other's prediction result, Who Would's unanimous/split badge)
 * while the fetch/pagination/back-button scaffolding lives in one place -
 * the same "generic mechanics here, type-specific rendering there" split
 * the Activity system itself already follows (see
 * services/activities/base.py).
 *
 * Usage from a game file:
 *   renderPastRoundsList(body, {
 *     activityType: 'would_you_rather',
 *     title: 'Past Rounds',
 *     renderItem: (activity) => { ...build and return a DOM element... },
 *     onBack: () => loadNext(body),
 *   });
 */
export function renderPastRoundsList(body, { activityType, title, renderItem, onBack }) {
  body.innerHTML = '';

  const header = document.createElement('div');
  header.className = 'back-row';
  header.innerHTML = `<button class="icon-btn" id="pr-back" aria-label="Back"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg></button>`;
  body.appendChild(header);
  header.querySelector('#pr-back').addEventListener('click', onBack);

  const heading = document.createElement('h2');
  heading.style.cssText = 'font-size:19px;margin:4px 0 14px;';
  heading.textContent = title || 'Past Rounds';
  body.appendChild(heading);

  const list = document.createElement('div');
  list.id = 'pr-list';
  body.appendChild(list);

  const moreBtn = document.createElement('button');
  moreBtn.className = 'btn btn-ghost btn-block mt-16 hidden';
  moreBtn.textContent = 'Load more';
  body.appendChild(moreBtn);

  let page = 1;

  async function load(reset) {
    if (reset) {
      list.innerHTML = '<div class="skeleton" style="height:100px;margin-bottom:10px;"></div>'.repeat(3);
    }
    let data;
    try {
      data = await api.activities.history(page, undefined, activityType);
    } catch (err) {
      showToast(err.message);
      return;
    }
    if (reset) list.innerHTML = '';

    if (data.activities.length === 0 && page === 1) {
      list.innerHTML = `
        <div class="empty-state">
          <div class="empty-emoji">📜</div>
          <h3>No past rounds yet</h3>
          <p>Play a round together and it'll show up here once you've both answered.</p>
        </div>
      `;
      moreBtn.classList.add('hidden');
      return;
    }

    data.activities.forEach((a) => list.appendChild(renderItem(a)));
    moreBtn.classList.toggle('hidden', !data.has_more);
  }

  moreBtn.addEventListener('click', () => { page += 1; load(false); });

  load(true);
}
