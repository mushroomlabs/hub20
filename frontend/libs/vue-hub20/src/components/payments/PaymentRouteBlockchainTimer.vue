<template>
  <div class="blockchain-timer" :class="{synced, online}">
    <span class="start-value">{{ created_on }}</span>
    <span class="current-value">{{ current }}</span>
    <span class="expiration-value">{{ expires_on }}</span>
  </div>
</template>

<script>
export default {
  props: {
    created_on: {
      type: Number
    },
    expires_on: {
      type: Number
    }
  },
  data() {
    return {
      current: this.$props.created_on,
      synced: false,
      online: false
    }
  }
}
</script>
