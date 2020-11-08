import {mapGetters} from 'vuex'

export const TokenMixin = {
  computed: mapGetters('tokens', ['tokensByAddress']),
  methods: {
    getToken(tokenAddress) {
      return this.tokensByAddress[tokenAddress]
    }
  }
}

export default TokenMixin
