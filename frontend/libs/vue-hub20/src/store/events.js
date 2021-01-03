export const EVENT_WEBSOCKET_OPEN = 'EVENT_WEBSOCKET_OPEN'
export const EVENT_WEBSOCKET_CLOSE = 'EVENT_WEBSOCKET_CLOSE'
export const EVENT_WEBSOCKET_SET_HANDLER = 'EVENT_WEBSOCKET_SET_HANDLER'
export const EVENT_RESET_STATE = 'EVENT_RESET_STATE'

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

const initialState = () => ({
  websocket: null,
  messageHandler: null
})

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
  },
  tearDown({commit}) {
    commit(EVENT_RESET_STATE)
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
  },
  [EVENT_RESET_STATE](state) {
    if (state.websocket) {
      state.websocket.close()
    }
    Object.assign(state, initialState())
  }
}

export default {
  namespaced: true,
  state: initialState(),
  actions,
  mutations
}
