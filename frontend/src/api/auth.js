import session from './session';

export default {
  login(username, password) {
    return session.post('/api/session/login', { username, password });
  },
  logout() {
    return session.post('/api/session/logout', {});
  },
  createAccount(username, password1, password2, email) {
    let payload = { username, password1, password2 };
    Object.assign(payload, email && {email});
    return session.post('/api/register/', payload);
  },
  changeAccountPassword(password1, password2) {
    return session.post('/auth/password/change/', { password1, password2 });
  },
  sendAccountPasswordResetEmail(email) {
    return session.post('/auth/password/reset/', { email });
  },
  resetAccountPassword(uid, token, new_password1, new_password2) { // eslint-disable-line camelcase
    return session.post('/auth/password/reset/confirm/', { uid, token, new_password1, new_password2 });
  },
  getAccountDetails() {
    return session.get('/api/accounts/user');
  },
  updateAccountDetails(data) {
    return session.patch('/api/accounts/user', data);
  },
  verifyAccountEmail(key) {
    return session.post('/registration/verify-email/', { key });
  },
};
