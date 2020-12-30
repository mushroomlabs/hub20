<template>
  <table class="table">
    <thead>
      <th>Token</th>
      <th>Treasury</th>
      <th>Wallet</th>
      <th>Raiden</th>
      <th>Total Assets</th>
      <th>User Accounts (Liabilities)</th>
    </thead>
    <tbody>
      <tr v-for="(token, address) in tokensByAddress" :key="address">
        <td>{{ token.code }}</td>
        <td>
          <accounting-token-balance-display :token-balance="treasuryTokenBalance(token)" />
        </td>
        <td>
          <accounting-token-balance-display :token-balance="walletTokenBalance(token)" />
        </td>
        <td>
          <accounting-token-balance-display :token-balance="raidenTokenBalance(token)" />
        </td>
        <td>
          <accounting-token-balance-display :token-balance="totalTokenAssets(token)" />
        </td>
        <td>
          <accounting-token-balance-display :token-balance="userTokenBalance(token)" />
        </td>
      </tr>
    </tbody>
  </table>
</template>
<script>
import {mapGetters} from 'vuex'
import {mixins} from 'vue-hub20'

import AccountingTokenBalanceDisplay from './AccountingTokenBalanceDisplay'

export default {
  name: 'AccountingReportTable',
  mixins: [mixins.TokenMixin],
  components: {
    AccountingTokenBalanceDisplay
  },
  computed: {
    ...mapGetters('audit', [
      'treasuryTokenBalance',
      'userTokenBalance',
      'walletTokenBalance',
      'raidenTokenBalance',
      'totalTokenAssets'
    ])
  }
}
</script>
