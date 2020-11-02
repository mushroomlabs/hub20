import {mapGetters} from 'vuex'

export default {
  computed: {
    ...mapGetters('tokens', ['tokensByAddress']),
    tokenOptions() {
      return Object.values(this.tokensByAddress).map(token => ({
        value: token.address,
        text: token.code
      }))
    }
  }
}
