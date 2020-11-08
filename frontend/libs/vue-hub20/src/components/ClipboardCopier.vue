<template>
  <span class="clipboard-copier">
    <slot>{{ value }}</slot>
  </span>
</template>

<script>
export default {
  props: {
    value: [String, Number]
  }
}
</script>
