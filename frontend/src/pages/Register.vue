<template>
  <div id="register-view">
    <template v-if="registrationLoading">
      loading...
    </template>
    <template v-else-if="!registrationCompleted">
      <form @submit.prevent="submit">
        <h1>Create Account</h1>
        <input v-model="inputs.username" type="text" id="username" placeholder="username">
        <input v-model="inputs.password1" type="password" id="password1" placeholder="password">
        <input v-model="inputs.password2" type="password" id="password2"
          placeholder="confirm password">
        <input v-model="inputs.email" type="email" id="email" placeholder="email">
      </form>
      <button @click="createAccount(inputs)">
        Signup
      </button>
      <span class="error" v-show="registrationError">
        An error occured while processing your request.
      </span>
      <div>
        Already have an account?
        <router-link to="/login">login</router-link> |
      </div>
    </template>
    <template v-else>
      <div>
        Registration complete. <router-link to="/login">Return to login page</router-link>
      </div>
    </template>
  </div>
</template>
<script>
import { mapActions, mapState } from 'vuex';
export default {
  data() {
    return {
      inputs: {
        username: '',
        password1: '',
        password2: '',
        email: '',
      },
    };
  },
  computed: mapState('signup', [
    'registrationCompleted',
    'registrationError',
    'registrationLoading',
  ]),
  methods: mapActions('signup', [
    'createAccount',
    'clearRegistrationStatus',
  ]),
  beforeRouteLeave(to, from, next) {
    this.clearRegistrationStatus();
    next();
  },
};
</script>
<style>
</style>
