import Vue from 'vue'

import client from '../api/funding'

export const FUNDING_INITIALIZE = 'FUNDING_INITIALIZE'
export const FUNDING_DEPOSIT_FAILURE = 'FUNDING_DEPOSIT_FAILURE'
export const FUNDING_DEPOSIT_LOADED = 'FUNDING_DEPOSIT_LOADED'
export const FUNDING_DEPOSIT_CREATED = 'FUNDING_DEPOSIT_CREATED'
export const FUNDING_DEPOSIT_LIST_LOADED = 'FUNDING_DEPOSIT_LIST_LOADED'

export const FUNDING_TRANSFER_CREATED = 'FUNDING_TRANSFER_CREATED'
export const FUNDING_TRANSFER_LOADED = 'FUNDING_TRANSFER_LOADED'
export const FUNDING_TRANSFER_FAILURE = 'FUNDING_TRANSFER_FAILURE'
export const FUNDING_TRANSFER_LIST_LOADED = 'FUNDING_TRANSFER_LIST_LOADED'

const initialState = {
  deposits: [],
  transfers: [],
  error: null
}

const getters = {
  depositsByToken: state => token =>
    state.deposits.filter(deposit => deposit.token == token.address),
  openDeposits: state => state.deposits.filter(deposit => deposit.status == 'open'),
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
      .then(({data}) => commit(FUNDING_DEPOSIT_LOADED, data))
      .catch(error => commit(FUNDING_DEPOSIT_FAILURE, error.response))
  },
  fetchDeposits({commit}) {
    return client
      .getDeposits()
      .then(({data}) => commit(FUNDING_DEPOSIT_LIST_LOADED, data))
      .catch(error => commit(FUNDING_DEPOSIT_FAILURE, error.response))
  },
  createTransfer({commit}, payload) {
    const {token, amount, ...params} = payload
    return client
      .scheduleTransfer(token, amount, params)
      .then(({data}) => commit(FUNDING_TRANSFER_CREATED, data))
      .catch(error => commit(FUNDING_TRANSFER_FAILURE, error.response))
  },
  fetchTransfers({commit}) {
    return client
      .getTransfers()
      .then(({data}) => commit(FUNDING_TRANSFER_LIST_LOADED, data))
      .catch(error => commit(FUNDING_TRANSFER_FAILURE, error.response))
  },
  initialize({commit, dispatch}) {
    commit(FUNDING_INITIALIZE)
    dispatch('fetchDeposits')
    dispatch('fetchTransfers')
  },
  refresh({dispatch}) {
    dispatch('fetchDeposits')
    dispatch('fetchTransfers')
  }
}

const mutations = {
  [FUNDING_INITIALIZE](state) {
    Object.assign({...initialState}, state)
  },
  [FUNDING_DEPOSIT_CREATED](state, depositData) {
    state.deposits.push(depositData)
  },
  [FUNDING_DEPOSIT_LOADED](state, depositData) {
    Vue.set(state.depositsById, depositData.id, depositData)
  },
  [FUNDING_DEPOSIT_FAILURE](state, error) {
    state.error = error.data
  },
  [FUNDING_DEPOSIT_LIST_LOADED](state, depositList) {
    state.deposits = depositList
  },
  [FUNDING_TRANSFER_CREATED](state, transferData) {
    state.transfers.push(transferData)
  },
  [FUNDING_TRANSFER_LOADED](state, transferData) {
    state.transfers.push(transferData)
  },
  [FUNDING_TRANSFER_FAILURE](state, error) {
    state.error = error.data
  },
  [FUNDING_TRANSFER_LIST_LOADED](state, transferList) {
    state.transfers = transferList
  }
}

export default {
  namespaced: true,
  state: initialState,
  actions,
  getters,
  mutations
}
