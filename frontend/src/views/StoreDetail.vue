<template>
<div id="store-detail" v-if="store">

  <fg-input label="Name" placeholder="Store Name" v-model="name" required/>
  <fg-input label="URL" placeholder="Store URL" v-model="siteUrl" required/>
  <fg-select label="Accepted Tokens" v-model="acceptedTokens" :options="tokenOptions" multiple />
</div>
</template>
<script>
import {mapState, mapGetters, mapMutations, mapActions} from "vuex"

export default {
  computed: {
    ...mapState("stores", {store: "editing", stores: "stores"}),
    ...mapGetters("tokens", {tokenMap: "tokensByAddress"}),
    tokenOptions() {
      return Object.values(this.tokenMap).map((token) => {
        return {
          value: token.address,
          text: token.code
        }})
    },
    name: {
      get() {
        return this.store && this.store.name
      },
      set(value) {
        return this.updateName(value)
      }
    },
    acceptedTokens: {
      get() {
        return this.store && this.store.accepted_currencies
      },
      set(value) {
        this.$store.commit("stores/STORE_SET_ACCEPTED_TOKENS", value)
      }
    },
    siteUrl: {
      get() {
        return this.store && this.store.site_url
      },
      set(value) {
        return this.updateSiteUrl(value)
      }
    }
  },
  methods: {
    ...mapMutations("stores", {
      updateName: "STORE_SET_NAME",
      updateSiteUrl: "STORE_SET_URL",
      updateAcceptedTokens: "STORE_SET_ACCEPTED_TOKENS"
    }),
    ...mapActions("stores", ["editStore"])
  },
  mounted() {
    this.editStore(this.$route.params.id)
  }
}
</script>
