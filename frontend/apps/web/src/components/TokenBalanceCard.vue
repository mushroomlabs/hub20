<template>
  <card :title="tokenBalance.currency.code">
    <slot>
      {{ tokenBalance.balance }}
    </slot>
  </card>
</template>
<script>
export default {
  name: "token-balance-card",
  props: {
    tokenBalance: {
      type: Object
    }
  }
}
</script>
