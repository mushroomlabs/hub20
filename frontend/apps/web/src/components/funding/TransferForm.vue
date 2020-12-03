<template>
  <form @submit.prevent="createTransfer(transferData)">
    <p>Available: {{ balance }} {{ token.code }}</p>

    <div class="button-bar">
      <button
        type="button"
        :class="{active: isInternalTransfer}"
        @click="setTransferType('internal')"
      >
        Internal
      </button>
      <button
        type="button"
        :class="{active: !isInternalTransfer}"
        @click="setTransferType('external')"
      >
        External
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
      v-if="!isInternalTransfer"
      v-model="address"
      :errorMessage="validationErrors.address"
    />

    <fg-input
      type="text"
      label="Recipient"
      v-if="isInternalTransfer"
      v-model="recipientUsername"
      :errorMessage="validationErrors.recipientUsername"
    />

    <fg-input
      type="text"
      label="Payment Identifier (optional)"
      v-model="identifier"
      :errorMessage="validationErrors.identifier"
    />

    <fg-input type="text" label="Memo" v-model="memo" :errorMessage="validationErrors.memo" />

    <p-button block :disabled="!isValid">
      Transfer
    </p-button>
  </form>
</template>
<script>
import {mapGetters, mapActions} from 'vuex'

export default {
  props: {
    token: Object
  },
  data() {
    return {
      validationErrors: {},
      transferType: 'external',
      amount: 0,
      address: null,
      recipientUsername: null,
      memo: null,
      identifier: null
    }
  },
  watch: {
    amount(value) {
      if (value <= 0) {
        this.$set(
          this.validationErrors,
          'amount',
          'Transfer amount should be greater than zero'
        )
      } else {
        this.$set(this.validationErrors, 'amount', null)
      }
    },
    transferType(value) {
      if (value === 'internal' && !this.recipientUsername) {
        this.$set(
          this.validationErrors,
          'recipientUsername', 'Please provide the username of the recipient'
        )
      }
      if (value === 'external' && !this.address) {
        this.$set(
          this.validationErrors,
          'address', 'Please provide recipient ethereum address'
        )
      }
    }
  },
  computed: {
    ...mapGetters('account', ['tokenBalance']),
    transferData() {
      let payload = {
        token: this.token.address,
        amount: this.amount,
        memo: this.memo,
        identifier: this.identifier
      }

      if (this.transferType == 'internal') {
        payload.recipient = this.recipientUsername
      } else {
        payload.address = this.address
      }
      return payload
    },
    isValid() {
      return [
        this.amount && this.amount > 0,
        this.transferType == 'internal' ? this.recipient != null : this.address != null
      ].every(pred => Boolean(pred))
    },
    balance() {
      return this.tokenBalance(this.token.address)
    },
    isInternalTransfer() {
      return this.transferType === 'internal'
    }
  },
  methods: {
    ...mapActions('funding', ['createTransfer']),
    setTransferType(transferType) {
      this.transferType = transferType
    },
    selectAmount(evt) {
      this.amount = evt.target.value
    }
  }
}
</script>
