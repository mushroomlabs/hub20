import stores from '../api/stores';

import {
  STORE_COLLECTION_SET,
  STORE_SETUP_BEGIN,
  STORE_SETUP_SUCCESS,
  STORE_SETUP_FAILURE,
  STORE_UPDATE_SUCCESS,
  STORE_UPDATE_FAILURE,
  STORE_CREATE_FAILURE
} from './types';

const initialState = {
  stores: [],
  error: null,
};

const getters = {
  storesById: state => state.stores.reduce((acc, store) => Object.assign({[store.id]: store}, acc), {})
};

const actions = {
  fetchStores({ commit }) {
    return stores.getList()
      .then(({ data }) => commit(STORE_COLLECTION_SET, data))
      .then(() => commit(STORE_SETUP_SUCCESS))
      .catch((error) => commit(STORE_SETUP_FAILURE, error));
  },
  updateStore({ commit }, storeData) {
    return stores.update(storeData)
      .then(() => commit(STORE_UPDATE_SUCCESS))
      .catch(() => commit(STORE_UPDATE_FAILURE));
  },
  createStore({commit, dispatch}, storeData) {
    return stores.create(storeData)
      .then(() => dispatch('stores/fetchStores'))
      .catch((error) => commit(STORE_CREATE_FAILURE, error))
  },
  initialize({ commit, dispatch }) {
    commit(STORE_SETUP_BEGIN);
    dispatch("fetchStores");
  }
};

const mutations = {
  [STORE_SETUP_BEGIN](state) {
    state.stores = [];
    state.error = null;
  },
  [STORE_SETUP_FAILURE](state, error) {
    state.error = error
  },
  [STORE_SETUP_SUCCESS](state) {
    state.error = null
  },
  [STORE_COLLECTION_SET](state, data) {
    state.stores = data;
  },
  [STORE_CREATE_FAILURE](state, error) {
    state.error = error
  }
};

export default {
  namespaced: true,
  state: initialState,
  getters,
  actions,
  mutations,
};
