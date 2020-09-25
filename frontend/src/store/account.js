import Decimal from 'decimal.js-light'

import account from '../api/account';

export const UPDATE_BALANCES_BEGIN = 'UPDATE_BALANCES_BEGIN';
export const UPDATE_BALANCES_SUCCESS = 'UPDATE_BALANCES_SUCCESS';
export const UPDATE_BALANCES_FAILURE = 'UPDATE_BALANCES_FAILURE';
export const SET_BALANCES = 'SET_BALANCES';

const initialState = {
  balances: [],
  error: null
};

const getters = {
  openBalances: state => state.balances.filter(balance => Decimal(balance.amount).gt(0))
}

const actions = {
  refreshBalances({ commit }) {
    commit(UPDATE_BALANCES_BEGIN);
    return account.getBalances()
      .then(({data}) => commit(SET_BALANCES, data))
      .then(() => commit(UPDATE_BALANCES_SUCCESS))
      .catch((exc) => commit(UPDATE_BALANCES_FAILURE, exc));
  },
  initialize({ commit }) {
    this.refreshBalances({commit});
  }
};

const mutations = {
  [UPDATE_BALANCES_BEGIN](state) {
    state.error = null;
  },
  [SET_BALANCES](state, balances) {
    state.balances = balances;
    state.error = null;
  },
  [UPDATE_BALANCES_SUCCESS](state) {
    state.error = null;
  },
  [UPDATE_BALANCES_FAILURE](state, exc) {
    state.balances = []
    state.error = exc;
  },
};

export default {
  namespaced: true,
  state: initialState,
  getters,
  actions,
  mutations,
};
