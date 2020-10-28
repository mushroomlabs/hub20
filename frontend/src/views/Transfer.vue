<template>
  <card :title="cardTitle">
    <p>Available: {{ balance }} {{ token.code }}</p>

    <div class="button-bar">
      <button
        type="button"
        v-for="step in steps"
        :value="balance * step"
        :class="{'active': (balance * step) == amount}"
        @click="selectAmount($event)"
        :key="step">
        {{ 100 * step }}%
      </button>
    </div>

    <fg-input
      type="number"
      label="Amount"
      v-model="amount"
      :errorMessage="validationErrors.amount"
      required
      />

    <fg-input
      type="text"
      label="Address"
      v-model="address"
      :errorMessage="validationErrors.address"
      required
      />

    <p-button
      block
      @click.native="createTransfer({token, amount, address})"
      :disabled="!isValid">
      Transfer
    </p-button>
  </card>
</template>
<script>
import {mapGetters, mapActions} from 'vuex'

export default {
  props: {
    steps: {
      type: Array,
      default: () => [0.25, 0.5, 0.75, 1]
    }
  },
  data() {
    return {
      validationErrors: {},
      amount: 0,
      address: null
    }
  },
  watch: {
    amount() {
      if (this.amount <= 0) {
        this.$set(
          this.validationErrors,
          'amount',
          'Transfer amount should be greater than zero'
        )
      } else {
        this.$set(this.validationErrors, 'amount', null)
      }
    }
  },
  computed: {
    ...mapGetters('account', ['tokenBalance']),
    ...mapGetters('funding', ['transfers']),
    ...mapGetters('tokens', ['tokensByAddress']),
    cardTitle() {
      return this.token && `Transfer ${this.token.code}`
    },
    isValid() {
      return this.amount && this.amount > 0
    },
    token() {
      return this.tokensByAddress[this.$route.params.token]
    },
    balance() {
      return this.token && this.tokenBalance(this.token.address)
    }
  },
  methods: {
    ...mapActions('funding', ['createTransfer']),
    selectAmount(evt) {
      this.amount = evt.target.value
    }
  }
}
</script>
