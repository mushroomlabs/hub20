<template>
<div class="payment-tracker">
  <div v-if="paymentRequest.amount" class="amount-total">
    <span>Requested Amount: </span>
    <span class="amount-value">{{ paymentRequest.amount | formattedAmount(paymentRequest.token)  }}</span>
  </div>

  <div v-if="paymentRequest.amount" class="amount-due">
    <span>Pending amount Amount: </span>
    <span class="amount-value">{{ amountDue | formattedAmount(paymentRequest.token) }}</span>
  </div>

  <div class="payments">
    <h5 v-if="hasPayments">Received Payments</h5>
    <ul v-if="hasPayments">
      <li :class="{'confirmed': payment.confirmed }" v-for="payment in payments" :key="payment.id">
        <span class="amount-value">{{ payment.amount | formattedAmount(payment.currency) }}</span>
        <span class="identifier" :title="payment.identifier">{{ payment.identifier }}</span>
      </li>
    </ul>
    <span v-if="!hasPayments">Received payments will be listed here...</span>
  </div>
</div>
</template>

<script>
import mixins from '../../mixins'

export default {
  mixins: [mixins.TokenMixin],
  props: {
    paymentRequest: {
       type: Object
     },
   },
   computed:{
     payments() {
       return this.paymentRequest.payments
     },
     hasPayments() {
       return this.payments.length > 0
     },
     amountPaid() {
       return 1
     },
     amountDue() {
       return 2
     },
     amountConfirmed() {
       return 0.5
     }
   }
 }
</script>
