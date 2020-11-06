<template>
<div class="payment-tracker">
  <div v-if="paymentRequest.amount" class="amount">
    <span class="amount-paid">Paid: </span>
    <span class="amount-paid-value">{{ paidAmount }}</span>

    <span class="amount-total">Total:</span>
    <span class="amount-total-value">{{ amount }}</span>
  </div>
</div>
</template>

<script>
  export default {
   props: {
     paymentRequest: {
       type: Object
     },
   },
   computed:{
     paidAmount() {
       return this.amount
     }
   }
 }
</script>
