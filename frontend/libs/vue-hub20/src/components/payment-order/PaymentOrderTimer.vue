<template>
<div class='payment-order-timer'>
  <span class='time-remaining-display'>Time Remaining: {{ timeRemainingFormatted }}</span>
  <progress-bar
    v-if='!isExpired'
    name='time-remaining-progress-bar'
    :val='timeRemainingPercentage'
    :class='timeRemainingStatus'
    />
  </div>
</template>


<script>
import Vue from 'vue'
import {mapState, mapGetters} from 'vuex'
import VueMoment from 'vue-moment'
import ProgressBar from 'vue-simple-progress'

Vue.use(VueMoment)


export default {
    name: 'PaymentOrderTimer',
    components: {
        ProgressBar
    },
    data() {
        return {
            now: null
        }
    },
    computed: {
        isExpired: function() {
            let time_info = this.$store.getters.paymentOrderTimerStatus(this.now)
            return time_info && time_info.isExpired || false
        },
        timeRemainingFormatted: function() {
            let time_info = this.$store.getters.paymentOrderTimerStatus(this.now)
            let remaining = time_info && time_info.timeRemaining
            return this.$moment.utc(remaining).format('mm:ss') || ''
        },
        timeRemainingPercentage: function() {
            let time_info = this.$store.getters.paymentOrderTimerStatus(this.now)
            return time_info && time_info.timeRemainingPercentage || 100
        },
        timeRemainingStatus: function() {
            let percentage = this.timeRemainingPercentage
            if (percentage >= 25) {
                return 'ok'
            }
            else if (percentage <= 10) {
                return 'critical'
            }
            return 'warning'
        },
        ...mapGetters(['paymentOrder', 'paymentOrderTimerStatus', 'paymentRouting']),
        ...mapState(['checkout'])
    },
    async mounted() {
        let self = this
        this.now = new Date()
        setInterval(() => {
            self.now = new Date()
            self.$forceUpdate()
        }, 1000)
    }
}
</script>
