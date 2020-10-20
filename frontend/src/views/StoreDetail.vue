<template>
<div id="store-detail" v-if="store">
  <card>
    Stores are used when you want to have any website or payment
    system that you like to receive payments on your behalf. For more
    information about the checkout system and how to create payment
    integrations, check the <a href="https://docs.hub20.io"
    target="_blank">documentation</a> site.
  </card>

  <fg-input v-if="store.id" label="Store ID" :value="store.id" addon-right-icon="ti-files" disabled />

  <fg-input
    :errorMessage="validationErrors.name"
    label="Name"
    placeholder="Store Name"
    v-model="name"
    required
    />

  <fg-input
    label="URL"
    placeholder="Store URL"
    v-model="siteUrl"
    :errorMessage="validationErrors.siteUrl"
    required />

  <fg-select
    label="Accepted Tokens"
    v-model="acceptedTokens"
    :options="tokenOptions"
    :errorMessage="validationErrors.acceptedTokens"
    multiple
    />

  <fg-input v-if="store.public_key" label="Public Key" :value="store.public_key" addon-right-icon="ti-files" disabled/>

  <p-button block @click.native="save(store)" :disabled="!isValid">Save</p-button>
</div>
</template>
<script>
import {mapGetters, mapMutations, mapActions} from 'vuex'

export default {
  data() {
    return {
      validationErrors: {}
    }
  },
  watch: {
    name() {
      if (!this.name.trim()) {
        this.$set(this.validationErrors, 'name', 'Store Name can not be empty')
      }
      else {
        this.$set(this.validationErrors, 'name', null)
      }
    },
    siteUrl() {
      if (!this.siteUrl.trim()) {
        this.$set(this.validationErrors, 'siteUrl', 'Store must have a valid URL')
      }
      else {
        this.$set(this.validationErrors, 'siteUrl', null)
      }
    },
    acceptedTokens() {
      if (!this.acceptedTokens.length) {
        this.$set(this.validationErrors, 'acceptedTokens', 'Stores must use at least one token')
      }
      else {
        this.$set(this.validationErrors, 'acceptedTokens', null)
      }
    },
  },
  computed: {
    ...mapGetters('stores', {store: 'storeEditData', stores: 'storesById', submissionErrors: 'storeEditError'}),
    ...mapGetters('tokens', {tokenMap: 'tokensByAddress'}),
    isValid() {
      return Object.values(this.validationErrors).every(attr => !attr)
    },
    tokenOptions() {
      return Object.values(this.tokenMap).map((token) => {
        return {
          value: token.address,
          text: token.code,
        }
      })
    },
    name: {
      get() {
        return this.store && this.store.name
      },
      set(value) {
        this.updateName(value.trim())
      }
    },
    acceptedTokens: {
      get() {
        return this.store && this.store.accepted_currencies
      },
      set(value) {
        this.updateAcceptedTokens(value)
      },
    },
    siteUrl: {
      get() {
        return this.store && this.store.site_url
      },
      set(value) {
        return this.updateSiteUrl(value)
      },
    },
  },
  methods: {
    ...mapMutations('stores', {
      updateName: 'STORE_UPDATE_SET_NAME',
      updateSiteUrl: 'STORE_UPDATE_SET_URL',
      updateAcceptedTokens: 'STORE_UPDATE_SET_ACCEPTED_TOKENS',
    }),
    ...mapActions('stores', ['editStore', 'updateStore', 'createStore']),
    save(storeData) {
      const action = storeData.id ? this.updateStore : this.createStore

      action(storeData)
        .then(() => this.$notify({message: `${storeData.name} saved successfully`, type: 'success'}))
        .then(() => this.$router.push({'name': 'stores'}))

    }
  },
  mounted() {
    this.editStore(this.$route.params.id)
  },
}
</script>

<style lang="scss">
#store-detail {
  div.form-group.input-group {
    label {
      display: block;
      width: 100%;
    }
  }
}
</style>
