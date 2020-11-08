<template>
  <tr>
    <td class="name" :title="token.address">{{ token.name }} ({{ token.code }})</td>
    <td class="balance">{{ balance }}</td>
    <td class="identifier">{{ token.id }}</td>
    <td class="actions">
      <button @click="requestDeposit(token)">Deposit</button>
      <router-link :to="{name: 'withdraw', params: {token: token.address}}" :disabled="!hasFunds"
        >Send</router-link
      >
    </td>
  </tr>
</template>
<script>
import {mapActions, mapGetters} from 'vuex'

export default {
  props: {
    token: {
      type: Object
    }
  },
  computed: {
    ...mapGetters('account', ['tokenBalance']),
    balance() {
      return this.tokenBalance(this.token.address)
    },
    hasFunds() {
      return this.balance.gt(0)
    }
  },
  methods: {
    ...mapActions('funding', ['createDeposit']),
    requestDeposit(token) {
      this.createDeposit(token)
        .then(() => this.$emit('depositRequested', token))
    }
  }
}
</script>
