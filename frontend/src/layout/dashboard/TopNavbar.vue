<template>
<nav>
  <h2>{{ routeName }}</h2>
  <ul>
    <li class="nav-item">
      <router-link :to="{'name': 'logout'}" class="nav-link">
        <i class="ti-power-off"></i>
        <p>logout</p>
      </router-link>
    </li>
  </ul>
</nav>
</template>
<script>
import { mapGetters } from 'vuex';

export default {
    computed: {
        routeName() {
            return this.$route.name;
        },
        ...mapGetters({
            notificationCount: 'notifications/count',
            notificationTimeline: 'notifications/timeline'
        })
    },
    methods: {
        addNotification(message) {
            this.$store.commit("notifications/ADD_NOTIFICATION", message);
        }
    }
};
</script>
