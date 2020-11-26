<template>
  <div>
    <card title="Current Tokens" subTitle="Tokens listed and managed by your account">
      <div v-if="!ethereumNodeOk" class="alert alert-warning">
        Server reported that can not connect with Ethereum network at the moment, so all funding
        operations are disabled.
      </div>

      <FundingTable v-on:depositRequested="onDepositRequested" />
    </card>
    <DepositModal v-if="deposit" :deposit="deposit" />
  </div>
</template>
<script>
import {mapGetters, mapState, mapMutations} from 'vuex'

import FundingTable from '@/components/funding/FundingTable'
import DepositModal from '@/components/funding/DepositModal'

export default {
  components: {
    FundingTable,
    DepositModal
  },
  computed: {
    ...mapGetters('funding', ['depositsByToken']),
    ...mapGetters('server', ['ethereumNodeOk']),
    ...mapState('funding', {deposit: state => state.currentDeposit})
  },
  methods: {
    ...mapMutations('funding', {openModal: 'FUNDING_DEPOSIT_SET_OPEN'}),
    onDepositRequested() {
      if (this.deposit) {
        this.openModal(this.deposit.id)
      }
    }
  }
}
</script>
