<template>
<tr>
  <td class="name">{{ store.name }}</td>
  <td class="url">{{ store.site_url }}</td>
  <td class="identifier">{{ store.id }}</td>
  <td class="actions">
    <router-link :to="{'name': 'store', 'params': {'id': store.id} }">Edit</router-link>
    <button class="destructive-action" name="remove" @click="promptRemoval(store)">Remove</button>
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
