<template>
<formGroupSelect
  :label="label"
  :options="tokenOptions"
 />
</template>
<script>

import {mapGetters} from "vuex"
import formGroupSelect from "@/widgets/forms/formGroupSelect"

export default {
  props: {
    label: {
      type: String,
      default: "Token"
    },
    addonRightIcon: String,
    addonLeftIcon: String,
    errorMessage: String,
    multiple: {
      type: Boolean,
      default: false
    },
  },
  components: {
    formGroupSelect
  },
  computed: {
    ...mapGetters("tokens", ["tokensByAddress"]),
    tokenOptions() {
      return Object.values(this.tokensByAddress).map((token) => ({
        value: token.address,
        text: token.code,
      }))
    }
  }
}
</script>
