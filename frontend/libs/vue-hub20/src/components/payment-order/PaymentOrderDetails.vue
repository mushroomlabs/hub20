<template>
<div class="payment-order-details">
  <div class="payment-reference">
    <span class="field-description">Payment Reference</span>
    <span class="field-value">{{ paymentOrder.identifier }}</span>
  </div>
  <div class="payment-amount">
    <span class="field-description">Amount</span>
    <span class="field-value">{{ amountFormatted }}</span>
    <span class="field-value">
      <TokenAmountDisplay
        :token='selectedToken'
        :amount='tokenAmount'
      />
    </span>
  </div>
</div>
</template>

<script>
import {mapGetters} from 'vuex'

import TokenAmountDisplay from './TokenAmountDisplay.vue'

export default {
    name: 'PaymentOrderDetails',
    components: {
        TokenAmountDisplay
    },
    computed:{
        tokenAmount: function() {
            return this.paymentOrder.tokenAmount && this.paymentOrder.tokenAmount.toNumber()
        },
        ...mapGetters(['paymentOrder', 'amountFormatted', 'selectedToken'])
    }
}
</script>
