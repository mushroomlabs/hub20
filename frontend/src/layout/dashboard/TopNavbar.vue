<template>
<nav class="navbar navbar-expand-lg navbar-light">
  <div class="container-fluid">
    <router-link :to="$route.name" class="navbar-brand" >
      {{routeName}}
    </router-link>
    <button class="navbar-toggler navbar-burger"
            type="button"
            @click="toggleSidebar"
            :aria-expanded="$sidebar.showSidebar"
            aria-label="Toggle navigation">
      <i class="ti-menu"></i>
    </button>
    <div class="collapse navbar-collapse">
      <ul class="navbar-nav ml-auto">
        <li class="nav-item">
          <router-link to="logout" class="nav-link">
            <i class="ti-power-off"></i>
            <p>
              logout
            </p>
          </router-link>
        </li>
      </ul>
    </div>
  </div>
</nav>
</template>
<script>
import { mapGetters } from 'vuex';

export default {
  computed: {
    routeName() {
      const { name } = this.$route;
      return this.capitalizeFirstLetter(name);
    }, ...mapGetters({
      notificationCount: 'notifications/count',
      notificationTimeline: 'notifications/timeline'
    })
  },
  methods: {
    capitalizeFirstLetter(string) {
      return string.charAt(0).toUpperCase() + string.slice(1);
    },
    toggleSidebar() {
      this.$sidebar.displaySidebar(!this.$sidebar.showSidebar);
    },
    hideSidebar() {
      this.$sidebar.displaySidebar(false);
    },
    addNotification(message) {
      this.$store.commit("notifications/ADD_NOTIFICATION", message);
    }
  }
};
</script>
<style>
</style>
