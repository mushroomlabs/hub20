<template>
<card :title="cardTitle">
  <fg-input type="number" label="Amount" v-model="amount" :errorMessage="validationErrors.amount" required />
  <p-button block @click.native="createDeposit({token, amount})" :disabled="!isValid">Deposit</p-button>
</card>
</template>
<script>
import {mapGetters, mapActions} from 'vuex'

export default {
  data() {
    return {
      validationErrors: {},
      amount: 0
    }
  },
  watch: {
    amount() {
      if (this.amount <= 0) {
        this.$set(this.validationErrors, 'amount', 'Deposit amount should be greater than zero')
      } else {
        this.$set(this.validationErrors, 'amount', null)
      }
    },
  },
  computed: {
    ...mapGetters('tokens', ['tokensByAddress']),
    ...mapGetters('funding', ['deposits']),
    cardTitle() {
      return this.token && `Deposit ${this.token.code}`
    },
    isValid() {
      return this.amount && this.amount > 0
    },
    token() {
      return this.tokensByAddress[this.$route.params.token]
    }
  },
  methods: {
    ...mapActions('funding', ['createDeposit']),
  }
}
</script>
