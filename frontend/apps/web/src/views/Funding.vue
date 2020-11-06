<template>
  <div>
    <card title="Current Tokens" subTitle="Tokens listed and managed by your account">
      <FundingTable />
    </card>
    <DepositModal v-if="openDeposit" :deposit="openDeposit" />
  </div>
</template>
<script>
import {mapGetters} from 'vuex'
import FundingTable from '@/components/funding/FundingTable'
import DepositModal from '@/components/funding/DepositModal'

export default {
  name: 'funding',
  components: {
    FundingTable,
    DepositModal
  },
  computed: {
    ...mapGetters('funding', ['openDeposits', 'deposits']),
    openDeposit() {
      return this.openDeposits.length > 0 ? this.openDeposits[0] : null
    }
  }
}
</script>
