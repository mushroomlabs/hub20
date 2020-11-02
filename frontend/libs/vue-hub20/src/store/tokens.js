import tokens from '../api/tokens'

export const TOKEN_COLLECTION_SET = 'TOKEN_COLLECTION_SET'
export const TOKEN_SETUP_BEGIN = 'TOKEN_SETUP_BEGIN'
export const TOKEN_SETUP_SUCCESS = 'TOKEN_SETUP_SUCCESS'
export const TOKEN_SETUP_FAILURE = 'TOKEN_SETUP_FAILURE'

const initialState = {
  tokens: [],
  error: null
}

const getters = {
  tokensByAddress: state =>
    state.tokens.reduce((acc, token) => Object.assign({[token.address]: token}, acc), {}),
  tokensByCode: state =>
    state.tokens.reduce((acc, token) => Object.assign({[token.code]: token}, acc), {})
}

const actions = {
  fetchTokens({commit}) {
    commit(TOKEN_SETUP_BEGIN)
    return tokens
      .getList()
      .then(({data}) => commit(TOKEN_COLLECTION_SET, data))
      .then(() => commit(TOKEN_SETUP_SUCCESS))
      .catch(error => commit(TOKEN_SETUP_FAILURE, error))
  },
  initialize({dispatch}) {
    dispatch('fetchTokens')
  }
}

const mutations = {
  [TOKEN_SETUP_BEGIN](state) {
    state.tokens = []
    state.error = null
  },
  [TOKEN_SETUP_FAILURE](state, error) {
    state.error = error
  },
  [TOKEN_SETUP_SUCCESS](state) {
    state.error = null
  },
  [TOKEN_COLLECTION_SET](state, data) {
    state.tokens = data
  }
}

export default {
  namespaced: true,
  state: initialState,
  getters,
  actions,
  mutations
}
