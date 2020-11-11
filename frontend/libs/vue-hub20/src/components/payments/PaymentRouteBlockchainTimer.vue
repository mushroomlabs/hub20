<template>
  <div class="blockchain-timer" :class="{synced, online, expired}">
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
    ...mapGetters('server', {
      synced: 'ethereumSynced',
      online: 'ethereumOnline',
      currentBlock: 'currentBlock',
    }),
    expired() {
      return this.currentBlock > this.expires_on
    },
  }
}
</script>
