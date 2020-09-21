<template>
<li @click="hideSidebar" class="nav-item">
  <slot>
    <router-link :to="to" class="nav-link" exact>
      <i v-if="icon" :class="icon"></i>
      <p>{{name}}</p>
    </router-link>
  </slot>
</li>
</template>

<script>
export default {
  name: "sidebar-link",
  props: {
    name: String,
    icon: String,
    to: String
  },
  computed: {
    isActive() {
      return this.to === this.$route.path;
    }
  },
  methods: {
    hideSidebar() {
      if (this.autoClose) {
        this.$sidebar.displaySidebar(false);
      }
    },
  },
};
</script>
<style>
</style>
