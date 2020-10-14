<template>
<tr>
  <td class="name">{{ store.name }}</td>
  <td class="url">{{ store.site_url }}</td>
  <td class="identifier">{{ store.id }}</td>
  <td class="actions">
    <router-link :to="{'name': 'store', 'params': {'id': store.id} }">Edit</router-link>
  </td>
</tr>
</template>
<script>
import {mapGetters} from "vuex";

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
    getToken(tokenAddress) {
      return this.tokensByAddress[tokenAddress]
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
@import "../assets/sass/paper/_variables";
@import "../assets/sass/paper/mixins/_buttons";


td {
    text-align: center;

    &.public-key {
        button {
            @include button-outline(
                $default-color,
                $default-states-color,
                $padding-small-vertical,
                $padding-small-horizontal,
                $font-size-large
            );
        }
        span {
            display: inline-block;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: pre-wrap;
        }
    }

    &.token {
        span {
            display: block;
            font-size: $font-size-base;
            padding: $padding-small-vertical $padding-small-horizontal;
        }
    }
}
</style>
