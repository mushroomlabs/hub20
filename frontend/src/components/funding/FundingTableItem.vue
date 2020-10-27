<template>
  <tr>
    <td class="name" :title="token.address">{{ token.name }} ({{ token.code }})</td>
    <td class="balance">{{ balance }}</td>
    <td class="identifier">{{ token.id }}</td>
    <td class="actions">
      <router-link :to="{'name': 'deposit', params: {'token': token.address} }">Deposit</router-link>
      <router-link :to="{'name': 'withdraw', params: {'token': token.address} }" :disabled="!hasFunds">Withdraw</router-link>
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
  methods: {
    startWithdraw() {
      console.log(this.token.code, 'withdraw')
    },
    startDeposit() {
      console.log(this.token.code, 'deposit')
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
