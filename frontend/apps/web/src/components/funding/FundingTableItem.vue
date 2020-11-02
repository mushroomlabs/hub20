<template>
  <tr>
    <td class="name" :title="token.address">{{ token.name }} ({{ token.code }})</td>
    <td class="balance">{{ balance }}</td>
    <td class="identifier">{{ token.id }}</td>
    <td class="actions">
      <router-link :to="{'name': 'deposit', params: {'token': token.address} }">Deposit</router-link>
      <router-link :to="{'name': 'send', params: {'token': token.address} }" :disabled="!hasFunds">Send</router-link>
    </td>
  </tr>
</template>
<script>
import {mapGetters} from 'vuex'

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
  }
}
</script>
