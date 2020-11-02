export const ADD_NOTIFICATION = 'ADD_NOTIFICATION'

const initialState = {
  notifications: new Array()
}

const getters = {
  count: state => state.notifications.length,
  timeline: state => {
    const compareDateReceived = function(one, other) {
      let oneDate = one.received
      let otherDate = other.received
      if (oneDate > otherDate) {
        return -1
      }
      if (oneDate < otherDate) {
        return 1
      }
      return 0
    }
    return [...state.notifications].sort(compareDateReceived)
  }
}

const mutations = {
  [ADD_NOTIFICATION](state, notification_text) {
    state.notifications.push({
      received: new Date(),
      text: notification_text
    })
  }
}

export default {
  namespaced: true,
  state: initialState,
  getters,
  mutations
}
