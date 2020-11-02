<template>
<card class="login-screen" title="Sign in">
  <slot>
    <form @submit.prevent="login(username, password)">
    <fg-input v-model="username"
              id="username"
              placeholder="Username"
              autocomplete="username"
              required
              />
    <fg-input v-model="password"
              id="password"
              type="password"
              placeholder="Password"
              autocomplete="current-password"
              required
              />
    <input type="submit" hidden />
    </form>
  </slot>
  <slot name="footer">
    <action-panel>
      <template v-slot:secondary>
        <router-link to="register">Not registered?</router-link>
      </template>
      <p-button type="submit" @click.native="login(username, password)">Login</p-button>
    </action-panel>
  </slot>
</card>
</template>

<script>
export default {
  name: "login",
  data(){
    return {
      username: "",
      password: ""
    }
  },
  methods: {
    login (username, password) {
      this.$store.dispatch('auth/login', { username, password })
        .then(() => this.$router.push('/'))
        .catch(err => console.error(err))
    }
  }
}
</script>
