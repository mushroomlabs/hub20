export const NOTIFICATION_SET_SERVER = 'NOTIFICATION_SET_SERVER'
export const NOTIFICATION_WEBSOCKET_OPEN = 'NOTIFICATION_WEBSOCKET_OPEN'
export const NOTIFICATION_WEBSOCKET_CLOSE = 'NOTIFICATION_WEBSOCKET_CLOSE'
export const NOTIFICATION_WEBSOCKET_EVENT_RECEIVED = 'NOTIFICATION_WEBSOCKET_EVENT_RECEIVED'

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
  serverUrl: null,
  websocket: null,
  events: new Array()
}

const getters = {
  endpoint: (state, getters) =>
    getters.websocketRootUrl && `${getters.websocketRootUrl}${ENDPOINT}`,
  isConnected: state => state.websocket !== null,
  websocketRootUrl: state => makeWebSocketUrl(state.serverUrl)
}

const actions = {
  initialize({commit}, {serverUrl}) {
    commit(NOTIFICATION_SET_SERVER, serverUrl)
  },
  openWebSocket({commit, getters}) {
    if (getters.endpoint) {
      let ws = new WebSocket(getters.endpoint)
      ws.onmessage = evt => commit(NOTIFICATION_WEBSOCKET_EVENT_RECEIVED, JSON.parse(evt.data))
      commit(NOTIFICATION_WEBSOCKET_OPEN, ws)
    }
  }
}

const mutations = {
  [NOTIFICATION_SET_SERVER](state, serverUrl) {
    state.serverUrl = serverUrl
  },
  [NOTIFICATION_WEBSOCKET_OPEN](state, websocket) {
    state.websocket = websocket
  },
  [NOTIFICATION_WEBSOCKET_CLOSE](state) {
    state.websocket = null
  },
  [NOTIFICATION_WEBSOCKET_EVENT_RECEIVED](state, eventData) {
    state.events.push(eventData)
  }
}

export default {
  namespaced: true,
  state: initialState,
  actions,
  getters,
  mutations
}
