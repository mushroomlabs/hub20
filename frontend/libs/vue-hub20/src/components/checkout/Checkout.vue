<template>
  <div id='hub20-checkout'>
    <Spinner v-if='!store' message='Connecting to store...' />
    <Spinner v-if='store && selectedToken && !paymentOrder' message='Creating Payment Order...' />
    <TokenSelector v-if='store && !paymentOrder'/>
    <PaymentOrder v-if='store && paymentOrder && !isPaid && !isCanceled' />
    <CheckoutReceipt v-if='store && paymentOrder && (isPaid || isCanceled)'/>
  </div>
</template>

<script>
import {mapState, mapGetters} from 'vuex'

import CheckoutReceipt from './CheckoutReceipt'
import TokenSelector from './TokenSelector'
import PaymentOrder from './PaymentOrder'
import Spinner from './Spinner'


export default {
    name: 'checkout',
    components: {
        CheckoutReceipt, TokenSelector, PaymentOrder, Spinner
    },
    props: {
        settings: Object
    },
    data() {
        return {
            exchangeRatePolling: null
        }
    },
    computed: {
        ...mapGetters(['paymentOrder', 'isPaid', 'isCanceled']),
        ...mapState(['store', 'selectedToken'])
    },
    created() {
        this.$store.commit('setup', this.$props.settings)
        this.$store.dispatch('getStore')
        this.exchangeRatePolling = setInterval(() => {
            this.$store.dispatch('pollExchangeRates')
        }, 30000)
    }
}
</script>
