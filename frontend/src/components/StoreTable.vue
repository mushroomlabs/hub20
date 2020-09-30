<template>
<table id="merchant-store-data" class="table">
  <thead>
    <th class="name">Name</th>
    <th class="url">Site URL</th>
    <th class="tokens">Accepted Tokens</th>
    <th class="identifier">Store Identifier</th>
    <th class="public-key">Public Key</th>
  </thead>
  <tbody>
    <StoreTableItem v-for="store in storesById" :store="store" :key="store.id" />
  </tbody>
</table>
</template>
<script>
import {mapGetters} from "vuex";
import StoreTableItem from "@/components/StoreTableItem";

export default {
  components: {
    StoreTableItem
  },
  computed: {
    ...mapGetters("stores", ["storesById"]),
  },
}
</script>

<style lang="scss">
@import "../assets/sass/paper/_variables";
@import "../assets/sass/paper/mixins/_buttons";

table#merchant-store-data {
    display: fixed;

    th {
        max-width: 20%;
        align-content: center;
        text-align: center;

        &.public-key {
            min-width: 40%;
        }
    }
}
</style>
