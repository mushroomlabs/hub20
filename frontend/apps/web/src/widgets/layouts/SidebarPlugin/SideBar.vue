<template>
  <div class="sidebar">
    <router-link to="/" class="logo" exact>
      <img src="@/assets/img/logos/ethereum.svg">
      <span>{{title}}</span>
    </router-link>
    <slot></slot>
    <ul class="nav">
      <slot name="links">
      </slot>
    </ul>
    <moving-arrow :move-y="arrowMovePx">

    </moving-arrow>
  </div>
</template>
<script>
import MovingArrow from "./MovingArrow";

export default {
  props: {
    title: {
      type: String,
      default: "Hub20"
    },
    autoClose: {
      type: Boolean,
      default: true
    }
  },
  provide() {
    return {
      autoClose: this.autoClose
    };
  },
  components: {
    MovingArrow,
  },
  computed: {
    /**
     * Styles to animate the arrow near the current active sidebar link
     * @returns {{transform: string}}
     */
    links() {
      return this.$children.filter(component => { return component.$options.name === "sidebar-link" });
    },
    arrowMovePx() {
      return this.linkHeight * this.activeLinkIndex;
    }
  },
  data() {
    return {
      linkHeight: 65,
      activeLinkIndex: 0,
      windowWidth: 0,
      isWindows: false,
      hasAutoHeight: false,
    };
  },
  methods: {
    findActiveLink() {
      this.links.forEach((link, index) => {
        if (link.isActive) {
          this.activeLinkIndex = index;
        }
      });
    }
  },
  mounted() {
    this.$watch("$route", this.findActiveLink, {
      immediate: true
    });
  }
};
</script>
