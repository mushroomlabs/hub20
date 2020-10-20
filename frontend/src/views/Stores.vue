<template>
  <div id="stores">
    <section class="header">
      <h1>Store Settings</h1>
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
<style lang="scss">
@import '../assets/sass/app.scss';

#stores {
  a {
    @include button($info-color, $info-states-color);
  }
}
</style>
