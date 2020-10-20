<template>
<tr>
  <td class="name">{{ store.name }}</td>
  <td class="url">{{ store.site_url }}</td>
  <td class="identifier">{{ store.id }}</td>
  <td class="actions">
    <router-link :to="{'name': 'store', 'params': {'id': store.id} }">Edit</router-link>
    <p-button name="remove" @click.native="promptRemoval(store)">Remove</p-button>
  </td>
</tr>
</template>
<script>
import {mapActions, mapGetters} from "vuex";

export default {
  props: {
    store: {
      type: Object
    }
  },
  computed: {
    ...mapGetters("tokens", ["tokensByAddress"]),
  },
  methods: {
    ...mapActions("stores", ["removeStore"]),
    getToken(tokenAddress) {
      return this.tokensByAddress[tokenAddress]
    },
    promptRemoval(store) {
      if (confirm(`Are you sure you want to remove ${store.name}?`)){
        this.removeStore(store)
          .then(() => this.$notify({message: `${store.name} removed`, type: 'info'}))
      }
    },
    async copyPublicKey(event) {

      let result = await navigator.permissions.query({name: "clipboard-write"});

      if (result.state == "granted" || result.state == "prompt") {
        let publicKey = event.target.textContent;
        navigator.clipboard.writeText(publicKey)
      }
      else {
        let range = document.createRange();
        range.selectNode(event.target);
        window.getSelection().addRange(range);
        try {
          document.execCommand("copy");
        }
        catch(err) {
          console.log("No clipboard for you!");
          console.log(err);
        }
      }
    }
  }
}
</script>
<style lang="scss">
@import '../assets/sass/app.scss';

td {
    text-align: center;
    &.actions {
      text-align: right;
      align-items: space-around;

      > * {
        display: inline-block;
        margin: 0.25vh 1em;
      }

      a {
        @include button($info-color, $info-states-color, $font-size: $font-size-small)
      }

      button[name=remove] {
        @include button($danger-color, $danger-states-color, $font-size: $font-size-small)
      }
    }
}
</style>
