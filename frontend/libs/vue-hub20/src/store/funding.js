import Vue from 'vue'

import client from '../api/funding'

export const FUNDING_INITIALIZE = 'FUNDING_INITIALIZE'
export const FUNDING_DEPOSIT_FAILURE = 'FUNDING_DEPOSIT_FAILURE'
export const FUNDING_DEPOSIT_SUCCESS = 'FUNDING_DEPOSIT_SUCCESS'
export const FUNDING_DEPOSIT_CREATED = 'FUNDING_DEPOSIT_CREATED'

export const FUNDING_TRANSFER_SUCCESS = 'FUNDING_TRANSFER_SUCCESS'
export const FUNDING_TRANSFER_FAILURE = 'FUNDING_TRANSFER_FAILURE'

const initialState = {
  depositsById: {},
  transfersById: {},
  error: null
}

const getters = {
  deposits: state => Object.values(state.depositsById),
  depositsByToken: (state, getters) => token =>
    getters.deposits.filter(deposit => deposit.token == token.address),
  transfers: state => Object.values(state.transfersById),
  openDeposits: (state, getters) =>
    getters.deposits.filter(deposit => deposit.status == 'open'),
  openDepositsByToken: (state, getters) => token =>
    getters.openDeposits.filter(deposit => deposit.token == token.address)
}

const actions = {
  createDeposit({commit}, token) {
    return client
      .createDeposit(token)
      .then(({data}) => {
        commit(FUNDING_DEPOSIT_CREATED, data)
        return new Promise(resolve => resolve(data))
      })
      .catch(error => commit(FUNDING_DEPOSIT_FAILURE, error.response))
  },
  fetchDeposit({commit}, depositId) {
    return client
      .getDeposit(depositId)
      .then(({data}) => commit(FUNDING_DEPOSIT_SUCCESS, data))
      .catch(error => commit(FUNDING_DEPOSIT_FAILURE, error.response))
  },
  fetchDeposits({commit}) {
    return client
      .getDeposits()
      .then(({data}) =>
        data.forEach(depositData => commit(FUNDING_DEPOSIT_SUCCESS, depositData))
      )
      .catch(error => commit(FUNDING_DEPOSIT_FAILURE, error.response))
  },
  createTransfer({commit}, payload) {
    const {token, amount, ...params} = payload
    return client
      .scheduleTransfer(token, amount, params)
      .then(({data}) => commit(FUNDING_TRANSFER_SUCCESS, data))
      .catch(error => commit(FUNDING_TRANSFER_FAILURE, error.response))
  },
  initialize({commit, dispatch}) {
    commit(FUNDING_INITIALIZE)
    dispatch('fetchDeposits')
  },
  refresh({state, dispatch}) {
    dispatch('fetchDeposits')
    Object.keys(state.transfersById).forEach(transferId =>
      dispatch('fetchTransfer', transferId)
    )
  }
}

const mutations = {
  [FUNDING_INITIALIZE](state) {
    Object.assign({...initialState}, state)
  },
  [FUNDING_DEPOSIT_CREATED](state, depositData) {
    Vue.set(state.depositsById, depositData.id, depositData)
  },
  [FUNDING_DEPOSIT_SUCCESS](state, depositData) {
    Vue.set(state.depositsById, depositData.id, depositData)
  },
  [FUNDING_DEPOSIT_FAILURE](state, error) {
    state.error = error.data
  },
  [FUNDING_TRANSFER_SUCCESS](state, transferData) {
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
