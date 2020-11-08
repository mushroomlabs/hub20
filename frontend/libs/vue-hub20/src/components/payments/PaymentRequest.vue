<template>
  <div class="payment-request">
    <div class="button-bar" v-if="hasMultipleRoutes">
      <button
        type="button"
        v-for="route in paymentRequest.routes"
        :value="route.type"
        :class="{active: route.type == (selectedRoute && selectedRoute.type)}"
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
      :selected="route == selectedRoute"
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
    }
  },
  data(){
    return {
      selectedRoute: this.paymentRequest.routes && this.paymentRequest.routes[0]
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
        blockchain: 'On-Chain',
        raiden: 'Raiden'
      }[route.type]
    },
    selectRoute(route) {
      this.selectedRoute = route
    }
  }
}
</script>
