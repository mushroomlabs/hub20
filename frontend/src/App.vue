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
  },
  mounted() {
    let self = this;
    let refreshStore = function() {
      if (self.isAuthenticated){
        self.$store.dispatch("tokens/fetchTokens")
          .then(() => self.$store.dispatch("account/fetchAll"))
          .then(() => self.$store.dispatch("stores/fetchStores"))
      }
    }

    self.$store.dispatch("stores/initialize")
      .then(() => refreshStore());
    setInterval(refreshStore, 60 * 1000);
  }
}
</script>

<style lang="scss">
@import "./assets/sass/app.scss";
</style>
