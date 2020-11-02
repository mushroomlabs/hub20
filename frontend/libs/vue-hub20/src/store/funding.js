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
  transfers: state => Object.values(state.transfersById)
}

const actions = {
  createDeposit({commit}, {token, amount}) {
    return client
      .createPaymentOrder(token, amount)
      .then(({data}) => commit(FUNDING_DEPOSIT_BEGIN, data))
      .catch(error => commit(FUNDING_DEPOSIT_FAILURE, error.response))
  },
  cancelDeposit({commit, dispatch}, orderId) {
    return client
      .cancelPaymentOrder(orderId)
      .then(() => dispatch('fetchDeposit', orderId))
      .catch(error => commit(FUNDING_DEPOSIT_FAILURE, error.response))
  },
  fetchDeposit({commit}, orderId) {
    return client
      .getPaymentOrder(orderId)
      .then(({orderData}) => commit(FUNDING_DEPOSIT_SUCCESS, orderData))
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
    Object.keys(state.depositsById).forEach(orderId => dispatch('fetchDeposit', orderId))
  }
}

const mutations = {
  [FUNDING_INITIALIZE](state) {
    Object.assign({...initialState}, state)
  },
  [FUNDING_DEPOSIT_BEGIN](state, orderData) {
    state.depositsById[orderData.id] = orderData
    state.error = null
  },
  [FUNDING_DEPOSIT_FAILURE](state, error) {
    state.error = error.data
  },
  [FUNDING_DEPOSIT_CANCEL](state, orderId) {
    let order = state.depositsById[orderId]

    if (order) {
      order.status = 'canceled'
    }
  },
  [FUNDING_DEPOSIT_SUCCESS](state, orderData) {
    state.depositsById[orderData.id] = orderData
  },
  [FUNDING_DEPOSIT_SET_EXPIRED](state, orderId) {
    let order = state.depositsById[orderId]

    if (order) {
      order.status = 'expired'
    }
  },
  [FUNDING_TRANSFER_BEGIN](state, transferData) {
    state.transfersById[transferData.id] = transferData
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
