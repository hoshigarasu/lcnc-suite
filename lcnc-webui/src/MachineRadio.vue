<script setup lang="ts">
import { computed } from 'vue';
import { usePermissions } from './permissions';
import { INPUT_DEFS, type InputType } from './machineControls';

defineOptions({ inheritAttrs: false });

const props = defineProps<{
  gate: InputType;
  disabled?: boolean;
  name: string;
  value: string | number;
}>();

const model = defineModel<string | number>();
const can = usePermissions();
const def = computed(() => INPUT_DEFS[props.gate]);
const isDisabled = computed(() => !can.value[def.value.gate] || props.disabled);
</script>

<template>
  <input v-bind="$attrs" type="radio" v-model="model" :disabled="isDisabled" :name="name" :value="value">
</template>
