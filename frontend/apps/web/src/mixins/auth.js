import {mapGetters} from 'vuex'

export const AuthMixin = {
  computed: {
    ...mapGetters('auth', ['isAuthenticated', 'loggedUsername'])
  }
}

export default AuthMixin
