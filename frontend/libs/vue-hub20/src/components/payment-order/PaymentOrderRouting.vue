<template>
  <ul v-if='paymentRouting' class='payment-order-routing'>
    <li class='payment-method ethereum'>
      <span class='payment-method'>Ethereum Transfer</span>
      <canvas class='qr-code'></canvas>
      <dl class='payment-instructions'>
          <dt>Address</dt>
          <dd><span class='ethereum transfer address'>{{ paymentRouting.blockchain.address }}</span></dd>
          <dt>Amount to Pay</dt>
          <dd>
            <TokenAmountDisplay
              class='ethereum transfer amount'
              :valueToCopy='tokenAmountDue'
              :token='selectedToken'
              :amount='tokenAmountDue'
              />
          </dd>
      </dl>
      <PaymentOrderWeb3Connector v-if='isWeb3BrowserAvailable' />
    </li>
    <li v-if='paymentRouting.raiden' class='payment-method raiden'>
      <span class='payment-method'>Raiden</span>
      <dl class='payment-instructions'>
        <dt>Address</dt>
        <dd><span class='ethereum transfer address'>{{ paymentRouting.raiden.address }}</span></dd>
        <dt>Amount</dt>
        <dd>
          <TokenAmountDisplay
            class='raiden transfer amount'
            :token='selectedToken'
            :amount='tokenAmountDue'
            :valueToCopy='tokenAmountDue'
            />
        </dd>
        <dt>Payment Identifier</dt>
        <dd><span class='raiden transfer identifier'>{{ paymentRouting.raiden.identifier }}</span></dd>
      </dl>
    </li>
  </ul>
</template>

<script>
import QRCode from 'qrcode'
import {mapState, mapGetters} from 'vuex'

import TokenAmountDisplay from './TokenAmountDisplay.vue'
import PaymentOrderWeb3Connector from './PaymentOrderWeb3Connector.vue'

async function generateQRCode(display_element, address) {
    let text = `ethereum:${address}`
    return await QRCode.toCanvas(display_element, text, {
        colorDark : '#000000',
        colorLight : '#ffffff',
        errorCorrectionLevel : 'H'
    })
}

export default {
    name: 'PaymentOrderRouting',
    components: {
        PaymentOrderWeb3Connector, TokenAmountDisplay
    },
    computed:{
        isWeb3BrowserAvailable: function() {
            return Boolean(window && (window.ethereum || window.web3))
        },
        ...mapGetters(['paymentRouting', 'paymentOrder', 'selectedToken', 'tokenAmountDue']),
        ...mapState(['store']),
        blockchainTransferAddress: function() {
            return this.paymentRouting && this.paymentRouting.blockchain && this.paymentRouting.blockchain.address
        }
    },
    async mounted() {
        let canvas = this.$el.querySelector('li.payment-method.ethereum canvas')
        if (this.blockchainTransferAddress) {
            await generateQRCode(canvas, this.blockchainTransferAddress)
        }
    }
}
</script>
