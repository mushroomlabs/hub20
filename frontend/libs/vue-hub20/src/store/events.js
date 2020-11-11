export const EVENT_WEBSOCKET_OPEN = 'EVENT_WEBSOCKET_OPEN'
export const EVENT_WEBSOCKET_CLOSE = 'EVENT_WEBSOCKET_CLOSE'
export const EVENT_WEBSOCKET_SET_HANDLER = 'EVENT_WEBSOCKET_SET_HANDLER'

function makeWebSocketUrl(httpUrl) {
  if (!httpUrl) {
    return null
  }

  let url = new URL(httpUrl)
  let ws_protocol = url.protocol == 'http:' ? 'ws:' : 'wss:'
  url.protocol = ws_protocol
  return url.origin
}

const ENDPOINT = '/ws/events'

const initialState = {
  websocket: null,
  messageHandler: null
}

const getters = {
  endpoint: state => state.websocket && state.websocket.url,
  isConnected: state => state.websocket && state.websocket.readyState == 1
}

const actions = {
  initialize({commit}, serverUrl) {
    const url = `${makeWebSocketUrl(serverUrl)}${ENDPOINT}`
    const ws = new WebSocket(url)
    commit(EVENT_WEBSOCKET_OPEN, ws)
  },
  setEventHandler({commit, state}, messageHandler) {
    if (state.websocket) {
      state.websocket.onmessage = messageHandler
    }

    commit(EVENT_WEBSOCKET_SET_HANDLER, messageHandler)
  }
}

const mutations = {
  [EVENT_WEBSOCKET_OPEN](state, websocket) {
    state.websocket = websocket
  },
  [EVENT_WEBSOCKET_CLOSE](state) {
    state.websocket = null
  },
  [EVENT_WEBSOCKET_SET_HANDLER](state, handler) {
    state.messageHandler = handler
  }
}

export default {
  namespaced: true,
  state: initialState,
  actions,
  getters,
  mutations
}
