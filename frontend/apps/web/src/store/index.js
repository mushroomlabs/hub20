import Vue from 'vue'
import Vuex from 'vuex'
import createLogger from 'vuex/dist/logger'

import {store} from 'vue-hub20'

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

    dispatch('auth/initialize').then(() => {
      if (getters['auth/isAuthenticated']) {
        dispatch('tokens/initialize')
          .then(() => dispatch('account/initialize'))
          .then(() => dispatch('network/initialize'))
          .then(() => dispatch('stores/initialize'))
          .then(() => dispatch('funding/initialize'))
          .then(() => dispatch('users/initialize'))
          .then(() => dispatch('events/initialize', SERVER_URL))
          .then(() => dispatch('events/setEventHandler', eventHandler))
          .then(() => commit(APP_SET_INITIALIZED))
      }
    })
  },
  refresh({dispatch}) {
    dispatch('account/refresh')
      .then(() => dispatch('stores/refresh'))
      .then(() => dispatch('coingecko/refresh'))
      .then(() => dispatch('funding/refresh'))
  }
}

export default new Vuex.Store({
  modules: store,
  state: initialState,
  strict: debug,
  plugins: debug ? [createLogger()] : [],
  actions,
  getters,
  mutations
})
