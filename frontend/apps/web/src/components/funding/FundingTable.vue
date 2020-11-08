<template>
<table id="funding-data" class="table">
  <thead>
    <th class="name">Token</th>
    <th class="balance">Current Balance</th>
    <th class="actions"></th>
  </thead>
  <tbody>
    <FundingTableItem v-for="(token, address) in tokensByAddress" :token="token" :key="address" v-on="$listeners"/>
  </tbody>
</table>
</template>
<script>
import {mapGetters} from "vuex";
import FundingTableItem from "@/components/funding/FundingTableItem";

export default {
  components: {
    FundingTableItem
  },
  computed: {
    ...mapGetters("tokens", ["tokensByAddress"]),
  },
}
</script>
