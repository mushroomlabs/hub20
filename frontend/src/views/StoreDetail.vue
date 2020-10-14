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
    ...mapState("stores", {store: "editing", stores: "stores"}),
  },
  mounted() {
    let storeId = this.$route.params.id
    this.$store.commit("stores/STORE_UPDATE_BEGIN", storeId)
  }
}
</script>
