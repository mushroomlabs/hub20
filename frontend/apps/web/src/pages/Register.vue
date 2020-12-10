<template>
  <card class="registration-screen" title="Create Account">
    <slot>
      <ServerIndicator>
        Register to an account on
      </ServerIndicator>

      <div v-if="registrationLoading">
        loading...
      </div>
      <form
        v-if="!registrationLoading && !registrationCompleted"
        @submit.prevent="signUp(inputs)"
      >
        <fg-input
          v-model="inputs.username"
          type="text"
          id="username"
          placeholder="username"
          autocomplete="username"
          required
        />
        <fg-input
          v-model="inputs.password1"
          type="password"
          id="password1"
          placeholder="password"
          autocomplete="new-password"
          required
        />
        <fg-input
          v-model="inputs.password2"
          type="password"
          id="password2"
          placeholder="confirm password"
          autocomplete="new-password"
          required
        />
        <fg-input v-model="inputs.email" type="email" id="email" placeholder="email" />
        <input type="submit" hidden />
        <span class="error" v-show="registrationError">
          An error occured while processing your request.
        </span>
      </form>
    </slot>
    <slot name="footer">
      <action-panel v-if="!registrationCompleted">
        <template v-slot:secondary>
          <router-link to="/login">Already have an account?</router-link>
        </template>
        <p-button @click.native="signUp(inputs)">Signup</p-button>
      </action-panel>
      <div v-if="registrationCompleted">
        Registration complete. <router-link to="/login">Return to login page</router-link>
      </div>
    </slot>
  </card>
</template>
<script>
import {mapActions, mapState} from 'vuex'

import ServerIndicator from '@/components/ServerIndicator'

export default {
  components: {
    ServerIndicator
  },
  data() {
    return {
      inputs: {
        username: '',
        password1: '',
        password2: '',
        email: ''
      }
    }
  },
  computed: {
    ...mapState('signup', ['registrationCompleted', 'registrationError', 'registrationLoading'])
  },
  methods: {
    ...mapActions('signup', ['createAccount', 'clearRegistrationStatus']),
    async signUp(inputs) {
      let token = await this.createAccount(inputs)
      this.$store.commit('auth/LOGIN_BEGIN')
      this.$store.commit('auth/SET_TOKEN', token)
      this.$router.push('/')
    }
  },
  beforeRouteLeave(to, from, next) {
    this.clearRegistrationStatus()
    next()
  }
}
</script>
