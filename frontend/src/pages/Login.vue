<template>
   <form class="login" @submit.prevent="login">
     <h1>Sign in</h1>
     <label>Username</label>
     <input id="username" v-model="username" placeholder="Username" required/>
     <label>Password</label>
     <input id="password" v-model="password" type="password" placeholder="Password" required/>
     <hr/>
     <button @click="login(username, password)">Login</button>
   </form>
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
<style>
</style>
