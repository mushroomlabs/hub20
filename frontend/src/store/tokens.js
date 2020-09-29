import tokens from '../api/tokens';

import {
  TOKEN_COLLECTION_SET,
  TOKEN_SETUP_BEGIN,
  TOKEN_SETUP_SUCCESS,
  TOKEN_SETUP_FAILURE,
} from './types';

const initialState = {
  tokens: [],
  error: null,
};

const getters = {
  tokensByAddress: state => state.tokens.reduce((acc, token) => Object.assign({[token.address]: token}, acc), {})
};

const actions = {
  fetchTokens({ commit }) {
    commit(TOKEN_SETUP_BEGIN);
    return tokens.getList()
      .then(({ data }) => commit(TOKEN_COLLECTION_SET, data))
      .then(() => commit(TOKEN_SETUP_SUCCESS))
      .catch((error) => commit(TOKEN_SETUP_FAILURE, error));
  },
};

const mutations = {
  [TOKEN_SETUP_BEGIN](state) {
    state.tokens = [];
    state.error = null;
  },
  [TOKEN_SETUP_FAILURE](state, error) {
    state.error = error
  },
  [TOKEN_SETUP_SUCCESS](state) {
    state.error = null
  },
  [TOKEN_COLLECTION_SET](state, data) {
    state.tokens = data;
  }
};

export default {
  namespaced: true,
  state: initialState,
  getters,
  actions,
  mutations,
};
