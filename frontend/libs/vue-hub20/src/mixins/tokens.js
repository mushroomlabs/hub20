import {mapGetters} from 'vuex'

import {formattedAmount} from '../filters'

export const TokenMixin = {
  computed: {
    ...mapGetters('tokens', ['tokensByAddress']),
    tokenOptions() {
      return Object.values(this.tokensByAddress).map(token => ({
        value: token.address,
        text: token.code
      }))
    }
  },
  filters: {formattedAmount},
  methods: {
    getToken(tokenAddress) {
      return this.tokensByAddress[tokenAddress]
    }
  }
}

export default TokenMixin
