<template>
<card class="setup-screen" title="Welcome to Hub20 - Setup">
  <slot>
    <form @submit.prevent="setupServer(serverUrl)">
      <fg-input v-model="serverUrl"
                id="url"
                placeholder="Hub20 Instance URL"
                :errorMessage="serverError"
                :disabled="processing"
                required
                />
    </form>
  </slot>
  <slot name="footer">
    <action-panel>
      <template v-slot:secondary>
        <span v-if="isConnected">Currently connected to: {{ current }} (v.{{ version }})</span>
      </template>
      <p-button type="submit" @click.native="setupServer(serverUrl)" :disabled="processing">Next</p-button>
    </action-panel>
  </slot>
</card>
</template>

<script>
import {mapActions, mapGetters, mapState} from 'vuex'

export default {
  name: "setup",
  data(){
    return {
      serverUrl: null,
    }
  },
  computed: {
    ...mapGetters('server', ['isConnected']),
    ...mapState('server', {current: 'rootUrl', version: 'version', serverError: 'error', processing: 'processing'})
  },
  methods: {
    ...mapActions('server', ['setUrl']),
    setupServer(url) {
      this.setUrl(url).then(() => this.$router.push({name: 'login'}))
    }
  },
  mounted() {
    this.serverUrl = this.current;
  }
}
</script>
