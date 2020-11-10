import Vue from 'vue'
import Vuex from 'vuex'
import createLogger from 'vuex/dist/logger'

import {default as hub20lib} from 'vue-hub20'

import {APP_SET_INITIALIZED} from './types'

const debug = process.env.NODE_ENV !== 'production'

Vue.use(Vuex)

const initialState = {
  serverUrl: window.origin,
  ready: false
}

const getters = {
  isReady: state => state.ready
}

const mutations = {
  [APP_SET_INITIALIZED](state) {
    state.ready = true
  }
}

const actions = {
  initialize({commit, dispatch, getters, state}) {
    dispatch('auth/initialize').then(() => {
      if (getters['auth/isAuthenticated']) {
        dispatch('tokens/initialize')
          .then(() => dispatch('account/initialize'))
          .then(() => dispatch('stores/initialize'))
          .then(() => dispatch('funding/initialize'))
          .then(() => dispatch('events/initialize', {serverUrl: state.serverUrl}))
          .then(() => dispatch('events/openWebSocket'))
          .then(() => commit(APP_SET_INITIALIZED))
      }
    })
  },
  refresh({dispatch}) {
    dispatch('account/refresh')
      .then(() => dispatch('stores/refresh'))
      .then(() => dispatch('funding/refresh'))
  }
}

export default new Vuex.Store({
  modules: hub20lib.store,
  state: initialState,
  strict: debug,
  plugins: debug ? [createLogger()] : [],
  actions,
  getters,
  mutations
})
