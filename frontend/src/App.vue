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

<style lang="scss">
@import "./assets/sass/paper/_variables.scss";

html {
    background: url("./assets/img/backgrounds/ethereum.jpg") no-repeat center center fixed;
    -webkit-background-size: cover;
    -moz-background-size: cover;
    -o-background-size: cover;
    background-size: cover;
}

body {
    background-color: rgba($medium-pale-bg, 0.75) !important;
    backdrop-filter: brightness(1.75) blur(3px) opacity(0.2);
}
</style>
