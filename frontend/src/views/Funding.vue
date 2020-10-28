<template>
<card title="Current Tokens" subTitle="Tokens listed and managed by your account">
  <FundingTable />
</card>
</template>
<script>
import FundingTable from "@/components/funding/FundingTable"

export default {
  name: "funding",
  components: {
    FundingTable
  }
}
</script>
