<template>
<card class="login-screen" title="Sign in">
  <slot>
    <form class="login" @submit.prevent="login">
      <fg-input id="username" v-model="username" placeholder="Username" required/>
      <fg-input id="password" v-model="password" type="password" placeholder="Password" required/>
    </form>
  </slot>
  <slot name="footer">
    <action-panel>
      <template v-slot:secondary>
        <router-link to="register">Not registered?</router-link>
      </template>
      <p-button @click.native="login(username, password)">Login</p-button>
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
      password : ""
    }
  },
  methods: {
    login: function () {
      let username = this.username
      let password = this.password
      this.$store.dispatch('auth/login', { username, password })
        .then(() => this.$router.push('/'))
        .catch(err => console.log(err))
    }
  }
}
</script>

<style lang="scss">
@import "../assets/sass/paper/_variables.scss";

div.login-screen {
    background-color: rgba($medium-pale-bg, 0.75) !important;
    display: grid;
    min-height: 100vh;
    padding: 5vh 3em;
    align-content: center;
}
</style>
