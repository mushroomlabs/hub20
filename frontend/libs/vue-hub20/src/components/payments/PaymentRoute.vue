<template>
  <div class="payment-route" :class="{'selected': selected}">
    <PaymentRouteBlockchainTimer
      v-if="isBlockchainRoute"
      :created_on="route.start_block"
      :expires_on="route.expiration_block"
    />
    <QrCode :message="QrCodeMessage" />
    <div class="payment-route-details">
      <ClipboardCopier :value="route.address">Address: {{ route.address }}</ClipboardCopier>
      <ClipboardCopier v-if="isRaidenRoute" :value="route.identifier">Payment Identifier: {{ route.identifier }}</ClipboardCopier>
    </div>
    <Web3TransferButton v-if="isBlockchainRoute" :token="token" :amount="amount" :recipientAddress="route.address" />
  </div>
</template>

<script>
import {toWei} from '../../filters'

import ClipboardCopier from '../ClipboardCopier'
import Web3TransferButton from '../web3/Web3TransferButton'

import QrCode from './QrCode'
import PaymentRouteBlockchainTimer from './PaymentRouteBlockchainTimer'


export default {
  components: {
    ClipboardCopier,
    PaymentRouteBlockchainTimer,
    QrCode,
    Web3TransferButton
  },
  props: {
    route: {
      type: Object
    },
    token: {
      type: Object,
      required: false
    },
    amount: {
      type: Number,
      required: false
    },
    selected: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    QrCodeMessage() {
      let protocol = {
        blockchain: "ethereum",
        raiden: "ethereum"
      }[this.route.type]

      let text = `${protocol}:${this.route.address}`

      if (this.amount && this.token) {
        let weiAmount = toWei(this.amount, this.token)
        text.concat(`&value=${weiAmount}`)
      }
      return text
    },
    isBlockchainRoute() {
      return this.route.type == 'blockchain'
    },
    isRaidenRoute() {
      return this.route.type == 'raiden'
    }
  }
}
</script>
