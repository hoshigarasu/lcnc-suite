<script setup lang="ts">
import { computed } from 'vue';
import { usePermissions } from './permissions';
import { INPUT_DEFS, type InputType } from './machineControls';

defineOptions({ inheritAttrs: false });

const props = defineProps<{
  gate: InputType;
  disabled?: boolean;
  label?: string;
}>();

const model = defineModel<boolean>();
const can = usePermissions();
const def = computed(() => INPUT_DEFS[props.gate]);
const isDisabled = computed(() => !can.value[def.value.gate] || props.disabled);
</script>

<template>
  <label class="toggleRow">
    <input v-bind="$attrs" type="checkbox" class="toggle" v-model="model" :disabled="isDisabled">
    {{ label }}
  </label>
</template>
