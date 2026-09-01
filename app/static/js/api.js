// Thin wrapper around fetch() for the /api/* JSON backend. Every mutating
// request carries the CSRF token from the <meta> tag in <head>, matching
// Flask-WTF's CSRFProtect (see app/__init__.py).

function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

class ApiError extends Error {
  constructor(status, payload) {
    super(payload && payload.message ? payload.message : 'Something went wrong.');
    this.status = status;
    this.code = payload && payload.error;
    this.errors = payload && payload.errors;
  }
}

async function request(method, path, body) {
  const options = {
    method,
    headers: { 'Accept': 'application/json' },
    credentials: 'same-origin',
  };
  if (body !== undefined) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }
  if (method !== 'GET') {
    options.headers['X-CSRFToken'] = getCsrfToken();
  }

  let response;
  try {
    response = await fetch(path, options);
  } catch (networkErr) {
    throw new ApiError(0, { error: 'network', message: "Couldn't reach the server. Check your connection." });
  }

  let payload = null;
  const text = await response.text();
  if (text) {
    try { payload = JSON.parse(text); } catch (e) { payload = null; }
  }

  if (!response.ok) {
    throw new ApiError(response.status, payload || {});
  }
  return payload;
}

export const api = {
  get: (path) => request('GET', path),
  post: (path, body) => request('POST', path, body === undefined ? {} : body),
  patch: (path, body) => request('PATCH', path, body === undefined ? {} : body),
  delete: (path) => request('DELETE', path),

  // Auth
  me: () => request('GET', '/api/auth/me'),
  registerCouple: (data) => request('POST', '/api/auth/register-couple', data),
  joinCouple: (data) => request('POST', '/api/auth/join-couple', data),
  login: (data) => request('POST', '/api/auth/login', data),
  logout: () => request('POST', '/api/auth/logout'),

  // Couple
  getCouple: () => request('GET', '/api/couple'),
  updateCouple: (data) => request('PATCH', '/api/couple', data),
  deleteCouple: (confirmation) => request('POST', '/api/couple/delete', { confirmation }),

  // Questions
  categories: () => request('GET', '/api/questions/categories'),
  questions: (category) => request('GET', `/api/questions${category ? `?category=${encodeURIComponent(category)}` : ''}`),
  playQuestion: (id) => request('POST', `/api/questions/${id}/play`),

  // Rounds
  currentRound: () => request('GET', '/api/rounds/current'),
  randomRound: (category) => request('GET', `/api/rounds/random${category ? `?category=${encodeURIComponent(category)}` : ''}`),
  round: (id) => request('GET', `/api/rounds/${id}`),
  history: (page, category) => {
    const params = new URLSearchParams({ page: page || 1 });
    if (category) params.set('category', category);
    return request('GET', `/api/rounds/history?${params.toString()}`);
  },

  // Answers
  submitAnswer: (data) => request('POST', '/api/answers', data),

  // Reactions / comments
  addReaction: (answerId, reactionType) => request('POST', '/api/reactions', { answer_id: answerId, reaction_type: reactionType }),
  removeReaction: (answerId) => request('DELETE', `/api/reactions/${answerId}`),
  comments: (roundId) => request('GET', `/api/comments/${roundId}`),
  addComment: (roundId, text) => request('POST', '/api/comments', { round_id: roundId, comment_text: text }),

  // Favourites
  favourites: () => request('GET', '/api/favourites'),
  addFavourite: (questionId) => request('POST', '/api/favourites', { question_id: questionId }),
  removeFavourite: (questionId) => request('DELETE', `/api/favourites/${questionId}`),

  // Stats
  stats: () => request('GET', '/api/stats'),

  // Settings
  updateProfile: (data) => request('PATCH', '/api/settings/profile', data),
  changePassword: (data) => request('POST', '/api/settings/password', data),
  setSpicy: (enabled, adultConfirmation) => request('POST', '/api/settings/spicy', { enabled, adult_confirmation: adultConfirmation }),
  deleteMyAnswers: () => request('POST', '/api/settings/delete-answers'),
  deleteAccount: () => request('POST', '/api/settings/delete-account'),

  // Spicy
  spicyMatches: () => request('GET', '/api/spicy/matches'),
  deleteSpicyRound: (roundId) => request('POST', `/api/spicy/rounds/${roundId}/delete`),
};

export { ApiError };
