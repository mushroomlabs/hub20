<template>
  <tr>
    <td class="name" :title="token.address">{{ token.name }} ({{ token.code }})</td>
    <td class="balance">{{ balance }}</td>
    <td class="identifier">{{ token.id }}</td>
    <td class="actions">
      <button @click="createDeposit(token)">Deposit</button>
      <router-link :to="{name: 'send', params: {token: token.address}}" :disabled="!hasFunds"
        >Send</router-link
      >
    </td>
  </tr>
</template>
<script>
import {mapGetters, mapActions} from 'vuex'

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
  methods: {...mapActions('funding', ['createDeposit'])}
}
</script>
