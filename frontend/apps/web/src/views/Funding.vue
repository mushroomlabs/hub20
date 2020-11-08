<template>
  <div>
    <card title="Current Tokens" subTitle="Tokens listed and managed by your account">
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
    ...mapState('funding', {deposit: state => state.currentDeposit}),
  },
  methods: {
    ...mapMutations('funding', {openModal: 'FUNDING_DEPOSIT_SET_OPEN'}),
    onDepositRequested() {
      if (this.deposit) {
        this.openModal(this.deposit.id)
      }
    }
  },
  mounted() {
    let depositId = "de869a07-9425-47c3-aa56-60b765336578"
    this.$store.dispatch("funding/fetchDeposit", depositId)
      .then(() => this.openModal(depositId))
  }
}
</script>
