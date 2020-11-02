<template>
  <div class='payment-order-action-panel'>
    <button v-if='checkout' v-on:click='reset' class="secondary-action">
      Back
    </button>
  </div>
</template>

<script>
import {mapState} from 'vuex'

export default {
    name: 'PaymentOrderActionPanel',
    computed: {
        ...mapState(['checkout'])
    },
    methods: {
        reset: function() {
            this.$store.dispatch('reset')
        }
    }
}
</script>
