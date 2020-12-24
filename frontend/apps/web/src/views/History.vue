<template>
<div id="history">
  <card title="Transactions">
    <table class="table">
      <thead>
        <th class="transaction-date">Date</th>
        <th class="description">Description</th>
        <th class="token">Token</th>
      </thead>
      <tbody>
        <tr v-for="transaction in transactions" :class="transaction.type" :key="transaction.reference">
          <td class="transaction-date">{{ new Date(transaction.created).toLocaleString() }}</td>
          <td class="description">{{ transaction.reference_type | humanize(transaction.type) }}</td>
          <td class="amount">{{ transaction.amount }}</td>
        </tr>
      </tbody>
    </table>
  </card>
</div>
</template>

<script>
import {mapGetters} from "vuex";

import {filters as hub20filters} from 'vue-hub20'

export default {
  name: "history",
  filters: {
    humanize: hub20filters.humanizeReference
  },
  computed: {
    ...mapGetters("account", ["transactions"])
  }
}
</script>

<style lang="scss">
@import '../../node_modules/bootstrap/scss/bootstrap.scss';

#history {
    @include make-container();

    table {
        tbody {

            tr.debit {
                td.amount {
                    &:before {
                        content: "- ";
                    }
                    color: red;
                }
            }
            tr.credit {
                td.amount {
                    color: green;
                }
            }
        }
    }
}
</style>
