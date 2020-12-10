<template>
<div id="stores">
  <section class="header">
    <h2>Store Settings</h2>
    <router-link :to="{'name': 'store-create'}">Add New</router-link>
  </section>
  <card>
    <store-table />
  </card>
</div>
</template>
<script>
import StoreTable from '@/components/StoreTable'

export default {
  components: {
    StoreTable,
  }
}
</script>
