<template>
  <nav>
    <h2>{{ title }}</h2>
    <ul>
      <li class="nav-item">
        <router-link :to="{name: 'logout'}" class="nav-link">
          <i class="ti-power-off"></i>
          <p>logout</p>
        </router-link>
      </li>
    </ul>
  </nav>
</template>
<script>
export default {
  props: {
    viewTitle: String
  },
  computed: {
    title() {
      return (this.$route.meta && this.$route.meta.viewTitle) || this.$route.name
    }
  }
}
</script>
