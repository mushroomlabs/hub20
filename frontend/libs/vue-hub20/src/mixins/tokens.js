import {mapGetters} from 'vuex'

import {formattedAmount} from '../filters'

export const TokenMixin = {
  computed: mapGetters('tokens', ['tokensByAddress']),
  filters: {formattedAmount},
  methods: {
    getToken(tokenAddress) {
      return this.tokensByAddress[tokenAddress]
    }
  }
}

export default TokenMixin
