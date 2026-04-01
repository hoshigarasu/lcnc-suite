<script setup lang="ts">
import { computed } from "vue";
import Gate from "./Gate.vue";
import MachineBtn from "./MachineBtn.vue";
import { Lock, LockOpen, TriangleAlert, Power } from "lucide-vue-next";

const props = defineProps<{
  armed: boolean;
  busy: boolean;
  isEstop: boolean;
  isEnabled: boolean;
  isHomed: boolean;
  canEstop: boolean;
  canResetEstop: boolean;
}>();

const emit = defineEmits<{
  (e: "arm", value: boolean): void;
  (e: "estop"): void;
  (e: "estopReset"): void;
  (e: "machineOn"): void;
  (e: "machineOff"): void;
}>();

const estopLabel = computed(() => props.isEstop ? "Reset" : "E-Stop");
</script>

<template>
  <div class="safetyStrip">
    <Gate gate="always" class="safetyGate">
      <MachineBtn
        type="arm"
        :variant="armed ? 'ok' : 'default'"
        :disabled="busy"
        :title="armed ? 'Disarm' : 'Arm'"
        @click="emit('arm', !armed)"
        block
      >
        <component :is="armed ? LockOpen : Lock" class="safetyIcon" />
      </MachineBtn>

      <div class="safetySep"></div>

      <MachineBtn
        type="estop"
        :flashing="isEstop"
        :disabled="!(isEstop ? canResetEstop : canEstop)"
        @click="isEstop ? emit('estopReset') : emit('estop')"
        block
      >
        <TriangleAlert class="safetyIcon" />
        <span class="safetyLabel">{{ estopLabel }}</span>
      </MachineBtn>

      <div class="safetySep"></div>
    </Gate>

    <Gate gate="safety" class="safetyGate">
      <MachineBtn
        type="machineOn"
        :variant="isEnabled ? 'ok' : 'default'"
        @click="isEnabled ? emit('machineOff') : emit('machineOn')"
        block
      >
        <Power class="safetyIcon" />
        <span class="safetyLabel">{{ isEnabled ? "On" : "Off" }}</span>
      </MachineBtn>
    </Gate>

    <div class="stripStatus">
      <span class="statusDot" :class="{ on: !isEstop }" title="E-Stop clear"></span>
      <span class="statusDot" :class="{ on: isEnabled }" title="Machine enabled"></span>
      <span class="statusDot" :class="{ on: isHomed }" title="All homed"></span>
    </div>
  </div>
</template>

<style scoped>
.safetyStrip {
  display: flex;
  flex-direction: column;
  gap: var(--gap-controls);
  align-items: stretch;
  width: 120px;
  flex-shrink: 0;
}
.safetyGate {
  display: flex;
  flex-direction: column;
  gap: var(--gap-controls);
}
.safetySep {
  height: 1px;
  background: var(--border);
}
.safetyIcon {
  width: 20px;
  height: 20px;
}
.safetyLabel {
  font-size: var(--fs-sm);
}
.stripStatus {
  display: flex;
  gap: var(--gap-controls);
  justify-content: center;
  padding-top: var(--gap-tight);
  border-top: 1px solid var(--border);
}
.statusDot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-pill);
  background: var(--danger);
}
.statusDot.on {
  background: var(--ok);
}
</style>
