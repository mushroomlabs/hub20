import Vue from 'vue'
import Vuex from 'vuex'
import createLogger from 'vuex/dist/logger'

import auth from './auth'
import account from './account'
import notifications from './notifications'
import password from './password'
import signup from './signup'
import stores from './stores'
import tokens from './tokens'
import funding from './funding'

import {
  APP_SET_INITIALIZED
} from './types'

const debug = process.env.NODE_ENV !== 'production'

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
  initialize({commit, getters, dispatch}) {
    dispatch('auth/initialize')
      .then(() => {
        if (getters['auth/isAuthenticated']){
          dispatch('tokens/initialize')
            .then(() => dispatch('account/initialize'))
            .then(() => dispatch('stores/initialize'))
            .then(() => dispatch('funding/initialize'))
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
  modules: {
    account,
    auth,
    funding,
    notifications,
    password,
    signup,
    stores,
    tokens,
  },
  state: initialState,
  strict: debug,
  plugins: debug ? [createLogger()] : [],
  actions,
  getters,
  mutations
})
