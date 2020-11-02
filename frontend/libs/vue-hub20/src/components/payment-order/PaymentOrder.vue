<template>
<div class='payment-order' v-if='paymentOrder'>
  <h1>
    Payment to <span class='store'>{{ store.name }}</span>
  </h1>
  <PaymentOrderStatus/>
  <PaymentOrderDetails/>
  <PaymentOrderRouting/>
  <PaymentOrderActionPanel v-if='showActionPanel'/>
</div>
</template>

<script>
import {mapState, mapGetters} from 'vuex'

import PaymentOrderActionPanel from './PaymentOrderActionPanel.vue'
import PaymentOrderDetails from './PaymentOrderDetails.vue'
import PaymentOrderRouting from './PaymentOrderRouting.vue'
import PaymentOrderStatus from './PaymentOrderStatus.vue'


 export default {
     name: 'PaymentOrder',
     components: {
         PaymentOrderActionPanel,
         PaymentOrderDetails,
         PaymentOrderRouting,
         PaymentOrderStatus
     },
     props: {
         showActionPanel: {
             type: Boolean,
             default: false
         }
     },
     computed:{
         ...mapGetters(['paymentOrder']),
         ...mapState(['store'])
     }
 }
</script>
