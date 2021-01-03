import Vue from 'vue'
import Vuex from 'vuex'
import createLogger from 'vuex/dist/logger'

import {store} from 'vue-hub20'

export const APP_SET_INITIALIZED = 'APP_SET_INITIALIZED'
export const APP_SET_RUNNING = 'APP_SET_RUNNING'
export const APP_SET_LOADED = 'APP_SET_LOADED'
export const APP_SET_FINALIZED = 'APP_SET_FINALIZED'
export const APP_RESET_STATE = 'APP_RESET_STATE'

const debug = process.env.NODE_ENV !== 'production'

Vue.use(Vuex)

const initialState = () => ({
  running: false,
  loaded: false
})

const getters = {
  isRunning: state => state.running,
  isLoaded: state => state.loaded,
  isReady: state => state.running && state.loaded
}

const mutations = {
  [APP_SET_INITIALIZED](state) {
    state.running = true
    state.loaded = true
  },
  [APP_SET_RUNNING](state) {
    state.running = true
  },
  [APP_SET_LOADED](state) {
    state.loaded = true
  },
  [APP_SET_FINALIZED](state) {
    state.running = false
  },
  [APP_RESET_STATE](state) {
    Object.assign(state, initialState())
  }
}

const actions = {
  setServer({dispatch}, url) {
    dispatch('server/setUrl', url)
  },
  initialize({commit, dispatch, getters}) {
    const eventHandler = evt => {
      let eventTypes = store.EVENT_TYPES
      const message = JSON.parse(evt.data)
      const eventData = message.data
      switch (message.event) {
        case eventTypes.BLOCKCHAIN_BLOCK_CREATED:
          commit('network/NETWORK_SET_ETHEREUM_CURRENT_BLOCK', eventData.number)
          break
        case eventTypes.BLOCKCHAIN_DEPOSIT_BROADCAST:
          commit('notifications/ADD_NOTIFICATION', {
            message: 'Blockchain transaction sent',
            type: 'info'
          })
          break
        case eventTypes.RAIDEN_ROUTE_EXPIRED:
        case eventTypes.BLOCKCHAIN_ROUTE_EXPIRED:
          commit('notifications/ADD_NOTIFICATION', {
            message:
              'Payment route is expired. Any payment received now will may not be credited to your account',
            type: 'warning'
          })
          break
        case eventTypes.ETHEREUM_NODE_UNAVAILABLE:
          commit('notifications/ADD_NOTIFICATION', {
            message: 'Server reported loss of connection with ethereum network',
            type: 'danger'
          })
          break
        case eventTypes.ETHEREUM_NODE_OK:
          commit('notifications/ADD_NOTIFICATION', {
            message: 'Server connection with ethereum network established',
            type: 'success'
          })
          break
        case eventTypes.BLOCKCHAIN_DEPOSIT_RECEIVED:
          dispatch('funding/fetchDeposit', eventData.depositId)
          commit('notifications/ADD_NOTIFICATION', {
            message: 'Deposit received via blockchain',
            type: 'success'
          })
          break
        default:
          console.log(evt)
      }
    }

    dispatch('coingecko/initialize')
    return dispatch('server/initialize').then(() => {
      if (getters['server/isConnected']) {
        const serverDomain = getters['server/serverDomain']
        dispatch('auth/initialize').then(() => {
          if (getters['auth/isAuthenticated']) {
            dispatch('tokens/initialize')
              .then(() => dispatch('account/initialize'))
              .then(() => dispatch('audit/initialize'))
              .then(() => dispatch('network/initialize'))
              .then(() => dispatch('stores/initialize'))
              .then(() => dispatch('funding/initialize'))
              .then(() => dispatch('users/initialize'))
              .then(() => dispatch('events/initialize', serverDomain))
              .then(() => dispatch('events/setEventHandler', eventHandler))
              .then(() => commit(APP_SET_INITIALIZED))
          }
        })
      }
    })
  },
  refresh({dispatch, getters}) {
    if (getters['isRunning']) {
      dispatch('coingecko/refresh')

      if (getters['server/isConnected'] && getters['auth/isAuthenticated']) {
        dispatch('account/refresh')
          .then(() => dispatch('stores/refresh'))
          .then(() => dispatch('funding/refresh'))
      }

      if (getters['account/hasAdminAccess']) {
        dispatch('audit/refresh')
      }
    }
  },
  tearDown({commit, dispatch}) {
    return dispatch('auth/logout')
      .then(() => dispatch('auth/tearDown'))
      .then(() => dispatch('account/tearDown'))
      .then(() => dispatch('notifications/tearDown'))
      .then(() => dispatch('funding/tearDown'))
      .then(() => dispatch('stores/tearDown'))
      .then(() => dispatch('events/tearDown'))
      .then(() => dispatch('audit/tearDown'))
      .finally(() => commit(APP_SET_FINALIZED))
  }
}

export default new Vuex.Store({
  modules: store,
  state: initialState(),
  strict: debug,
  plugins: debug ? [createLogger()] : [],
  actions,
  getters,
  mutations
})
