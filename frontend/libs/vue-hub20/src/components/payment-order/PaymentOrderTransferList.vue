<template>
<div class='payment-order-transfers' v-if='transfers.length > 0'>
  <h3>Transfers</h3>
  <span class='info'>
    <slot></slot>
  </span>
  <ul>
    <PaymentOrderTransferListItem
      v-for='transfer in transfers'
      :transfer='transfer'
      :key='transfer.identifier'
      />
  </ul>
</div>
</template>


<script>
import Vue from 'vue'
import {mapGetters} from 'vuex'
import VueMoment from 'vue-moment'

import PaymentOrderTransferListItem from './PaymentOrderTransferListItem'


Vue.use(VueMoment)


export default {
    name: 'PaymentOrderTransferList',
    components: {
        PaymentOrderTransferListItem
    },
    computed: {
        ...mapGetters(['paymentOrder', 'transfers']),
    },
}
</script>
