<template>
  <div>
    <p-button outline round>
      Send
    </p-button>
    <p-button outline round>
      Request
    </p-button>
  </div>
</template>
<script>
  import {Button} from '@/components'

export default {
  components: {
    [Button.name]: Button
  }
};
</script>
<style>
</style>
