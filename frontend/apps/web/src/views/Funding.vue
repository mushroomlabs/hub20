<template>
<div>
  <card title="Current Tokens" subTitle="Tokens listed and managed by your account">
    <div v-if="!ethereumNodeOk" class="alert alert-warning">
      Server reported that can not connect with Ethereum network at the moment, so all funding
      operations are disabled.
    </div>

    <FundingTable />
  </card>

</div>
</template>
<script>
import {mapGetters} from 'vuex'

import FundingTable from '@/components/funding/FundingTable'
export default {
  components: {
    FundingTable,
  },
  computed: {
    ...mapGetters('network', ['ethereumNodeOk']),
  },
}
</script>
