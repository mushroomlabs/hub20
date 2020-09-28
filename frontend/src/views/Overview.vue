<template>
  <div id="overview">
    <ul class="token-balances">
      <li v-for="balance in openBalances" :key="balance.address">
        <token-balance-card :tokenBalance="balance"/>
      </li>
    </ul>
  </div>
</template>
<script>
import {mapGetters} from "vuex";
import TokenBalanceCard from "@/components/TokenBalanceCard";

export default {
  name: "overview",
  components: {
    TokenBalanceCard
  },
  computed: {...mapGetters("account", ["openBalances"])}
}
</script>
<style lang="scss">
@import '../../node_modules/bootstrap/scss/bootstrap.scss';

#overview {
    @include make-container();

    ul.token-balances {
        @include make-row();

        list-style-type: none;
        list-style-position: inside;
        padding-inline-start: 0;

        li {
            @include make-col(3, 12);
            padding-right: 1rem;
        }
    }
}
</style>
