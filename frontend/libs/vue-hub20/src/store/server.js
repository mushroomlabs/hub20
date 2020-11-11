import Vue from 'vue'

import client from '../api/server'

export const SERVER_SET_URL = 'SERVER_SET_URL'
export const SERVER_SET_ETHEREUM_NODE_OFFLINE = 'SERVER_SET_ETHEREUM_NODE_OFFLINE'
export const SERVER_SET_ETHEREUM_NODE_ONLINE = 'SERVER_SET_ETHEREUM_NODE_ONLINE'
export const SERVER_SET_ETHEREUM_NODE_SYNCED = 'SERVER_SET_ETHEREUM_NODE_SYNCED'
export const SERVER_SET_ETHEREUM_NETWORK = 'SERVER_SET_ETHEREUM_NETWORK'
export const SERVER_SET_ETHEREUM_ONLINE_STATUS = 'SERVER_SET_ETHEREUM_ONLINE_STATUS'
export const SERVER_SET_ETHEREUM_SYNCED_STATUS = 'SERVER_SET_ETHEREUM_SYNCED_STATUS'
export const SERVER_SET_ETHEREUM_CURRENT_BLOCK = 'SERVER_SET_ETHEREUM_CURRENT_BLOCK'

const initialState = {
  rootUrl: window.origin,
  ethereum: {
    network: null,
    synced: false,
    online: false,
    currentBlock: null
  },
  error: null
}

const getters = {
  ethereumNodeOk: state => state.ethereum.synced && state.ethereum.online,
  ethereumOnline: state => state.ethereum.online,
  ethereumSynced: state => state.ethereum.synced,
  currentBlock: state => state.ethereum.currentBlock
}

const actions = {
  getStatus({commit}) {
    client.getStatus().then(({data}) => {
      commit(SERVER_SET_ETHEREUM_NETWORK, data.ethereum.network)
      commit(SERVER_SET_ETHEREUM_ONLINE_STATUS, data.ethereum.online)
      commit(SERVER_SET_ETHEREUM_SYNCED_STATUS, data.ethereum.synced)
      commit(SERVER_SET_ETHEREUM_CURRENT_BLOCK, data.ethereum.highest_block)
    })
  },
  initialize({dispatch}) {
    dispatch('getStatus')
  },
  refresh({dispatch}) {
    dispatch('getStatus')
  }
}

const mutations = {
  [SERVER_SET_URL](state, url) {
    state.rootUrl = url
  },
  [SERVER_SET_ETHEREUM_NODE_OFFLINE](state) {
    Vue.set(state.ethereum, 'online', false)
    Vue.set(state.ethereum, 'synced', false)
  },
  [SERVER_SET_ETHEREUM_NODE_ONLINE](state) {
    Vue.set(state.ethereum, 'online', true)
  },
  [SERVER_SET_ETHEREUM_NODE_SYNCED](state) {
    Vue.set(state.ethereum, 'synced', true)
  },
  [SERVER_SET_ETHEREUM_NETWORK](state, networkId) {
    Vue.set(state.ethereum, 'network', networkId)
  },
  [SERVER_SET_ETHEREUM_ONLINE_STATUS](state, onlineStatus) {
    Vue.set(state.ethereum, 'online', onlineStatus)
  },
  [SERVER_SET_ETHEREUM_SYNCED_STATUS](state, syncedStatus) {
    Vue.set(state.ethereum, 'synced', syncedStatus)
  },
  [SERVER_SET_ETHEREUM_CURRENT_BLOCK](state, blockNumber) {
    Vue.set(state.ethereum, 'currentBlock', blockNumber)
  }
}

export default {
  namespaced: true,
  state: initialState,
  actions,
  getters,
  mutations
}
