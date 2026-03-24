<script setup lang="ts">
defineProps<{ allow: boolean }>();
</script>

<template>
  <fieldset :disabled="!allow" class="fs-reset">
    <legend v-if="$slots.exempt" class="gate-exempt">
      <slot name="exempt" />
    </legend>
    <slot />
  </fieldset>
</template>

<style scoped>
.gate-exempt {
  float: none;
  padding: 0;
  width: auto;
}
</style>
