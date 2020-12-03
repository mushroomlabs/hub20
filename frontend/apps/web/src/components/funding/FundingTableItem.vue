<template>
  <tr>
    <td class="name" :title="token.address">{{ token.name }} ({{ token.code }})</td>
    <td class="balance">{{ balance }}</td>
    <td class="identifier">{{ token.id }}</td>
    <td class="actions">
      <button @click="openDepositModal()" :disabled="!ethereumNodeOk">Receive</button>
      <button @click="openTransferModal()" :disabled="!ethereumNodeOk || !hasFunds">Send</button>
    </td>
    <DepositModal v-if="currentDeposit" :deposit="currentDeposit" @modalClosed="onDepositClosed()"/>
    <TransferModal :token="token" :hidden="!hasOpenTransfer" @modalClosed="onTransferClosed()"/>
  </tr>
</template>
<script>
import {mapActions, mapGetters} from 'vuex'

import DepositModal from './DepositModal'
import TransferModal from './TransferModal'

export default {
  components: {
    DepositModal,
    TransferModal
  },
  props: {
    token: {
      type: Object
    }
  },
  data() {
    return {
      currentDeposit: null,
      hasOpenTransfer: false,
    }
  },
  computed: {
    ...mapGetters('account', ['tokenBalance']),
    ...mapGetters('server', ['ethereumNodeOk']),
    ...mapGetters('funding', ['openDepositsByToken']),
    balance() {
      return this.tokenBalance(this.token.address)
    },
    hasFunds() {
      return this.balance.gt(0)
    },
    hasOpenDeposits() {
      return this.openDeposits.length > 0
    },
    openDeposits() {
      return this.openDepositsByToken(this.token)
    },
  },
  methods: {
    ...mapActions('funding', ['createDeposit']),
    openDepositModal() {
      if (!this.hasOpenDeposits) {
        this.createDeposit(this.token).then(depositData => {
          this.currentDeposit = depositData
        })
      }
      else {
        this.currentDeposit = this.openDeposits[0]
      }
    },
    openTransferModal() {
      this.hasOpenTransfer = true;
    },
    onDepositClosed() {
      this.currentDeposit = null
    },
    onTransferClosed() {
      this.hasOpenTransfer = false
    },
  }
}
</script>
