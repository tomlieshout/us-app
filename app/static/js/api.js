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
  questions: (category, { unansweredOnly } = {}) => {
    const params = new URLSearchParams();
    if (category) params.set('category', category);
    if (unansweredOnly) params.set('unanswered_only', 'true');
    const qs = params.toString();
    return request('GET', `/api/questions${qs ? `?${qs}` : ''}`);
  },
  // Browse tab's "Waiting On You" discovery card - classic questions the
  // partner has answered and this user hasn't. Never includes their answer.
  partnerAnsweredQuestions: () => request('GET', '/api/questions/partner-answered'),
  playQuestion: (id) => request('POST', `/api/questions/${id}/play`),

  // Rounds (legacy engine - kept for rollback safety; the live UI now
  // uses `activities` below instead. Routes are untouched and still work.)
  currentRound: () => request('GET', '/api/rounds/current'),
  randomRound: (category) => request('GET', `/api/rounds/random${category ? `?category=${encodeURIComponent(category)}` : ''}`),
  round: (id) => request('GET', `/api/rounds/${id}`),
  history: (page, category) => {
    const params = new URLSearchParams({ page: page || 1 });
    if (category) params.set('category', category);
    return request('GET', `/api/rounds/history?${params.toString()}`);
  },

  // Answers (legacy engine - see note above)
  submitAnswer: (data) => request('POST', '/api/answers', data),

  // Activities - the live engine for the question/answer experience as of
  // the architectural-integration phase. See app/routes/activities.py.
  activities: {
    current: () => request('GET', '/api/activities/current'),
    // mode: 'unanswered' (default) | 'partner_pending' - the Answer
    // Coordination toggle. See app/routes/activities.py's /random.
    random: ({ category, activity_type, mode } = {}) => {
      const params = new URLSearchParams();
      if (category) params.set('category', category);
      if (activity_type) params.set('activity_type', activity_type);
      if (mode) params.set('mode', mode);
      const qs = params.toString();
      return request('GET', `/api/activities/random${qs ? `?${qs}` : ''}`);
    },
    // Starts one fresh cycle through this game's bank once the user has
    // personally answered everything in it.
    playAgain: (activity_type) => request('POST', '/api/activities/play-again', { activity_type }),
    play: (legacyQuestionId) => request('POST', `/api/activities/play/${legacyQuestionId}`),
    get: (id) => request('GET', `/api/activities/${id}`),
    submit: (id, data) => request('POST', `/api/activities/${id}/submit`, data),
    // view: 'mine' | 'mutual' (default) | 'partner' - the three-way Past
    // Answers structure, shared by all four features. Options-object
    // form: the old positional (page, category) signature silently
    // dropped the activity_type argument game_history.js was passing.
    history: ({ page, category, activityType, view } = {}) => {
      const params = new URLSearchParams({ page: page || 1 });
      if (category) params.set('category', category);
      if (activityType) params.set('activity_type', activityType);
      if (view) params.set('view', view);
      return request('GET', `/api/activities/history?${params.toString()}`);
    },
  },

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

  // Home dashboard - aggregates Today's Activity/Recent Activity/Champion
  // from the systems above. See app/routes/home.py.
  home: () => request('GET', '/api/home'),

  // Notifications - see app/routes/notifications.py.
  notifications: {
    list: () => request('GET', '/api/notifications'),
    markSeen: () => request('POST', '/api/notifications/seen'),
  },

  // Settings
  updateProfile: (data) => request('PATCH', '/api/settings/profile', data),
  changePassword: (data) => request('POST', '/api/settings/password', data),
  setSpicy: (enabled, adultConfirmation) => request('POST', '/api/settings/spicy', { enabled, adult_confirmation: adultConfirmation }),
  deleteMyAnswers: () => request('POST', '/api/settings/delete-answers'),
  deleteAccount: () => request('POST', '/api/settings/delete-account'),

  // Spicy
  spicyMatches: () => request('GET', '/api/spicy/matches'),
  deleteSpicyRound: (roundId) => request('POST', `/api/spicy/rounds/${roundId}/delete`),

  // Emoji Story
  emojiStory: {
    create: (emoji_sequence, explanation) => request('POST', '/api/emoji-story/create', { emoji_sequence, explanation }),
    mine: () => request('GET', '/api/emoji-story/mine'),
    guess: () => request('POST', '/api/emoji-story/guess'),
  },

  // 20 Questions
  twentyQuestions: {
    current: () => request('GET', '/api/twenty-questions/current'),
    get: (id) => request('GET', `/api/twenty-questions/${id}`),
    create: (category, secret_text) => request('POST', '/api/twenty-questions/create', { category, secret_text }),
    ask: (id, question_text, is_guess) => request('POST', `/api/twenty-questions/${id}/ask`, { question_text, is_guess }),
    answer: (id, answer) => request('POST', `/api/twenty-questions/${id}/answer`, { answer }),
    abandon: (id) => request('POST', `/api/twenty-questions/${id}/abandon`),
  },

  // Challenges
  challenges: {
    random: (category) => request('GET', `/api/challenges/random${category ? `?category=${encodeURIComponent(category)}` : ''}`),
    accept: (content_id) => request('POST', '/api/challenges/accept', { content_id }),
    mine: (status) => request('GET', `/api/challenges/mine${status ? `?status=${encodeURIComponent(status)}` : ''}`),
    complete: (id) => request('POST', `/api/challenges/${id}/complete`),
  },

  // Appreciation
  appreciation: {
    send: (message_text) => request('POST', '/api/appreciation/send', { message_text }),
    received: (unseenOnly) => request('GET', `/api/appreciation/received${unseenOnly ? '?unseen_only=true' : ''}`),
    sent: () => request('GET', '/api/appreciation/sent'),
    unseenCount: () => request('GET', '/api/appreciation/unseen-count'),
    markSeen: (id) => request('POST', `/api/appreciation/${id}/seen`),
    react: (id, reaction_type) => request('POST', `/api/appreciation/${id}/react`, { reaction_type }),
    removeReaction: (id) => request('DELETE', `/api/appreciation/${id}/react`),
    keep: (id) => request('POST', `/api/appreciation/${id}/keep`),
    remove: (id) => request('POST', `/api/appreciation/${id}/delete`),
  },

  // Memories
  memories: {
    list: () => request('GET', '/api/memories'),
    get: (id) => request('GET', `/api/memories/${id}`),
    create: (data) => request('POST', '/api/memories', data),
    update: (id, data) => request('PATCH', `/api/memories/${id}`, data),
    remove: (id) => request('DELETE', `/api/memories/${id}`),
  },
  plans: {
    categories: () => request('GET', '/api/plans/categories'),
    statuses: () => request('GET', '/api/plans/statuses'),
    list: (params = {}) => {
      const qs = new URLSearchParams(params).toString();
      return request('GET', `/api/plans${qs ? `?${qs}` : ''}`);
    },
    get: (id) => request('GET', `/api/plans/${id}`),
    create: (data) => request('POST', '/api/plans', data),
    update: (id, data) => request('PATCH', `/api/plans/${id}`, data),
    remove: (id) => request('DELETE', `/api/plans/${id}`),
  },
};

export { ApiError };
