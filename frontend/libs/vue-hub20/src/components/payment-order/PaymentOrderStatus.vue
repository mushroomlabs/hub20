<template>
  <div class='payment-order-status'>
    <PaymentOrderTransferList v-if='transfers'>
      The following transfers are processed but are not sufficient to pay the total due
    </PaymentOrderTransferList>
  </div>
</template>


<script>
import Vue from 'vue'
import {mapGetters} from 'vuex'
import VueMoment from 'vue-moment'

import PaymentOrderTransferList from './PaymentOrderTransferList.vue'

Vue.use(VueMoment)


export default {
    name: 'PaymentOrderStatus',
    components: {
        PaymentOrderTransferList
    },
    computed: {
        ...mapGetters(['paymentOrder', 'transfers']),
    },
}
</script>
