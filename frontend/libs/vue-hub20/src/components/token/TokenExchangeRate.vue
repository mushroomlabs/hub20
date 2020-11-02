<template>
<div v-if='token' class='token-exchange-rate'>
  <div class='rate'>Current rate: {{ exchangeRateFormatted }}</div>
  <div class='due'>Total to Pay:
    <TokenAmountDisplay
      :token='token'
      :amount='tokenAmountDue'
      :max-significant-digits=6
      />
  </div>
</div>
</template>


<script>
import {mapState, mapGetters} from 'vuex'

import TokenAmountDisplay from './TokenAmountDisplay.vue'

export default {
    name: 'TokenExchangeRate',
    components: {
        TokenAmountDisplay
    },
    props: {
        token: Object,
    },
    computed: {
        exchangeRateFormatted: function() {
            let exchangeRate = this.getExchangeRate(this.token)
            let formatter = new Intl.NumberFormat(
                [], {style: 'currency', currency: this.pricingCurrency, minimumFractionDigits: 3}
            )
            return `${formatter.format(exchangeRate)} / ${this.token.code}`
        },
        tokenAmountDue: function() {
            let amount = this.convertToTokenAmount(this.amountDue, this.token)
            return (this.amountDue && this.token && amount && amount.toNumber()) || 0
        },
        ...mapGetters(['convertToTokenAmount', 'getExchangeRate']),
        ...mapState(['amountDue', 'pricingCurrency']),
    }
}
</script>
