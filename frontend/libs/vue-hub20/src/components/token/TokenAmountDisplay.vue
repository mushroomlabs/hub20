<template>
  <span v-on:click='copyToClipboard' :title='titleCaption' class='token-amount-display'>{{ result }}</span>
</template>

<script>
import mixins from '../mixins'
import Decimal from 'decimal.js-light'

export default {
    name: 'TokenAmountDisplay',
    mixins: [mixins.CopyToClipboardMixin],
    props: {
        token: Object,
        amount: [Number, Decimal],
        maxSignificantDigits: Number,
    },
    computed: {
        titleCaption: function() {
            return this.valueToCopy && this.toolTip ? this.toolTip : ''
        },
        result: function () {
            if (this.amount == 0){
                return 0
            }

            if (!this.token || !this.amount) {
                return 'N/A'
            }

            let digits = this.maxSignificantDigits || this.token.decimals
            let formatter = new Intl.NumberFormat([], {maximumSignificantDigits: digits})
            let formattedAmount = formatter.format(this.amount)
            return `${formattedAmount} ${this.token.code}`
        }
    }
}
</script>
