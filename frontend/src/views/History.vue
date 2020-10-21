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
          <td class="description">{{ transaction.summary }}</td>
          <td class="amount">{{ transaction.amount }}</td>
        </tr>
      </tbody>
    </table>
  </card>
</div>
</template>

<script>
import {mapGetters} from "vuex";

export default {
  name: "history",
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
