import stores from '../api/stores'

export const STORE_INITIALIZE = 'STORE_INITIALIZE'
export const STORE_COLLECTION_SET = 'STORE_COLLECTION_SET'
export const STORE_COLLECTION_SETUP_SUCCESS = 'STORE_COLLECTION_SETUP_SUCCESS'
export const STORE_COLLECTION_SETUP_FAILURE = 'STORE_COLLECTION_SETUP_FAILURE'
export const STORE_EDIT_BEGIN = 'STORE_EDIT_BEGIN'
export const STORE_EDIT_SET_NAME = 'STORE_EDIT_SET_NAME'
export const STORE_EDIT_SET_URL = 'STORE_EDIT_SET_URL'
export const STORE_EDIT_SET_ACCEPTED_TOKENS = 'STORE_EDIT_SET_ACCEPTED_TOKENS'
export const STORE_EDIT_SUCCESS = 'STORE_EDIT_SUCCESS'
export const STORE_EDIT_FAILURE = 'STORE_EDIT_FAILURE'

const initialStoreData = {
  name: '',
  site_url: '',
  accepted_currencies: []
}

const initialState = {
  collection: {
    data: [],
    error: null
  },
  edit: {
    data: null,
    error: null
  }
}

const getters = {
  stores: state => state.collection.data,
  storesById: state =>
    state.collection.data.reduce((acc, store) => Object.assign({[store.id]: store}, acc), {}),
  storeEditData: state => state.edit.data,
  storeEditError: state => state.edit.error
}

const actions = {
  fetchStores({commit}) {
    return stores
      .getList()
      .then(({data}) => commit(STORE_COLLECTION_SET, data))
      .catch(error => commit(STORE_COLLECTION_SETUP_FAILURE, error.response))
  },
  updateStore({commit}, storeData) {
    return stores
      .update(storeData)
      .then(() => commit(STORE_EDIT_SUCCESS))
      .catch(error => commit(STORE_EDIT_FAILURE, error.response))
  },
  createStore({commit, dispatch}, storeData) {
    return stores
      .create(storeData)
      .then(() => commit(STORE_EDIT_SUCCESS))
      .then(() => dispatch('fetchStores'))
      .catch(error => commit(STORE_EDIT_FAILURE, error))
  },
  editStore({getters, commit}, storeId) {
    const isCached = storeId in getters.storesById
    const storeData = storeId ? getters.storesById[storeId] : initialStoreData
    const storeDataPromise =
      storeId && !isCached ? stores.get(storeId) : Promise.resolve({data: storeData})

    return storeDataPromise
      .then(({data}) => commit(STORE_EDIT_BEGIN, data))
      .catch(error => commit(STORE_EDIT_FAILURE, error))
  },
  removeStore({dispatch}, storeData) {
    return stores.remove(storeData.id).then(() => dispatch('fetchStores'))
  },
  initialize({commit, dispatch}) {
    commit(STORE_INITIALIZE)
    dispatch('fetchStores')
  },
  refresh({dispatch}) {
    dispatch('fetchStores')
  }
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
  [STORE_EDIT_BEGIN](state, storeData) {
    state.edit.data = storeData || initialStoreData
  },
  [STORE_EDIT_SUCCESS](state) {
    state.edit.error = null
  },
  [STORE_EDIT_FAILURE](state, error) {
    state.edit.error = error.data
  },
  [STORE_EDIT_SET_NAME](state, name) {
    if (state.edit.data) {
      state.edit.data.name = name
    }
  },
  [STORE_EDIT_SET_URL](state, siteUrl) {
    if (state.edit.data) {
      state.edit.data.site_url = siteUrl
    }
  },
  [STORE_EDIT_SET_ACCEPTED_TOKENS](state, acceptedTokens) {
    if (state.edit.data) {
      state.edit.data.accepted_currencies = acceptedTokens
    }
  },
  [STORE_COLLECTION_SET](state, data) {
    state.collection.data = data
  }
}

export default {
  namespaced: true,
  state: initialState,
  actions,
  getters,
  mutations
}
