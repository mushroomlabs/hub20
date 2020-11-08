<template>
  <div class="payment-request">
    <div class="button-bar" v-if="hasMultipleRoutes">
      <button
        type="button"
        v-for="route in paymentRequest.routes"
        :value="route.type"
        :class="{active: route.type == (selectedRoute && selectedroute.type)}"
        @click="selectRoute(route)"
        :key="route.type"
      >
        {{ routeDisplayName(route) }}
      </button>
    </div>

    <PaymentRoute
      v-for="route in paymentRequest.routes"
      :route="route"
      :token="token"
      :amount="paymentRequest.amount"
      :key="route.type"
    />
    <PaymentTracker :paymentRequest="paymentRequest" />
  </div>
</template>

<script>
import mixins from '../../mixins'

import PaymentRoute from './PaymentRoute'
import PaymentTracker from './PaymentTracker'

export default {
  mixins: [mixins.TokenMixin],
  components: {
    PaymentRoute,
    PaymentTracker
  },
  props: {
    paymentRequest: {
      type: Object
    },
    selectedRoute: {
      type: Object,
      default: null
    }
  },
  computed: {
    hasMultipleRoutes() {
      return this.paymentRequest.routes.length > 1
    },
    token() {
      return this.getToken(this.paymentRequest.token)
    }
  },
  methods: {
    routeDisplayName(route) {
      return {
        internal: 'From hub20 account',
        blockchain: 'Ethereum On-Chain',
        raiden: 'Raiden Payment Network'
      }[route.type]
    },
    selectRoute(route) {
      this.selectedRoute = route
    }
  }
}
</script>
