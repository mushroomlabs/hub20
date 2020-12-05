<template>
  <div>
    <span v-if="submitted">Transfer submitted successfully!</span>
    <form v-if="!submitted" name="transfer">
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
        :label="amountLabel"
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

      <fg-select
        type="text"
        label="Recipient"
        v-if="isInternalTransfer"
        v-model="recipientUsername"
        :options="recipientOptions"
        :errorMessage="validationErrors.recipientUsername"
      />

      <fg-input
        type="text"
        label="Payment Identifier (optional)"
        v-model="identifier"
        :errorMessage="validationErrors.identifier"
      />

      <fg-input
        type="text"
        label="Memo (optional)"
        v-model="memo"
        :errorMessage="validationErrors.memo"
      />

      <p-button block :disabled="!isValid" @click.native="submitTransfer()">
        Transfer
      </p-button>
    </form>
  </div>
</template>
<script>
import {ethers} from 'ethers'
import {mapGetters, mapActions} from 'vuex'

import AuthMixin from '@/mixins/auth'

export default {
  mixins: [AuthMixin],
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
      identifier: null,
      submitted: false
    }
  },
  watch: {
    address(value) {
      const isAddress = ethers.utils.isAddress(value)
      this.$set(
        this.validationErrors,
        'address',
        isAddress ? null : 'not a valid ethereum address'
      )
    },
    amount(value) {
      if (value <= 0) {
        this.$set(
          this.validationErrors,
          'amount',
          'Transfer amount should be greater than zero'
        )
      } else if (value > this.balance) {
        this.$set(
          this.validationErrors,
          'amount',
          'Transfer amount is greater than available balance'
        )
      } else {
        this.$set(this.validationErrors, 'amount', null)
      }
    },
    transferType(value) {
      if (value === 'internal' && !this.recipientUsername) {
        this.$set(
          this.validationErrors,
          'recipientUsername',
          'Please provide username of recipient'
        )
      }
      if (value === 'external' && !this.address) {
        this.$set(this.validationErrors, 'address', 'Please provide recipient ethereum address')
      }
    },
    recipientUsername(value) {
      if (!value) {
        this.$set(
          this.validationErrors,
          'recipientUsername',
          'Please provide username of recipient'
        )
      } else {
        this.$set(this.validationErrors, 'recipientUsername', null)
      }
    },
    identifier(value) {
      const isNumericOrEmpty = !isNaN(value) || value.trim() == ''
      this.$set(
        this.validationErrors,
        'identifier',
        isNumericOrEmpty ? null : 'Identifier must be numeric value'
      )
    }
  },
  computed: {
    ...mapGetters('account', ['tokenBalance']),
    ...mapGetters('users', ['usersByUsername']),
    transferData() {
      let payload = {
        token: this.token,
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
    amountLabel() {
      return `Amount (max. available: ${this.balance} ${this.token.code})`
    },
    balance() {
      return this.tokenBalance(this.token.address)
    },
    isInternalTransfer() {
      return this.transferType === 'internal'
    },
    isValid() {
      return [
        this.amount && this.amount > 0,
        this.transferType == 'internal' ? this.recipientUsername != null : this.address != null,
        !this.validationErrors.identifier,
        !this.validationErrors.memo
      ].every(pred => Boolean(pred))
    },
    recipients() {
      return Object.values(this.usersByUsername).filter(
        user => user.username != this.loggedUsername
      )
    },
    recipientOptions() {
      return this.recipients.map(user => ({value: user.username, text: user.username}))
    }
  },
  methods: {
    ...mapActions('funding', ['createTransfer']),
    setTransferType(transferType) {
      this.transferType = transferType
    },
    selectAmount(evt) {
      this.amount = evt.target.value
    },
    submitTransfer() {
      this.createTransfer(this.transferData).then(() => {
        this.$emit('transferFormSubmitted')
        this.submitted = true
      })
    }
  }
}
</script>
