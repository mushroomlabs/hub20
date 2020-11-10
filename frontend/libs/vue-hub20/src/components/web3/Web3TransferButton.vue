<template>
  <button v-if="hasWeb3Provider" class="web3-transfer" @click="startTransfer()">
    <slot>Pay {{ amount }} {{ token.code }} with wallet</slot>
  </button>
</template>

<script>
import {mapGetters, mapActions} from 'vuex'

export default {
  props: {
    token: {
      type: Object,
      required: true
    },
    amount: {
      type: Number,
      required: false
    },
    recipientAddress: {
      type: String,
      required: true
    }
  },
  computed: {...mapGetters('web3', ['hasWeb3Provider', 'isConnected'])},
  methods: {
    ...mapActions('web3', ['enableWeb3', 'requestTransfer']),
    async startTransfer() {
      if (!this.isConnected) {
        await this.enableWeb3()
      }

      this.requestTransfer({
        token: this.token,
        amount: this.amount,
        recipientAddress: this.recipientAddress
      })
    }
  }
}
</script>
