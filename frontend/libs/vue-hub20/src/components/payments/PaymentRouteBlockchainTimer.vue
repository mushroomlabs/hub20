<template>
  <div class="blockchain-timer" :class="{synced, online, expired}" :title="title">
    <span class="start-value">{{ created_on }}</span>
    <span class="current-value">{{ currentBlock }}</span>
    <span class="expiration-value">{{ expires_on }}</span>
  </div>
</template>

<script>
import {mapGetters} from 'vuex'

export default {
  props: {
    created_on: {
      type: Number
    },
    expires_on: {
      type: Number
    }
  },
  computed: {
    ...mapGetters('network', {
      synced: 'ethereumSynced',
      online: 'ethereumOnline',
      currentBlock: 'currentBlock',
    }),
    expired() {
      return this.currentBlock > this.expires_on
    },
    blocksRemaining() {
      return this.currentBlock ? this.expires_on - this.currentBlock : null
    },
    progress() {
      return this.currentBlock ? this.currentBlock - this.created_on : null
    },
    title() {
      if (this.expired) {
        return `This route has expired on block ${this.expires_on}. DO NOT send any transfers`
      }

      if (!this.online) {
        return `Server lost connection with ethereum network. Please wait until it is restored`
      }

      if (!this.synced) {
        return `Server is out of sync with ethererum network. Payments might not be displayed here.`
      }

      return `Payments will be accepted for transactions in the next ${this.blocksRemaining} blocks`
    }
  }
}
</script>
