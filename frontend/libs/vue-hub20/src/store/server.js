import Vue from 'vue'

export const SERVER_SET_URL = 'SERVER_SET_URL'
export const SERVER_SET_ETHEREUM_NODE_OFFLINE = 'SERVER_SET_ETHEREUM_NODE_OFFLINE'
export const SERVER_SET_ETHEREUM_NODE_ONLINE = 'SERVER_SET_ETHEREUM_NODE_ONLINE'
export const SERVER_SET_ETHEREUM_NODE_SYNCED = 'SERVER_SET_ETHEREUM_NODE_SYNCED'
export const SERVER_SET_ETHEREUM_NODE_CURRENT_BLOCK = 'SERVER_SET_ETHEREUM_NODE_CURRENT_BLOCK'

const initialState = {
  rootUrl: window.origin,
  ethereum: {
    synced: false,
    online: false,
    currentBlock: null
  }
}

const getters = {
  ethereumNodeOk: state => state.ethereum.synced && state.ethereum.online,
  ethereumOnline: state => state.ethereum.online,
  ethereumSynced: state => state.ethereum.synced,
  currentBlock: state => state.ethereum.currentBlock
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
  [SERVER_SET_ETHEREUM_NODE_CURRENT_BLOCK](state, blockNumber) {
    Vue.set(state.ethereum, 'currentBlock', blockNumber)
  }
}

export default {
  namespaced: true,
  state: initialState,
  getters,
  mutations
}
