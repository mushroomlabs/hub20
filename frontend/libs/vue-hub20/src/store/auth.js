import auth from '../api/auth'
import session from '../api/session'

const TOKEN_STORAGE_KEY = 'token'
const USERNAME_STORAGE_KEY = 'username'

export const LOGIN_BEGIN = 'LOGIN_BEGIN'
export const LOGIN_CLEAR = 'LOGIN_CLEAR'
export const LOGIN_FAILURE = 'LOGIN_FAILURE'
export const LOGIN_SUCCESS = 'LOGIN_SUCCESS'
export const LOGOUT = 'LOGOUT'
export const AUTH_SET_USERNAME = 'AUTH_SET_USERNAME'
export const AUTH_SET_TOKEN = 'AUTH_SET_TOKEN'
export const AUTH_REMOVE_TOKEN = 'AUTH_REMOVE_TOKEN'
export const AUTH_REMOVE_USERNAME = 'AUTH_REMOVE_USERNAME'

const initialState = {
  authenticating: false,
  error: false,
  username: null,
  token: null
}

const getters = {
  isAuthenticated: state => !!state.token,
  loggedUsername: (state, getters) => getters.isAuthenticated && state.username
}

const actions = {
  login({commit}, {username, password}) {
    commit(LOGIN_BEGIN)
    return auth
      .login(username, password)
      .then(({data}) => {
        commit(AUTH_SET_TOKEN, data.key)
        commit(AUTH_SET_USERNAME, username)
      })
      .then(() => commit(LOGIN_SUCCESS))
      .catch(() => commit(LOGIN_FAILURE))
  },
  logout({commit}) {
    return auth
      .logout()
      .then(() => commit(LOGOUT))
      .finally(() => {
        commit(AUTH_REMOVE_TOKEN)
        commit(AUTH_REMOVE_USERNAME)
      })
  },
  initialize({commit}) {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY)
    const username = localStorage.getItem(USERNAME_STORAGE_KEY)

    if (token) {
      commit(AUTH_SET_TOKEN, token)
    }

    if (username) {
      commit(AUTH_SET_USERNAME, username)
    }
  }
}

const mutations = {
  [LOGIN_BEGIN](state) {
    state.authenticating = true
    state.error = false
  },
  [LOGIN_FAILURE](state) {
    state.authenticating = false
    state.error = true
  },
  [LOGIN_SUCCESS](state) {
    state.authenticating = false
    state.error = false
  },
  [LOGOUT](state) {
    state.authenticating = false
    state.error = false
  },
  [AUTH_SET_TOKEN](state, token) {
    localStorage.setItem(TOKEN_STORAGE_KEY, token)
    session.defaults.headers.Authorization = `Token ${token}`
    state.token = token
  },
  [AUTH_REMOVE_TOKEN](state) {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    delete session.defaults.headers.Authorization
    state.token = null
  },
  [AUTH_SET_USERNAME](state, username) {
    localStorage.setItem(USERNAME_STORAGE_KEY, username)
    state.username = username
  },
  [AUTH_REMOVE_USERNAME](state) {
    localStorage.removeItem(USERNAME_STORAGE_KEY)
    state.username = null
  }
}

export default {
  namespaced: true,
  state: initialState,
  getters,
  actions,
  mutations
}
