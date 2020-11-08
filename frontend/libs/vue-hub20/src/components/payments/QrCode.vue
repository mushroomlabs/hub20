<template>
  <canvas class="qr-code"></canvas>
</template>

<script>
import QRCode from 'qrcode'

export default {
  name: 'qr-code',
  props: {
    message: String
  },
  methods: {
    async generate() {
      return await QRCode.toCanvas(this.$el, this.message, {
        colorDark: '#000000',
        colorLight: '#ffffff',
        errorCorrectionLevel: 'H'
      })
    }
  },
  mounted() {
    this.generate()
  }
}
</script>
