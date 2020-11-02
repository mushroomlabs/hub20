l<template>
<li v-on:click='selectToken' class='token-selector-item'>
  <span v-if='token' class='token-name'>{{ token.name }}</span>
  <img
    v-if='token'
    :src='getTokenLogo(token)'
    :alt='token.name'
  />
  <TokenExchangeRate v-if="token" :token='token' />

  <Spinner v-if='!token' message='Fetching token information...' />
</li>
</template>


<script>
import {mapState, mapGetters} from 'vuex'

import TokenExchangeRate from './TokenExchangeRate'
import Spinner from './Spinner'

export default {
    name: 'TokenSelectorItem',
    components: {
        TokenExchangeRate, Spinner
    },
    props: {
        token: Object,
    },
    computed: {
        ...mapGetters(['getTokenLogo']),
        ...mapState(['apiRootUrl', 'pricingCurrency'])
    },
    methods: {
        selectToken: function() {
            this.$store.commit('selectToken', this.token)
            this.$store.dispatch('makeCheckout', this.token)
        }
    },
    async mounted() {
        let token_logo_url = await this.$store.dispatch('fetchTokenLogo', this.token)
        this.$store.commit('setTokenLogo', {token: this.token, url: token_logo_url})
    }
}
</script>
