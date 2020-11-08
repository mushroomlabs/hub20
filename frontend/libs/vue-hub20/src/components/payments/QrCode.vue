<template>
<canvas class='qr-code'></canvas>
</template>

<script>
import QRCode from 'qrcode'
import {toWei} from '../../filters'

export default {
  name: 'qr-code',
  data() {
    return {
      protocol: 'ethereum',
      address: '',
      token: null,
      amount: null
    }
  },
  methods: {
    async generate() {
      let text = `${this.protocol}:${this.address}`

      if (this.amount && this.token) {
        let weiAmount = toWei(this.amount, this.token)
        text.concat(`&value=${weiAmount}`)
      }
      return await QRCode.toCanvas(this.$el, text, {
        colorDark : '#000000',
        colorLight : '#ffffff',
        errorCorrectionLevel : 'H'
      })
    }
  },
  mounted() {
    this.generate()
  }
}
</script>
