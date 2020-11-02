import Decimal from 'decimal.js-light'

import account from '../api/account'
import utils from './utils'

export const UPDATE_BALANCES_BEGIN = 'UPDATE_BALANCES_BEGIN'
export const UPDATE_BALANCES_SUCCESS = 'UPDATE_BALANCES_SUCCESS'
export const UPDATE_BALANCES_FAILURE = 'UPDATE_BALANCES_FAILURE'
export const UPDATE_CREDITS_BEGIN = 'UPDATE_CREDITS_BEGIN'
export const UPDATE_CREDITS_SUCCESS = 'UPDATE_CREDITS_SUCCESS'
export const UPDATE_CREDITS_FAILURE = 'UPDATE_CREDITS_FAILURE'
export const UPDATE_DEBITS_BEGIN = 'UPDATE_DEBITS_BEGIN'
export const UPDATE_DEBITS_SUCCESS = 'UPDATE_DEBITS_SUCCESS'
export const UPDATE_DEBITS_FAILURE = 'UPDATE_DEBITS_FAILURE'
export const SET_BALANCES = 'SET_BALANCES'
export const SET_CREDITS = 'SET_CREDITS'
export const SET_DEBITS = 'SET_DEBITS'

const initialState = {
  balances: [],
  credits: [],
  debits: [],
  error: null
}

const getters = {
  openBalances: state =>
    state.balances.filter(balance =>
      Decimal(balance.amount)
        .abs()
        .gt(0)
    ),
  balancesByTokenAddress: state =>
    state.balances.reduce(
      (acc, balance) =>
        Object.assign({[balance.currency.address]: Decimal(balance.amount)}, acc),
      {}
    ),
  transactions: state => utils.sortedByDate(state.credits.concat(state.debits)),
  tokenBalance: (state, getters) => tokenAddress =>
    getters.balancesByTokenAddress[tokenAddress] || Decimal(0)
}

const actions = {
  fetchBalances({commit}) {
    commit(UPDATE_BALANCES_BEGIN)
    return account
      .getBalances()
      .then(({data}) => commit(SET_BALANCES, data))
      .then(() => commit(UPDATE_BALANCES_SUCCESS))
      .catch(exc => commit(UPDATE_BALANCES_FAILURE, exc))
  },
  fetchCredits({commit}) {
    commit(UPDATE_CREDITS_BEGIN)
    return account
      .getCredits()
      .then(({data}) => commit(SET_CREDITS, data))
      .then(() => commit(UPDATE_CREDITS_SUCCESS))
      .catch(exc => commit(UPDATE_CREDITS_FAILURE, exc))
  },
  fetchDebits({commit}) {
    commit(UPDATE_DEBITS_BEGIN)
    return account
      .getDebits()
      .then(({data}) => commit(SET_DEBITS, data))
      .then(() => commit(UPDATE_DEBITS_SUCCESS))
      .catch(exc => commit(UPDATE_DEBITS_FAILURE, exc))
  },
  fetchAll({dispatch}) {
    dispatch('fetchBalances')
    dispatch('fetchCredits')
    dispatch('fetchDebits')
  },
  initialize({dispatch}) {
    dispatch('fetchAll')
  },
  refresh({dispatch}) {
    dispatch('fetchAll')
  }
}

const mutations = {
  [UPDATE_BALANCES_BEGIN](state) {
    state.error = null
  },
  [SET_BALANCES](state, balances) {
    state.balances = balances
    state.error = null
  },
  [UPDATE_BALANCES_SUCCESS](state) {
    state.error = null
  },
  [UPDATE_BALANCES_FAILURE](state, exc) {
    state.balances = []
    state.error = exc
  },
  [UPDATE_CREDITS_BEGIN](state) {
    state.error = null
  },
  [SET_CREDITS](state, credits) {
    state.credits = credits
    state.error = null
  },
  [UPDATE_CREDITS_SUCCESS](state) {
    state.error = null
  },
  [UPDATE_CREDITS_FAILURE](state, exc) {
    state.credits = []
    state.error = exc
  },
  [UPDATE_DEBITS_BEGIN](state) {
    state.error = null
  },
  [SET_DEBITS](state, debits) {
    state.debits = debits
    state.error = null
  },
  [UPDATE_DEBITS_SUCCESS](state) {
    state.error = null
  },
  [UPDATE_DEBITS_FAILURE](state, exc) {
    state.debits = []
    state.error = exc
  }
}

export default {
  namespaced: true,
  state: initialState,
  getters,
  actions,
  mutations
}
