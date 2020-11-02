<template>
<div role="dialog" :aria-labelledby="label" aria-hidden="{{ hidden }}">
  <div class="modal-dialog">
    <div class="header">
      <button type="button" class="close" aria-hidden="{{ hidden }}">&times;</button>
      <h4 class="modal-title" id="{{ label }}">{{ title }}</h4>
    </div>
    <div class="content">
      <slot>
      </slot>
    </div>
    <div class="footer">
      <slot name="footer">
      </slot>
    </div>
  </div>
</div>
</template>

<script>
export default {
  props: {
    id: {
      type: String,
      default: "modal"
    },
    label: {
      type: String,
      default: "label"
    },
    title: {
      type: String,
      default: ""
    },
    dismissMessage: {
      type: String,
      default: "Dismiss"
    },
    actionMessage: {
      type: String,
    },
    hidden: {
      type: Boolean,
      default: true
    }
  }
}
</script>
