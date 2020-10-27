<template>
  <div id="dashboard">
    <side-bar>
      <template slot="links">
        <sidebar-link to="/" name="Overview" icon="ti-dashboard" />
        <sidebar-link to="/history" name="History" icon="ti-receipt" />
        <sidebar-link to="/funding" name="Funding" icon="ti-exchange-vertical" />
        <sidebar-link to="/stores" name="Stores" icon="ti-credit-card" />
      </template>
    </side-bar>
    <div class="main-panel">
      <top-navbar />
      <dashboard-content v-if="isReady" />
    </div>
  </div>
</template>

<script>
import {mapGetters} from 'vuex'

import TopNavbar from './TopNavbar'
import DashboardContent from './Content'

export default {
  components: {
    TopNavbar,
    DashboardContent,
  },
  computed: {
    ...mapGetters({
      isReady: 'isReady',
    }),
  },
}
</script>
