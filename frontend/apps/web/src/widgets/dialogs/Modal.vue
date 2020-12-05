<template>
  <div
    role="dialog"
    :aria-labelledby="label"
    :aria-hidden="hidden"
    :class="{fade: fade, show: !hidden, scrollable: scrollable}"
  >
    <div class="modal-dialog">
      <div class="header">
        <h4 :id="label">{{ title }}</h4>
        <button type="button" @click="close()" :aria-hidden="hidden">&times;</button>
      </div>
      <div class="content">
        <slot></slot>
      </div>
      <div class="footer">
        <slot name="footer"></slot>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    id: {
      type: String,
      default: 'modal'
    },
    label: {
      type: String,
      default: 'label'
    },
    title: {
      type: String,
      default: ''
    },
    scrollable: {
      type: Boolean,
      default: false
    },
    fade: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      hidden: false
    }
  },
  methods: {
    close() {
      this.$emit('modalClosed')
    },
    open() {
      this.$emit('modalOpened')
    }
  }
}
</script>

<style lang="scss">
@use "@/assets/sass/paper/mixins/_modals.scss" as modals;
@use "@/assets/sass/paper/mixins/_close.scss";

div[role='dialog'] {
  @include modals.modal-container();
  padding-top: 60px;

  div.modal-dialog {
    &.fade {
      @include modals.modal-fade();
    }

    &.show {
      @include modals.modal-show();
    }

    @include modals.modal-content();

    > .header {
      @include modals.modal-header();

      button {
        @include close.close-button();
        background-color: transparent;
        border: none;
      }

      h4 {
        @include modals.modal-title();
        margin: auto;
      }
    }
  }
}
</style>
