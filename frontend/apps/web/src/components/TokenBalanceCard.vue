<template>
  <card :title="tokenBalance.currency.code">
    <slot>
      {{ tokenBalance.amount | formattedAmount(tokenBalance.currency) }}
    </slot>
  </card>
</template>
<script>
import {filters as hub20filters} from 'vue-hub20'

export default {
  name: "token-balance-card",
  filters: {
    formattedAmount: hub20filters.formattedAmount
  },
  props: {
    tokenBalance: {
      type: Object
    }
  }
}
</script>
