<template>
  <PaymentRequest v-if="deposit" :paymentRequest="deposit" />
</template>

<script>
import {mapActions, mapGetters} from 'vuex'
import {components as hub20Components} from 'vue-hub20'

export default {
  components: {
    PaymentRequest: hub20Components.PaymentRequest
  },
  props: {
    token: {
      type: Object
    }
  },
  computed: {
    ...mapGetters('funding', ['openDepositsByToken']),
    deposit() {
      return this.openDeposits && this.openDeposits[0]
    },
    hasOpenDeposits() {
      return this.openDeposits.length > 0
    },
    openDeposits() {
      return this.openDepositsByToken(this.token)
    }
  },
  methods: {
    ...mapActions('funding', ['createDeposit'])
  },
  mounted() {
    if (!this.deposit) {
      this.createDeposit(this.token)
    }
  }
}
</script>
