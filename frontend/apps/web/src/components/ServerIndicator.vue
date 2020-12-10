<template>
  <div class="server-indicator">
    <span><slot>Connected to:</slot></span>
    <span v-if="isConnected" class="server-url" :title="rootUrl">{{ url }}</span>
    <router-link v-if="isConnected" to="setup">Change?</router-link>
    <span v-if="!isConnected">Hub20 Server not defined</span>
  </div>
</template>
<script>
import {mapGetters, mapState} from 'vuex'

export default {
  name: "server-indicator",
  computed: {
    ...mapGetters('server', ['isConnected']),
    ...mapState('server', ['rootUrl']),
    url() {
      return new URL(this.rootUrl).host
    }
  }
}
</script>
