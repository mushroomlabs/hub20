<template>
  <div class="form-group" :class="{'input-group': hasIcon}">
    <slot name="label">
      <label v-if="label" class="control-label">
        {{ label }}
      </label>
    </slot>
    <slot name="addonLeft">
      <span v-if="addonLeftIcon" class="input-group-prepend">
        <i :class="addonLeftIcon" class="input-group-text"></i>
      </span>
    </slot>
    <select
      class="form-control"
      aria-describedby="addon-right addon-left"
      :multiple="multiple"
      v-model="selected"
      >
      <option
        v-for="option in options"
        :key="option.value"
        :value="option.value"
        :selected="Boolean(option && selected) && selected.indexOf(option.value) != -1"
      >
        {{ option.text }}
      </option>
    </select>
    <slot></slot>
    <slot name="addonRight">
      <span v-if="addonRightIcon" class="input-group-append">
        <i :class="addonRightIcon" class="input-group-text"></i>
      </span>
    </slot>
    <span v-if="errorMessage" class="error-message">{{ errorMessage }}</span>
  </div>
</template>
<script>
export default {
  inheritAttrs: false,
  name: 'fg-select',
  model: {
    prop: 'selected',
    event: 'change',
  },
  props: {
    label: String,
    addonRightIcon: String,
    addonLeftIcon: String,
    options: Array,
    errorMessage: String,
    multiple: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      selected: this.$attrs.selected
    }
  },
  watch: {
    selected(newValue) {
      this.$emit("change", newValue)
    },
  },
  computed: {
    hasIcon() {
      const {addonRight, addonLeft} = this.$slots
      return (
        addonRight !== undefined ||
        addonLeft !== undefined ||
        this.addonRightIcon !== undefined ||
        this.addonLeftIcon !== undefined
      )
    },
  },
}
</script>
