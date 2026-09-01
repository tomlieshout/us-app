import { api } from '../api.js';
import { escapeHtml, showToast, openModal } from '../utils.js';
import { openRoundModal } from './round.js';

export async function renderQuestions(container) {
  await renderCategoryGrid(container);
}

async function renderCategoryGrid(container) {
  container.innerHTML = `
    <h1 class="page-title">Questions</h1>
    <p class="page-subtitle">Browse by category and pick what to answer next.</p>
    <div class="category-grid">${Array(8).fill('<div class="skeleton" style="height:110px;border-radius:18px;"></div>').join('')}</div>
  `;

  let categories;
  try {
    categories = (await api.categories()).categories;
  } catch (err) {
    container.innerHTML = `<h1 class="page-title">Questions</h1><p class="text-muted mt-16">${escapeHtml(err.message)}</p>`;
    return;
  }

  const grid = document.createElement('div');
  grid.className = 'category-grid';
  categories.forEach((cat) => {
    const card = document.createElement('button');
    card.className = `category-card card-tap ${cat.locked ? 'locked' : ''}`;
    card.innerHTML = `
      <span class="emoji">${cat.emoji}</span>
      <span class="label">${escapeHtml(cat.label)}</span>
      <span class="desc">${escapeHtml(cat.description)}</span>
      ${cat.locked ? '<span class="lock-badge">🔒</span>' : ''}
    `;
    card.addEventListener('click', () => {
      if (cat.locked) {
        renderSpicyLocked(container);
      } else {
        renderQuestionList(container, cat);
      }
    });
    grid.appendChild(card);
  });

  container.innerHTML = '<h1 class="page-title">Questions</h1><p class="page-subtitle">Browse by category and pick what to answer next.</p>';
  container.appendChild(grid);
}

function renderSpicyLocked(container) {
  container.innerHTML = `
    <div class="back-row"><button class="icon-btn" id="q-back"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg></button></div>
    <div class="empty-state">
      <div class="empty-emoji">🔒</div>
      <h3>Spicy is locked</h3>
      <p>Both of you need to opt in independently before this category unlocks. Head to Settings to turn it on for your side.</p>
      <button class="btn btn-primary mt-16" id="go-settings">Go to Settings</button>
    </div>
  `;
  container.querySelector('#q-back').addEventListener('click', () => renderCategoryGrid(container));
  container.querySelector('#go-settings').addEventListener('click', () => document.querySelector('.nav-btn[data-view="settings"]').click());
}

async function renderQuestionList(container, cat) {
  container.innerHTML = `
    <div class="back-row"><button class="icon-btn" id="q-back"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg></button></div>
    <h1 class="page-title">${cat.emoji} ${escapeHtml(cat.label)}</h1>
    <p class="page-subtitle">${escapeHtml(cat.description)}</p>
    <div class="skeleton" style="height:300px;"></div>
  `;
  container.querySelector('#q-back').addEventListener('click', () => renderCategoryGrid(container));

  let questions;
  try {
    questions = (await api.questions(cat.key)).questions;
  } catch (err) {
    showToast(err.message);
    return;
  }

  const header = document.createElement('div');
  header.innerHTML = `
    <div class="back-row"><button class="icon-btn" id="q-back"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg></button></div>
    <h1 class="page-title">${cat.emoji} ${escapeHtml(cat.label)}</h1>
    <p class="page-subtitle">${escapeHtml(cat.description)}</p>
  `;

  container.innerHTML = '';
  container.appendChild(header);
  container.querySelector('#q-back').addEventListener('click', () => renderCategoryGrid(container));

  if (cat.key === 'spicy') {
    const matchesBtn = document.createElement('button');
    matchesBtn.className = 'btn btn-secondary btn-block mt-8';
    matchesBtn.textContent = '🔥 Find Your Matches';
    matchesBtn.addEventListener('click', showSpicyMatches);
    container.appendChild(matchesBtn);
  }

  const listCard = document.createElement('div');
  listCard.className = 'card mt-16';

  if (questions.length === 0) {
    listCard.innerHTML = `<div class="empty-state" style="padding:30px 10px;"><div class="empty-emoji">💭</div><p>No questions here yet.</p></div>`;
  } else {
    questions.forEach((q) => {
      const item = document.createElement('div');
      item.className = 'question-list-item';
      item.innerHTML = `
        <div style="flex:1;" class="q-tap">
          <div class="qtext">${escapeHtml(q.text)}</div>
          <div class="qmeta">${q.already_played ? 'Played before' : 'Not played yet'}</div>
        </div>
        <button class="fav-btn ${q.is_favourite ? 'active' : ''}">${q.is_favourite ? '❤️' : '🤍'}</button>
      `;
      item.querySelector('.q-tap').addEventListener('click', async () => {
        try {
          const round = await api.playQuestion(q.id);
          openRoundModal(round.round_id);
        } catch (err) {
          showToast(err.message);
        }
      });
      const favBtn = item.querySelector('.fav-btn');
      favBtn.addEventListener('click', async () => {
        try {
          if (favBtn.classList.contains('active')) {
            await api.removeFavourite(q.id);
            favBtn.classList.remove('active');
            favBtn.textContent = '🤍';
          } else {
            await api.addFavourite(q.id);
            favBtn.classList.add('active');
            favBtn.textContent = '❤️';
          }
        } catch (err) {
          showToast(err.message);
        }
      });
      listCard.appendChild(item);
    });
  }
  container.appendChild(listCard);
}

async function showSpicyMatches() {
  const { close, body } = openModal('round-modal', { title: '🔥 Find Your Matches', render: () => '<div class="skeleton" style="height:160px;"></div>' });
  try {
    const data = await api.spicyMatches();
    body.innerHTML = `
      <p class="text-muted small mt-8">Based on ${data.explored_together} question${data.explored_together === 1 ? '' : 's'} you've both answered.</p>
      ${data.mutual_matches.length > 0 ? `
        <p class="section-title">You both said yes to</p>
        ${data.mutual_matches.map((m) => `<div class="card" style="padding:14px;margin-bottom:8px;">❤️ ${escapeHtml(m)}</div>`).join('')}
      ` : `<div class="empty-state" style="padding:24px 10px;"><div class="empty-emoji">🔥</div><p>No mutual matches yet — answer a few more Intimate or Adventurous questions together.</p></div>`}
      ${data.discuss_count > 0 ? `<div class="card mt-16" style="background:var(--warn-soft);border:none;"><p style="color:var(--warn);font-size:13.5px;font-weight:600;">💬 You had different comfort levels on ${data.discuss_count} topic${data.discuss_count === 1 ? '' : 's'} — might be worth a conversation.</p></div>` : ''}
    `;
  } catch (err) {
    body.innerHTML = `<p class="text-muted" style="padding:20px 0;">${escapeHtml(err.message)}</p>`;
  }
}
