<template>
  <div class="wrapper">
    <side-bar>
      <template slot="links">
        <sidebar-link to="/overview" name="Overview" icon="ti-dashboard"/>
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
</template>
<style lang="scss">
</style>
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
      'notificationList': 'notifications/'
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
