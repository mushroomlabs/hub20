<template>
  <card id="store-detail" v-if="store" :title="cardTitle">
    <fg-input
      v-if="store.id"
      label="Store ID"
      :value="store.id"
      addon-right-icon="ti-files"
      disabled
    />

    <fg-input
      :errorMessage="validationErrors.name"
      placeholder='"My Shopify Integration" or "Acme, Inc"'
      label="Name"
      v-model="name"
      required
    />

    <fg-input
      label="URL"
      placeholder="https://acme.example.com"
      v-model="siteUrl"
      :errorMessage="validationErrors.siteUrl"
      required
    />

    <fg-select
      label="Accepted Tokens"
      helpMessage="Check all tokens this store will accept as payment"
      v-model="acceptedTokens"
      :options="tokenOptions"
      :errorMessage="validationErrors.acceptedTokens"
      multiple
    />

    <fg-input
      v-if="store.public_key"
      label="Public Key"
      :value="store.public_key"
      addon-right-icon="ti-files"
      disabled
    />

    <p-button block @click.native="save(store)" :disabled="!isValid">Save</p-button>
  </card>
</template>
<script>
import {mapGetters, mapMutations, mapActions} from 'vuex'

export default {
  data() {
    return {
      validationErrors: {},
    }
  },
  watch: {
    name() {
      if (!this.name.trim()) {
        this.$set(this.validationErrors, 'name', 'Store Name can not be empty')
      } else {
        this.$set(this.validationErrors, 'name', null)
      }
    },
    siteUrl() {
      if (!this.siteUrl.trim()) {
        this.$set(this.validationErrors, 'siteUrl', 'Store must have a valid URL')
      } else {
        this.$set(this.validationErrors, 'siteUrl', null)
      }
    },
    acceptedTokens() {
      if (!this.acceptedTokens.length) {
        this.$set(this.validationErrors, 'acceptedTokens', 'Stores must use at least one token')
      } else {
        this.$set(this.validationErrors, 'acceptedTokens', null)
      }
    },
  },
  computed: {
    ...mapGetters('stores', {
      store: 'storeEditData',
      stores: 'storesById',
      submissionErrors: 'storeEditError',
    }),
    ...mapGetters('tokens', {tokenMap: 'tokensByAddress'}),
    isNew() {
      return this.$route.name == 'store-create'
    },
    cardTitle() {
      return this.isNew ? 'Create new Store' : `Edit Store ${this.store.name}`
    },
    isValid() {
      return Object.values(this.validationErrors).every((attr) => !attr)
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
      },
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
      updateName: 'STORE_EDIT_SET_NAME',
      updateSiteUrl: 'STORE_EDIT_SET_URL',
      updateAcceptedTokens: 'STORE_EDIT_SET_ACCEPTED_TOKENS',
    }),
    ...mapActions('stores', ['editStore', 'updateStore', 'createStore']),
    save(storeData) {
      const action = this.isNew ? this.createStore : this.updateStore

      action(storeData)
        .then(() =>
          this.$notify({message: `${storeData.name} saved successfully`, type: 'success'})
        )
        .then(() => this.$router.push({name: 'stores'}))
    },
  },
  mounted() {
    const storeId = this.isNew ? null : this.$route.params.id
    this.editStore(storeId).then(() => (this.validationErrors = {}))
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
