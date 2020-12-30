<template>
  <div id="overview">
    <ul v-if="!hasAdminAccess" class="token-balances">
      <li v-for="balance in openBalances" :key="balance.address">
        <token-balance-card :tokenBalance="balance" />
      </li>
    </ul>

    <card v-if="hasAdminAccess" title="Accounting Books (Summary)">
      <accounting-report-table/>
    </card>

    <card v-if="hasAdminAccess" title="Ethereum Account Balances">
      <accounting-wallet-balances/>
    </card>

  </div>
</template>
<script>
import {mapGetters} from 'vuex'

import TokenBalanceCard from '@/components/TokenBalanceCard'
import AccountingReportTable from '@/components/accounting/AccountingReportTable.vue'
import AccountingWalletBalances from '@/components/accounting/AccountingWalletBalances.vue'

export default {
  name: 'overview',
  components: {
    TokenBalanceCard,
    AccountingReportTable,
    AccountingWalletBalances
  },
  computed: {
    ...mapGetters('account', ['openBalances', 'hasAdminAccess']),
  }
}
</script>
