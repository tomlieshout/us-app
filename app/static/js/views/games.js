import { openWyrGame } from './wyr.js';
import { openKnowEachOtherGame } from './know_each_other.js';
import { openEmojiStoryMenu } from './emoji_story.js';
import { open20QGame } from './twenty_questions.js';
import { openWhoWouldGame } from './who_would.js';
import { openChallengesMenu } from './challenges.js';

const GAMES = [
  {
    id: 'know_each_other',
    emoji: '🧠',
    name: 'Know Each Other',
    desc: 'Answer for yourself, predict your partner, see who knows who best.',
    open: openKnowEachOtherGame,
  },
  {
    id: 'would_you_rather',
    emoji: '🤔',
    name: 'Would You Rather',
    desc: 'Choose privately, then see if you matched.',
    open: openWyrGame,
  },
  {
    id: 'who_would',
    emoji: '👀',
    name: 'Who Would...?',
    desc: 'Who\'s more likely to? Pick, reveal, and see if you agree.',
    open: openWhoWouldGame,
  },
  {
    id: 'challenges',
    emoji: '🎲',
    name: 'Challenges',
    desc: 'Cute, funny, deep, or romantic - accept a challenge, no pressure.',
    open: openChallengesMenu,
  },
  {
    id: 'emoji_story',
    emoji: '😂',
    name: 'Emoji Story',
    desc: 'Guess the story, or create one for your partner to guess.',
    open: openEmojiStoryMenu,
  },
  {
    id: 'twenty_questions',
    emoji: '❓',
    name: '20 Questions',
    desc: 'Pick a secret, or ask yes/no questions to guess theirs.',
    open: open20QGame,
  },
];

export async function renderGames(container) {
  container.innerHTML = `
    <h1 class="page-title">🎮 Games</h1>
    <p class="page-subtitle">Play together, see how you match up.</p>
  `;

  const list = document.createElement('div');
  list.style.display = 'flex';
  list.style.flexDirection = 'column';
  list.style.gap = '12px';

  GAMES.forEach((game) => {
    const tile = document.createElement('button');
    tile.className = 'game-tile card-tap';
    tile.innerHTML = `
      <span class="game-emoji">${game.emoji}</span>
      <span>
        <span class="game-name">${game.name}</span>
        <span class="game-desc">${game.desc}</span>
      </span>
    `;
    tile.addEventListener('click', () => game.open());
    list.appendChild(tile);
  });

  container.appendChild(list);
}
