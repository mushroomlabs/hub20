import Vue from 'vue'
import Vuex from 'vuex'
import createLogger from 'vuex/dist/logger'

import {default as hub20lib} from 'vue-hub20'

import {APP_SET_INITIALIZED} from './types'

const debug = process.env.NODE_ENV !== 'production'

const SERVER_URL = window.origin

Vue.use(Vuex)

const initialState = {
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
  initialize({commit, dispatch, getters}) {
    const eventHandler = evt => {
      let eventTypes = hub20lib.store.EVENT_TYPES
      const eventData = JSON.parse(evt.data)
      switch (eventData.event) {
        case eventTypes.BLOCKCHAIN_BLOCK_CREATED:
          commit('server/SERVER_SET_ETHEREUM_NODE_CURRENT_BLOCK', eventData.block_data.number)
          break
        default:
          console.log(evt)
      }
    }

    commit('server/SERVER_SET_URL', SERVER_URL)

    dispatch('auth/initialize').then(() => {
      if (getters['auth/isAuthenticated']) {
        dispatch('tokens/initialize')
          .then(() => dispatch('account/initialize'))
          .then(() => dispatch('stores/initialize'))
          .then(() => dispatch('funding/initialize'))
          .then(() => dispatch('events/initialize', SERVER_URL))
          .then(() => dispatch('events/setEventHandler', eventHandler))
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
