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
  computed: {
    title() {
      return this.$route.name
    }
  }
}
</script>
