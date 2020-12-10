import semver from 'semver'

import client from '../api/server'

const SERVER_URL_STORAGE_KEY = 'serverUrl'
const SERVER_VERSION_STORAGE_KEY = 'serverVersion'

export const SERVER_SET_URL_BEGIN = 'SERVER_SET_URL_BEGIN'
export const SERVER_SET_URL_CANCEL = 'SERVER_SET_URL_CANCEL'
export const SERVER_SET_URL_SUCCESS = 'SERVER_SET_URL_SUCCESS'
export const SERVER_SET_URL_FAILURE = 'SERVER_SET_URL_FAILURE'
export const SERVER_CLEAR_URL = 'SERVER_CLEAR_URL'

const VERSION = '0.2.1'

const initialState = {
  rootUrl: null,
  version: null,
  error: null,
  processing: false
}

const getters = {
  isConnected: state => Boolean(state.rootUrl),
  isCompatible: state => semver.satisfies(VERSION, `^${state.version}`)
}

const actions = {
  initialize({commit, dispatch}) {
    const savedUrl = localStorage.getItem(SERVER_URL_STORAGE_KEY)
    return dispatch('setUrl', savedUrl).catch(() => commit(SERVER_CLEAR_URL))
  },
  setUrl({commit}, url) {
    commit(SERVER_SET_URL_BEGIN)
    return client
      .checkHub20Server(url)
      .then(version => {
        if (semver.satisfies(VERSION, `^${version}`)) {
          client.setUrl(url)
          commit(SERVER_SET_URL_SUCCESS, {url, version})
        } else {
          return Promise.reject(`server advertising incompatible version ${version}`)
        }
      })
      .catch(error => {
        commit(SERVER_SET_URL_FAILURE, `Failed to connect: ${error}`)
        return Promise.reject(error)
      })
  }
}

const mutations = {
  [SERVER_SET_URL_BEGIN](state) {
    state.processing = true
  },
  [SERVER_SET_URL_SUCCESS](state, {url, version}) {
    state.rootUrl = url
    state.version = version
    state.error = null
    state.processing = false

    localStorage.setItem(SERVER_URL_STORAGE_KEY, url)
    localStorage.setItem(SERVER_VERSION_STORAGE_KEY, version)
  },
  [SERVER_SET_URL_FAILURE](state, error) {
    state.error = error
    state.processing = false
  },
  [SERVER_CLEAR_URL](state) {
    state.rootUrl = null
    state.version = null
    state.error = null
    state.processing = false

    localStorage.removeItem(SERVER_URL_STORAGE_KEY)
    localStorage.removeItem(SERVER_VERSION_STORAGE_KEY)
  }
}

export default {
  namespaced: true,
  state: initialState,
  actions,
  getters,
  mutations
}
