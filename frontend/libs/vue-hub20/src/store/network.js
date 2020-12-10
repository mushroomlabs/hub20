import Vue from 'vue'

import client from '../api/network'

export const NETWORK_SET_ETHEREUM_NODE_OFFLINE = 'NETWORK_SET_ETHEREUM_NODE_OFFLINE'
export const NETWORK_SET_ETHEREUM_NODE_ONLINE = 'NETWORK_SET_ETHEREUM_NODE_ONLINE'
export const NETWORK_SET_ETHEREUM_NODE_SYNCED = 'NETWORK_SET_ETHEREUM_NODE_SYNCED'
export const NETWORK_SET_ETHEREUM_NETWORK = 'NETWORK_SET_ETHEREUM_NETWORK'
export const NETWORK_SET_ETHEREUM_ONLINE_STATUS = 'NETWORK_SET_ETHEREUM_ONLINE_STATUS'
export const NETWORK_SET_ETHEREUM_SYNCED_STATUS = 'NETWORK_SET_ETHEREUM_SYNCED_STATUS'
export const NETWORK_SET_ETHEREUM_CURRENT_BLOCK = 'NETWORK_SET_ETHEREUM_CURRENT_BLOCK'

const initialState = {
  ethereum: {
    network: null,
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

const actions = {
  getStatus({commit}) {
    client.getStatus().then(({data}) => {
      commit(NETWORK_SET_ETHEREUM_NETWORK, data.ethereum.network)
      commit(NETWORK_SET_ETHEREUM_ONLINE_STATUS, data.ethereum.online)
      commit(NETWORK_SET_ETHEREUM_SYNCED_STATUS, data.ethereum.synced)
      commit(NETWORK_SET_ETHEREUM_CURRENT_BLOCK, data.ethereum.highest_block)
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
  [NETWORK_SET_ETHEREUM_NODE_OFFLINE](state) {
    Vue.set(state.ethereum, 'online', false)
    Vue.set(state.ethereum, 'synced', false)
  },
  [NETWORK_SET_ETHEREUM_NODE_ONLINE](state) {
    Vue.set(state.ethereum, 'online', true)
  },
  [NETWORK_SET_ETHEREUM_NODE_SYNCED](state) {
    Vue.set(state.ethereum, 'synced', true)
  },
  [NETWORK_SET_ETHEREUM_NETWORK](state, networkId) {
    Vue.set(state.ethereum, 'network', networkId)
  },
  [NETWORK_SET_ETHEREUM_ONLINE_STATUS](state, onlineStatus) {
    Vue.set(state.ethereum, 'online', onlineStatus)
  },
  [NETWORK_SET_ETHEREUM_SYNCED_STATUS](state, syncedStatus) {
    Vue.set(state.ethereum, 'synced', syncedStatus)
  },
  [NETWORK_SET_ETHEREUM_CURRENT_BLOCK](state, blockNumber) {
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
