import Decimal from 'decimal.js-light'

import client from '../api/audit'

export const AUDIT_FETCH_ACCOUNTING_REPORT_BEGIN = 'AUDIT_FETCH_ACCOUNTING_REPORT_BEGIN'
export const AUDIT_FETCH_ACCOUNTING_REPORT_FAILURE = 'AUDIT_FETCH_ACCOUNTING_REPORT_FAILURE'
export const AUDIT_FETCH_ACCOUNTING_REPORT_SUCCESS = 'AUDIT_FETCH_ACCOUNTING_REPORT_SUCCESS'
export const AUDIT_FETCH_WALLET_BALANCES_BEGIN = 'AUDIT_FETCH_WALLET_BALANCES_BEGIN'
export const AUDIT_FETCH_WALLET_BALANCES_FAILURE = 'AUDIT_FETCH_WALLET_BALANCES_FAILURE'
export const AUDIT_FETCH_WALLET_BALANCES_SUCCESS = 'AUDIT_FETCH_WALLET_BALANCES_SUCCESS'
export const AUDIT_RESET_STATE = 'AUDIT_RESET_STATE'

const isSameToken = (one, another) =>
  one.address == another.address && one.network_id == another.network_id

const sumBalances = (one, another) => {
  if (!one) {
    return another
  }

  if (!another) {
    return one
  }

  if (!isSameToken(one, another)) {
    throw `Can not sum ${one.code} (${one.address}) with ${another.code} (${another.address})`
  }

  let sum = new Decimal(one.balance || 0).add(new Decimal(another.balance || 0))

  return {...one, balance: sum.toString()}
}

const filterByToken = (tokenList, token) =>
  tokenList && tokenList.filter(tokenBalance => isSameToken(tokenBalance, token))

const getTokenBalance = (tokenList, token) =>
  tokenList && filterByToken(tokenList, token).shift()

const initialState = () => ({
  loadingBooks: false,
  loadingWallets: false,
  accountingBooks: null,
  wallets: null,
  error: null
})

const getters = {
  treasuryBalances: state => state.accountingBooks && state.accountingBooks.treasury,
  userBalances: state => state.accountingBooks && state.accountingBooks.user_accounts,
  walletBalances: state => state.accountingBooks && state.accountingBooks.wallets,
  raidenBalances: state => state.accountingBooks && state.accountingBooks.raiden,
  externalAccountBalances: state =>
    state.accountingBooks && state.accountingBooks.external_addresses,
  treasuryTokenBalance: (state, getters) => token =>
    getTokenBalance(getters.treasuryBalances, token),
  userTokenBalance: (state, getters) => token => getTokenBalance(getters.userBalances, token),
  walletTokenBalance: (state, getters) => token =>
    getTokenBalance(getters.walletBalances, token),
  raidenTokenBalance: (state, getters) => token =>
    getTokenBalance(getters.raidenBalances, token),
  externalTokenBalance: (state, getters) => token =>
    getTokenBalance(getters.externalAccountBalances, token),
  totalTokenAssets: (state, getters) => token => {
    let storedAssets = sumBalances(
      getters.walletTokenBalance(token),
      getters.raidenTokenBalance(token)
    )
    return sumBalances(storedAssets, getters.treasuryTokenBalance(token))
  },
  walletAddresses: state => state.wallets && Object.keys(state.wallets),
  walletBalance: state => (address, token) => {
    let walletBalances = state.wallets && state.wallets[address]
    return walletBalances && getTokenBalance(walletBalances, token)
  }
}

const actions = {
  fetchAccountingReport({commit}) {
    commit(AUDIT_FETCH_ACCOUNTING_REPORT_BEGIN)
    client
      .getAccountingReport()
      .then(({data}) => commit(AUDIT_FETCH_ACCOUNTING_REPORT_SUCCESS, data))
      .catch(exc => commit(AUDIT_FETCH_ACCOUNTING_REPORT_FAILURE, exc))
  },
  fetchWalletBalances({commit}) {
    commit(AUDIT_FETCH_WALLET_BALANCES_BEGIN)
    client
      .getWalletBalances()
      .then(({data}) => commit(AUDIT_FETCH_WALLET_BALANCES_SUCCESS, data))
      .catch(exc => commit(AUDIT_FETCH_WALLET_BALANCES_FAILURE, exc))
  },
  initialize({dispatch}) {
    dispatch('fetchAccountingReport')
    dispatch('fetchWalletBalances')
  },
  refresh({dispatch}) {
    dispatch('fetchAccountingReport')
    dispatch('fetchWalletBalances')
  },
  tearDown({commit}) {
    commit(AUDIT_RESET_STATE)
  }
}

const mutations = {
  [AUDIT_FETCH_ACCOUNTING_REPORT_BEGIN](state) {
    state.loadingBooks = true
  },
  [AUDIT_FETCH_ACCOUNTING_REPORT_SUCCESS](state, accountingBooksData) {
    state.loadingBooks = false
    state.accountingBooks = accountingBooksData
  },
  [AUDIT_FETCH_ACCOUNTING_REPORT_FAILURE](state, error) {
    state.loadingBooks = false
    state.error = error
  },
  [AUDIT_FETCH_WALLET_BALANCES_BEGIN](state) {
    state.loadingWallets = true
  },
  [AUDIT_FETCH_WALLET_BALANCES_SUCCESS](state, walletData) {
    state.loadingWallets = false
    state.wallets = walletData
  },
  [AUDIT_FETCH_WALLET_BALANCES_FAILURE](state, error) {
    state.loadingWallets = false
    state.error = error
  },
  [AUDIT_RESET_STATE](state) {
    Object.assign(state, initialState())
  }
}

export default {
  namespaced: true,
  state: initialState(),
  actions,
  getters,
  mutations
}
