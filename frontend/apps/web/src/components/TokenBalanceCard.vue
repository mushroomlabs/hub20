<template>
  <card :title="tokenBalance.code">
    <slot>
      {{ tokenBalance.balance | formattedAmount(tokenBalance) }}
    </slot>
  </card>
</template>
<script>
import {filters} from 'vue-hub20'

export default {
  name: 'token-balance-card',
  filters: {
    formattedAmount: filters.formattedAmount
  },
  props: {
    tokenBalance: {
      type: Object
    }
  }
}
</script>
