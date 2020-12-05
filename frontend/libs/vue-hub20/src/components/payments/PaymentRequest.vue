<template>
<div class="payment-request">
    <div class="button-bar" v-if="hasMultipleRoutes">
      <button
        type="button"
        v-for="route in openRoutes"
        :value="route.type"
        :class="{active: !hasMultipleRoutes || (route.type == (selectedRoute && selectedRoute.type))}"
        @click="selectRoute(route)"
        :key="route.type"
      >
        {{ routeDisplayName(route) }}
      </button>
    </div>

    <PaymentRoute
      v-for="route in openRoutes"
      :route="route"
      :token="token"
      :amount="paymentRequest.amount"
      :key="route.type"
      :selected="!hasMultipleRoutes || (route == selectedRoute)"
    />
    <PaymentTracker :paymentRequest="paymentRequest" />
  </div>
</template>

<script>
import {mapGetters} from 'vuex'

import PaymentRoute from './PaymentRoute'
import PaymentTracker from './PaymentTracker'

import TokenMixin from '../../mixins/tokens'


export default {
  mixins: [TokenMixin],
  components: {
    PaymentRoute,
    PaymentTracker
  },
  props: {
    paymentRequest: {
      type: Object
    }
  },
  data(){
    return {
      selectedRoute: null
    }
  },
  computed: {
    ...mapGetters('server', ['currentBlock']),
    hasMultipleRoutes() {
      return this.openRoutes.length > 1
    },
    token() {
      return this.getToken(this.paymentRequest.token)
    },
    openRoutes() {
      return this.paymentRequest ? this.paymentRequest.routes.filter(route => this.isOpenRoute(route)) : []
    }
  },
  methods: {
    routeDisplayName(route) {
      return {
        blockchain: 'On-Chain',
        raiden: 'Raiden'
      }[route.type]
    },
    selectRoute(route) {
      this.selectedRoute = route
    },
    isOpenRoute(route) {
      if (route.type == 'blockchain'){
        return this.currentBlock <= route.expiration_block
      }
      return true
    }
  },
  mounted() {
    this.selectRoute(this.openRoutes.length >= 1 ? this.openRoutes[0] : null)
  }
}
</script>
