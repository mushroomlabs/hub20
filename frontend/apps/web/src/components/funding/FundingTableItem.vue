<template>
  <tr>
    <td class="name" :title="token.address">{{ token.name }} ({{ token.code }})</td>
    <td class="price">{{ exchangeRate(token) | formattedCurrency(baseCurrency) }}</td>
    <td class="balance">{{ balance }}</td>
    <td class="actions">
      <button @click="openDepositModal()" :disabled="!ethereumNodeOk">Receive</button>
      <button @click="openTransferModal()" :disabled="!ethereumNodeOk || !hasFunds">
        Send
      </button>
    </td>
    <Modal
      label="funding-modal"
      :title="modalTitle"
      :id="modalId"
      :hidden="!isModalOpen"
      @modalClosed="onModalClosed()"
    >
      <DepositTracker :token="token" v-if="hasOpenDeposit" />
      <TransferForm :token="token" v-if="hasOpenTransfer" @transferFormSubmitted="onTransferSubmitted()" />
    </Modal>
  </tr>
</template>
<script>
import {mapActions, mapGetters, mapState} from 'vuex'
import {filters as hub20filters} from 'vue-hub20'

import Modal from '@/widgets/dialogs/Modal'

import DepositTracker from './DepositTracker'
import TransferForm from './TransferForm'

export default {
  components: {
    Modal,
    DepositTracker,
    TransferForm
  },
  filters: {
    formattedCurrency: hub20filters.formattedCurrency
  },
  props: {
    token: {
      type: Object
    }
  },
  data() {
    return {
      hasOpenDeposit: false,
      hasOpenTransfer: false
    }
  },
  computed: {
    ...mapGetters('account', ['tokenBalance']),
    ...mapGetters('server', ['ethereumNodeOk']),
    ...mapGetters('coingecko', ['exchangeRate']),
    ...mapState('coingecko', ['baseCurrency']),
    balance() {
      return this.tokenBalance(this.token.address)
    },
    hasFunds() {
      return this.balance.gt(0)
    },
    modalTitle() {
      const action = this.hasOpenDeposit ? 'Deposit' : 'Transfer'
      return `${action} ${this.token.code}`
    },
    modalId() {
      return `modal-funding-${this.token.address}`
    },
    isModalOpen() {
      return this.hasOpenDeposit || this.hasOpenTransfer
    }
  },
  methods: {
    ...mapActions('coingecko', ['fetchRate']),
    openDepositModal() {
      this.hasOpenDeposit = true
    },
    openTransferModal() {
      this.hasOpenTransfer = true
    },
    onModalClosed() {
      this.hasOpenDeposit = false
      this.hasOpenTransfer = false
    },
    onTransferSubmitted() {
      this.hasOpenTransfer = false
    }
  },
  mounted() {
    this.fetchRate(this.token)
  }
}
</script>
