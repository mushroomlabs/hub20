export const ADD_NOTIFICATION = 'ADD_NOTIFICATION'

const initialState = {
  notifications: new Array()
}

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

const mutations = {
  [ADD_NOTIFICATION](state, notification) {
    notification.created = new Date()
    state.notifications.push(notification)
  }
}

export default {
  namespaced: true,
  state: initialState,
  getters,
  mutations
}
