<template>
<div class="payment-route">
  <QrCode :address="route.address" v-bind="$attrs" />
</div>
</template>

<script>
import QrCode from './QrCode'

export default {
  components: {
    QrCode
  },
  props: {
    route: {
      type: Object
    }
  }
}
</script>
