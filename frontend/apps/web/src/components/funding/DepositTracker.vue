<template>
  <PaymentRequest v-if="deposit" :paymentRequest="deposit" />
</template>

<script>
import {mapActions, mapGetters} from 'vuex'
import {default as hub20lib} from 'vue-hub20'

const {PaymentRequest} = hub20lib.components

export default {
  components: {
    PaymentRequest
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
