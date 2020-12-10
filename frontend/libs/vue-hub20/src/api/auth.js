import client from './client'

export default {
  _client: client,
  login(username, password) {
    return this._client.post('/session/login', {username, password})
  },
  logout() {
    return this._client.post('/session/logout', {})
  },
  createAccount(username, password1, password2, email) {
    let payload = {username, password1, password2}
    Object.assign(payload, email && {email})
    return this._client.post('/register/', payload)
  },
  changeAccountPassword(password1, password2) {
    return this._client.post('/auth/password/change/', {password1, password2})
  },
  sendAccountPasswordResetEmail(email) {
    return this._client.post('/auth/password/reset/', {email})
  },
  resetAccountPassword(uid, token, new_password1, new_password2) {
    // eslint-disable-line camelcase
    return this._client.post('/auth/password/reset/confirm/', {
      uid,
      token,
      new_password1,
      new_password2
    })
  },
  getAccountDetails() {
    return this._client.get('/accounts/user')
  },
  updateAccountDetails(data) {
    return this._client.patch('/accounts/user', data)
  },
  verifyAccountEmail(key) {
    return this._client.post('/registration/verify-email/', {key})
  },
  setToken(token) {
    this._client.defaults.headers.Authorization = `Token ${token}`
  },
  removeToken() {
    delete this._client.defaults.headers.Authorization
  }
}
