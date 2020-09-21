<template>
  <div :class="{'nav-open': $sidebar.showSidebar}">
    <notifications></notifications>

    <div class="wrapper">
      <side-bar>
        <template slot="links">
          <sidebar-link to="/" name="Overview" icon="ti-dashboard"/>
          <sidebar-link to="/history" name="History" icon="ti-receipt"/>
          <sidebar-link to="/market" name="Market" icon="ti-pulse"/>
          <sidebar-link to="/exchange" name="Exchange" icon="ti-exchange-vertical"/>
          <sidebar-link to="/stores" name="Stores" icon="ti-credit-card"/>
        </template>
      </side-bar>
      <div class="main-panel">
        <top-navbar></top-navbar>

        <dashboard-content @click.native="toggleSidebar">
        </dashboard-content>

        <action-menu></action-menu>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';

import TopNavbar from "./TopNavbar";
import DashboardContent from "./Content";
import ActionMenu from "@/components/ActionMenu";

export default {
  components: {
    TopNavbar,
    ActionMenu,
    DashboardContent,
  },
  computed: {
    ...mapGetters({
      'notificationCount': 'notifications/count',
      'notificationList': 'notifications/timeline'
    })
  },
  methods: {
    toggleSidebar() {
      if (this.$sidebar.showSidebar) {
        this.$sidebar.displaySidebar(false);
      }
    }
  }

};
</script>

<style lang="scss">
.vue-notifyjs.notifications {
  .alert {
    z-index: 10000;
  }
  .list-move {
    transition: transform 0.3s, opacity 0.4s;
  }
  .list-item {
    display: inline-block;
    margin-right: 10px;
  }
  .list-enter-active {
    transition: transform 0.2s ease-in, opacity 0.4s ease-in;
  }
  .list-leave-active {
    transition: transform 1s ease-out, opacity 0.4s ease-out;
  }

  .list-enter {
    opacity: 0;
    transform: scale(1.1);
  }
  .list-leave-to {
    opacity: 0;
    transform: scale(1.2, 0.7);
  }
}
</style>
