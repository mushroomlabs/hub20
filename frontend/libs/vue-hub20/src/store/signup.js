import auth from '../api/auth'

export const ACTIVATION_BEGIN = 'ACTIVATION_BEGIN'
export const ACTIVATION_CLEAR = 'ACTIVATION_CLEAR'
export const ACTIVATION_FAILURE = 'ACTIVATION_FAILURE'
export const ACTIVATION_SUCCESS = 'ACTIVATION_SUCCESS'
export const REGISTRATION_BEGIN = 'REGISTRATION_BEGIN'
export const REGISTRATION_CLEAR = 'REGISTRATION_CLEAR'
export const REGISTRATION_FAILURE = 'REGISTRATION_FAILURE'
export const REGISTRATION_SUCCESS = 'REGISTRATION_SUCCESS'

export default {
  namespaced: true,
  state: {
    activationCompleted: false,
    activationError: false,
    activationLoading: false,
    registrationCompleted: false,
    registrationError: false,
    registrationLoading: false
  },
  actions: {
    createAccount({commit}, {username, password1, password2, email}) {
      commit(REGISTRATION_BEGIN)
      return auth
        .createAccount(username, password1, password2, email)
        .then(({data}) => {
          commit(REGISTRATION_SUCCESS)
          return data.key
        })
        .catch(() => commit(REGISTRATION_FAILURE))
    },
    activateAccount({commit}, {key}) {
      commit(ACTIVATION_BEGIN)
      return auth
        .verifyAccountEmail(key)
        .then(() => commit(ACTIVATION_SUCCESS))
        .catch(() => commit(ACTIVATION_FAILURE))
    },
    clearRegistrationStatus({commit}) {
      commit(REGISTRATION_CLEAR)
    },
    clearActivationStatus({commit}) {
      commit(ACTIVATION_CLEAR)
    }
  },
  mutations: {
    [ACTIVATION_BEGIN](state) {
      state.activationLoading = true
    },
    [ACTIVATION_CLEAR](state) {
      state.activationCompleted = false
      state.activationError = false
      state.activationLoading = false
    },
    [ACTIVATION_FAILURE](state) {
      state.activationError = true
      state.activationLoading = false
    },
    [ACTIVATION_SUCCESS](state) {
      state.activationCompleted = true
      state.activationError = false
      state.activationLoading = false
    },
    [REGISTRATION_BEGIN](state) {
      state.registrationLoading = true
    },
    [REGISTRATION_CLEAR](state) {
      state.registrationCompleted = false
      state.registrationError = false
      state.registrationLoading = false
    },
    [REGISTRATION_FAILURE](state) {
      state.registrationError = true
      state.registrationLoading = false
    },
    [REGISTRATION_SUCCESS](state) {
      state.registrationCompleted = true
      state.registrationError = false
      state.registrationLoading = false
    }
  }
}
