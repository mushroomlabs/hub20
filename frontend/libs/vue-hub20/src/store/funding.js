import Vue from 'vue'

import client from '../api/funding'

export const FUNDING_INITIALIZE = 'FUNDING_INITIALIZE'
export const FUNDING_DEPOSIT_BEGIN = 'FUNDING_DEPOSIT_BEGIN'
export const FUNDING_DEPOSIT_SUCCESS = 'FUNDING_DEPOSIT_SUCCESS'
export const FUNDING_DEPOSIT_FAILURE = 'FUNDING_DEPOSIT_FAILURE'
export const FUNDING_DEPOSIT_SET_CLOSED = 'FUNDING_DEPOSIT_SET_CLOSED'
export const FUNDING_DEPOSIT_SET_OPEN = 'FUNDING_DEPOSIT_SET_OPEN'
export const FUNDING_TRANSFER_BEGIN = 'FUNDING_TRANSFER_BEGIN'
export const FUNDING_TRANSFER_FAILURE = 'FUNDING_TRANSFER_FAILURE'

const initialState = {
  depositsById: {},
  transfersById: {},
  currentDeposit: null,
  error: null
}

const getters = {
  deposits: state => Object.values(state.depositsById),
  depositsByToken: (state, getters) => token =>
    getters.deposits.filter(deposit => deposit.token == token.address),
  transfers: state => Object.values(state.transfersById),
  openDeposits: (state, getters) => getters.deposits.filter(deposit => deposit.status == 'open')
}

const actions = {
  createDeposit({commit}, token) {
    return client
      .createDeposit(token)
      .then(({data}) => commit(FUNDING_DEPOSIT_BEGIN, data))
      .catch(error => commit(FUNDING_DEPOSIT_FAILURE, error.response))
  },
  fetchDeposit({commit}, depositId) {
    return client
      .getDeposit(depositId)
      .then(({data}) => commit(FUNDING_DEPOSIT_SUCCESS, data))
      .catch(error => commit(FUNDING_DEPOSIT_FAILURE, error.response))
  },
  createTransfer({commit}, args) {
    const {token, amount, address, ...params} = args
    return client
      .scheduleExternalTransfer(token, amount, address, params)
      .then(({data}) => commit(FUNDING_TRANSFER_BEGIN, data))
      .catch(error => commit(FUNDING_TRANSFER_FAILURE, error.response))
  },
  initialize({commit}) {
    commit(FUNDING_INITIALIZE)
  },
  refresh({state, dispatch}) {
    Object.keys(state.depositsById).forEach(depositId => dispatch('fetchDeposit', depositId))
  }
}

const mutations = {
  [FUNDING_INITIALIZE](state) {
    Object.assign({...initialState}, state)
  },
  [FUNDING_DEPOSIT_BEGIN](state, depositData) {
    Vue.set(state.depositsById, depositData.id, depositData)
    state.currentDeposit = depositData
    state.error = null
  },
  [FUNDING_DEPOSIT_SET_OPEN](state, depositId) {
    let deposit = state.depositsById[depositId]
    if (deposit) {
      state.currentDeposit = deposit
      state.error = null
    }
  },
  [FUNDING_DEPOSIT_SET_CLOSED](state, depositId) {
    let deposit = state.depositsById[depositId]
    if (deposit) {
      state.currentDeposit = null
      state.error = null
    }
  },
  [FUNDING_DEPOSIT_FAILURE](state, error) {
    state.currentDeposit = null
    state.error = error.data
  },
  [FUNDING_DEPOSIT_SUCCESS](state, depositData) {
    Vue.set(state.depositsById, depositData.id, depositData)
  },
  [FUNDING_TRANSFER_BEGIN](state, transferData) {
    Vue.set(state.transfersById, transferData.id, transferData)
    state.error = null
  },
  [FUNDING_TRANSFER_FAILURE](state, error) {
    state.error = error.data
  }
}

export default {
  namespaced: true,
  state: initialState,
  actions,
  getters,
  mutations
}
