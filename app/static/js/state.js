export const state = {
  user: null,
  couple: null,
};

export function setAuth(user, couple) {
  state.user = user;
  state.couple = couple;
}

export function partnerMember() {
  if (!state.couple || !state.user) return null;
  return state.couple.members.find((m) => m.id !== state.user.id) || null;
}

export function meMember() {
  if (!state.couple || !state.user) return null;
  return state.couple.members.find((m) => m.id === state.user.id) || null;
}

export function isSpicyUnlocked() {
  return !!(state.couple && state.couple.spicy_unlocked);
}
