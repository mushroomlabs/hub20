<template>
<div class='token-selector'>
  <h6 class='token-selector-payment-info'>
    Select one of the following tokens to initiate a transfer equivalent to {{ amountFormatted }}
  </h6>
  <ul class='token-selector-options'>
    <TokenSelectorItem
      v-for='token in allTokens'
      :key='token.code'
      :token='token'
      />
  </ul>
</div>
</template>


<script>
import {mapState, mapGetters} from 'vuex'

import TokenSelectorItem from './TokenSelectorItem.vue'

export default {
    name: 'TokenSelector',
    components: {
        TokenSelectorItem,
    },
    computed: {
        amountFormatted() {
            let formatter = new Intl.NumberFormat([], {style: 'currency', currency: this.pricingCurrency})
            return formatter.format(this.amountDue)
        },
        ...mapGetters(['allTokens']),
        ...mapState(['pricingCurrency', 'store', 'amountDue'])
    },
    async mounted() {
        this.$store.dispatch('fetchAllTokenData')
    }
}
</script>
