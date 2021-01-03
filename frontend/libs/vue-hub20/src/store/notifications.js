export const ADD_NOTIFICATION = 'ADD_NOTIFICATION'
export const NOTIFICATION_RESET_STATE = 'NOTIFICATION_RESET_STATE'

const initialState = () => ({
  notifications: new Array()
})

const getters = {
  count: state => state.notifications.length,
  timeline: state => {
    const compareDateCreated = function(one, other) {
      let oneDate = one.created
      let otherDate = other.created
      if (oneDate > otherDate) {
        return -1
      }
      if (oneDate < otherDate) {
        return 1
      }
      return 0
    }
    return [...state.notifications].sort(compareDateCreated)
  }
}

const actions = {
  tearDown({commit}) {
    commit(NOTIFICATION_RESET_STATE)
  }
}

const mutations = {
  [ADD_NOTIFICATION](state, notification) {
    notification.created = new Date()
    state.notifications.push(notification)
  },
  [NOTIFICATION_RESET_STATE](state) {
    Object.assign(state, initialState())
  }
}

export default {
  namespaced: true,
  state: initialState(),
  actions,
  getters,
  mutations
}
