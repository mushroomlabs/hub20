<template>
<li :class='transfer.status'>
  <TokenAmountDisplay :token='transfer.token' :amount='transfer.amount'/>
  <span class="identifier">{{ transfer.identifier }}</span>
</li>
</template>

<script>
import {mapGetters} from 'vuex'

import TokenAmountDisplay from './TokenAmountDisplay.vue'

export default {
    name: 'PaymentOrderTransferListItem',
    components: {
        TokenAmountDisplay
    },
    props: {
        transfer: Object
    },
    computed: {
        ...mapGetters(['paymentOrder']),
    },
}
</script>
