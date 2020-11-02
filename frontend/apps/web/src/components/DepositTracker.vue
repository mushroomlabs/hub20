<template>
<card title="Deposit">
  <fg-input type="number" label="Amount" v-model="amount" required />
  <fg-select label="Token" v-model="token" :options="tokenOptions" />
</card>
</template>
<script>
import {mapGetters} from "vuex"
import TokenMixin from "@/mixins/tokens.js"

export default {
  mixins: [TokenMixin],
  data() {
    return {
      amount: 0,
      token: "ETH"
    }
  },
  computed: {
    ...mapGetters("funding", ["deposits"]),
    ...mapGetters("tokens", ["tokensByAddress", "tokensByCode"]),
  },
}
</script>

<style lang="scss">
</style>
B
