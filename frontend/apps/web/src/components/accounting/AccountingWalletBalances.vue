<template>
  <table class="table">
    <thead>
      <th>Account Address</th>
      <th v-for="(token, address) in tokensByAddress" :key="address" :title="address">
        {{ token.code }}
      </th>
    </thead>
    <tbody>
      <AccountingWalletBalancesTableItem
        v-for="walletAddress in walletAddresses"
        :key="walletAddress"
        :address="walletAddress"
      />
    </tbody>
  </table>
</template>
<script>
import {mapGetters} from 'vuex'
import {mixins} from 'vue-hub20'

import AccountingWalletBalancesTableItem from './AccountingWalletBalancesTableItem'


export default {
  name: 'AccountingWalletBalances',
  components: {
    AccountingWalletBalancesTableItem,
  },
  mixins: [mixins.TokenMixin],
  computed: {
    ...mapGetters('audit', ['walletAddresses'])
  }
}
</script>
