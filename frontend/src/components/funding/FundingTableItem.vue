<template>
  <tr>
    <td class="name" :title="token.address">{{ token.name }} ({{ token.code }})</td>
    <td class="balance">{{ balance }}</td>
    <td class="identifier">{{ token.id }}</td>
    <td class="actions">
      <p-button name="deposit" @click.native="startDeposit()">Deposit</p-button>
      <p-button name="withdrawal" @click.native="startWithdraw()">Withdraw</p-button>
    </td>
  </tr>
</template>
<script>
import {mapGetters} from 'vuex'
import TokenMixin from '@/mixins/tokens'

export default {
  mixins: [TokenMixin],
  props: {
    token: {
      type: Object
    }
  },
  methods: {
    startWithdraw() {
      console.log(this.token.code)
    },
    startDeposit() {
      console.log(this.token.code, 'deposit')
    }
  },
  computed: {
    ...mapGetters('account', ['tokenBalance']),
    balance() {
      return this.tokenBalance(this.token.address)
    }
  }
}
</script>
