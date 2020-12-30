<template>
  <span :class="{negative: isNegativeValue}">{{ formattedAmount }}</span>
</template>
<script>
export default {
  name: 'accounting-token-balance-display',
  props: {
    tokenBalance: Object
  },
  computed: {
    isNegativeValue() {
      return this.tokenBalance && parseInt(this.tokenBalance.balance) < 0
    },
    formattedAmount() {
      if (!this.tokenBalance) {
        return '-'
      }

      let formatter = new Intl.NumberFormat([], {
        maximumSignificantDigits: this.tokenBalance.decimals
      })
      return formatter.format(this.tokenBalance.balance)
    }
  }
}
</script>
