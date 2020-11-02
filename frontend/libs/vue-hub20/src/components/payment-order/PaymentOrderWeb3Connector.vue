<template>
  <button v-on:click='makeTransfer' class='payment-order-web3-connector'>Pay with Web3 Wallet</button>
</template>

<script>
  export default {
      name: 'PaymentOrderWeb3Connector',
      methods: {
          makeTransfer: function() {
              this.$store.dispatch('makeWeb3Transfer')
          }
      }
  }
</script>
