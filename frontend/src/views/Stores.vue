<template>
<div id="stores">
  <card title="Merchant store Setup">
    <store-table/>
  </card>
</div>
</template>
<script>
import StoreTable from "@/components/StoreTable";

export default {
  components: {
    StoreTable
  }
}
</script>
