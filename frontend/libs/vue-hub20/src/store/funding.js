import Vue from 'vue'

import client from '../api/funding'

export const FUNDING_INITIALIZE = 'FUNDING_INITIALIZE'
export const FUNDING_DEPOSIT_BEGIN = 'FUNDING_DEPOSIT_BEGIN'
export const FUNDING_DEPOSIT_CANCEL = 'FUNDING_DEPOSIT_CANCEL'
export const FUNDING_DEPOSIT_SUCCESS = 'FUNDING_DEPOSIT_SUCCESS'
export const FUNDING_DEPOSIT_SET_EXPIRED = 'FUNDING_DEPOSIT_SET_EXPIRED'
export const FUNDING_DEPOSIT_FAILURE = 'FUNDING_DEPOSIT_FAILURE'
export const FUNDING_TRANSFER_BEGIN = 'FUNDING_TRANSFER_BEGIN'
export const FUNDING_TRANSFER_FAILURE = 'FUNDING_TRANSFER_FAILURE'

const initialState = {
  depositsById: {},
  transfersById: {},
  error: null
}

const getters = {
  deposits: state => Object.values(state.depositsById),
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
  cancelDeposit({commit, dispatch}, depositId) {
    return client
      .cancelDeposit(depositId)
      .then(() => dispatch('fetchDeposit', depositId))
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
    state.error = null
  },
  [FUNDING_DEPOSIT_FAILURE](state, error) {
    state.error = error.data
  },
  [FUNDING_DEPOSIT_CANCEL](state, depositId) {
    let deposit = state.depositsById[depositId]

    if (deposit) {
      deposit.status = 'canceled'
      Vue.set(state.depositsById, depositId, deposit)
    }
  },
  [FUNDING_DEPOSIT_SUCCESS](state, depositData) {
    Vue.set(state.depositsById, depositData.id, depositData)
  },
  [FUNDING_DEPOSIT_SET_EXPIRED](state, depositId) {
    let deposit = state.depositsById[depositId]

    if (deposit) {
      deposit.status = 'expired'
      Vue.set(state.depositsById, depositId, deposit)
    }
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
