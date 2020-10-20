import stores from '../api/stores'

import {
  STORE_INITIALIZE,
  STORE_COLLECTION_SET,
  STORE_COLLECTION_SETUP_SUCCESS,
  STORE_COLLECTION_SETUP_FAILURE,
  STORE_UPDATE_SET_NAME,
  STORE_UPDATE_SET_URL,
  STORE_UPDATE_SET_ACCEPTED_TOKENS,
  STORE_UPDATE_BEGIN,
  STORE_UPDATE_SUCCESS,
  STORE_UPDATE_FAILURE,
  STORE_CREATE_FAILURE,
} from './types'

const initialState = {
  collection: {
    data: [],
    error: null,
  },
  create: {
    data: null,
    error: null,
  },
  update: {
    data: null,
    error: null,
  },
}

const getters = {
  stores: (state) => state.collection.data,
  storesById: (state) =>
    state.collection.data.reduce((acc, store) => Object.assign({[store.id]: store}, acc), {}),
  storeEditData: (state) => state.create.data || state.update.data,
  storeEditError: (state) => state.create.error || state.update.error,
}

const actions = {
  fetchStores({commit}) {
    return stores
      .getList()
      .then(({data}) => commit(STORE_COLLECTION_SET, data))
      .catch((error) => commit(STORE_COLLECTION_SETUP_FAILURE, error.response))
  },
  updateStore({commit}, storeData) {
    return stores
      .update(storeData)
      .then(() => commit(STORE_UPDATE_SUCCESS))
      .catch((error) => commit(STORE_UPDATE_FAILURE, error.response))
  },
  createStore({commit, dispatch}, storeData) {
    return stores
      .create(storeData)
      .then(() => dispatch('fetchStores'))
      .catch((error) => commit(STORE_CREATE_FAILURE, error))
  },
  editStore({getters, commit}, storeId) {
    const store = getters.storesById[storeId]
    const storeDataPromise = store ? Promise.resolve({data: store}) : stores.get(storeId)

    return storeDataPromise
      .then(({data}) => commit(STORE_UPDATE_BEGIN, data))
      .catch((error) => commit(STORE_UPDATE_FAILURE, error))
  },
  initialize({commit, dispatch}) {
    commit(STORE_INITIALIZE)
    dispatch('fetchStores')
  },
  refresh({dispatch}) {
    dispatch('fetchStores')
  },
}

const mutations = {
  [STORE_INITIALIZE](state) {
    Object.assign({...initialState}, state)
  },
  [STORE_COLLECTION_SETUP_FAILURE](state, error) {
    state.collection.error = error
  },
  [STORE_COLLECTION_SETUP_SUCCESS](state) {
    state.collection.error = null
  },
  [STORE_UPDATE_BEGIN](state, storeData) {
    state.update.data = storeData
  },
  [STORE_UPDATE_SUCCESS](state) {
    state.update.error = null
  },
  [STORE_UPDATE_FAILURE](state, error) {
    state.update.error = error.data
  },
  [STORE_UPDATE_SET_NAME](state, name) {
    if (state.update.data) {
      state.update.data.name = name
    }
  },
  [STORE_UPDATE_SET_URL](state, siteUrl) {
    if (state.update.data) {
      state.update.data.site_url = siteUrl
    }
  },
  [STORE_UPDATE_SET_ACCEPTED_TOKENS](state, acceptedTokens) {
    if (state.update.data) {
      state.update.data.accepted_currencies = acceptedTokens
    }
  },
  [STORE_COLLECTION_SET](state, data) {
    state.collection.data = data
  },
  [STORE_CREATE_FAILURE](state, error) {
    state.create.error = error.data
  },
}

export default {
  namespaced: true,
  state: initialState,
  actions,
  getters,
  mutations,
}
