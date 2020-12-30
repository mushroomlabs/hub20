<template>
  <tr>
    <td><etherscan-link :address="address" :networkId="ethereumNetworkId" /></td>
    <td v-for="token in tokensByAddress" :key="token.address">
      <accounting-token-balance-display :tokenBalance="walletBalance(address, token)" />
    </td>
  </tr>
</template>
<script>
import {mapGetters} from 'vuex'
import {mixins, components} from 'vue-hub20'

import AccountingTokenBalanceDisplay from './AccountingTokenBalanceDisplay'

export default {
  name: 'AccountingWalletBalances',
  mixins: [mixins.TokenMixin],
  components: {
    AccountingTokenBalanceDisplay,
    EtherscanLink: components.EtherscanLink
  },
  props: {
    address: String
  },
  computed: {
    ...mapGetters('audit', ['walletBalance']),
    ...mapGetters('network', ['ethereumNetworkId'])
  }
}
</script>
