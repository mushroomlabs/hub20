<template>
<div id="store-detail" v-if="store">

  <fg-input label="Name" placeholder="Store Name" v-model="store.name" required/>
  <fg-input label="URL" placeholder="Store URL" v-model="store.url" required/>

</div>
</template>
<script>
import {mapState} from "vuex"

export default {
  computed: {
    ...mapState("stores", {stores: "stores"}),
    store() {
      return this.stores[this.$route.params.id];
    }
  }
}
</script>
