<template>
<div class='checkout-receipt'>
  <slot>Payment Completed!</slot>
</div>
</template>

<script>
import {mapGetters, mapActions} from 'vuex'

export default {
    name: 'CheckoutReceipt',
    computed: {
        ...mapGetters(['paymentOrder']),
        ...mapActions(['handleCheckoutFinished'])
    },
    mounted() {
        this.handleCheckoutFinished()
    }
}
</script>
