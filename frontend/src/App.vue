<template>
  <div>
    <router-view v-if="isAuthenticated" />
    <BaseLayout v-if="!isAuthenticated" />
  </div>
</template>

<script>
import BaseLayout from "@/layout/BaseLayout";

export default {
  components: {
    BaseLayout
  },
  computed: {
    isAuthenticated() {
      return this.$store.getters["auth/isAuthenticated"];
    }
  }
}
</script>
