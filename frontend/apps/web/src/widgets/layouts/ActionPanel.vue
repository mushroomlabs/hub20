<template>
  <component
    :is="tag"
    class="action-panel"
    >
    <div class="secondary">
      <slot name="secondary">
      </slot>
    </div>
    <div class="primary">
      <slot>
      </slot>
    </div>
  </component>
</template>

<script>
export default {
  name: "action-panel",
  props: {
    tag: {
      type: String,
      default: "div"
    }
  }
}
</script>
